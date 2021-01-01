"""Init file for Supervisor Open Peer Power RESTful API."""
import asyncio
import logging
from typing import Any, Awaitable, Dict

from aiohttp import web
import voluptuous as vol

from ..const import (
    ATTR_ARCH,
    ATTR_AUDIO_INPUT,
    ATTR_AUDIO_OUTPUT,
    ATTR_BLK_READ,
    ATTR_BLK_WRITE,
    ATTR_BOOT,
    ATTR_CPU_PERCENT,
    ATTR_IMAGE,
    ATTR_IP_ADDRESS,
    ATTR_MACHINE,
    ATTR_MEMORY_LIMIT,
    ATTR_MEMORY_PERCENT,
    ATTR_MEMORY_USAGE,
    ATTR_NETWORK_RX,
    ATTR_NETWORK_TX,
    ATTR_PORT,
    ATTR_REFRESH_TOKEN,
    ATTR_SSL,
    ATTR_UPDATE_AVAILABLE,
    ATTR_VERSION,
    ATTR_VERSION_LATEST,
    ATTR_WAIT_BOOT,
    ATTR_WATCHDOG,
    CONTENT_TYPE_BINARY,
)
from ..coresys import CoreSysAttributes
from ..exceptions import APIError
from ..validate import docker_image, network_port, version_tag
from .utils import api_process, api_process_raw, api_validate

_LOGGER: logging.Logger = logging.getLogger(__name__)

# pylint: disable=no-value-for-parameter
SCHEMA_OPTIONS = vol.Schema(
    {
        vol.Optional(ATTR_BOOT): vol.Boolean(),
        vol.Optional(ATTR_IMAGE): docker_image,
        vol.Optional(ATTR_PORT): network_port,
        vol.Optional(ATTR_SSL): vol.Boolean(),
        vol.Optional(ATTR_WATCHDOG): vol.Boolean(),
        vol.Optional(ATTR_WAIT_BOOT): vol.All(vol.Coerce(int), vol.Range(min=60)),
        vol.Optional(ATTR_REFRESH_TOKEN): vol.Maybe(vol.Coerce(str)),
        vol.Optional(ATTR_AUDIO_OUTPUT): vol.Maybe(vol.Coerce(str)),
        vol.Optional(ATTR_AUDIO_INPUT): vol.Maybe(vol.Coerce(str)),
    }
)

SCHEMA_VERSION = vol.Schema({vol.Optional(ATTR_VERSION): version_tag})


class APIOpenPeerPower(CoreSysAttributes):
    """Handle RESTful API for Open Peer Power functions."""

    @api_process
    async def info(self, request: web.Request) -> Dict[str, Any]:
        """Return host information."""
        return {
            ATTR_VERSION: self.sys_openpeerpower.version,
            ATTR_VERSION_LATEST: self.sys_openpeerpower.latest_version,
            ATTR_UPDATE_AVAILABLE: self.sys_openpeerpower.need_update,
            ATTR_MACHINE: self.sys_openpeerpower.machine,
            ATTR_IP_ADDRESS: str(self.sys_openpeerpower.ip_address),
            ATTR_ARCH: self.sys_openpeerpower.arch,
            ATTR_IMAGE: self.sys_openpeerpower.image,
            ATTR_BOOT: self.sys_openpeerpower.boot,
            ATTR_PORT: self.sys_openpeerpower.api_port,
            ATTR_SSL: self.sys_openpeerpower.api_ssl,
            ATTR_WATCHDOG: self.sys_openpeerpower.watchdog,
            ATTR_WAIT_BOOT: self.sys_openpeerpower.wait_boot,
            ATTR_AUDIO_INPUT: self.sys_openpeerpower.audio_input,
            ATTR_AUDIO_OUTPUT: self.sys_openpeerpower.audio_output,
            # Remove end of Q3 2020
            "last_version": self.sys_openpeerpower.latest_version,
        }

    @api_process
    async def options(self, request: web.Request) -> None:
        """Set Open Peer Power options."""
        body = await api_validate(SCHEMA_OPTIONS, request)

        if ATTR_IMAGE in body:
            self.sys_openpeerpower.image = body[ATTR_IMAGE]

        if ATTR_BOOT in body:
            self.sys_openpeerpower.boot = body[ATTR_BOOT]

        if ATTR_PORT in body:
            self.sys_openpeerpower.api_port = body[ATTR_PORT]

        if ATTR_SSL in body:
            self.sys_openpeerpower.api_ssl = body[ATTR_SSL]

        if ATTR_WATCHDOG in body:
            self.sys_openpeerpower.watchdog = body[ATTR_WATCHDOG]

        if ATTR_WAIT_BOOT in body:
            self.sys_openpeerpower.wait_boot = body[ATTR_WAIT_BOOT]

        if ATTR_REFRESH_TOKEN in body:
            self.sys_openpeerpower.refresh_token = body[ATTR_REFRESH_TOKEN]

        if ATTR_AUDIO_INPUT in body:
            self.sys_openpeerpower.audio_input = body[ATTR_AUDIO_INPUT]

        if ATTR_AUDIO_OUTPUT in body:
            self.sys_openpeerpower.audio_output = body[ATTR_AUDIO_OUTPUT]

        self.sys_openpeerpower.save_data()

    @api_process
    async def stats(self, request: web.Request) -> Dict[Any, str]:
        """Return resource information."""
        stats = await self.sys_openpeerpower.core.stats()
        if not stats:
            raise APIError("No stats available")

        return {
            ATTR_CPU_PERCENT: stats.cpu_percent,
            ATTR_MEMORY_USAGE: stats.memory_usage,
            ATTR_MEMORY_LIMIT: stats.memory_limit,
            ATTR_MEMORY_PERCENT: stats.memory_percent,
            ATTR_NETWORK_RX: stats.network_rx,
            ATTR_NETWORK_TX: stats.network_tx,
            ATTR_BLK_READ: stats.blk_read,
            ATTR_BLK_WRITE: stats.blk_write,
        }

    @api_process
    async def update(self, request: web.Request) -> None:
        """Update Open Peer Power."""
        body = await api_validate(SCHEMA_VERSION, request)
        version = body.get(ATTR_VERSION, self.sys_openpeerpower.latest_version)

        await asyncio.shield(self.sys_openpeerpower.core.update(version))

    @api_process
    def stop(self, request: web.Request) -> Awaitable[None]:
        """Stop Open Peer Power."""
        return asyncio.shield(self.sys_openpeerpower.core.stop())

    @api_process
    def start(self, request: web.Request) -> Awaitable[None]:
        """Start Open Peer Power."""
        return asyncio.shield(self.sys_openpeerpower.core.start())

    @api_process
    def restart(self, request: web.Request) -> Awaitable[None]:
        """Restart Open Peer Power."""
        return asyncio.shield(self.sys_openpeerpower.core.restart())

    @api_process
    def rebuild(self, request: web.Request) -> Awaitable[None]:
        """Rebuild Open Peer Power."""
        return asyncio.shield(self.sys_openpeerpower.core.rebuild())

    @api_process_raw(CONTENT_TYPE_BINARY)
    def logs(self, request: web.Request) -> Awaitable[bytes]:
        """Return Open Peer Power Docker logs."""
        return self.sys_openpeerpower.core.logs()

    @api_process
    async def check(self, request: web.Request) -> None:
        """Check configuration of Open Peer Power."""
        result = await self.sys_openpeerpower.core.check_config()
        if not result.valid:
            raise APIError(result.log)
