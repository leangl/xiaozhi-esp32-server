"""Local address discovery must never probe a remote destination or DNS."""
import socket
from types import SimpleNamespace
from unittest.mock import Mock

import psutil
import pytest

from core.utils.util import get_local_ip


def address(value, family=socket.AF_INET):
    return SimpleNamespace(family=family, address=value)


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    for name in ("socket", "getaddrinfo", "gethostbyname", "gethostbyname_ex"):
        monkeypatch.setattr(socket, name, Mock(side_effect=AssertionError("No network discovery")))
    yield
    for name in ("socket", "getaddrinfo", "gethostbyname", "gethostbyname_ex"):
        getattr(socket, name).assert_not_called()


def interfaces(monkeypatch, addresses, *, down=(), missing=()):
    monkeypatch.setattr(psutil, "net_if_addrs", lambda: addresses)
    monkeypatch.setattr(psutil, "net_if_stats", lambda: {
        name: SimpleNamespace(isup=name not in down)
        for name in addresses if name not in missing
    })


def test_active_interface_without_default_route(monkeypatch):
    interfaces(monkeypatch, {"lo": [address("127.0.0.1")],
                             "eth0": [address("172.20.0.4")]})
    assert get_local_ip() == "172.20.0.4"


def test_skip_down_missing_and_non_ipv4_interfaces(monkeypatch):
    interfaces(monkeypatch, {
        "down": [address("10.0.0.1")], "gone": [address("10.0.0.2")],
        "ipv6": [address("fe80::1", socket.AF_INET6)],
        "wifi": [address("192.168.1.20")],
    }, down=("down",), missing=("gone",))
    assert get_local_ip() == "192.168.1.20"


def test_skip_unusable_addresses(monkeypatch):
    interfaces(monkeypatch, {"eth0": [address(value) for value in
                                     ("invalid", "127.2.3.4", "0.0.0.0", "224.0.0.1", "10.0.0.8")]})
    assert get_local_ip() == "10.0.0.8"


def test_first_active_ipv4_is_selected_in_os_order(monkeypatch):
    interfaces(monkeypatch, {"vpn": [address("10.1.0.2")],
                             "wifi": [address("192.168.1.20")]})
    assert get_local_ip() == "10.1.0.2"


@pytest.mark.parametrize("addresses", [{}, {"lo": [address("127.0.0.1")]},
                                       {"eth0": [address("::1", socket.AF_INET6)]}])
def test_no_usable_ipv4_falls_back_to_loopback(monkeypatch, addresses):
    interfaces(monkeypatch, addresses)
    assert get_local_ip() == "127.0.0.1"


@pytest.mark.parametrize("failed_read", ["net_if_addrs", "net_if_stats"])
def test_interface_read_failure_does_not_probe_network(monkeypatch, failed_read):
    interfaces(monkeypatch, {"eth0": [address("10.0.0.8")]})
    monkeypatch.setattr(psutil, failed_read, Mock(side_effect=OSError("Interface unavailable")))
    assert get_local_ip() == "127.0.0.1"
