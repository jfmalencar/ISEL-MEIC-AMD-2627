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
         f"PTS | mLDm | the MoP folder ({mop_path}) must be inside the folder: "
         f"{FOLDER_NAME_WORKSPACE}" )
   return workspace_path


def create_common_workspace_structure( workspace_path ):
   postgres_path = workspace_path / "__container" / "postgres"

   ( postgres_path / "data_pgadmin" ) \
   .mkdir( parents = True, exist_ok = True )
   
   ( postgres_path / "data_postgres" ) \
   .mkdir( parents = True, exist_ok = True )
   
   ( workspace_path / "__venv" ) \
   .mkdir( parents = True, exist_ok = True )

   compose_path = postgres_path / "compose.yaml"
   if not compose_path.exists(): compose_path.touch()


# ----------------------------------------------------------------------
def main():
   try:
      workspace_path = get_workspace_path()
      create_common_workspace_structure( workspace_path )
      print( f"PTS | mLDm | > workspace-ready: {workspace_path}" )
   except PermissionError as error:
      print( f"PTS | mLDm | error | permission-denied: {error}" )
      sys.exit( 1 )
   except FileExistsError as error:
      print( f"PTS | mLDm | error | already-exists: {error}" )
      sys.exit( 1 )
   except OSError as error:
      print( f"PTS | mLDm | error | operating-system-error: {error}" )
      sys.exit( 1 )
   except Exception as error:
      print( f"PTS | mLDm | error | unexpected-error: {error}" )
      sys.exit( 1 )


# ----------------------------------------------------------------------
if __name__ == "__main__": main()
