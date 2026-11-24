from unittest.mock import MagicMock, patch

import pytest

from app.ssh_client import SSHError, check_connectivity, connect, run_command


def test_run_command_rejects_non_allowlisted():
    client = MagicMock()
    with pytest.raises(SSHError, match="allowlisted"):
        run_command(client, "rm -rf /")


def test_connect_requires_credentials():
    with pytest.raises(SSHError, match="credentials"):
        connect("host", 22, "user", password=None, private_key=None)


@patch("app.ssh_client.paramiko.SSHClient")
def test_check_connectivity_mocked(mock_ssh_cls):
    mock_client = MagicMock()
    mock_ssh_cls.return_value = mock_client
    stdout = MagicMock()
    stdout.read.return_value = b"Linux demo 5.15\n"
    stdout.channel.recv_exit_status.return_value = 0
    stderr = MagicMock()
    stderr.read.return_value = b""
    mock_client.exec_command.return_value = (MagicMock(), stdout, stderr)

    result = check_connectivity("10.0.0.1", 22, "ubuntu", password="x")
    assert "Linux" in result
    mock_client.connect.assert_called_once()
    # Ensure password not present in logger path — connect was called with password kw
    kwargs = mock_client.connect.call_args.kwargs
    assert kwargs["hostname"] == "10.0.0.1"
    assert "password" in kwargs
