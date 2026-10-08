#!/usr/bin/env python3
BANNER = \
"""
# ----------------------------------------------------------------------
# PTS | Paulo Trigo Silva
# mLDm | MoP
# v02
# ----------------------------------------------------------------------
"""

from pathlib import Path
import platform
import shutil
import subprocess
import sys


FOLDER_NAME_WORKSPACE = "mLDm_MoP_workspace"
FOLDER_NAME_CODE = "02_code"

VENV_PYTHON_PATH_WINDOWS = ( "Scripts", "python.exe" )
VENV_PYTHON_PATH_POSIX = ( "bin", "python" )

OUTPUT_FILE_CHECK_PYTHON = "01_check_python.txt"
OUTPUT_FILE_CHECK_PACKAGE = "02_check_package.txt"
OUTPUT_FILE_CHECK_CONTAINER = "03_check_container.txt"
OUTPUT_FILE_CHECK_POSTGRES = "04_check_postgres.txt"


PACKAGE_CHECK_CODE = \
r"""
import importlib

package_list = [
   ( "numpy", "numpy" ),
   ( "pandas", "pandas" ),
   ( "duckdb", "duckdb" ),
   ( "psycopg", "psycopg" ),
   ( "sklearn", "scikit-learn" ),
   ( "matplotlib", "matplotlib" ),
   ( "plotly", "plotly" ),
   ( "jupyterlab", "jupyterlab" ),
   ( "ipykernel", "ipykernel" ),
   ( "ipywidgets", "ipywidgets" )
]

for module_name, package_name in package_list:
   module = importlib.import_module( module_name )
   version = getattr( module, "__version__", "version-not-available" )
   print( f"PTS | mLDm | {package_name}: {version}" )
"""


POSTGRES_CHECK_CODE = \
r"""
import psycopg

connection = psycopg.connect(
   host = "localhost",
   port = 5432,
   dbname = "mldm",
   user = "mldm",
   password = "mldm",
   connect_timeout = 5
)

with connection:
   with connection.cursor() as cursor:
      cursor.execute(
         '''
         SELECT
            current_database(),
            current_user,
            version();
         '''
      )
      database_name, user_name, postgres_version = cursor.fetchone()

      print( f"database: {database_name}" )
      print( f"user: {user_name}" )
      print( f"version: {postgres_version}" )
"""


def get_file_path():
   return Path( __file__ ).resolve()


def get_code_path():
   file_path = get_file_path()
   code_path = file_path.parent

   if code_path.name != FOLDER_NAME_CODE:
      raise ValueError(
         f"PTS | mLDm | script must be placed inside a "
         f"{FOLDER_NAME_CODE} folder: {file_path}" )

   return code_path


def get_mop_path():
   return get_code_path().parent


def get_workspace_path():
   mop_path = get_mop_path()
   workspace_path = mop_path.parent

   if workspace_path.name != FOLDER_NAME_WORKSPACE:
      raise ValueError(
         f"PTS | mLDm | MoP folder ({mop_path}) must be inside the folder: "
         f"{FOLDER_NAME_WORKSPACE}" )
   return workspace_path


def get_output_path():
   output_path = get_mop_path() / "03_output"
   output_path.mkdir( parents = True, exist_ok = True )
   return output_path


def get_venv_path():
   return get_workspace_path() / "__venv"


def get_venv_python_path():
   venv_path = get_venv_path()
   if sys.platform.startswith( "win" ):
      return venv_path.joinpath( *VENV_PYTHON_PATH_WINDOWS )
   return venv_path.joinpath( *VENV_PYTHON_PATH_POSIX )


def write_output( file_name, text ):
   output_file_path = get_output_path() / file_name
   output_file_path.write_text( text, encoding = "utf-8" )
   print( f"PTS | mLDm | > output-written: {output_file_path}" )


def run_command_capture( command, cwd = None ):
   try:
      completed_process = \
         subprocess.run(
            command,
            cwd = cwd,
            capture_output = True,
            text = True,
            check = False )
      output = \
         "COMMAND: " + " ".join( str( item ) for item in command ) + "\n" \
         + f"RETURN_CODE: {completed_process.returncode}\n\n" \
         + "STDOUT:\n" + completed_process.stdout + "\n" \
         + "STDERR:\n" + completed_process.stderr + "\n"
      return completed_process.returncode == 0, output
   except Exception as error:
      return False, f"PTS | mLDm | COMMAND_FAILED: {command}\nERROR: {error}\n"


def check_python():
   venv_python_path = get_venv_python_path()
   text = \
      f"system_python: {sys.executable}\n" \
      f"system_python_version: {sys.version}\n" \
      f"platform: {platform.platform()}\n" \
      f"mop_path: {get_mop_path()}\n" \
      f"workspace_path: {get_workspace_path()}\n" \
      f"venv_path: {get_venv_path()}\n" \
      f"venv_python_path: {venv_python_path}\n"

   if not get_workspace_path().exists():
      text = text + "\nPTS | mLDm | ERROR: workspace not found\n"
      return False, text

   if not get_venv_path().exists():
      text = text + "\nPTS | mLDm | ERROR: venv folder not found\n"
      return False, text

   if not venv_python_path.exists():
      text = text + "\nPTS | mLDm | ERROR: venv python not found\n"
      return False, text

   ok, output = run_command_capture( [ str( venv_python_path ), "--version" ] )
   text = text + "\n" + output
   return ok, text


def check_packages():
   venv_python_path = get_venv_python_path()
   if not venv_python_path.exists():
      return False, f"PTS | mLDm | ERROR: venv python not found: {venv_python_path}\n"
   ok, output = run_command_capture(
      [ str( venv_python_path ), "-c", PACKAGE_CHECK_CODE ] )
   return ok, output


def check_one_container_tool( tool_path, tool_name ):
   text = f"PTS | mLDm | checking container tool: {tool_name}\n\n"

   version_ok, version_output = run_command_capture( [ tool_path, "--version" ] )
   text = text + version_output + "\n"

   compose_ok, compose_output = run_command_capture(
      [ tool_path, "compose", "version" ] )
   text = text + compose_output + "\n"

   ps_ok, ps_output = run_command_capture( [ tool_path, "ps" ] )
   text = text + ps_output + "\n"

   ok = version_ok and compose_ok and ps_ok

   if ok:
      text = text + f"PTS | mLDm | container-tool-ok: {tool_name}\n"
   else:
      text = text + f"PTS | mLDm | container-tool-failed: {tool_name}\n"

   return ok, text


def check_container_tool():
   podman_path = shutil.which( "podman" )
   docker_path = shutil.which( "docker" )

   text = ""
   ok = False

   if podman_path is not None:
      podman_ok, podman_text = check_one_container_tool( podman_path, "podman" )
      text = text + podman_text + "\n"
      ok = ok or podman_ok

   if docker_path is not None:
      if not ok:
         docker_ok, docker_text = check_one_container_tool( docker_path, "docker" )
         text = text + docker_text + "\n"
         ok = ok or docker_ok
      else:
         text = text + "PTS | mLDm | docker check skipped because podman is OK\n"

   if podman_path is None and docker_path is None:
      text = "PTS | mLDm | ERROR: neither podman nor docker was found in PATH\n"

   if ok:
      text = text + "PTS | mLDm | at least one container tool is available\n"
   else:
      text = text + "PTS | mLDm | ERROR: no working container tool found\n"

   return ok, text


def check_postgres_connection():
   venv_python_path = get_venv_python_path()
   if not venv_python_path.exists():
      return False, f"PTS | mLDm | ERROR: venv python not found: {venv_python_path}\n"
   ok, output = run_command_capture(
      [ str( venv_python_path ), "-c", POSTGRES_CHECK_CODE ] )
   return ok, output


# ----------------------------------------------------------------------
def main():
   try:
      check_list = [
         ( OUTPUT_FILE_CHECK_PYTHON, check_python ),
         ( OUTPUT_FILE_CHECK_PACKAGE, check_packages ),
         ( OUTPUT_FILE_CHECK_CONTAINER, check_container_tool ),
         ( OUTPUT_FILE_CHECK_POSTGRES, check_postgres_connection ) ]

      failed_check_list = []
      for file_name, check_function in check_list:
         ok, text = check_function()
         write_output( file_name, text )
         if not ok:
            failed_check_list.append( file_name )

      if len( failed_check_list ) == 0:
         print( "PTS | mLDm | > environment-check-ok" )
         sys.exit( 0 )
      print( "PTS | mLDm | error | failed-checks: " + ", ".join( failed_check_list ) )
      sys.exit( 1 )
   except Exception as error:
      print( f"PTS | mLDm | error | unexpected-error: {error}" )
      sys.exit( 1 )


# ----------------------------------------------------------------------
if __name__ == "__main__": main()
