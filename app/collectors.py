"""Parse read-only /proc and ss/netstat output into metric dicts."""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional

from app.ssh_client import SSHError, connect, run_command


def parse_cpu_percent(stat_text: str, sample_idle: Optional[tuple] = None) -> float:
    """
    Estimate CPU usage from a single /proc/stat snapshot.
    Uses (1 - idle/total) * 100 from the aggregate 'cpu ' line.
    """
    for line in stat_text.splitlines():
        if line.startswith("cpu "):
            parts = line.split()
            values = [int(x) for x in parts[1:]]
            total = sum(values)
            idle = values[3] if len(values) > 3 else 0
            if total <= 0:
                return 0.0
            return round(100.0 * (1.0 - (idle / total)), 2)
    raise ValueError("No cpu line in /proc/stat")


def parse_memory(meminfo_text: str) -> Dict[str, float]:
    data: Dict[str, int] = {}
    for line in meminfo_text.splitlines():
        m = re.match(r"^(\w+):\s+(\d+)", line)
        if m:
            data[m.group(1)] = int(m.group(2))
    total_kb = data.get("MemTotal", 0)
    available_kb = data.get("MemAvailable")
    if available_kb is None:
        free_kb = data.get("MemFree", 0)
        buffers = data.get("Buffers", 0)
        cached = data.get("Cached", 0)
        available_kb = free_kb + buffers + cached
    used_kb = max(total_kb - available_kb, 0)
    total_mb = round(total_kb / 1024.0, 2)
    used_mb = round(used_kb / 1024.0, 2)
    percent = round(100.0 * used_kb / total_kb, 2) if total_kb else 0.0
    return {
        "memory_used_mb": used_mb,
        "memory_total_mb": total_mb,
        "memory_percent": percent,
    }


def parse_network(netdev_text: str) -> Dict[str, int]:
    rx_total = 0
    tx_total = 0
    for line in netdev_text.splitlines():
        if ":" not in line:
            continue
        iface, rest = line.split(":", 1)
        iface = iface.strip()
        if iface == "lo":
            continue
        cols = rest.split()
        if len(cols) < 9:
            continue
        try:
            rx_total += int(cols[0])
            tx_total += int(cols[8])
        except ValueError:
            continue
    return {"network_rx_bytes": rx_total, "network_tx_bytes": tx_total}


def parse_ports(ss_or_netstat: str) -> List[Dict[str, str]]:
    ports: List[Dict[str, str]] = []
    seen = set()
    # ss: LISTEN ... *:22 or 0.0.0.0:22 or [::]:22
    for line in ss_or_netstat.splitlines():
        if "LISTEN" not in line.upper() and "LISTEN" not in line:
            # netstat uses LISTEN; ss uses LISTEN too
            if not re.search(r"\bLISTEN\b", line, re.I):
                continue
        # Find address:port at end-ish
        matches = re.findall(r"(\S+):(\d+)\s", line + " ")
        if not matches:
            matches = re.findall(r"(\S+):(\d+)$", line)
        for addr, port in matches:
            key = f"{addr}:{port}"
            if key in seen:
                continue
            seen.add(key)
            ports.append({"address": addr, "port": port})
        if not matches:
            m = re.search(r":(\d+)\b", line)
            if m:
                port = m.group(1)
                if port not in seen:
                    seen.add(port)
                    ports.append({"address": "*", "port": port})
    return ports[:100]


def collect_metrics_via_ssh(
    host: str,
    port: int,
    username: str,
    password: Optional[str] = None,
    private_key: Optional[str] = None,
    timeout: int = 10,
    auto_trust: bool = True,
) -> Dict[str, Any]:
    """Connect once and gather CPU, memory, network, ports (read-only)."""
    client = connect(
        host, port, username, password, private_key, timeout=timeout, auto_trust=auto_trust
    )
    try:
        cpu_raw = run_command(client, "cat /proc/stat")
        mem_raw = run_command(client, "cat /proc/meminfo")
        net_raw = run_command(client, "cat /proc/net/dev")
        try:
            ports_raw = run_command(client, "ss -tuln")
        except SSHError:
            ports_raw = run_command(client, "netstat -tuln")

        mem = parse_memory(mem_raw)
        net = parse_network(net_raw)
        ports = parse_ports(ports_raw)
        cpu = parse_cpu_percent(cpu_raw)

        status = "ok"
        if cpu >= 90 or mem["memory_percent"] >= 90:
            status = "warning"

        return {
            "status": status,
            "cpu_percent": cpu,
            "memory_used_mb": mem["memory_used_mb"],
            "memory_total_mb": mem["memory_total_mb"],
            "memory_percent": mem["memory_percent"],
            "network_rx_bytes": net["network_rx_bytes"],
            "network_tx_bytes": net["network_tx_bytes"],
            "ports": ports,
            "ports_json": json.dumps(ports),
        }
    finally:
        client.close()
