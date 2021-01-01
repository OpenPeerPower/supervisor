"""OppOS support on supervisor."""
import asyncio
import logging
from pathlib import Path
from typing import Awaitable, Optional

import aiohttp
from awesomeversion import AwesomeVersion, AwesomeVersionException
from cpe import CPE

from .coresys import CoreSys, CoreSysAttributes
from .dbus.rauc import RaucState
from .exceptions import DBusError, OppOSNotSupportedError, OppOSUpdateError
from .utils import process_lock

_LOGGER: logging.Logger = logging.getLogger(__name__)


class OppOS(CoreSysAttributes):
    """OppOS interface inside supervisor."""

    def __init__(self, coresys: CoreSys):
        """Initialize OppOS handler."""
        self.coresys: CoreSys = coresys
        self.lock: asyncio.Lock = asyncio.Lock()
        self._available: bool = False
        self._version: Optional[AwesomeVersion] = None
        self._board: Optional[str] = None

    @property
    def available(self) -> bool:
        """Return True, if OppOS on host."""
        return self._available

    @property
    def version(self) -> Optional[AwesomeVersion]:
        """Return version of OppOS."""
        return self._version

    @property
    def latest_version(self) -> Optional[AwesomeVersion]:
        """Return version of OppOS."""
        return self.sys_updater.version_oppos

    @property
    def need_update(self) -> bool:
        """Return true if a OppOS update is available."""
        try:
            return self.version < self.latest_version
        except (AwesomeVersionException, TypeError):
            return False

    @property
    def board(self) -> Optional[str]:
        """Return board name."""
        return self._board

    def _check_host(self) -> None:
        """Check if OppOS is available."""
        if not self.available:
            _LOGGER.error("No Open Peer Power Operating System available")
            raise OppOSNotSupportedError()

    async def _download_raucb(self, version: AwesomeVersion) -> Path:
        """Download rauc bundle (OTA) from github."""
        raw_url = self.sys_updater.ota_url
        if raw_url is None:
            _LOGGER.error("Don't have an URL for OTA updates!")
            raise OppOSNotSupportedError()
        url = raw_url.format(version=version.string, board=self.board)

        _LOGGER.info("Fetch OTA update from %s", url)
        raucb = Path(self.sys_config.path_tmp, f"oppos-{version.string}.raucb")
        try:
            timeout = aiohttp.ClientTimeout(total=60 * 60, connect=180)
            async with self.sys_websession.get(url, timeout=timeout) as request:
                if request.status != 200:
                    raise OppOSUpdateError()

                # Download RAUCB file
                with raucb.open("wb") as ota_file:
                    while True:
                        chunk = await request.content.read(1_048_576)
                        if not chunk:
                            break
                        ota_file.write(chunk)

            _LOGGER.info("OTA update is downloaded on %s", raucb)
            return raucb

        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            _LOGGER.warning("Can't fetch versions from %s: %s", url, err)

        except OSError as err:
            _LOGGER.error("Can't write OTA file: %s", err)

        raise OppOSUpdateError()

    async def load(self) -> None:
        """Load OppOS data."""
        try:
            if not self.sys_host.info.cpe:
                raise NotImplementedError()

            cpe = CPE(self.sys_host.info.cpe)
            if cpe.get_product()[0] != "oppos":
                raise NotImplementedError()
        except NotImplementedError:
            _LOGGER.info("No Open Peer Power Operating System found")
            return
        else:
            self._available = True
            self.sys_host.supported_features.cache_clear()

        # Store meta data
        self._version = AwesomeVersion(cpe.get_version()[0])
        self._board = cpe.get_target_hardware()[0]

        await self.sys_dbus.rauc.update()

        _LOGGER.info(
            "Detect OppOS %s / BootSlot %s", self.version, self.sys_dbus.rauc.boot_slot
        )

    def config_sync(self) -> Awaitable[None]:
        """Trigger a host config reload from usb.

        Return a coroutine.
        """
        self._check_host()

        _LOGGER.info(
            "Synchronizing configuration from USB with Open Peer Power Operating System."
        )
        return self.sys_host.services.restart("oppos-config.service")

    @process_lock
    async def update(self, version: Optional[AwesomeVersion] = None) -> None:
        """Update OppOS system."""
        version = version or self.latest_version

        # Check installed version
        self._check_host()
        if version == self.version:
            _LOGGER.warning("Version %s is already installed", version)
            raise OppOSUpdateError()

        # Fetch files from internet
        int_ota = await self._download_raucb(version)
        ext_ota = Path(self.sys_config.path_extern_tmp, int_ota.name)

        try:
            await self.sys_dbus.rauc.install(ext_ota)
            completed = await self.sys_dbus.rauc.signal_completed()

        except DBusError as err:
            _LOGGER.error("Rauc communication error")
            raise OppOSUpdateError() from err

        finally:
            int_ota.unlink()

        # Update success
        if 0 in completed:
            _LOGGER.info(
                "Install of Open Peer Power Operating System %s success", version
            )
            self.sys_create_task(self.sys_host.control.reboot())
            return

        # Update failed
        await self.sys_dbus.rauc.update()
        _LOGGER.error(
            "Open Peer Power Operating System update failed with: %s",
            self.sys_dbus.rauc.last_error,
        )
        raise OppOSUpdateError()

    async def mark_healthy(self) -> None:
        """Set booted partition as good for rauc."""
        try:
            response = await self.sys_dbus.rauc.mark(RaucState.GOOD, "booted")
        except DBusError:
            _LOGGER.error("Can't mark booted partition as healty!")
        else:
            _LOGGER.info("Rauc: %s - %s", self.sys_dbus.rauc.boot_slot, response[1])
