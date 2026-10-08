#!/usr/bin/env python3
BANNER = \
"""
# ----------------------------------------------------------------------
# PTS | Paulo Trigo Silva
# mLDm | MoP
# v01
# ----------------------------------------------------------------------
"""

from pathlib import Path
import subprocess

# PTS | choose the one you are using (comment-out the other)
# RUNTIME = "podman"
RUNTIME = "docker"

CONTAINER = "mldm_postgres"
DATABASE = "mldm"
USER = "mldm"


BASE_DIR = Path(__file__).resolve().parent
INPUT_DIR = BASE_DIR.parent / "01_input"

FILES = [
    INPUT_DIR / "_mLDm_01_penguins_schema.sql",
    INPUT_DIR / "_mLDm_02_penguins_data_db.sql" ]
SQL = "\n".join( filename.read_text(encoding="utf-8") for filename in FILES )

try:
    subprocess.run(
        [
            RUNTIME,
            "exec",
            "-i",
            CONTAINER,
            "psql",
            "-v", "ON_ERROR_STOP=1",
            "-1",
            "-U", USER,
            "-d", DATABASE,
        ],
        input=SQL,
        text=True,
        check=True,
    )
    print("PTS | database successfully initialized")

except FileNotFoundError:
    print(f"PTS | ERROR: {RUNTIME} is not installed or is not available in PATH")
    raise

except subprocess.CalledProcessError:
    print(f"PTS | ERROR: {RUNTIME} not running, or container '{CONTAINER}' not available")
    raise