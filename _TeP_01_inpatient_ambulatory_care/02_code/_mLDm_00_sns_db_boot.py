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
RUNTIME = "podman"
# RUNTIME = "docker"

CONTAINER = "mldm_postgres"
DATABASE = "mldm_tep"
USER = "mldm"


BASE_DIR = Path(__file__).resolve().parent
INPUT_DIR = BASE_DIR.parent / "01_input"

FILES = [
  INPUT_DIR / "_mLDm_01_sns_schema.sql",
  INPUT_DIR / "_mLDm_02_sns_data_db.sql" ]

# get_canonical_name() uses Unicode NFC, which requires a UTF8 database.
UTF8_CHECK = """
DO $$
BEGIN
  IF current_setting('server_encoding') <> 'UTF8' THEN
    RAISE EXCEPTION 'PTS | mLDm | PostgreSQL database must use UTF8';
  END IF;
END
$$;
"""

SQL = UTF8_CHECK + "\n" + "\n".join(
  filename.read_text(encoding="utf-8") for filename in FILES )

try:
  # create the TeP database only when it does not exist
  result = subprocess.run(
    [
      RUNTIME, "exec", "-i", CONTAINER,
      "psql", "-U", USER, "-d", "postgres",
      "-v", "ON_ERROR_STOP=1", "-tAc",
      f"SELECT 1 FROM pg_database WHERE datname = '{DATABASE}'"
    ],
    capture_output=True,
    text=True,
    check=True,
  )

  if not result.stdout.strip():
    subprocess.run(
      [
        RUNTIME, "exec", "-i", CONTAINER,
        "psql", "-U", USER, "-d", "postgres",
        "-v", "ON_ERROR_STOP=1", "-c",
        f"CREATE DATABASE {DATABASE} "
        f"WITH OWNER = {USER} ENCODING = 'UTF8' TEMPLATE = template0"
      ],
      check=True,
    )

  # recreate schema and load reference data in one transaction
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
