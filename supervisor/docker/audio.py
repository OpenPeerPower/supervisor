"""Audio docker object."""
import logging
from pathlib import Path
from typing import Dict

from ..const import ENV_TIME, MACHINE_ID
from ..coresys import CoreSysAttributes
from .interface import DockerInterface

_LOGGER: logging.Logger = logging.getLogger(__name__)

AUDIO_DOCKER_NAME: str = "oppio_audio"


class DockerAudio(DockerInterface, CoreSysAttributes):
    """Docker Supervisor wrapper for Supervisor Audio."""

    @property
    def image(self) -> str:
        """Return name of Supervisor Audio image."""
        return self.sys_plugins.audio.image

    @property
    def name(self) -> str:
        """Return name of Docker container."""
        return AUDIO_DOCKER_NAME

    @property
    def volumes(self) -> Dict[str, Dict[str, str]]:
        """Return Volumes for the mount."""
        volumes = {
            str(self.sys_config.path_extern_audio): {"bind": "/data", "mode": "rw"},
            "/run/dbus": {"bind": "/run/dbus", "mode": "ro"},
        }

        # Machine ID
        if MACHINE_ID.exists():
            volumes.update({str(MACHINE_ID): {"bind": str(MACHINE_ID), "mode": "ro"}})

        # SND support
        if Path("/dev/snd").exists():
            volumes.update({"/dev/snd": {"bind": "/dev/snd", "mode": "rw"}})
        else:
            _LOGGER.warning("Kernel have no audio support")

        return volumes

    def _run(self) -> None:
        """Run Docker image.

        Need run inside executor.
        """
        if self._is_running():
            return

        # Cleanup
        self._stop()

        # Create & Run container
        docker_container = self.sys_docker.run(
            self.image,
            tag=self.sys_plugins.audio.version.string,
            init=False,
            ipv4=self.sys_docker.network.audio,
            name=self.name,
            hostname=self.name.replace("_", "-"),
            detach=True,
            privileged=True,
            environment={ENV_TIME: self.sys_config.timezone},
            volumes=self.volumes,
        )

        self._meta = docker_container.attrs
        _LOGGER.info(
            "Starting Audio %s with version %s - %s",
            self.image,
            self.version,
            self.sys_docker.network.audio,
        )
