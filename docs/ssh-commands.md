# Remote commands used for metrics

All commands are **read-only** and allowlisted in `app/ssh_client.py`.

| Purpose | Command |
|---------|---------|
| Connectivity check | `uname -a` |
| CPU | `cat /proc/stat` |
| Memory | `cat /proc/meminfo` |
| Network counters | `cat /proc/net/dev` |
| Listening ports | `ss -tuln` (fallback: `netstat -tuln`) |

No remote writes, package installs, or shell interpolation of user input into commands.
