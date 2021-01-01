"""Core Exceptions."""


class OppioError(Exception):
    """Root exception."""


class OppioNotSupportedError(OppioError):
    """Function is not supported."""


# JobManager


class JobException(OppioError):
    """Base job exception."""


# OpenPeerPower


class OpenPeerPowerError(OppioError):
    """Open Peer Power exception."""


class OpenPeerPowerUpdateError(OpenPeerPowerError):
    """Error on update of a Open Peer Power."""


class OpenPeerPowerCrashError(OpenPeerPowerError):
    """Error on crash of a Open Peer Power startup."""


class OpenPeerPowerAPIError(OpenPeerPowerError):
    """Open Peer Power API exception."""


class OpenPeerPowerAuthError(OpenPeerPowerAPIError):
    """Open Peer Power Auth API exception."""


class OpenPeerPowerJobError(OpenPeerPowerError, JobException):
    """Raise on Open Peer Power job error."""


# Supervisor


class SupervisorError(OppioError):
    """Supervisor error."""


class SupervisorUpdateError(SupervisorError):
    """Supervisor update error."""


class SupervisorJobError(SupervisorError, JobException):
    """Raise on job errors."""


# OppOS


class OppOSError(OppioError):
    """OppOS exception."""


class OppOSUpdateError(OppOSError):
    """Error on update of a OppOS."""


class OppOSNotSupportedError(OppioNotSupportedError):
    """Function not supported by OppOS."""


# HaCli


class CliError(OppioError):
    """HA cli exception."""


class CliUpdateError(CliError):
    """Error on update of a HA cli."""


# Observer


class ObserverError(OppioError):
    """General Observer exception."""


class ObserverUpdateError(ObserverError):
    """Error on update of a Observer."""


# Multicast


class MulticastError(OppioError):
    """Multicast exception."""


class MulticastUpdateError(MulticastError):
    """Error on update of a multicast."""


# DNS


class CoreDNSError(OppioError):
    """CoreDNS exception."""


class CoreDNSUpdateError(CoreDNSError):
    """Error on update of a CoreDNS."""


# DNS


class AudioError(OppioError):
    """PulseAudio exception."""


class AudioUpdateError(AudioError):
    """Error on update of a Audio."""


# Addons


class AddonsError(OppioError):
    """Addons exception."""


class AddonConfigurationError(AddonsError):
    """Error with add-on configuration."""


class AddonsNotSupportedError(OppioNotSupportedError):
    """Addons don't support a function."""


class AddonsJobError(AddonsError, JobException):
    """Raise on job errors."""


# Arch


class OppioArchNotFound(OppioNotSupportedError):
    """No matches with exists arch."""


# Updater


class UpdaterError(OppioError):
    """Error on Updater."""


class UpdaterJobError(UpdaterError, JobException):
    """Raise on job error."""


# Auth


class AuthError(OppioError):
    """Auth errors."""


class AuthPasswordResetError(OppioError):
    """Auth error if password reset failed."""


# Host


class HostError(OppioError):
    """Internal Host error."""


class HostNotSupportedError(OppioNotSupportedError):
    """Host function is not supprted."""


class HostServiceError(HostError):
    """Host service functions failed."""


class HostAppArmorError(HostError):
    """Host apparmor functions failed."""


class HostNetworkError(HostError):
    """Error with host network."""


class HostNetworkNotFound(HostError):
    """Return if host interface is not found."""


# API


class APIError(OppioError, RuntimeError):
    """API errors."""


class APIForbidden(APIError):
    """API forbidden error."""


# Service / Discovery


class DiscoveryError(OppioError):
    """Discovery Errors."""


class ServicesError(OppioError):
    """Services Errors."""


# utils/gdbus


class DBusError(OppioError):
    """DBus generic error."""


class DBusNotConnectedError(HostNotSupportedError):
    """DBus is not connected and call a method."""


class DBusInterfaceError(OppioNotSupportedError):
    """DBus interface not connected."""


class DBusFatalError(DBusError):
    """DBus call going wrong."""


class DBusParseError(DBusError):
    """DBus parse error."""


class DBusProgramError(DBusError):
    """DBus application error."""


# util/apparmor


class AppArmorError(HostAppArmorError):
    """General AppArmor error."""


class AppArmorFileError(AppArmorError):
    """AppArmor profile file error."""


class AppArmorInvalidError(AppArmorError):
    """AppArmor profile validate error."""


# util/json


class JsonFileError(OppioError):
    """Invalid json file."""


# docker/api


class DockerError(OppioError):
    """Docker API/Transport errors."""


class DockerAPIError(DockerError):
    """Docker API error."""


class DockerRequestError(DockerError):
    """Dockerd OS issues."""


class DockerNotFound(DockerError):
    """Docker object don't Exists."""


# Hardware


class HardwareNotSupportedError(OppioNotSupportedError):
    """Raise if hardware function is not supported."""


# Pulse Audio


class PulseAudioError(OppioError):
    """Raise if an sound error is happening."""


# Resolution


class ResolutionError(OppioError):
    """Raise if an error is happning on resoltuion."""


class ResolutionNotFound(ResolutionError):
    """Raise if suggestion/issue was not found."""


class ResolutionFixupError(OppioError):
    """Rasie if a fixup fails."""


class ResolutionFixupJobError(ResolutionFixupError, JobException):
    """Raise on job error."""


# Store


class StoreError(OppioError):
    """Raise if an error on store is happening."""


class StoreGitError(StoreError):
    """Raise if something on git is happening."""


class StoreNotFound(StoreError):
    """Raise if slug is not known."""


class StoreJobError(StoreError, JobException):
    """Raise on job error with git."""
