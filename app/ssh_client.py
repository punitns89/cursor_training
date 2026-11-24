"""Thin SSH helper. Credentials are never logged."""

from __future__ import annotations

import io
import logging
from typing import Optional

import paramiko

logger = logging.getLogger(__name__)

# Allowlisted read-only commands for collectors / connectivity
ALLOWED_COMMANDS = frozenset(
    {
        "uname -a",
        "cat /proc/stat",
        "cat /proc/meminfo",
        "cat /proc/net/dev",
        "ss -tuln",
        "netstat -tuln",
    }
)


class SSHError(Exception):
    """Raised when SSH connect or command fails."""


def _load_pkey(private_key: str) -> paramiko.PKey:
    key_file = io.StringIO(private_key.strip())
    for key_cls in (paramiko.RSAKey, paramiko.Ed25519Key, paramiko.ECDSAKey):
        try:
            key_file.seek(0)
            return key_cls.from_private_key(key_file)
        except Exception:
            continue
    raise SSHError("Unsupported or invalid private key format")


def connect(
    host: str,
    port: int,
    username: str,
    password: Optional[str] = None,
    private_key: Optional[str] = None,
    timeout: int = 10,
    auto_trust: bool = True,
) -> paramiko.SSHClient:
    """Open an SSH client. Does not log password or private key material."""
    if not password and not private_key:
        raise SSHError("No SSH credentials provided")

    client = paramiko.SSHClient()
    if auto_trust:
        # Demo only — documented in README. Prefer known_hosts in real deployments.
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    else:
        client.load_system_host_keys()
        client.set_missing_host_key_policy(paramiko.RejectPolicy())

    connect_kwargs = {
        "hostname": host,
        "port": port,
        "username": username,
        "timeout": timeout,
        "allow_agent": False,
        "look_for_keys": False,
    }
    if private_key and private_key.strip():
        connect_kwargs["pkey"] = _load_pkey(private_key)
    elif password:
        connect_kwargs["password"] = password
    else:
        raise SSHError("No SSH credentials provided")

    try:
        logger.info("SSH connecting to %s:%s as %s", host, port, username)
        client.connect(**connect_kwargs)
    except Exception as exc:
        client.close()
        # Message only — no credential material
        raise SSHError(f"SSH connection failed: {exc.__class__.__name__}") from exc
    return client


def run_command(client: paramiko.SSHClient, command: str, timeout: int = 15) -> str:
    """Run an allowlisted read-only command and return stdout."""
    if command not in ALLOWED_COMMANDS:
        raise SSHError("Command not allowlisted")
    _stdin, stdout, stderr = client.exec_command(command, timeout=timeout)
    exit_status = stdout.channel.recv_exit_status()
    out = stdout.read().decode("utf-8", errors="replace")
    err = stderr.read().decode("utf-8", errors="replace")
    if exit_status != 0 and not out:
        raise SSHError(f"Remote command failed ({exit_status}): {err.strip()[:200]}")
    return out


def check_connectivity(
    host: str,
    port: int,
    username: str,
    password: Optional[str] = None,
    private_key: Optional[str] = None,
    timeout: int = 10,
    auto_trust: bool = True,
) -> str:
    """Run `uname -a` to verify SSH access."""
    client = connect(
        host, port, username, password, private_key, timeout=timeout, auto_trust=auto_trust
    )
    try:
        return run_command(client, "uname -a").strip()
    finally:
        client.close()
