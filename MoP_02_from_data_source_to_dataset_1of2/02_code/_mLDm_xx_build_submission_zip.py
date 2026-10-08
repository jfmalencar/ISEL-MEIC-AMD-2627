#!/usr/bin/env python3
BANNER = \
"""
# ----------------------------------------------------------------------
# PTS | Paulo Trigo Silva
# mLDm | MoP
# submission tool
# v03
# ----------------------------------------------------------------------
"""

from pathlib import Path
import fnmatch
import shutil
import sys
import zipfile


FOLDER_NAME_WORKSPACE = "mLDm_MoP_workspace"
FOLDER_NAME_INPUT = "01_input"
FOLDER_NAME_CODE = "02_code"
FOLDER_NAME_OUTPUT = "03_output"
FOLDER_NAME_REPORT = "04_report"

REQUIREMENTS_FILE_NAME = "_mLDm_xx_submission_requirements.txt"
SUBMISSION_CHECK_FILE_NAME = "submission_check.txt"

COURSE_FILE_PREFIX = "_mLDm_"

ZIP_PREFIX = "submitted"
GROUP_PREFIX = "G"

REQUIREMENT_SECTION_NAMES = [
   "TO_ADAPT",
   "TO_CREATE",
   "OTHER"
]

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


# ----------------------------------------------------------------------
def get_file_path():
   return Path( __file__ ).resolve()


def print_info( message ):
   print( f"PTS | mLDm | > {message}" )


def print_warning( message ):
   print( f"PTS | mLDm | warning | {message}" )


def raise_error( message ):
   raise ValueError( f"PTS | mLDm | error | {message}" )


# ----------------------------------------------------------------------
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


# ----------------------------------------------------------------------
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


# ----------------------------------------------------------------------
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


# ----------------------------------------------------------------------
def validate_required_folder( folder_path ):
   if not folder_path.exists():
      raise_error( f"required-folder-not-found: {folder_path}" )

   if not folder_path.is_dir():
      raise_error( f"required-path-is-not-a-folder: {folder_path}" )


def get_relative_path( path_text, context_label ):
   relative_path = Path( path_text.strip() )

   if str( relative_path ) in [ "", "." ]:
      raise_error( f"empty-relative-path: {context_label}" )

   if relative_path.is_absolute():
      raise_error(
         f"absolute-path-not-allowed-in-requirements: {path_text}" )

   if ".." in relative_path.parts:
      raise_error(
         f"parent-path-not-allowed-in-requirements: {path_text}" )

   return relative_path


def get_requirements_file_path( mop_path ):
   return mop_path / FOLDER_NAME_INPUT / REQUIREMENTS_FILE_NAME


def read_submission_requirements( mop_path ):
   requirements_file_path = get_requirements_file_path( mop_path )

   if not requirements_file_path.exists():
      raise_error(
         f"submission-requirements-file-not-found: {requirements_file_path}" )

   if not requirements_file_path.is_file():
      raise_error(
         f"submission-requirements-path-is-not-a-file: {requirements_file_path}" )

   requirement_map = {
      section_name: []
      for section_name in REQUIREMENT_SECTION_NAMES
   }

   current_section_name = None

   for line_number, raw_line in enumerate(
      requirements_file_path.read_text( encoding = "utf-8" ).splitlines(),
      start = 1
   ):
      line = raw_line.strip()

      if line == "" or line.startswith( "#" ):
         continue

      if line.startswith( "[" ) and line.endswith( "]" ):
         section_name = line[ 1:-1 ].strip().upper()

         if section_name not in REQUIREMENT_SECTION_NAMES:
            raise_error(
               f"unknown-requirements-section-at-line-{line_number}: "
               f"{section_name}" )

         current_section_name = section_name
         continue

      if current_section_name is None:
         raise_error(
            f"requirement-outside-section-at-line-{line_number}: {line}" )

      relative_path = get_relative_path(
         line,
         f"line-{line_number}" )

      if relative_path in requirement_map[ current_section_name ]:
         raise_error(
            f"duplicate-requirement-at-line-{line_number}: {line}" )

      requirement_map[ current_section_name ].append( relative_path )

   return requirements_file_path, requirement_map


# ----------------------------------------------------------------------
def get_adapted_relative_path( original_relative_path ):
   original_name = original_relative_path.name

   if not original_name.startswith( COURSE_FILE_PREFIX ):
      raise_error(
         f"TO_ADAPT-file-must-start-with-{COURSE_FILE_PREFIX}: "
         f"{original_relative_path.as_posix()}" )

   adapted_name = original_name[ len( COURSE_FILE_PREFIX ): ]

   if adapted_name == "":
      raise_error(
         f"invalid-TO_ADAPT-file-name: {original_relative_path.as_posix()}" )

   return original_relative_path.with_name( adapted_name )


def validate_submission_requirements( mop_path, requirement_map ):
   code_path = mop_path / FOLDER_NAME_CODE

   validate_required_folder( code_path )

   check_line_list = []
   code_path_list = []
   other_path_list = []

   required_count = 0
   found_count = 0
   missing_count = 0
   configuration_error_count = 0

   check_line_list.append( "[TO_ADAPT]" )

   for original_relative_path in requirement_map[ "TO_ADAPT" ]:
      required_count = required_count + 1

      try:
         adapted_relative_path = get_adapted_relative_path(
            original_relative_path )
      except Exception as error:
         configuration_error_count = configuration_error_count + 1
         check_line_list.append(
            f"[ERROR] {original_relative_path.as_posix()} | {error}" )
         continue

      original_path = code_path / original_relative_path
      adapted_path = code_path / adapted_relative_path

      if not original_path.exists() or not original_path.is_file():
         configuration_error_count = configuration_error_count + 1
         check_line_list.append(
            f"[ERROR] source-not-found: "
            f"02_code/{original_relative_path.as_posix()}" )

      if adapted_path.exists() and adapted_path.is_file():
         found_count = found_count + 1
         code_path_list.append(
            ( adapted_path, Path( FOLDER_NAME_CODE ) / adapted_relative_path ) )
         check_line_list.append(
            f"[OK] {original_relative_path.as_posix()} "
            f"-> {adapted_relative_path.as_posix()}" )
      else:
         missing_count = missing_count + 1
         check_line_list.append(
            f"[MISSING] 02_code/{adapted_relative_path.as_posix()}" )

   check_line_list.append( "" )
   check_line_list.append( "[TO_CREATE]" )

   for created_relative_path in requirement_map[ "TO_CREATE" ]:
      required_count = required_count + 1

      if created_relative_path.name.startswith( COURSE_FILE_PREFIX ):
         configuration_error_count = configuration_error_count + 1
         check_line_list.append(
            f"[ERROR] TO_CREATE-file-must-not-start-with-{COURSE_FILE_PREFIX}: "
            f"{created_relative_path.as_posix()}" )
         continue

      created_path = code_path / created_relative_path

      if created_path.exists():
         found_count = found_count + 1
         code_path_list.append(
            ( created_path, Path( FOLDER_NAME_CODE ) / created_relative_path ) )
         check_line_list.append(
            f"[OK] 02_code/{created_relative_path.as_posix()}" )
      else:
         missing_count = missing_count + 1
         check_line_list.append(
            f"[MISSING] 02_code/{created_relative_path.as_posix()}" )

   check_line_list.append( "" )
   check_line_list.append( "[OTHER]" )

   for other_relative_path in requirement_map[ "OTHER" ]:
      required_count = required_count + 1
      other_path = mop_path / other_relative_path

      if other_path.exists():
         found_count = found_count + 1
         other_path_list.append(
            ( other_path, other_relative_path ) )
         check_line_list.append(
            f"[OK] {other_relative_path.as_posix()}" )
      else:
         missing_count = missing_count + 1
         check_line_list.append(
            f"[MISSING] {other_relative_path.as_posix()}" )

   status_ok = \
      missing_count == 0 and configuration_error_count == 0

   return {
      "status_ok": status_ok,
      "required_count": required_count,
      "found_count": found_count,
      "missing_count": missing_count,
      "configuration_error_count": configuration_error_count,
      "check_line_list": check_line_list,
      "code_path_list": code_path_list,
      "other_path_list": other_path_list
   }


# ----------------------------------------------------------------------
def get_submission_check_path( mop_path ):
   return mop_path / FOLDER_NAME_REPORT / SUBMISSION_CHECK_FILE_NAME


def write_submission_check(
   mop_path,
   requirements_file_path,
   validation_result
):
   report_path = mop_path / FOLDER_NAME_REPORT
   report_path.mkdir( parents = True, exist_ok = True )

   check_path = get_submission_check_path( mop_path )

   line_list = [
      "PTS | mLDm | submission check",
      "",
      f"MoP: {mop_path.name}",
      f"requirements: {requirements_file_path.relative_to( mop_path ).as_posix()}",
      ""
   ]

   line_list.extend( validation_result[ "check_line_list" ] )

   line_list.extend( [
      "",
      "summary:",
      f"required: {validation_result['required_count']}",
      f"found: {validation_result['found_count']}",
      f"missing: {validation_result['missing_count']}",
      f"configuration-errors: {validation_result['configuration_error_count']}",
      "",
      "STATUS: " + ( "OK" if validation_result[ "status_ok" ] else "ERROR" ),
      ""
   ] )

   check_path.write_text(
      "\n".join( line_list ),
      encoding = "utf-8" )

   print_info( f"submission-check-written: {check_path}" )
   return check_path


def write_submission_check_error( mop_path, error_message ):
   report_path = mop_path / FOLDER_NAME_REPORT
   report_path.mkdir( parents = True, exist_ok = True )

   check_path = get_submission_check_path( mop_path )

   check_path.write_text(
      "\n".join( [
         "PTS | mLDm | submission check",
         "",
         f"MoP: {mop_path.name}",
         "",
         f"[ERROR] {error_message}",
         "",
         "STATUS: ERROR",
         ""
      ] ),
      encoding = "utf-8" )

   print_info( f"submission-check-written: {check_path}" )
   return check_path


# ----------------------------------------------------------------------
def should_exclude_path( relative_path ):
   if any( part in EXCLUDE_FOLDER_NAMES for part in relative_path.parts ):
      return True

   for pattern in EXCLUDE_FILE_PATTERNS:
      if fnmatch.fnmatch( relative_path.name, pattern ):
         return True

   return False


def write_zip_entry(
   zip_file,
   source_path,
   archive_path,
   added_archive_name_set
):
   archive_name = archive_path.as_posix()

   if source_path.is_dir() and not archive_name.endswith( "/" ):
      archive_name = archive_name + "/"

   if archive_name in added_archive_name_set:
      return 0

   zip_file.write( source_path, arcname = archive_name )
   added_archive_name_set.add( archive_name )

   return 0 if source_path.is_dir() else 1


def add_path_to_zip(
   zip_file,
   source_path,
   archive_path,
   added_archive_name_set,
   apply_exclusions_to_children = True
):
   file_count = write_zip_entry(
      zip_file,
      source_path,
      archive_path,
      added_archive_name_set )

   if not source_path.is_dir():
      return file_count

   for child_path in sorted( source_path.rglob( "*" ) ):
      child_relative_path = child_path.relative_to( source_path )

      if apply_exclusions_to_children and should_exclude_path(
         child_relative_path ):
         continue

      child_archive_path = archive_path / child_relative_path

      file_count = file_count + write_zip_entry(
         zip_file,
         child_path,
         child_archive_path,
         added_archive_name_set )

   return file_count


def add_folder_to_zip(
   zip_file,
   folder_path,
   archive_root_name,
   added_archive_name_set
):
   return add_path_to_zip(
      zip_file,
      folder_path,
      Path( archive_root_name ),
      added_archive_name_set,
      apply_exclusions_to_children = True )


def is_path_inside_folder( path, folder_path ):
   try:
      path.relative_to( folder_path )
      return True
   except ValueError:
      return False


# ----------------------------------------------------------------------
def get_submission_zip_path( workspace_path, mop_path, group_label ):
   zip_file_name = f"{ZIP_PREFIX}_{group_label}_{mop_path.name}.zip"
   return workspace_path / zip_file_name


def remove_stale_submission_zip( zip_file_path ):
   if zip_file_path.exists():
      print_warning( f"removing-stale-submission-zip: {zip_file_path}" )
      zip_file_path.unlink()


def build_submission_zip(
   workspace_path,
   mop_path,
   group_label,
   validation_result
):
   code_path = mop_path / FOLDER_NAME_CODE
   output_path = mop_path / FOLDER_NAME_OUTPUT
   report_path = mop_path / FOLDER_NAME_REPORT

   validate_required_folder( code_path )
   validate_required_folder( output_path )
   validate_required_folder( report_path )

   zip_file_path = get_submission_zip_path(
      workspace_path,
      mop_path,
      group_label )

   if zip_file_path.exists():
      print_info( f"replacing-existing-zip: {zip_file_path}" )
      zip_file_path.unlink()

   print_info( f"zip-target-folder: {workspace_path}" )
   print_info( f"adding-folder: {FOLDER_NAME_CODE} (selected files only)" )
   print_info( f"adding-folder: {FOLDER_NAME_OUTPUT}" )
   print_info( f"adding-folder: {FOLDER_NAME_REPORT}" )

   with zipfile.ZipFile(
      zip_file_path,
      mode = "w",
      compression = zipfile.ZIP_DEFLATED
   ) as zip_file:
      added_archive_name_set = set()
      total_file_count = 0

      total_file_count = total_file_count + write_zip_entry(
         zip_file,
         code_path,
         Path( FOLDER_NAME_CODE ),
         added_archive_name_set )

      for source_path, archive_path in validation_result[ "code_path_list" ]:
         total_file_count = total_file_count + add_path_to_zip(
            zip_file,
            source_path,
            archive_path,
            added_archive_name_set,
            apply_exclusions_to_children = True )

      total_file_count = total_file_count + add_folder_to_zip(
         zip_file,
         output_path,
         FOLDER_NAME_OUTPUT,
         added_archive_name_set )

      total_file_count = total_file_count + add_folder_to_zip(
         zip_file,
         report_path,
         FOLDER_NAME_REPORT,
         added_archive_name_set )

      for source_path, archive_path in validation_result[ "other_path_list" ]:
         if is_path_inside_folder( source_path, output_path ):
            continue

         if is_path_inside_folder( source_path, report_path ):
            continue

         already_selected_in_code = any(
            selected_source_path == source_path
            for selected_source_path, _ in validation_result[ "code_path_list" ] )

         if already_selected_in_code:
            continue

         total_file_count = total_file_count + add_path_to_zip(
            zip_file,
            source_path,
            archive_path,
            added_archive_name_set,
            apply_exclusions_to_children = True )

   print_info( f"submission-created: {zip_file_path}" )
   print_info( f"submission-file-count: {total_file_count}" )

   return zip_file_path


# ----------------------------------------------------------------------
def main():
   context = None
   mop_path = None
   group_label = None
   submission_check_written = False

   try:
      context = detect_execution_context()
      group_label, mop_path = parse_arguments( context )

      workspace_path = context[ "workspace_path" ]

      print_info( f"workspace-detected: {workspace_path}" )
      print_info( f"mop-detected: {mop_path}" )
      print_info( f"group-detected: {group_label}" )

      install_tool_in_workspace( workspace_path )

      validate_required_folder( mop_path / FOLDER_NAME_INPUT )
      validate_required_folder( mop_path / FOLDER_NAME_CODE )
      validate_required_folder( mop_path / FOLDER_NAME_OUTPUT )

      requirements_file_path, requirement_map = \
         read_submission_requirements( mop_path )

      validation_result = validate_submission_requirements(
         mop_path,
         requirement_map )

      write_submission_check(
         mop_path,
         requirements_file_path,
         validation_result )
      submission_check_written = True

      zip_file_path = get_submission_zip_path(
         workspace_path,
         mop_path,
         group_label )

      if not validation_result[ "status_ok" ]:
         remove_stale_submission_zip( zip_file_path )
         raise_error( "submission-validation-failed" )

      build_submission_zip(
         workspace_path,
         mop_path,
         group_label,
         validation_result )

      print_info( "SUCCESS" )
      sys.exit( 0 )

   except Exception as error:
      if mop_path is not None:
         if not submission_check_written:
            write_submission_check_error(
               mop_path,
               str( error ) )

         if context is not None and group_label is not None:
            workspace_path = context[ "workspace_path" ]
            zip_file_path = get_submission_zip_path(
               workspace_path,
               mop_path,
               group_label )
            remove_stale_submission_zip( zip_file_path )

      print( error )
      sys.exit( 1 )


# ----------------------------------------------------------------------
if __name__ == "__main__": main()
