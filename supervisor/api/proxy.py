"""Utils for Open Peer Power Proxy."""
import asyncio
from contextlib import asynccontextmanager
import logging

import aiohttp
from aiohttp import web
from aiohttp.client_exceptions import ClientConnectorError
from aiohttp.hdrs import AUTHORIZATION, CONTENT_TYPE
from aiohttp.web_exceptions import HTTPBadGateway, HTTPUnauthorized

from ..coresys import CoreSysAttributes
from ..exceptions import APIError, OpenPeerPowerAPIError, OpenPeerPowerAuthError

_LOGGER: logging.Logger = logging.getLogger(__name__)


FORWARD_HEADERS = ("X-Speech-Content",)
HEADER_HA_ACCESS = "X-Ha-Access"


class APIProxy(CoreSysAttributes):
    """API Proxy for Open Peer Power."""

    def _check_access(self, request: web.Request):
        """Check the Supervisor token."""
        if AUTHORIZATION in request.headers:
            bearer = request.headers[AUTHORIZATION]
            supervisor_token = bearer.split(" ")[-1]
        else:
            supervisor_token = request.headers.get(HEADER_HA_ACCESS)

        addon = self.sys_addons.from_token(supervisor_token)
        if not addon:
            _LOGGER.warning("Unknown Open Peer Power API access!")
        elif not addon.access_openpeerpower_api:
            _LOGGER.warning("Not permitted API access: %s", addon.slug)
        else:
            _LOGGER.debug("%s access from %s", request.path, addon.slug)
            return

        raise HTTPUnauthorized()

    @asynccontextmanager
    async def _api_client(self, request: web.Request, path: str, timeout: int = 300):
        """Return a client request with proxy origin for Open Peer Power."""
        try:
            async with self.sys_openpeerpower.api.make_request(
                request.method.lower(),
                f"api/{path}",
                headers={
                    name: value
                    for name, value in request.headers.items()
                    if name in FORWARD_HEADERS
                },
                content_type=request.content_type,
                data=request.content,
                timeout=timeout,
                params=request.query,
            ) as resp:
                yield resp
                return

        except OpenPeerPowerAuthError:
            _LOGGER.error("Authenticate error on API for request %s", path)
        except OpenPeerPowerAPIError:
            _LOGGER.error("Error on API for request %s", path)
        except aiohttp.ClientError as err:
            _LOGGER.error("Client error on API %s request %s", path, err)
        except asyncio.TimeoutError:
            _LOGGER.error("Client timeout error on API request %s", path)

        raise HTTPBadGateway()

    async def stream(self, request: web.Request):
        """Proxy OpenPeerPower EventStream Requests."""
        self._check_access(request)
        if not await self.sys_openpeerpower.api.check_api_state():
            raise HTTPBadGateway()

        _LOGGER.info("Open Peer Power EventStream start")
        async with self._api_client(request, "stream", timeout=None) as client:
            response = web.StreamResponse()
            response.content_type = request.headers.get(CONTENT_TYPE)
            try:
                await response.prepare(request)
                async for data in client.content:
                    await response.write(data)

            except (aiohttp.ClientError, aiohttp.ClientPayloadError):
                pass

            _LOGGER.info("Open Peer Power EventStream close")
            return response

    async def api(self, request: web.Request):
        """Proxy Open Peer Power API Requests."""
        self._check_access(request)
        if not await self.sys_openpeerpower.api.check_api_state():
            raise HTTPBadGateway()

        # Normal request
        path = request.match_info.get("path", "")
        async with self._api_client(request, path) as client:
            data = await client.read()
            return web.Response(
                body=data, status=client.status, content_type=client.content_type
            )

    async def _websocket_client(self):
        """Initialize a WebSocket API connection."""
        url = f"{self.sys_openpeerpower.api_url}/api/websocket"

        try:
            client = await self.sys_websession_ssl.ws_connect(
                url, heartbeat=30, verify_ssl=False
            )

            # Handle authentication
            data = await client.receive_json()

            if data.get("type") == "auth_ok":
                return client

            if data.get("type") != "auth_required":
                # Invalid protocol
                _LOGGER.error(
                    "Got unexpected response from Open Peer Power WebSocket: %s", data
                )
                raise APIError()

            # Auth session
            await self.sys_openpeerpower.api.ensure_access_token()
            await client.send_json(
                {
                    "type": "auth",
                    "access_token": self.sys_openpeerpower.api.access_token,
                }
            )

            data = await client.receive_json()

            if data.get("type") == "auth_ok":
                return client

            # Renew the Token is invalid
            if (
                data.get("type") == "invalid_auth"
                and self.sys_openpeerpower.refresh_token
            ):
                self.sys_openpeerpower.api.access_token = None
                return await self._websocket_client()

            raise OpenPeerPowerAuthError()

        except (RuntimeError, ValueError, TypeError, ClientConnectorError) as err:
            _LOGGER.error("Client error on WebSocket API %s.", err)
        except OpenPeerPowerAuthError:
            _LOGGER.error("Failed authentication to Open Peer Power WebSocket")

        raise APIError()

    async def websocket(self, request: web.Request):
        """Initialize a WebSocket API connection."""
        if not await self.sys_openpeerpower.api.check_api_state():
            raise HTTPBadGateway()
        _LOGGER.info("Open Peer Power WebSocket API request initialize")

        # init server
        server = web.WebSocketResponse(heartbeat=30)
        await server.prepare(request)

        # handle authentication
        try:
            await server.send_json(
                {"type": "auth_required", "ha_version": self.sys_openpeerpower.version}
            )

            # Check API access
            response = await server.receive_json()
            supervisor_token = response.get("api_password") or response.get(
                "access_token"
            )
            addon = self.sys_addons.from_token(supervisor_token)

            if not addon or not addon.access_openpeerpower_api:
                _LOGGER.warning("Unauthorized WebSocket access!")
                await server.send_json(
                    {"type": "auth_invalid", "message": "Invalid access"}
                )
                return server

            _LOGGER.info("WebSocket access from %s", addon.slug)

            await server.send_json(
                {"type": "auth_ok", "ha_version": self.sys_openpeerpower.version}
            )
        except (RuntimeError, ValueError) as err:
            _LOGGER.error("Can't initialize handshake: %s", err)
            return server

        # init connection to opp
        try:
            client = await self._websocket_client()
        except APIError:
            return server

        _LOGGER.info("Open Peer Power WebSocket API request running")
        try:
            client_read = None
            server_read = None
            while not server.closed and not client.closed:
                if not client_read:
                    client_read = self.sys_create_task(client.receive_str())
                if not server_read:
                    server_read = self.sys_create_task(server.receive_str())

                # wait until data need to be processed
                await asyncio.wait(
                    [client_read, server_read], return_when=asyncio.FIRST_COMPLETED
                )

                # server
                if server_read.done() and not client.closed:
                    server_read.exception()
                    await client.send_str(server_read.result())
                    server_read = None

                # client
                if client_read.done() and not server.closed:
                    client_read.exception()
                    await server.send_str(client_read.result())
                    client_read = None

        except asyncio.CancelledError:
            pass

        except (RuntimeError, ConnectionError, TypeError) as err:
            _LOGGER.info("Open Peer Power WebSocket API error: %s", err)

        finally:
            if client_read:
                client_read.cancel()
            if server_read:
                server_read.cancel()

            # close connections
            if not client.closed:
                await client.close()
            if not server.closed:
                await server.close()

        _LOGGER.info("Open Peer Power WebSocket API connection is closed")
        return server
