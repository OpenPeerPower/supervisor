"""Open Peer Power control object."""
import asyncio
from contextlib import suppress
import logging
from pathlib import Path
import re
import secrets
import shutil
import time
from typing import Awaitable, Optional

import attr
from awesomeversion import AwesomeVersion, AwesomeVersionException

from ..coresys import CoreSys, CoreSysAttributes
from ..docker.openpeerpower import DockerOpenPeerPower
from ..docker.stats import DockerStats
from ..exceptions import (
    DockerError,
    OpenPeerPowerCrashError,
    OpenPeerPowerError,
    OpenPeerPowerJobError,
    OpenPeerPowerUpdateError,
)
from ..jobs.decorator import Job, JobCondition
from ..resolution.const import ContextType, IssueType
from ..utils import convert_to_ascii, process_lock

_LOGGER: logging.Logger = logging.getLogger(__name__)

RE_YAML_ERROR = re.compile(r"openpeerpower\.util\.yaml")

LANDINGPAGE: AwesomeVersion = AwesomeVersion("landingpage")


@attr.s(frozen=True)
class ConfigResult:
    """Return object from config check."""

    valid = attr.ib()
    log = attr.ib()


class OpenPeerPowerCore(CoreSysAttributes):
    """Open Peer Power core object for handle it."""

    def __init__(self, coresys: CoreSys):
        """Initialize Open Peer Power object."""
        self.coresys: CoreSys = coresys
        self.instance: DockerOpenPeerPower = DockerOpenPeerPower(coresys)
        self.lock: asyncio.Lock = asyncio.Lock()
        self._error_state: bool = False

    @property
    def error_state(self) -> bool:
        """Return True if system is in error."""
        return self._error_state

    async def load(self) -> None:
        """Prepare Open Peer Power object."""
        try:
            # Evaluate Version if we lost this information
            if not self.sys_openpeerpower.version:
                self.sys_openpeerpower.version = (
                    await self.instance.get_latest_version()
                )

            await self.instance.attach(tag=self.sys_openpeerpower.version)
        except DockerError:
            _LOGGER.info(
                "No Open Peer Power Docker image %s found.", self.sys_openpeerpower.image
            )
            await self.install_landingpage()
        else:
            self.sys_openpeerpower.version = self.instance.version
            self.sys_openpeerpower.image = self.instance.image
            self.sys_openpeerpower.save_data()

        # Start landingpage
        if self.instance.version != LANDINGPAGE:
            return

        _LOGGER.info("Starting OpenPeerPower landingpage")
        if not await self.instance.is_running():
            with suppress(OpenPeerPowerError):
                await self._start()

    @process_lock
    async def install_landingpage(self) -> None:
        """Install a landing page."""
        _LOGGER.info("Setting up Open Peer Power landingpage")
        while True:
            if not self.sys_updater.image_openpeerpower:
                _LOGGER.warning(
                    "Found no information about Open Peer Power. Retry in 30sec"
                )
                await asyncio.sleep(30)
                await self.sys_updater.reload()
                continue

            try:
                await self.instance.install(
                    LANDINGPAGE, image=self.sys_updater.image_openpeerpower
                )
            except DockerError:
                _LOGGER.warning("Fails install landingpage, retry after 30sec")
                await asyncio.sleep(30)
            except Exception as err:  # pylint: disable=broad-except
                self.sys_capture_exception(err)
            else:
                self.sys_openpeerpower.version = self.instance.version
                self.sys_openpeerpower.image = self.sys_updater.image_openpeerpower
                self.sys_openpeerpower.save_data()
                break

    @process_lock
    async def install(self) -> None:
        """Install a landing page."""
        _LOGGER.info("Open Peer Power setup")
        while True:
            # read openpeerpower tag and install it
            if not self.sys_openpeerpower.latest_version:
                await self.sys_updater.reload()

            if self.sys_openpeerpower.latest_version:
                try:
                    await self.instance.update(
                        self.sys_openpeerpower.latest_version,
                        image=self.sys_updater.image_openpeerpower,
                    )
                    break
                except DockerError:
                    pass
                except Exception as err:  # pylint: disable=broad-except
                    self.sys_capture_exception(err)

            _LOGGER.warning("Error on Open Peer Power installation. Retry in 30sec")
            await asyncio.sleep(30)

        _LOGGER.info("Open Peer Power docker now installed")
        self.sys_openpeerpower.version = self.instance.version
        self.sys_openpeerpower.image = self.sys_updater.image_openpeerpower
        self.sys_openpeerpower.save_data()

        # finishing
        try:
            _LOGGER.info("Starting Open Peer Power")
            await self._start()
        except OpenPeerPowerError:
            _LOGGER.error("Can't start Open Peer Power!")

        # Cleanup
        with suppress(DockerError):
            await self.instance.cleanup()

    @process_lock
    @Job(
        conditions=[
            JobCondition.FREE_SPACE,
            JobCondition.HEALTHY,
            JobCondition.INTERNET_HOST,
        ],
        on_condition=OpenPeerPowerJobError,
    )
    async def update(self, version: Optional[AwesomeVersion] = None) -> None:
        """Update OpenPeerPower version."""
        version = version or self.sys_openpeerpower.latest_version
        old_image = self.sys_openpeerpower.image
        rollback = self.sys_openpeerpower.version if not self.error_state else None
        running = await self.instance.is_running()
        exists = await self.instance.exists()

        if exists and version == self.instance.version:
            _LOGGER.warning("Version %s is already installed", version)
            return

        # process an update
        async def _update(to_version: AwesomeVersion) -> None:
            """Run Open Peer Power update."""
            _LOGGER.info("Updating Open Peer Power to version %s", to_version)
            try:
                await self.instance.update(
                    to_version, image=self.sys_updater.image_openpeerpower
                )
            except DockerError as err:
                _LOGGER.warning("Updating Open Peer Power image failed")
                raise OpenPeerPowerUpdateError() from err
            else:
                self.sys_openpeerpower.version = self.instance.version
                self.sys_openpeerpower.image = self.sys_updater.image_openpeerpower

            if running:
                await self._start()
            _LOGGER.info("Successful started Open Peer Power %s", to_version)

            # Successfull - last step
            self.sys_openpeerpower.save_data()
            with suppress(DockerError):
                await self.instance.cleanup(old_image=old_image)

        # Update Open Peer Power
        with suppress(OpenPeerPowerError):
            await _update(version)
            return

        # Update going wrong, revert it
        if self.error_state and rollback:
            _LOGGER.critical("OpenPeerPower update failed -> rollback!")
            self.sys_resolution.create_issue(
                IssueType.UPDATE_ROLLBACK, ContextType.CORE
            )

            # Make a copy of the current log file if it exsist
            logfile = self.sys_config.path_openpeerpower / "openpeerpower.log"
            if logfile.exists():
                backup = (
                    self.sys_config.path_openpeerpower / "openpeerpower-rollback.log"
                )

                shutil.copy(logfile, backup)
                _LOGGER.info(
                    "A backup of the logfile is stored in /config/openpeerpower-rollback.log"
                )
            await _update(rollback)
        else:
            self.sys_resolution.create_issue(IssueType.UPDATE_FAILED, ContextType.CORE)
            raise OpenPeerPowerUpdateError()

    async def _start(self) -> None:
        """Start Open Peer Power Docker & wait."""
        # Create new API token
        self.sys_openpeerpower.supervisor_token = secrets.token_hex(56)
        self.sys_openpeerpower.save_data()

        # Write audio settings
        self.sys_openpeerpower.write_pulse()

        try:
            await self.instance.run()
        except DockerError as err:
            raise OpenPeerPowerError() from err

        await self._block_till_run(self.sys_openpeerpower.version)

    @process_lock
    async def start(self) -> None:
        """Run Open Peer Power docker."""
        if await self.instance.is_running():
            _LOGGER.warning("Open Peer Power is already running!")
            return

        # Instance/Container exists, simple start
        if await self.instance.is_initialize():
            try:
                await self.instance.start()
            except DockerError as err:
                raise OpenPeerPowerError() from err

            await self._block_till_run(self.sys_openpeerpower.version)
        # No Instance/Container found, extended start
        else:
            await self._start()

    @process_lock
    async def stop(self) -> None:
        """Stop Open Peer Power Docker.

        Return a coroutine.
        """
        try:
            return await self.instance.stop(remove_container=False)
        except DockerError as err:
            raise OpenPeerPowerError() from err

    @process_lock
    async def restart(self) -> None:
        """Restart Open Peer Power Docker."""
        try:
            await self.instance.restart()
        except DockerError as err:
            raise OpenPeerPowerError() from err

        await self._block_till_run(self.sys_openpeerpower.version)

    @process_lock
    async def rebuild(self) -> None:
        """Rebuild Open Peer Power Docker container."""
        with suppress(DockerError):
            await self.instance.stop()
        await self._start()

    def logs(self) -> Awaitable[bytes]:
        """Get OpenPeerPower docker logs.

        Return a coroutine.
        """
        return self.instance.logs()

    async def stats(self) -> DockerStats:
        """Return stats of Open Peer Power.

        Return a coroutine.
        """
        try:
            return await self.instance.stats()
        except DockerError as err:
            raise OpenPeerPowerError() from err

    def is_running(self) -> Awaitable[bool]:
        """Return True if Docker container is running.

        Return a coroutine.
        """
        return self.instance.is_running()

    def is_failed(self) -> Awaitable[bool]:
        """Return True if a Docker container is failed state.

        Return a coroutine.
        """
        return self.instance.is_failed()

    @property
    def in_progress(self) -> bool:
        """Return True if a task is in progress."""
        return self.instance.in_progress or self.lock.locked()

    async def check_config(self) -> ConfigResult:
        """Run Open Peer Power config check."""
        result = await self.instance.execute_command(
            "python3 -m openpeerpower -c /config --script check_config"
        )

        # If not valid
        if result.exit_code is None:
            _LOGGER.error("Fatal error on config check!")
            raise OpenPeerPowerError()

        # Convert output
        log = convert_to_ascii(result.output)
        _LOGGER.debug("Result config check: %s", log.strip())

        # Parse output
        if result.exit_code != 0 or RE_YAML_ERROR.search(log):
            _LOGGER.error("Invalid Open Peer Power config found!")
            return ConfigResult(False, log)

        _LOGGER.info("Open Peer Power config is valid")
        return ConfigResult(True, log)

    async def _block_till_run(self, version: AwesomeVersion) -> None:
        """Block until Open-Peer-Power is booting up or startup timeout."""
        # Skip landingpage
        if version == LANDINGPAGE:
            return
        _LOGGER.info("Wait until Open Peer Power is ready")

        # Manage timeouts
        timeout: bool = True
        start_time = time.monotonic()
        with suppress(AwesomeVersionException):
            # Version provide early stage UI
            if version >= AwesomeVersion("0.112.0"):
                _LOGGER.debug("Disable startup timeouts - early UI")
                timeout = False

        # Database migration
        migration_progress = False
        migration_file = Path(self.sys_config.path_openpeerpower, ".migration_progress")

        # PIP installation
        pip_progress = False
        pip_file = Path(self.sys_config.path_openpeerpower, ".pip_progress")

        while True:
            await asyncio.sleep(5)

            # 1: Check if Container is is_running
            if not await self.instance.is_running():
                _LOGGER.error("Open Peer Power has crashed!")
                break

            # 2: Check if API response
            if await self.sys_openpeerpower.api.check_api_state():
                _LOGGER.info("Detect a running Open Peer Power instance")
                self._error_state = False
                return

            # 3: Running DB Migration
            if migration_file.exists():
                if not migration_progress:
                    migration_progress = True
                    _LOGGER.info("Open Peer Power record migration in progress")
                continue
            if migration_progress:
                migration_progress = False  # Reset start time
                start_time = time.monotonic()
                _LOGGER.info("Open Peer Power record migration done")

            # 4: Running PIP installation
            if pip_file.exists():
                if not pip_progress:
                    pip_progress = True
                    _LOGGER.info("Open Peer Power pip installation in progress")
                continue
            if pip_progress:
                pip_progress = False  # Reset start time
                start_time = time.monotonic()
                _LOGGER.info("Open Peer Power pip installation done")

            # 5: Timeout
            if (
                timeout
                and time.monotonic() - start_time > self.sys_openpeerpower.wait_boot
            ):
                _LOGGER.warning("Don't wait anymore on Open Peer Power startup!")
                break

        self._error_state = True
        raise OpenPeerPowerCrashError()

    @Job(
        conditions=[
            JobCondition.FREE_SPACE,
            JobCondition.INTERNET_HOST,
        ]
    )
    async def repair(self):
        """Repair local Open Peer Power data."""
        if await self.instance.exists():
            return

        _LOGGER.info("Repair Open Peer Power %s", self.sys_openpeerpower.version)
        try:
            await self.instance.install(self.sys_openpeerpower.version)
        except DockerError:
            _LOGGER.error("Repairing of Open Peer Power failed")
