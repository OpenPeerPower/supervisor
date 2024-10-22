"""Init file for Supervisor network RESTful API."""
import voluptuous as vol

from ..const import (
    ATTR_ADDON,
    ATTR_CONFIG,
    ATTR_DISCOVERY,
    ATTR_SERVICE,
    ATTR_SERVICES,
    ATTR_UUID,
    REQUEST_FROM,
)
from ..coresys import CoreSysAttributes
from ..discovery.validate import valid_discovery_service
from ..exceptions import APIError, APIForbidden
from .utils import api_process, api_validate

SCHEMA_DISCOVERY = vol.Schema(
    {
        vol.Required(ATTR_SERVICE): valid_discovery_service,
        vol.Optional(ATTR_CONFIG): vol.Maybe(dict),
    }
)


class APIDiscovery(CoreSysAttributes):
    """Handle RESTful API for discovery functions."""

    def _extract_message(self, request):
        """Extract discovery message from URL."""
        message = self.sys_discovery.get(request.match_info.get("uuid"))
        if not message:
            raise APIError("Discovery message not found")
        return message

    def _check_permission_ha(self, request):
        """Check permission for API call / Open Peer Power."""
        if request[REQUEST_FROM] != self.sys_openpeerpower:
            raise APIForbidden("Only OpenPeerPower can use this API!")

    @api_process
    async def list(self, request):
        """Show register services."""
        self._check_permission_ha(request)

        # Get available discovery
        discovery = []
        for message in self.sys_discovery.list_messages:
            discovery.append(
                {
                    ATTR_ADDON: message.addon,
                    ATTR_SERVICE: message.service,
                    ATTR_UUID: message.uuid,
                    ATTR_CONFIG: message.config,
                }
            )

        # Get available services/add-ons
        services = {}
        for addon in self.sys_addons.all:
            for name in addon.discovery:
                services.setdefault(name, []).append(addon.slug)

        return {ATTR_DISCOVERY: discovery, ATTR_SERVICES: services}

    @api_process
    async def set_discovery(self, request):
        """Write data into a discovery pipeline."""
        body = await api_validate(SCHEMA_DISCOVERY, request)
        addon = request[REQUEST_FROM]

        # Access?
        if body[ATTR_SERVICE] not in addon.discovery:
            raise APIForbidden("Can't use discovery!")

        # Process discovery message
        message = self.sys_discovery.send(addon, **body)

        return {ATTR_UUID: message.uuid}

    @api_process
    async def get_discovery(self, request):
        """Read data into a discovery message."""
        message = self._extract_message(request)

        # OpenPeerPower?
        self._check_permission_ha(request)

        return {
            ATTR_ADDON: message.addon,
            ATTR_SERVICE: message.service,
            ATTR_UUID: message.uuid,
            ATTR_CONFIG: message.config,
        }

    @api_process
    async def del_discovery(self, request):
        """Delete data into a discovery message."""
        message = self._extract_message(request)
        addon = request[REQUEST_FROM]

        # Permission
        if message.addon != addon.slug:
            raise APIForbidden("Can't remove discovery message")

        self.sys_discovery.remove(message)
        return True
