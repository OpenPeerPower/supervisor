"""Const for plugins."""
from pathlib import Path

from ..const import SUPERVISOR_DATA

FILE_OPPIO_AUDIO = Path(SUPERVISOR_DATA, "audio.json")
FILE_OPPIO_CLI = Path(SUPERVISOR_DATA, "cli.json")
FILE_OPPIO_DNS = Path(SUPERVISOR_DATA, "dns.json")
FILE_OPPIO_OBSERVER = Path(SUPERVISOR_DATA, "observer.json")
FILE_OPPIO_MULTICAST = Path(SUPERVISOR_DATA, "multicast.json")
