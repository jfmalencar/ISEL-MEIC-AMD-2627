#!/usr/bin/env python3
BANNER = \
"""
# ----------------------------------------------------------------------
# PTS | Paulo Trigo Silva
# mLDm | MoP
# submission tool
# v02
# ----------------------------------------------------------------------
"""

from pathlib import Path
import fnmatch
import shutil
import sys
import zipfile


FOLDER_NAME_WORKSPACE = "mLDm_MoP_workspace"
FOLDER_NAME_CODE = "02_code"
FOLDER_NAME_OUTPUT = "03_output"
FOLDER_NAME_REPORT = "04_report"

ZIP_PREFIX = "submitted"
GROUP_PREFIX = "G"

EXCLUDE_FOLDER_NAMES = {
   "__pycache__",
   ".ipynb_checkpoints"
}

EXCLUDE_FILE_PATTERNS = [
   ".DS_Store",
   "Thumbs.db",
   "*.pyc",
   "*.pyo",
   "submitted_*.zip"
]


def get_file_path():
   return Path( __file__ ).resolve()


def print_info( message ):
   print( f"PTS | mLDm | > {message}" )


def print_warning( message ):
   print( f"PTS | mLDm | warning | {message}" )


def raise_error( message ):
   raise ValueError( f"PTS | mLDm | error | {message}" )


def is_workspace_path( path ):
   return path.is_dir() and path.name == FOLDER_NAME_WORKSPACE


def is_mop_path( path ):
   return path.is_dir() and path.name.startswith( "MoP_" )


def find_workspace_from_path( path ):
   for current_path in [ path, *path.parents ]:
      if current_path.name == FOLDER_NAME_WORKSPACE:
         return current_path

   raise_error(
      f"workspace-folder-not-found: {FOLDER_NAME_WORKSPACE}" )


def detect_execution_context():
   file_path = get_file_path()
   file_parent_path = file_path.parent

   if file_parent_path.name == FOLDER_NAME_CODE:
      mop_path = file_parent_path.parent
      workspace_path = mop_path.parent

      if not is_mop_path( mop_path ):
         raise_error(
            f"invalid-mop-folder-name: {mop_path.name}" )

      if not is_workspace_path( workspace_path ):
         raise_error(
            f"MoP folder must be inside {FOLDER_NAME_WORKSPACE}: {mop_path}" )

      return {
         "mode": "mop_code",
         "workspace_path": workspace_path,
         "mop_path": mop_path
      }

   if file_parent_path.name == FOLDER_NAME_WORKSPACE:
      workspace_path = file_parent_path

      return {
         "mode": "workspace",
         "workspace_path": workspace_path,
         "mop_path": None
      }

   workspace_path = find_workspace_from_path( file_parent_path )

   return {
      "mode": "unknown_inside_workspace",
      "workspace_path": workspace_path,
      "mop_path": None
   }


def normalize_group_argument( group_argument ):
   if group_argument is None:
      raise_error( "missing-group-number" )

   group_text = str( group_argument ).strip()

   if group_text.upper().startswith( GROUP_PREFIX ):
      group_text = group_text[ len( GROUP_PREFIX ): ]

   if not group_text.isdigit():
      raise_error(
         f"group-number-must-be-integer: {group_argument}" )

   group_number = int( group_text )

   if group_number < 1 or group_number > 99:
      raise_error(
         f"group-number-out-of-range-1-to-99: {group_number}" )

   return f"{GROUP_PREFIX}{group_number:02d}"


def get_mop_path_from_argument( workspace_path, mop_argument ):
   if mop_argument is None:
      raise_error( "missing-mop-folder-name" )

   mop_name = str( mop_argument ).strip()

   if not mop_name.startswith( "MoP_" ):
      raise_error(
         f"mop-folder-name-must-start-with-MoP_: {mop_name}" )

   mop_path = workspace_path / mop_name

   if not mop_path.exists():
      raise_error(
         f"mop-folder-not-found: {mop_path}" )

   if not mop_path.is_dir():
      raise_error(
         f"mop-path-is-not-a-folder: {mop_path}" )

   return mop_path


def parse_arguments( context ):
   argument_list = sys.argv[ 1: ]

   if context[ "mode" ] == "mop_code":
      if len( argument_list ) != 1:
         raise_error(
            "usage-from-MoP-02_code: "
            "python3 _mLDm_xx_build_submission_zip.py <group-number>" )

      group_label = normalize_group_argument( argument_list[ 0 ] )
      mop_path = context[ "mop_path" ]

      return group_label, mop_path

   if context[ "mode" ] == "workspace":
      if len( argument_list ) != 2:
         raise_error(
            "usage-from-workspace: "
            "python3 _mLDm_xx_build_submission_zip.py <group-number> <MoP-folder-name>" )

      group_label = normalize_group_argument( argument_list[ 0 ] )
      mop_path = get_mop_path_from_argument(
         context[ "workspace_path" ],
         argument_list[ 1 ] )

      return group_label, mop_path

   raise_error(
      "script must be executed either from a MoP 02_code folder "
      "or from the mLDm_MoP_workspace folder" )


def install_tool_in_workspace( workspace_path ):
   source_file_path = get_file_path()
   target_file_path = workspace_path / source_file_path.name

   if source_file_path == target_file_path:
      print_info( f"tool-already-in-workspace: {target_file_path}" )
      return target_file_path

   if target_file_path.exists():
      print_info( f"updating-tool-in-workspace: {target_file_path}" )
   else:
      print_info( f"installing-tool-in-workspace: {target_file_path}" )

   shutil.copy2( source_file_path, target_file_path )
   return target_file_path


def validate_submission_folder( folder_path ):
   if not folder_path.exists():
      raise_error( f"required-folder-not-found: {folder_path}" )

   if not folder_path.is_dir():
      raise_error( f"required-path-is-not-a-folder: {folder_path}" )

   if not any( folder_path.iterdir() ):
      print_warning( f"folder-is-empty: {folder_path}" )


def should_exclude_path( relative_path ):
   if any( part in EXCLUDE_FOLDER_NAMES for part in relative_path.parts ):
      return True

   for pattern in EXCLUDE_FILE_PATTERNS:
      if fnmatch.fnmatch( relative_path.name, pattern ):
         return True

   return False


def add_folder_to_zip( zip_file, folder_path, archive_root_name ):
   file_count = 0

   zip_file.write(
      folder_path,
      arcname = archive_root_name + "/"
   )

   for path in sorted( folder_path.rglob( "*" ) ):
      relative_path = path.relative_to( folder_path )
      archive_path = Path( archive_root_name ) / relative_path

      if should_exclude_path( relative_path ):
         continue

      if path.is_dir():
         zip_file.write( path, arcname = str( archive_path ) + "/" )
      else:
         zip_file.write( path, arcname = archive_path.as_posix() )
         file_count = file_count + 1

   return file_count


def build_submission_zip( workspace_path, mop_path, group_label ):
   output_path = mop_path / FOLDER_NAME_OUTPUT
   report_path = mop_path / FOLDER_NAME_REPORT

   validate_submission_folder( output_path )
   validate_submission_folder( report_path )

   zip_file_name = f"{ZIP_PREFIX}_{group_label}_{mop_path.name}.zip"
   zip_file_path = workspace_path / zip_file_name

   if zip_file_path.exists():
      print_info( f"replacing-existing-zip: {zip_file_path}" )
      zip_file_path.unlink()

   print_info( f"zip-target-folder: {workspace_path}" )
   print_info( f"adding-folder: {FOLDER_NAME_OUTPUT}" )
   print_info( f"adding-folder: {FOLDER_NAME_REPORT}" )

   with zipfile.ZipFile(
      zip_file_path,
      mode = "w",
      compression = zipfile.ZIP_DEFLATED
   ) as zip_file:
      output_file_count = add_folder_to_zip(
         zip_file,
         output_path,
         FOLDER_NAME_OUTPUT )

      report_file_count = add_folder_to_zip(
         zip_file,
         report_path,
         FOLDER_NAME_REPORT )

   total_file_count = output_file_count + report_file_count

   if total_file_count == 0:
      print_warning( "submission-zip-has-no-files" )

   print_info( f"submission-created: {zip_file_path}" )
   print_info( f"submission-file-count: {total_file_count}" )

   return zip_file_path


def main():
   try:
      context = detect_execution_context()
      group_label, mop_path = parse_arguments( context )

      workspace_path = context[ "workspace_path" ]

      print_info( f"workspace-detected: {workspace_path}" )
      print_info( f"mop-detected: {mop_path}" )
      print_info( f"group-detected: {group_label}" )

      install_tool_in_workspace( workspace_path )
      build_submission_zip( workspace_path, mop_path, group_label )

      print_info( "SUCCESS" )
      sys.exit( 0 )

   except Exception as error:
      print( error )
      sys.exit( 1 )


# ----------------------------------------------------------------------
if __name__ == "__main__": main()
