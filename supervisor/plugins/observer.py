"""Open Peer Power observer plugin.

Code: https://github.com/openpeerpower/plugin-observer
"""
import asyncio
from contextlib import suppress
import logging
import secrets
from typing import Awaitable, Optional

import aiohttp
from packaging.version import parse as pkg_parse

from ..const import ATTR_ACCESS_TOKEN, ATTR_IMAGE, ATTR_VERSION
from ..coresys import CoreSys, CoreSysAttributes
from ..docker.observer import DockerObserver
from ..docker.stats import DockerStats
from ..exceptions import DockerError, ObserverError, ObserverUpdateError
from ..utils.json import JsonConfig
from .const import FILE_OPPIO_OBSERVER
from .validate import SCHEMA_OBSERVER_CONFIG

_LOGGER: logging.Logger = logging.getLogger(__name__)


class Observer(CoreSysAttributes, JsonConfig):
    """Supervisor observer instance."""

    slug: str = "observer"

    def __init__(self, coresys: CoreSys):
        """Initialize observer handler."""
        super().__init__(FILE_OPPIO_OBSERVER, SCHEMA_OBSERVER_CONFIG)
        self.coresys: CoreSys = coresys
        self.instance: DockerObserver = DockerObserver(coresys)

    @property
    def version(self) -> Optional[str]:
        """Return version of observer."""
        return self._data.get(ATTR_VERSION)

    @version.setter
    def version(self, value: str) -> None:
        """Set current version of observer."""
        self._data[ATTR_VERSION] = value

    @property
    def image(self) -> str:
        """Return current image of observer."""
        if self._data.get(ATTR_IMAGE):
            return self._data[ATTR_IMAGE]
        return f"openpeerpower/{self.sys_arch.supervisor}-oppio-observer"

    @image.setter
    def image(self, value: str) -> None:
        """Return current image of observer."""
        self._data[ATTR_IMAGE] = value

    @property
    def latest_version(self) -> str:
        """Return version of latest observer."""
        return self.sys_updater.version_observer

    @property
    def need_update(self) -> bool:
        """Return true if a observer update is available."""
        try:
            return pkg_parse(self.version) < pkg_parse(self.latest_version)
        except (TypeError, ValueError):
            return True

    @property
    def supervisor_token(self) -> str:
        """Return an access token for the Observer API."""
        return self._data.get(ATTR_ACCESS_TOKEN)

    @property
    def in_progress(self) -> bool:
        """Return True if a task is in progress."""
        return self.instance.in_progress

    async def load(self) -> None:
        """Load observer setup."""
        # Check observer state
        try:
            # Evaluate Version if we lost this information
            if not self.version:
                self.version = await self.instance.get_latest_version()

            await self.instance.attach(tag=self.version)
        except DockerError:
            _LOGGER.info(
                "No observer plugin Docker image %s found.", self.instance.image
            )

            # Install observer
            with suppress(ObserverError):
                await self.install()
        else:
            self.version = self.instance.version
            self.image = self.instance.image
            self.save_data()

        # Run Observer
        with suppress(ObserverError):
            if not await self.instance.is_running():
                await self.start()

    async def install(self) -> None:
        """Install observer."""
        _LOGGER.info("Running setup for observer plugin")
        while True:
            # read observer tag and install it
            if not self.latest_version:
                await self.sys_updater.reload()

            if self.latest_version:
                with suppress(DockerError):
                    await self.instance.install(
                        self.latest_version, image=self.sys_updater.image_observer
                    )
                    break
            _LOGGER.warning("Error on install observer plugin. Retry in 30sec")
            await asyncio.sleep(30)

        _LOGGER.info("observer plugin now installed")
        self.version = self.instance.version
        self.image = self.sys_updater.image_observer
        self.save_data()

    async def update(self, version: Optional[str] = None) -> None:
        """Update local HA observer."""
        version = version or self.latest_version
        old_image = self.image

        if version == self.version:
            _LOGGER.warning("Version %s is already installed for observer", version)
            return

        try:
            await self.instance.update(version, image=self.sys_updater.image_observer)
        except DockerError as err:
            _LOGGER.error("HA observer update failed")
            raise ObserverUpdateError() from err
        else:
            self.version = version
            self.image = self.sys_updater.image_observer
            self.save_data()

        # Cleanup
        with suppress(DockerError):
            await self.instance.cleanup(old_image=old_image)

        # Start observer
        await self.start()

    async def start(self) -> None:
        """Run observer."""
        # Create new API token
        if not self.supervisor_token:
            self._data[ATTR_ACCESS_TOKEN] = secrets.token_hex(56)
            self.save_data()

        # Start Instance
        _LOGGER.info("Starting observer plugin")
        try:
            await self.instance.run()
        except DockerError as err:
            _LOGGER.error("Can't start observer plugin")
            raise ObserverError() from err

    async def stats(self) -> DockerStats:
        """Return stats of observer."""
        try:
            return await self.instance.stats()
        except DockerError as err:
            raise ObserverError() from err

    def is_running(self) -> Awaitable[bool]:
        """Return True if Docker container is running.

        Return a coroutine.
        """
        return self.instance.is_running()

    async def rebuild(self) -> None:
        """Rebuild Observer Docker container."""
        with suppress(DockerError):
            await self.instance.stop()
        await self.start()

    async def check_system_runtime(self) -> bool:
        """Check if the observer is running."""
        try:
            timeout = aiohttp.ClientTimeout(total=5)
            async with self.sys_websession.get(
                f"http://{self.sys_docker.network.observer!s}/ping", timeout=timeout
            ) as request:
                if request.status == 200:
                    return True
        except (aiohttp.ClientError, asyncio.TimeoutError):
            pass

        return False

    async def repair(self) -> None:
        """Repair observer container."""
        if await self.instance.exists():
            return

        _LOGGER.info("Repairing HA observer %s", self.version)
        try:
            await self.instance.install(self.version)
        except DockerError as err:
            _LOGGER.error("Repair of HA observer failed")
            self.sys_capture_exception(err)