# V19 Linux Systemd Service

V19 can run as a Linux systemd service on the 0.13 server. This keeps the API alive after the SSH session closes and lets deploy restart the service without opening another terminal window.

## First Install On Server

Run once after pulling the latest code:

```bash
cd ~/bazi/qiazhi/v19/scripts
HOST=0.0.0.0 PORT=9019 SERVICE_NAME=qiazhi-v19 ./install_systemd_service.sh
```

Useful checks:

```bash
sudo systemctl status qiazhi-v19 --no-pager
journalctl -u qiazhi-v19 -f
```

## Deploy With Service Restart

After the service is installed, use:

```bash
cd ~/bazi/qiazhi/v19/scripts
HOST=0.0.0.0 PORT=9019 USE_SYSTEMD=1 ./deploy_linux.sh
```

`deploy_linux.sh` still supports the old detached process mode when `USE_SYSTEMD` is not set.

## Runtime Sync Note

`qiazhi/v19/.runtime/` is server-local runtime state. Back it up before major deploys if needed, but it is no longer tracked by Git.

To sync the current codebase knowledge seeds, source archive, draft units, and Rule DB into the server runtime:

```bash
cd ~/bazi/qiazhi/v19/scripts
BASE_URL=http://127.0.0.1:9019 INGEST_RULE_DB=1 RUN_AUDIT=1 ./sync_knowledge_runtime.sh
```

To restore from the newest local backup file:

```bash
cd ~/bazi
LATEST_RUNTIME_BACKUP="$(ls -t ~/qiazhi-v19-runtime-*.tgz | head -n 1)"
tar -xzf "${LATEST_RUNTIME_BACKUP}" -C .
```
