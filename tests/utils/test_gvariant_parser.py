"""Test gdbus gvariant parser."""
from supervisor.utils.gdbus import DBus


def test_simple_return():
    """Test Simple return value."""
    raw = "(objectpath '/org/freedesktop/systemd1/job/35383',)"

    # parse data
    data = DBus.parse_gvariant(raw)

    assert data == ["/org/freedesktop/systemd1/job/35383"]


def test_get_property():
    """Test Property parsing."""
    raw = "({'Hostname': <'oppio'>, 'StaticHostname': <'oppio'>, 'PrettyHostname': <''>, 'IconName': <'computer-embedded'>, 'Chassis': <'embedded'>, 'Deployment': <'production'>, 'Location': <''>, 'KernelName': <'Linux'>, 'KernelRelease': <'4.14.98-v7'>, 'KernelVersion': <'#1 SMP Sat May 11 02:17:06 UTC 2019'>, 'OperatingSystemPrettyName': <'OppOS 2.12'>, 'OperatingSystemCPEName': <'cpe:2.3:o:open_peer_power:oppos:2.12:*:production:*:*:*:rpi3:*'>, 'HomeURL': <'https://opp.io/'>},)"

    # parse data
    data = DBus.parse_gvariant(raw)

    assert data[0] == {
        "Hostname": "oppio",
        "StaticHostname": "oppio",
        "PrettyHostname": "",
        "IconName": "computer-embedded",
        "Chassis": "embedded",
        "Deployment": "production",
        "Location": "",
        "KernelName": "Linux",
        "KernelRelease": "4.14.98-v7",
        "KernelVersion": "#1 SMP Sat May 11 02:17:06 UTC 2019",
        "OperatingSystemPrettyName": "OppOS 2.12",
        "OperatingSystemCPEName": "cpe:2.3:o:open_peer_power:oppos:2.12:*:production:*:*:*:rpi3:*",
        "HomeURL": "https://opp.io/",
    }


def test_systemd_unitlist_simple():
    """Test Systemd Unit list simple."""
    raw = "([('systemd-remount-fs.service', 'Remount Root and Kernel File Systems', 'loaded', 'active', 'exited', '', objectpath '/org/freedesktop/systemd1/unit/systemd_2dremount_2dfs_2eservice', uint32 0, '', objectpath '/'), ('sys-subsystem-net-devices-veth5714b4e.device', '/sys/subsystem/net/devices/veth5714b4e', 'loaded', 'active', 'plugged', '', '/org/freedesktop/systemd1/unit/sys_2dsubsystem_2dnet_2ddevices_2dveth5714b4e_2edevice', 0, '', '/'), ('rauc.service', 'Rauc Update Service', 'loaded', 'active', 'running', '', '/org/freedesktop/systemd1/unit/rauc_2eservice', 0, '', '/'), ('mnt-data-docker-overlay2-7493c48dd99ab0e68420e3317d93711630dd55a76d4f2a21863a220031203ac2-merged.mount', '/mnt/data/docker/overlay2/7493c48dd99ab0e68420e3317d93711630dd55a76d4f2a21863a220031203ac2/merged', 'loaded', 'active', 'mounted', '', '/org/freedesktop/systemd1/unit/mnt_2ddata_2ddocker_2doverlay2_2d7493c48dd99ab0e68420e3317d93711630dd55a76d4f2a21863a220031203ac2_2dmerged_2emount', 0, '', '/'), ('oppos-hardware.target', 'OppOS hardware targets', 'loaded', 'active', 'active', '', '/org/freedesktop/systemd1/unit/oppos_2dhardware_2etarget', 0, '', '/'), ('dev-zram1.device', '/dev/zram1', 'loaded', 'active', 'plugged', 'sys-devices-virtual-block-zram1.device', '/org/freedesktop/systemd1/unit/dev_2dzram1_2edevice', 0, '', '/'), ('sys-subsystem-net-devices-oppio.device', '/sys/subsystem/net/devices/oppio', 'loaded', 'active', 'plugged', '', '/org/freedesktop/systemd1/unit/sys_2dsubsystem_2dnet_2ddevices_2doppio_2edevice', 0, '', '/'), ('cryptsetup.target', 'cryptsetup.target', 'not-found', 'inactive', 'dead', '', '/org/freedesktop/systemd1/unit/cryptsetup_2etarget', 0, '', '/'), ('sys-devices-virtual-net-vethd256dfa.device', '/sys/devices/virtual/net/vethd256dfa', 'loaded', 'active', 'plugged', '', '/org/freedesktop/systemd1/unit/sys_2ddevices_2dvirtual_2dnet_2dvethd256dfa_2edevice', 0, '', '/'), ('network-pre.target', 'Network (Pre)', 'loaded', 'inactive', 'dead', '', '/org/freedesktop/systemd1/unit/network_2dpre_2etarget', 0, '', '/'), ('sys-devices-virtual-net-veth5714b4e.device', '/sys/devices/virtual/net/veth5714b4e', 'loaded', 'active', 'plugged', '', '/org/freedesktop/systemd1/unit/sys_2ddevices_2dvirtual_2dnet_2dveth5714b4e_2edevice', 0, '', '/'), ('sys-kernel-debug.mount', 'Kernel Debug File System', 'loaded', 'active', 'mounted', '', '/org/freedesktop/systemd1/unit/sys_2dkernel_2ddebug_2emount', 0, '', '/'), ('slices.target', 'Slices', 'loaded', 'active', 'active', '', '/org/freedesktop/systemd1/unit/slices_2etarget', 0, '', '/'), ('etc-NetworkManager-system\x2dconnections.mount', 'NetworkManager persistent system connections', 'loaded', 'active', 'mounted', '', '/org/freedesktop/systemd1/unit/etc_2dNetworkManager_2dsystem_5cx2dconnections_2emount', 0, '', '/'), ('run-docker-netns-26ede3178729.mount', '/run/docker/netns/26ede3178729', 'loaded', 'active', 'mounted', '', '/org/freedesktop/systemd1/unit/run_2ddocker_2dnetns_2d26ede3178729_2emount', 0, '', '/'), ('dev-disk-by\x2dpath-platform\x2d3f202000.mmc\x2dpart2.device', '/dev/disk/by-path/platform-3f202000.mmc-part2', 'loaded', 'active', 'plugged', 'sys-devices-platform-soc-3f202000.mmc-mmc_host-mmc0-mmc0:e624-block-mmcblk0-mmcblk0p2.device', '/org/freedesktop/systemd1/unit/dev_2ddisk_2dby_5cx2dpath_2dplatform_5cx2d3f202000_2emmc_5cx2dpart2_2edevice', 0, '', '/')],)"

    # parse data
    data = DBus.parse_gvariant(raw)

    assert data == [
        [
            [
                "systemd-remount-fs.service",
                "Remount Root and Kernel File Systems",
                "loaded",
                "active",
                "exited",
                "",
                "/org/freedesktop/systemd1/unit/systemd_2dremount_2dfs_2eservice",
                0,
                "",
                "/",
            ],
            [
                "sys-subsystem-net-devices-veth5714b4e.device",
                "/sys/subsystem/net/devices/veth5714b4e",
                "loaded",
                "active",
                "plugged",
                "",
                "/org/freedesktop/systemd1/unit/sys_2dsubsystem_2dnet_2ddevices_2dveth5714b4e_2edevice",
                0,
                "",
                "/",
            ],
            [
                "rauc.service",
                "Rauc Update Service",
                "loaded",
                "active",
                "running",
                "",
                "/org/freedesktop/systemd1/unit/rauc_2eservice",
                0,
                "",
                "/",
            ],
            [
                "mnt-data-docker-overlay2-7493c48dd99ab0e68420e3317d93711630dd55a76d4f2a21863a220031203ac2-merged.mount",
                "/mnt/data/docker/overlay2/7493c48dd99ab0e68420e3317d93711630dd55a76d4f2a21863a220031203ac2/merged",
                "loaded",
                "active",
                "mounted",
                "",
                "/org/freedesktop/systemd1/unit/mnt_2ddata_2ddocker_2doverlay2_2d7493c48dd99ab0e68420e3317d93711630dd55a76d4f2a21863a220031203ac2_2dmerged_2emount",
                0,
                "",
                "/",
            ],
            [
                "oppos-hardware.target",
                "OppOS hardware targets",
                "loaded",
                "active",
                "active",
                "",
                "/org/freedesktop/systemd1/unit/oppos_2dhardware_2etarget",
                0,
                "",
                "/",
            ],
            [
                "dev-zram1.device",
                "/dev/zram1",
                "loaded",
                "active",
                "plugged",
                "sys-devices-virtual-block-zram1.device",
                "/org/freedesktop/systemd1/unit/dev_2dzram1_2edevice",
                0,
                "",
                "/",
            ],
            [
                "sys-subsystem-net-devices-oppio.device",
                "/sys/subsystem/net/devices/oppio",
                "loaded",
                "active",
                "plugged",
                "",
                "/org/freedesktop/systemd1/unit/sys_2dsubsystem_2dnet_2ddevices_2doppio_2edevice",
                0,
                "",
                "/",
            ],
            [
                "cryptsetup.target",
                "cryptsetup.target",
                "not-found",
                "inactive",
                "dead",
                "",
                "/org/freedesktop/systemd1/unit/cryptsetup_2etarget",
                0,
                "",
                "/",
            ],
            [
                "sys-devices-virtual-net-vethd256dfa.device",
                "/sys/devices/virtual/net/vethd256dfa",
                "loaded",
                "active",
                "plugged",
                "",
                "/org/freedesktop/systemd1/unit/sys_2ddevices_2dvirtual_2dnet_2dvethd256dfa_2edevice",
                0,
                "",
                "/",
            ],
            [
                "network-pre.target",
                "Network (Pre)",
                "loaded",
                "inactive",
                "dead",
                "",
                "/org/freedesktop/systemd1/unit/network_2dpre_2etarget",
                0,
                "",
                "/",
            ],
            [
                "sys-devices-virtual-net-veth5714b4e.device",
                "/sys/devices/virtual/net/veth5714b4e",
                "loaded",
                "active",
                "plugged",
                "",
                "/org/freedesktop/systemd1/unit/sys_2ddevices_2dvirtual_2dnet_2dveth5714b4e_2edevice",
                0,
                "",
                "/",
            ],
            [
                "sys-kernel-debug.mount",
                "Kernel Debug File System",
                "loaded",
                "active",
                "mounted",
                "",
                "/org/freedesktop/systemd1/unit/sys_2dkernel_2ddebug_2emount",
                0,
                "",
                "/",
            ],
            [
                "slices.target",
                "Slices",
                "loaded",
                "active",
                "active",
                "",
                "/org/freedesktop/systemd1/unit/slices_2etarget",
                0,
                "",
                "/",
            ],
            [
                "etc-NetworkManager-system-connections.mount",
                "NetworkManager persistent system connections",
                "loaded",
                "active",
                "mounted",
                "",
                "/org/freedesktop/systemd1/unit/etc_2dNetworkManager_2dsystem_5cx2dconnections_2emount",
                0,
                "",
                "/",
            ],
            [
                "run-docker-netns-26ede3178729.mount",
                "/run/docker/netns/26ede3178729",
                "loaded",
                "active",
                "mounted",
                "",
                "/org/freedesktop/systemd1/unit/run_2ddocker_2dnetns_2d26ede3178729_2emount",
                0,
                "",
                "/",
            ],
            [
                "dev-disk-by-path-platform-3f202000.mmc-part2.device",
                "/dev/disk/by-path/platform-3f202000.mmc-part2",
                "loaded",
                "active",
                "plugged",
                "sys-devices-platform-soc-3f202000.mmc-mmc_host-mmc0-mmc0:e624-block-mmcblk0-mmcblk0p2.device",
                "/org/freedesktop/systemd1/unit/dev_2ddisk_2dby_5cx2dpath_2dplatform_5cx2d3f202000_2emmc_5cx2dpart2_2edevice",
                0,
                "",
                "/",
            ],
        ]
    ]


def test_systemd_unitlist_complex():
    """Test Systemd Unit list simple."""
    raw = "([('systemd-remount-fs.service', 'Remount Root and \"Kernel File Systems\"', 'loaded', 'active', 'exited', '', objectpath '/org/freedesktop/systemd1/unit/systemd_2dremount_2dfs_2eservice', uint32 0, '', objectpath '/'), ('sys-subsystem-net-devices-veth5714b4e.device', '/sys/subsystem/net/devices/veth5714b4e for \" is', 'loaded', 'active', 'plugged', '', '/org/freedesktop/systemd1/unit/sys_2dsubsystem_2dnet_2ddevices_2dveth5714b4e_2edevice', 0, '', '/')],)"

    # parse data
    data = DBus.parse_gvariant(raw)

    assert data == [
        [
            [
                "systemd-remount-fs.service",
                'Remount Root and "Kernel File Systems"',
                "loaded",
                "active",
                "exited",
                "",
                "/org/freedesktop/systemd1/unit/systemd_2dremount_2dfs_2eservice",
                0,
                "",
                "/",
            ],
            [
                "sys-subsystem-net-devices-veth5714b4e.device",
                '/sys/subsystem/net/devices/veth5714b4e for " is',
                "loaded",
                "active",
                "plugged",
                "",
                "/org/freedesktop/systemd1/unit/sys_2dsubsystem_2dnet_2ddevices_2dveth5714b4e_2edevice",
                0,
                "",
                "/",
            ],
        ]
    ]


def test_networkmanager_dns_properties():
    """Test NetworkManager DNS properties."""
    raw = "({'Mode': <'default'>, 'RcManager': <'file'>, 'Configuration': <[{'nameservers': <['192.168.23.30']>, 'domains': <['syshack.local']>, 'interface': <'eth0'>, 'priority': <100>, 'vpn': <false>}]>},)"

    # parse data
    data = DBus.parse_gvariant(raw)

    assert data == [
        {
            "Mode": "default",
            "RcManager": "file",
            "Configuration": [
                {
                    "nameservers": ["192.168.23.30"],
                    "domains": ["syshack.local"],
                    "interface": "eth0",
                    "priority": 100,
                    "vpn": False,
                }
            ],
        }
    ]


def test_networkmanager_dns_properties_empty():
    """Test NetworkManager DNS properties."""
    raw = "({'Mode': <'default'>, 'RcManager': <'resolvconf'>, 'Configuration': <@aa{sv} []>},)"

    # parse data
    data = DBus.parse_gvariant(raw)

    assert data == [{"Mode": "default", "RcManager": "resolvconf", "Configuration": []}]


def test_networkmanager_binary_data():
    """Test NetworkManager Binary datastrings."""
    raw = "({'802-11-wireless': {'mac-address-blacklist': <@as []>, 'mode': <'infrastructure'>, 'security': <'802-11-wireless-security'>, 'seen-bssids': <['7C:2E:BD:98:1B:06']>, 'ssid': <[byte 0x4e, 0x45, 0x54, 0x54]>}, 'connection': {'id': <'NETT'>, 'interface-name': <'wlan0'>, 'permissions': <@as []>, 'timestamp': <uint64 1598526799>, 'type': <'802-11-wireless'>, 'uuid': <'13f9af79-a6e9-4e07-9353-165ad57bf1a8'>}, 'ipv6': {'address-data': <@aa{sv} []>, 'addresses': <@a(ayuay) []>, 'dns': <@aay []>, 'dns-search': <@as []>, 'method': <'auto'>, 'route-data': <@aa{sv} []>, 'routes': <@a(ayuayu) []>}, '802-11-wireless-security': {'auth-alg': <'open'>, 'key-mgmt': <'wpa-psk'>}, 'ipv4': {'address-data': <@aa{sv} []>, 'addresses': <@aau []>, 'dns': <@au []>, 'dns-search': <@as []>, 'method': <'auto'>, 'route-data': <@aa{sv} []>, 'routes': <@aau []>}, 'proxy': {}},)"

    data = DBus.parse_gvariant(raw)

    assert data == [
        {
            "802-11-wireless": {
                "mac-address-blacklist": [],
                "mode": "infrastructure",
                "security": "802-11-wireless-security",
                "seen-bssids": ["7C:2E:BD:98:1B:06"],
                "ssid": [78, 69, 84, 84],
            },
            "connection": {
                "id": "NETT",
                "interface-name": "wlan0",
                "permissions": [],
                "timestamp": 1598526799,
                "type": "802-11-wireless",
                "uuid": "13f9af79-a6e9-4e07-9353-165ad57bf1a8",
            },
            "ipv6": {
                "address-data": [],
                "addresses": [],
                "dns": [],
                "dns-search": [],
                "method": "auto",
                "route-data": [],
                "routes": [],
            },
            "802-11-wireless-security": {"auth-alg": "open", "key-mgmt": "wpa-psk"},
            "ipv4": {
                "address-data": [],
                "addresses": [],
                "dns": [],
                "dns-search": [],
                "method": "auto",
                "route-data": [],
                "routes": [],
            },
            "proxy": {},
        }
    ]

    raw = "({'802-11-wireless': {'mac-address-blacklist': <@as []>, 'mac-address': <[byte 0xca, 0x0b, 0x61, 0x00, 0xd8, 0xbd]>, 'mode': <'infrastructure'>, 'security': <'802-11-wireless-security'>, 'seen-bssids': <['7C:2E:BD:98:1B:06']>, 'ssid': <[byte 0x4e, 0x45, 0x54, 0x54]>}, 'connection': {'id': <'NETT'>, 'interface-name': <'wlan0'>, 'permissions': <@as []>, 'timestamp': <uint64 1598526799>, 'type': <'802-11-wireless'>, 'uuid': <'13f9af79-a6e9-4e07-9353-165ad57bf1a8'>}, 'ipv6': {'address-data': <@aa{sv} []>, 'addresses': <@a(ayuay) []>, 'dns': <@aay []>, 'dns-search': <@as []>, 'method': <'auto'>, 'route-data': <@aa{sv} []>, 'routes': <@a(ayuayu) []>}, '802-11-wireless-security': {'auth-alg': <'open'>, 'key-mgmt': <'wpa-psk'>}, 'ipv4': {'address-data': <@aa{sv} []>, 'addresses': <@aau []>, 'dns': <@au []>, 'dns-search': <@as []>, 'method': <'auto'>, 'route-data': <@aa{sv} []>, 'routes': <@aau []>}, 'proxy': {}},)"

    data = DBus.parse_gvariant(raw)

    assert data == [
        {
            "802-11-wireless": {
                "mac-address": [202, 11, 97, 0, 216, 189],
                "mac-address-blacklist": [],
                "mode": "infrastructure",
                "security": "802-11-wireless-security",
                "seen-bssids": ["7C:2E:BD:98:1B:06"],
                "ssid": [78, 69, 84, 84],
            },
            "802-11-wireless-security": {"auth-alg": "open", "key-mgmt": "wpa-psk"},
            "connection": {
                "id": "NETT",
                "interface-name": "wlan0",
                "permissions": [],
                "timestamp": 1598526799,
                "type": "802-11-wireless",
                "uuid": "13f9af79-a6e9-4e07-9353-165ad57bf1a8",
            },
            "ipv4": {
                "address-data": [],
                "addresses": [],
                "dns": [],
                "dns-search": [],
                "method": "auto",
                "route-data": [],
                "routes": [],
            },
            "ipv6": {
                "address-data": [],
                "addresses": [],
                "dns": [],
                "dns-search": [],
                "method": "auto",
                "route-data": [],
                "routes": [],
            },
            "proxy": {},
        }
    ]


def test_networkmanager_binary_string_data():
    """Test NetworkManager Binary string datastrings."""
    raw = "({'802-11-wireless': {'mac-address-blacklist': <@as []>, 'mac-address': <b'*~_\\\\035\\\\311'>, 'mode': <'infrastructure'>, 'security': <'802-11-wireless-security'>, 'seen-bssids': <['7C:2E:BD:98:1B:06']>, 'ssid': <[byte 0x4e, 0x45, 0x54, 0x54]>}, 'connection': {'id': <'NETT'>, 'interface-name': <'wlan0'>, 'permissions': <@as []>, 'timestamp': <uint64 1598526799>, 'type': <'802-11-wireless'>, 'uuid': <'13f9af79-a6e9-4e07-9353-165ad57bf1a8'>}, 'ipv6': {'address-data': <@aa{sv} []>, 'addresses': <@a(ayuay) []>, 'dns': <@aay []>, 'dns-search': <@as []>, 'method': <'auto'>, 'route-data': <@aa{sv} []>, 'routes': <@a(ayuayu) []>}, '802-11-wireless-security': {'auth-alg': <'open'>, 'key-mgmt': <'wpa-psk'>}, 'ipv4': {'address-data': <@aa{sv} []>, 'addresses': <@aau []>, 'dns': <@au []>, 'dns-search': <@as []>, 'method': <'auto'>, 'route-data': <@aa{sv} []>, 'routes': <@aau []>}, 'proxy': {}},)"

    data = DBus.parse_gvariant(raw)

    assert data == [
        {
            "802-11-wireless": {
                "mac-address": [42, 126, 95, 29, 195, 137],
                "mac-address-blacklist": [],
                "mode": "infrastructure",
                "security": "802-11-wireless-security",
                "seen-bssids": ["7C:2E:BD:98:1B:06"],
                "ssid": [78, 69, 84, 84],
            },
            "802-11-wireless-security": {"auth-alg": "open", "key-mgmt": "wpa-psk"},
            "connection": {
                "id": "NETT",
                "interface-name": "wlan0",
                "permissions": [],
                "timestamp": 1598526799,
                "type": "802-11-wireless",
                "uuid": "13f9af79-a6e9-4e07-9353-165ad57bf1a8",
            },
            "ipv4": {
                "address-data": [],
                "addresses": [],
                "dns": [],
                "dns-search": [],
                "method": "auto",
                "route-data": [],
                "routes": [],
            },
            "ipv6": {
                "address-data": [],
                "addresses": [],
                "dns": [],
                "dns-search": [],
                "method": "auto",
                "route-data": [],
                "routes": [],
            },
            "proxy": {},
        }
    ]


def test_v6():
    """Test IPv6 Property."""
    raw = "({'addresses': <[([byte 0x20, 0x01, 0x04, 0x70, 0x79, 0x2d, 0x00, 0x01, 0x00, 0x12, 0x00, 0x00, 0x00, 0x00, 0x00, 0x10], uint32 64, [byte 0x20, 0x01, 0x04, 0x70, 0x79, 0x2d, 0x00, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01])]>, 'dns': <[[byte 0x20, 0x01, 0x04, 0x70, 0x79, 0x2d, 0x00, 0x01, 0x00, 0x12, 0x00, 0x00, 0x00, 0x00, 0x00, 0x05], [0x20, 0x01, 0x04, 0x70, 0x79, 0x2d, 0x00, 0x01, 0x00, 0x12, 0x00, 0x00, 0x00, 0x00, 0x00, 0x05]]>})"

    data = DBus.parse_gvariant(raw)

    assert data == [
        {
            "addresses": [
                [
                    [32, 1, 4, 112, 121, 45, 0, 1, 0, 18, 0, 0, 0, 0, 0, 16],
                    64,
                    [32, 1, 4, 112, 121, 45, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1],
                ]
            ],
            "dns": [
                [32, 1, 4, 112, 121, 45, 0, 1, 0, 18, 0, 0, 0, 0, 0, 5],
                [32, 1, 4, 112, 121, 45, 0, 1, 0, 18, 0, 0, 0, 0, 0, 5],
            ],
        }
    ]


def test_single_byte():
    """Test a singlebyte response."""
    raw = "({'Flags': <uint32 1>, 'WpaFlags': <uint32 0>, 'RsnFlags': <uint32 392>, 'Ssid': <[byte 0x53, 0x59, 0x53, 0x48, 0x41, 0x43, 0x4b, 0x5f, 0x48, 0x6f, 0x6d, 0x65]>, 'Frequency': <uint32 5660>, 'HwAddress': <'18:4B:0D:A3:A1:9C'>, 'Mode': <uint32 2>, 'MaxBitrate': <uint32 540000>, 'Strength': <byte 0x2c>, 'LastSeen': <1646569>},)"

    data = DBus.parse_gvariant(raw)

    assert data == [
        {
            "Flags": 1,
            "Frequency": 5660,
            "HwAddress": "18:4B:0D:A3:A1:9C",
            "LastSeen": 1646569,
            "MaxBitrate": 540000,
            "Mode": 2,
            "RsnFlags": 392,
            "Ssid": [83, 89, 83, 72, 65, 67, 75, 95, 72, 111, 109, 101],
            "Strength": [44],
            "WpaFlags": 0,
        }
    ]
