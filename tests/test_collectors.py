from app.collectors import parse_cpu_percent, parse_memory, parse_network, parse_ports


PROC_STAT = """cpu  1000 0 1000 6000 0 0 0 0 0 0
cpu0 500 0 500 3000 0 0 0 0 0 0
"""

PROC_MEMINFO = """MemTotal:        2048000 kB
MemFree:          512000 kB
MemAvailable:    1024000 kB
Buffers:          128000 kB
Cached:           256000 kB
"""

PROC_NET = """Inter-|   Receive                                                |  Transmit
 face |bytes    packets errs drop fifo frame compressed multicast|bytes    packets errs drop fifo colls carrier compressed
    lo: 1000       10    0    0    0     0          0         0     1000      10    0    0    0     0       0          0
  eth0: 2000000   100    0    0    0     0          0         0   3000000     120    0    0    0     0       0          0
"""

SS_OUT = """Netid State  Recv-Q Send-Q Local Address:Port Peer Address:Port
tcp   LISTEN 0      128          0.0.0.0:22         0.0.0.0:*
tcp   LISTEN 0      128             [::]:80            [::]:*
"""


def test_parse_cpu_percent():
    # idle 6000 / total 8000 => 25% used
    assert parse_cpu_percent(PROC_STAT) == 25.0


def test_parse_memory():
    mem = parse_memory(PROC_MEMINFO)
    assert mem["memory_total_mb"] == 2000.0
    assert mem["memory_used_mb"] == 1000.0
    assert mem["memory_percent"] == 50.0


def test_parse_network_skips_loopback():
    net = parse_network(PROC_NET)
    assert net["network_rx_bytes"] == 2000000
    assert net["network_tx_bytes"] == 3000000


def test_parse_ports():
    ports = parse_ports(SS_OUT)
    port_nums = {p["port"] for p in ports}
    assert "22" in port_nums
    assert "80" in port_nums
