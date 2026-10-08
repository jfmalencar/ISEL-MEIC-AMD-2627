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
import sys


FOLDER_NAME_WORKSPACE = "mLDm_MoP_workspace"
FOLDER_NAME_CODE = "02_code"


COMPOSE_CONTENT = \
"""
services:
  postgres:
    image: postgres:16
    container_name: mldm_postgres
    restart: unless-stopped
    environment:
      POSTGRES_USER: mldm
      POSTGRES_PASSWORD: mldm
      POSTGRES_DB: mldm
    ports:
      - "5432:5432"
    volumes:
      - ./data_postgres:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U mldm -d mldm"]
      interval: 10s
      timeout: 5s
      retries: 5

  pgadmin:
    image: dpage/pgadmin4:9.5
    container_name: mldm_pgadmin
    restart: unless-stopped
    environment:
      PGADMIN_DEFAULT_EMAIL: admin@example.com
      PGADMIN_DEFAULT_PASSWORD: admin
    ports:
      - "5050:80"
    volumes:
      - ./data_pgadmin:/var/lib/pgadmin
    depends_on:
      - postgres
"""


def get_file_path():
   return Path( __file__ ).resolve()


def get_code_path():
   file_path = get_file_path()
   code_path = file_path.parent
   if code_path.name != FOLDER_NAME_CODE:
      raise ValueError(
         f"PTS | mLDm | script must be placed inside a \
          {FOLDER_NAME_CODE} folder: {file_path}" )
   return code_path


def get_workspace_path():
   code_path = get_code_path()
   mop_path = code_path.parent
   workspace_path = mop_path.parent

   if workspace_path.name != FOLDER_NAME_WORKSPACE:
      raise ValueError(
         f"PTS | mLDm | MoP folder ({mop_path}) must be inside the folder: "
         f"{FOLDER_NAME_WORKSPACE}" )
   return workspace_path


def get_postgres_path():
   return get_workspace_path() / "__container" / "postgres"


def get_compose_file_path():
   return get_postgres_path() / "compose.yaml"


def validate_workspace_exists():
   workspace_path = get_workspace_path()
   if not workspace_path.exists():
      raise FileNotFoundError(
         f"PTS | mLDm | workspace not found: {workspace_path}" )


def create_compose_file():
   postgres_path = get_postgres_path()
   postgres_path \
   .mkdir( parents = True, exist_ok = True )

   ( postgres_path / "data_pgadmin" ) \
   .mkdir( parents = True, exist_ok = True )
   ( postgres_path / "data_postgres" ) \
   .mkdir( parents = True, exist_ok = True )

   compose_file_path = get_compose_file_path()
   if compose_file_path.exists() and compose_file_path.stat().st_size > 0:
      print( f"PTS | mLDm | > compose-already-exists: {compose_file_path}" )
      return compose_file_path

   compose_file_path.write_text( COMPOSE_CONTENT, encoding = "utf-8" )
   return compose_file_path


# ----------------------------------------------------------------------
def main():
   try:
      validate_workspace_exists()
      compose_file_path = create_compose_file()
      print( f"PTS | mLDm | > compose-created: {compose_file_path}" )
   except FileExistsError as error:
      print( f"PTS | mLDm | error | file-already-exists: {error}" )
      sys.exit( 1 )
   except PermissionError as error:
      print( f"PTS | mLDm | error | permission-denied: {error}" )
      sys.exit( 1 )
   except OSError as error:
      print( f"PTS | mLDm | error | operating-system-error: {error}" )
      sys.exit( 1 )
   except Exception as error:
      print( f"PTS | mLDm | error | unexpected-error: {error}" )
      sys.exit( 1 )


# ----------------------------------------------------------------------
if __name__ == "__main__": main()
