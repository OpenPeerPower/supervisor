"""Snapshot system control."""
import asyncio
import logging
from pathlib import Path
from typing import Set

from ..const import FOLDER_OPENPEERPOWER, SNAPSHOT_FULL, SNAPSHOT_PARTIAL, CoreState
from ..coresys import CoreSysAttributes
from ..exceptions import AddonsError
from ..jobs.decorator import Job, JobCondition
from ..utils.dt import utcnow
from .snapshot import Snapshot
from .utils import create_slug

_LOGGER: logging.Logger = logging.getLogger(__name__)


class SnapshotManager(CoreSysAttributes):
    """Manage snapshots."""

    def __init__(self, coresys):
        """Initialize a snapshot manager."""
        self.coresys = coresys
        self.snapshots_obj = {}
        self.lock = asyncio.Lock()

    @property
    def list_snapshots(self) -> Set[Snapshot]:
        """Return a list of all snapshot object."""
        return set(self.snapshots_obj.values())

    def get(self, slug):
        """Return snapshot object."""
        return self.snapshots_obj.get(slug)

    def _create_snapshot(self, name, sys_type, password):
        """Initialize a new snapshot object from name."""
        date_str = utcnow().isoformat()
        slug = create_slug(name, date_str)
        tar_file = Path(self.sys_config.path_backup, f"{slug}.tar")

        # init object
        snapshot = Snapshot(self.coresys, tar_file)
        snapshot.new(slug, name, date_str, sys_type, password)

        # set general data
        snapshot.store_openpeerpower()
        snapshot.store_repositories()
        snapshot.store_dockerconfig()

        return snapshot

    def load(self):
        """Load exists snapshots data.

        Return a coroutine.
        """
        return self.reload()

    async def reload(self):
        """Load exists backups."""
        self.snapshots_obj = {}

        async def _load_snapshot(tar_file):
            """Load the snapshot."""
            snapshot = Snapshot(self.coresys, tar_file)
            if await snapshot.load():
                self.snapshots_obj[snapshot.slug] = snapshot

        tasks = [
            _load_snapshot(tar_file)
            for tar_file in self.sys_config.path_backup.glob("*.tar")
        ]

        _LOGGER.info("Found %d snapshot files", len(tasks))
        if tasks:
            await asyncio.wait(tasks)

    def remove(self, snapshot):
        """Remove a snapshot."""
        try:
            snapshot.tarfile.unlink()
            self.snapshots_obj.pop(snapshot.slug, None)
            _LOGGER.info("Removed snapshot file %s", snapshot.slug)

        except OSError as err:
            _LOGGER.error("Can't remove snapshot %s: %s", snapshot.slug, err)
            return False

        return True

    async def import_snapshot(self, tar_file):
        """Check snapshot tarfile and import it."""
        snapshot = Snapshot(self.coresys, tar_file)

        # Read meta data
        if not await snapshot.load():
            return None

        # Already exists?
        if snapshot.slug in self.snapshots_obj:
            _LOGGER.warning(
                "Snapshot %s already exists! overwriting snapshot", snapshot.slug
            )
            self.remove(self.get(snapshot.slug))

        # Move snapshot to backup
        tar_origin = Path(self.sys_config.path_backup, f"{snapshot.slug}.tar")
        try:
            snapshot.tarfile.rename(tar_origin)

        except OSError as err:
            _LOGGER.error("Can't move snapshot file to storage: %s", err)
            return None

        # Load new snapshot
        snapshot = Snapshot(self.coresys, tar_origin)
        if not await snapshot.load():
            return None
        _LOGGER.info("Successfully imported %s", snapshot.slug)

        self.snapshots_obj[snapshot.slug] = snapshot
        return snapshot

    @Job(conditions=[JobCondition.FREE_SPACE, JobCondition.RUNNING])
    async def do_snapshot_full(self, name="", password=None):
        """Create a full snapshot."""
        if self.lock.locked():
            _LOGGER.error("A snapshot/restore process is already running")
            return None

        snapshot = self._create_snapshot(name, SNAPSHOT_FULL, password)
        _LOGGER.info("Creating new full-snapshot with slug %s", snapshot.slug)
        try:
            self.sys_core.state = CoreState.FREEZE
            await self.lock.acquire()

            async with snapshot:
                # Snapshot add-ons
                _LOGGER.info("Snapshotting %s store Add-ons", snapshot.slug)
                await snapshot.store_addons()

                # Snapshot folders
                _LOGGER.info("Snapshotting %s store folders", snapshot.slug)
                await snapshot.store_folders()

        except Exception as err:  # pylint: disable=broad-except
            _LOGGER.exception("Snapshot %s error", snapshot.slug)
            self.sys_capture_exception(err)
            return None

        else:
            _LOGGER.info("Creating full-snapshot with slug %s completed", snapshot.slug)
            self.snapshots_obj[snapshot.slug] = snapshot
            return snapshot

        finally:
            self.sys_core.state = CoreState.RUNNING
            self.lock.release()

    @Job(conditions=[JobCondition.FREE_SPACE, JobCondition.RUNNING])
    async def do_snapshot_partial(
        self, name="", addons=None, folders=None, password=None
    ):
        """Create a partial snapshot."""
        if self.lock.locked():
            _LOGGER.error("A snapshot/restore process is already running")
            return None

        addons = addons or []
        folders = folders or []
        snapshot = self._create_snapshot(name, SNAPSHOT_PARTIAL, password)

        _LOGGER.info("Creating new partial-snapshot with slug %s", snapshot.slug)
        try:
            self.sys_core.state = CoreState.FREEZE
            await self.lock.acquire()

            async with snapshot:
                # Snapshot add-ons
                addon_list = []
                for addon_slug in addons:
                    addon = self.sys_addons.get(addon_slug)
                    if addon and addon.is_installed:
                        addon_list.append(addon)
                        continue
                    _LOGGER.warning("Add-on %s not found/installed", addon_slug)

                if addon_list:
                    _LOGGER.info("Snapshotting %s store Add-ons", snapshot.slug)
                    await snapshot.store_addons(addon_list)

                # Snapshot folders
                if folders:
                    _LOGGER.info("Snapshotting %s store folders", snapshot.slug)
                    await snapshot.store_folders(folders)

        except Exception as err:  # pylint: disable=broad-except
            _LOGGER.exception("Snapshot %s error", snapshot.slug)
            self.sys_capture_exception(err)
            return None

        else:
            _LOGGER.info(
                "Creating partial-snapshot with slug %s completed", snapshot.slug
            )
            self.snapshots_obj[snapshot.slug] = snapshot
            return snapshot

        finally:
            self.sys_core.state = CoreState.RUNNING
            self.lock.release()

    @Job(
        conditions=[
            JobCondition.FREE_SPACE,
            JobCondition.HEALTHY,
            JobCondition.INTERNET_HOST,
            JobCondition.INTERNET_SYSTEM,
            JobCondition.RUNNING,
        ]
    )
    async def do_restore_full(self, snapshot, password=None):
        """Restore a snapshot."""
        if self.lock.locked():
            _LOGGER.error("A snapshot/restore process is already running")
            return False

        if snapshot.sys_type != SNAPSHOT_FULL:
            _LOGGER.error("%s is only a partial snapshot!", snapshot.slug)
            return False

        if snapshot.protected and not snapshot.set_password(password):
            _LOGGER.error("Invalid password for snapshot %s", snapshot.slug)
            return False

        _LOGGER.info("Full-Restore %s start", snapshot.slug)
        try:
            self.sys_core.state = CoreState.FREEZE
            await self.lock.acquire()

            async with snapshot:
                # Stop Open-Peer-Power / Add-ons
                await self.sys_core.shutdown()

                # Restore folders
                _LOGGER.info("Restoring %s folders", snapshot.slug)
                await snapshot.restore_folders()

                # Restore docker config
                _LOGGER.info("Restoring %s Docker Config", snapshot.slug)
                snapshot.restore_dockerconfig()

                # Start openpeerpower restore
                _LOGGER.info("Restoring %s Open-Peer-Power", snapshot.slug)
                snapshot.restore_openpeerpower()
                task_opp = self.sys_create_task(
                    self.sys_openpeerpower.core.update(snapshot.openpeerpower_version)
                )

                # Restore repositories
                _LOGGER.info("Restoring %s Repositories", snapshot.slug)
                await snapshot.restore_repositories()

                # Delete delta add-ons
                _LOGGER.info("Removing add-ons not in the snapshot %s", snapshot.slug)
                for addon in self.sys_addons.installed:
                    if addon.slug in snapshot.addon_list:
                        continue

                    # Remove Add-on because it's not a part of the new env
                    # Do it sequential avoid issue on slow IO
                    try:
                        await addon.uninstall()
                    except AddonsError:
                        _LOGGER.warning("Can't uninstall Add-on %s", addon.slug)

                # Restore add-ons
                _LOGGER.info("Restore %s old add-ons", snapshot.slug)
                await snapshot.restore_addons()

                # finish openpeerpower task
                _LOGGER.info("Restore %s wait until openpeerpower ready", snapshot.slug)
                await task_opp
                await self.sys_openpeerpower.core.start()

        except Exception as err:  # pylint: disable=broad-except
            _LOGGER.exception("Restore %s error", snapshot.slug)
            self.sys_capture_exception(err)
            return False

        else:
            _LOGGER.info("Full-Restore %s done", snapshot.slug)
            return True

        finally:
            self.sys_core.state = CoreState.RUNNING
            self.lock.release()

    @Job(
        conditions=[
            JobCondition.FREE_SPACE,
            JobCondition.HEALTHY,
            JobCondition.INTERNET_HOST,
            JobCondition.INTERNET_SYSTEM,
            JobCondition.RUNNING,
        ]
    )
    async def do_restore_partial(
        self, snapshot, openpeerpower=False, addons=None, folders=None, password=None
    ):
        """Restore a snapshot."""
        if self.lock.locked():
            _LOGGER.error("A snapshot/restore process is already running")
            return False

        if snapshot.protected and not snapshot.set_password(password):
            _LOGGER.error("Invalid password for snapshot %s", snapshot.slug)
            return False

        addons = addons or []
        folders = folders or []

        _LOGGER.info("Partial-Restore %s start", snapshot.slug)
        try:
            self.sys_core.state = CoreState.FREEZE
            await self.lock.acquire()

            async with snapshot:
                # Restore docker config
                _LOGGER.info("Restoring %s Docker Config", snapshot.slug)
                snapshot.restore_dockerconfig()

                # Stop Open-Peer-Power for config restore
                if FOLDER_OPENPEERPOWER in folders:
                    await self.sys_openpeerpower.core.stop()
                    snapshot.restore_openpeerpower()

                # Process folders
                if folders:
                    _LOGGER.info("Restoring %s folders", snapshot.slug)
                    await snapshot.restore_folders(folders)

                # Process Open-Peer-Power
                task_opp = None
                if openpeerpower:
                    _LOGGER.info("Restoring %s Open-Peer-Power", snapshot.slug)
                    task_opp = self.sys_create_task(
                        self.sys_openpeerpower.core.update(
                            snapshot.openpeerpower_version
                        )
                    )

                if addons:
                    _LOGGER.info("Restoring %s Repositories", snapshot.slug)
                    await snapshot.restore_repositories()

                    _LOGGER.info("Restoring %s old add-ons", snapshot.slug)
                    await snapshot.restore_addons(addons)

                # Make sure openpeerpower run agen
                if task_opp:
                    _LOGGER.info("Restore %s wait for Open-Peer-Power", snapshot.slug)
                    await task_opp

                # Do we need start OpenPeerPower?
                if not await self.sys_openpeerpower.core.is_running():
                    await self.sys_openpeerpower.core.start()

                # Check If we can access to API / otherwise restart
                if not await self.sys_openpeerpower.api.check_api_state():
                    _LOGGER.warning("Need restart OpenPeerPower for API")
                    await self.sys_openpeerpower.core.restart()

        except Exception as err:  # pylint: disable=broad-except
            _LOGGER.exception("Restore %s error", snapshot.slug)
            self.sys_capture_exception(err)
            return False

        else:
            _LOGGER.info("Partial-Restore %s done", snapshot.slug)
            return True

        finally:
            self.sys_core.state = CoreState.RUNNING
            self.lock.release()
