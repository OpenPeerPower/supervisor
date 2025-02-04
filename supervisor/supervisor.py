"""Open Peer Power control object."""
import asyncio
from contextlib import suppress
from ipaddress import IPv4Address
import logging
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Awaitable, Optional

import aiohttp
from aiohttp.client_exceptions import ClientError
from awesomeversion import AwesomeVersion, AwesomeVersionException

from supervisor.jobs.decorator import Job, JobCondition

from .const import SUPERVISOR_VERSION, URL_OPPIO_APPARMOR
from .coresys import CoreSys, CoreSysAttributes
from .docker.stats import DockerStats
from .docker.supervisor import DockerSupervisor
from .exceptions import (
    DockerError,
    HostAppArmorError,
    SupervisorError,
    SupervisorJobError,
    SupervisorUpdateError,
)
from .resolution.const import ContextType, IssueType

_LOGGER: logging.Logger = logging.getLogger(__name__)


class Supervisor(CoreSysAttributes):
    """Open Peer Power core object for handle it."""

    def __init__(self, coresys: CoreSys):
        """Initialize opp object."""
        self.coresys: CoreSys = coresys
        self.instance: DockerSupervisor = DockerSupervisor(coresys)
        self._connectivity: bool = True

    async def load(self) -> None:
        """Prepare Open Peer Power object."""
        try:
            await self.instance.attach(version=self.version)
        except DockerError:
            _LOGGER.critical("Can't setup Supervisor Docker container!")

        with suppress(DockerError):
            await self.instance.cleanup()

    @property
    def connectivity(self) -> bool:
        """Return true if we are connected to the internet."""
        return self._connectivity

    @property
    def ip_address(self) -> IPv4Address:
        """Return IP of Supervisor instance."""
        return self.instance.ip_address

    @property
    def need_update(self) -> bool:
        """Return True if an update is available."""
        if self.sys_dev:
            return False

        try:
            return self.version < self.latest_version
        except (AwesomeVersionException, TypeError):
            return False

    @property
    def version(self) -> AwesomeVersion:
        """Return version of running Open Peer Power."""
        return AwesomeVersion(SUPERVISOR_VERSION)

    @property
    def latest_version(self) -> AwesomeVersion:
        """Return last available version of Open Peer Power."""
        return self.sys_updater.version_supervisor

    @property
    def image(self) -> str:
        """Return image name of Open Peer Power container."""
        return self.instance.image

    @property
    def arch(self) -> str:
        """Return arch of the Supervisor container."""
        return self.instance.arch

    async def update_apparmor(self) -> None:
        """Fetch last version and update profile."""
        url = URL_OPPIO_APPARMOR
        try:
            _LOGGER.info("Fetching AppArmor profile %s", url)
            async with self.sys_websession.get(url, timeout=10) as request:
                data = await request.text()

        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            _LOGGER.warning("Can't fetch AppArmor profile: %s", err)
            raise SupervisorError() from err

        with TemporaryDirectory(dir=self.sys_config.path_tmp) as tmp_dir:
            profile_file = Path(tmp_dir, "apparmor.txt")
            try:
                profile_file.write_text(data)
            except OSError as err:
                _LOGGER.error("Can't write temporary profile: %s", err)
                raise SupervisorError() from err

            try:
                await self.sys_host.apparmor.load_profile(
                    "oppio-supervisor", profile_file
                )
            except HostAppArmorError as err:
                _LOGGER.error("Can't update AppArmor profile!")
                raise SupervisorError() from err

    async def update(self, version: Optional[AwesomeVersion] = None) -> None:
        """Update Open Peer Power version."""
        version = version or self.latest_version

        if version == self.sys_supervisor.version:
            _LOGGER.warning("Version %s is already installed", version)
            return

        _LOGGER.info("Update Supervisor to version %s", version)
        try:
            await self.instance.install(
                version, image=self.sys_updater.image_supervisor
            )
            await self.instance.update_start_tag(
                self.sys_updater.image_supervisor, version
            )
        except DockerError as err:
            _LOGGER.error("Update of Supervisor failed!")
            self.sys_resolution.create_issue(
                IssueType.UPDATE_FAILED, ContextType.SUPERVISOR
            )
            self.sys_capture_exception(err)
            raise SupervisorUpdateError() from err
        else:
            self.sys_config.version = version
            self.sys_config.save_data()

        with suppress(SupervisorError):
            await self.update_apparmor()
        self.sys_create_task(self.sys_core.stop())

    @Job(conditions=[JobCondition.RUNNING], on_condition=SupervisorJobError)
    async def restart(self) -> None:
        """Restart Supervisor soft."""
        self.sys_core.exit_code = 100
        self.sys_create_task(self.sys_core.stop())

    @property
    def in_progress(self) -> bool:
        """Return True if a task is in progress."""
        return self.instance.in_progress

    def logs(self) -> Awaitable[bytes]:
        """Get Supervisor docker logs.

        Return Coroutine.
        """
        return self.instance.logs()

    async def stats(self) -> DockerStats:
        """Return stats of Supervisor."""
        try:
            return await self.instance.stats()
        except DockerError as err:
            raise SupervisorError() from err

    async def repair(self):
        """Repair local Supervisor data."""
        if await self.instance.exists():
            return

        _LOGGER.info("Repairing Supervisor %s", self.version)
        try:
            await self.instance.retag()
        except DockerError:
            _LOGGER.error("Repair of Supervisor failed")

    async def check_connectivity(self):
        """Check the connection."""
        timeout = aiohttp.ClientTimeout(total=10)
        try:
            await self.sys_websession.head(
                "https://version.openpeerpower.io/online.txt", timeout=timeout
            )
        except (ClientError, asyncio.TimeoutError):
            self._connectivity = False
        else:
            self._connectivity = True
