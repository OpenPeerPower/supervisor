# Open Peer Power Supervisor

## First private cloud solution for home automation

Open Peer Power (former Opp.io) is a container-based system for managing your
Open Peer Power Core installation and related applications. The system is
controlled via Open Peer Power which communicates with the Supervisor. The
Supervisor provides an API to manage the installation. This includes changing
network settings or installing and updating software.

## Installation

Installation instructions can be found at https://openpeerpower.io/oppio.

## Development

The development of the Supervisor is not difficult but tricky.

- You can use the builder to create your Supervisor: https://github.com/openpeerpower/oppio-builder
- Access a OppOS device or VM and pull your Supervisor.
- Set the developer modus with the CLI tool: `ha supervisor options --channel=dev`
- Tag it as `openpeerpower/xy-oppio-supervisor:latest`
- Restart the service with `systemctl restart oppos-supervisor | journalctl -fu oppos-supervisor`
- Test your changes

For small bugfixes or improvements, make a PR. For significant changes open a RFC first, please. Thanks.

## Release

Follow is the relase circle process:

1. Merge master into dev / make sure version stay on dev
2. Merge dev into master
3. Bump the release on master
4. Create a GitHub Release from master with the right version tag
