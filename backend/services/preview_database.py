"""Restore the isolated preview database after container inactivity.

Opt-in only: a normal Supabase configuration never invokes local processes.
The database itself and its configuration live in the persistent workspace.
"""
import asyncio
import os
import socket
import subprocess
import time
import logging
from pathlib import Path
from urllib.parse import urlsplit


def _start_preview_database():
    directory = os.environ.get("PREVIEW_POSTGRES_DATA")
    if not directory:
        return
    target = urlsplit(os.environ["DATABASE_URL"])
    if target.hostname not in {"127.0.0.1", "localhost"} or not target.port:
        raise RuntimeError("Preview database startup requires an explicit loopback DATABASE_URL and port")
    data = Path(directory).resolve()
    if not (data / "PG_VERSION").is_file():
        raise RuntimeError("Preview PostgreSQL data is missing; refusing to initialize or overwrite it")
    try:
        with socket.create_connection((target.hostname, target.port), timeout=1):
            return
    except OSError:
        pass
    # Supervisor can have a minimal PATH after inactivity; use configured executables.
    bindir = Path(os.environ["PREVIEW_POSTGRES_BIN"])
    runuser = os.environ["PREVIEW_RUNUSER"]
    # Runtime files can be restored just after the preview's app process starts.
    # A failed Uvicorn child otherwise stays offline until a code reload.
    executables = [bindir / "pg_ctl", bindir / "postgres", Path(runuser)]
    deadline = time.monotonic() + 120
    waiting = False
    while not all(path.is_file() and os.access(path, os.X_OK) for path in executables):
        if time.monotonic() >= deadline:
            raise RuntimeError("The configured preview PostgreSQL runtime was not restored within 120 seconds")
        if not waiting:
            logging.warning("Waiting for the configured preview database runtime to be restored")
            waiting = True
        time.sleep(1)
    # Paths are resolved server configuration, never derived from a web request.
    def quoted(value):
        return str(value).replace("'", "''")
    config = data / "preview.conf"
    hba = data / "preview_hba.conf"
    config.write_text(
        f"data_directory = '{quoted(data)}'\n"
        f"hba_file = '{quoted(hba)}'\n"
        f"listen_addresses = '{target.hostname}'\n"
        f"port = {target.port}\n"
        f"unix_socket_directories = '{quoted(data)}'\n"
        "ssl = off\nmax_connections = 100\nshared_buffers = 128MB\n"
    )
    hba.write_text("local all all peer\nhost all all 127.0.0.1/32 scram-sha-256\nhost all all ::1/128 scram-sha-256\n")
    config.chmod(0o644)
    hba.chmod(0o644)
    subprocess.run([runuser, "-u", "postgres", "--", str(bindir / "pg_ctl"),
                    "-D", str(data), "-l", str(data / "preview.log"),
                    "-o", f"-c config_file={config}", "-w", "-t", "30", "start"],
                   check=True, timeout=40, cwd="/app")


async def ensure_preview_database():
    await asyncio.to_thread(_start_preview_database)