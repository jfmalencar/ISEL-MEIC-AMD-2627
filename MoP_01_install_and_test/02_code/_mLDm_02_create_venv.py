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
import sys
import venv


FOLDER_NAME_WORKSPACE = "mLDm_MoP_workspace"
FOLDER_NAME_CODE = "02_code"
FILE_NAME_REQUIREMENTS = "_mLDm_00_requirements.txt"
PYTHON_VERSION_MIN = ( 3, 12 )

VENV_PYTHON_PATH_WINDOWS = ( "Scripts", "python.exe" )
VENV_PYTHON_PATH_POSIX = ( "bin", "python" )


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


def get_venv_path():
   return get_workspace_path() / "__venv"


def get_venv_python_path( venv_path ):
   if sys.platform.startswith( "win" ):
      return venv_path.joinpath( *VENV_PYTHON_PATH_WINDOWS )
   return venv_path.joinpath( *VENV_PYTHON_PATH_POSIX )


def get_requirements_file_path():
   return get_code_path() / FILE_NAME_REQUIREMENTS


def validate_python_version():
   if sys.version_info < PYTHON_VERSION_MIN:
      raise RuntimeError(
         "PTS | mLDm | Python 3.12 or later is required to create this environment" )


def validate_workspace_exists():
   workspace_path = get_workspace_path()
   if not workspace_path.exists():
      raise FileNotFoundError(
         f"PTS | mLDm | workspace not found: {workspace_path}" )
   if not workspace_path.is_dir():
      raise NotADirectoryError(
         f"PTS | mLDm | workspace path is not a directory: {workspace_path}" )


def validate_requirements_file_exists():
   requirements_file_path = get_requirements_file_path()
   if not requirements_file_path.exists():
      raise FileNotFoundError(
         f"PTS | mLDm | requirements file not found: {requirements_file_path}" )


def venv_already_exists( venv_path ):
   return ( venv_path / "pyvenv.cfg" ).exists()


def create_venv( venv_path ):
   if venv_already_exists( venv_path ):
      print( f"PTS | mLDm | > venv-already-exists: {venv_path}" )
      return
   if venv_path.exists() and any( venv_path.iterdir() ):
      raise FileExistsError(
         f"PTS | mLDm | __venv exists but is not an empty virtual environment: {venv_path}" )

   builder = \
      venv.EnvBuilder(
         system_site_packages = False,
         clear = False,
         symlinks = False,
         with_pip = True
      )
   builder.create( venv_path )
   print( f"PTS | mLDm | > venv-created: {venv_path}" )


def run_command( command ):
   print( "PTS | mLDm | > " + " ".join( str( item ) for item in command ) )
   subprocess.run( command, check = True )


def install_requirements( venv_path ):
   venv_python_path = get_venv_python_path( venv_path )
   requirements_file_path = get_requirements_file_path()
   run_command(
      [ str( venv_python_path ), "-m", "pip", "install", "--upgrade", "pip" ] )
   run_command(
      [ str( venv_python_path ), "-m", "pip", "install", "-r", str( requirements_file_path ) ] )


def register_jupyter_kernel( venv_path ):
   venv_python_path = get_venv_python_path( venv_path )
   run_command(
      [ str( venv_python_path ), "-m", "ipykernel", "install",
         "--user", "--name", "mldm",
         "--display-name", "myPython (mLDm)" ] )


# ----------------------------------------------------------------------
def main():
   try:
      validate_python_version()
      validate_workspace_exists()
      validate_requirements_file_exists()
      venv_path = get_venv_path()
      create_venv( venv_path )
      install_requirements( venv_path )
      register_jupyter_kernel( venv_path )
      print( f"PTS | mLDm | > SUCCESS > venv-ready: {venv_path}" )
   except subprocess.CalledProcessError as error:
      print( f"PTS | mLDm | error | command-failed: {error}" )
      sys.exit( 1 )
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
