#!/usr/bin/env python3
BANNER = \
"""
# ----------------------------------------------------------------------
# PTS | Paulo Trigo Silva
# mLDm | MoP
# submission ZIP builder — rev01 (MoP and TeP)
# rev01-v01
# ----------------------------------------------------------------------
"""


"""
# ----------------------------------------------------------------------
the requirements file is always located at:
    01_input/_mLDm_xx_submission_requirements_rev01.txt

three independent sections:
    [TO_ADAPT]  original instructor files whose adapted copies must exist
    [TO_EXIST]  local artefacts that must exist, not necessarily submitted
    [TO_ZIP]    the exhaustive list of files/directories to put in the ZIP

the generated 04_report/submission_check.txt is always included once
- only structural validation is performed; the contents are not graded

run from activity/02_code:
    python3 _mLDm_xx_build_submission_zip_rev01.py 3

run from mLDm_MoP_workspace (installed copy):
    python3 _mLDm_xx_build_submission_zip_rev01.py G03 MoP_04
    python3 _mLDm_xx_build_submission_zip_rev01.py 3 _TeP_01_example

# ----------------------------------------------------------------------
"""


# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
from __future__ import annotations

from dataclasses import dataclass
from fnmatch import fnmatchcase
import hashlib
import ntpath
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import sys
import tempfile
import unicodedata
import zipfile
# ----------------------------------------------------------------------


VERSION = "rev01"
SCRIPT_NAME = "_mLDm_xx_build_submission_zip_rev01.py"
REQUIREMENTS_NAME = "_mLDm_xx_submission_requirements_rev01.txt"
WORKSPACE_NAME = "mLDm_MoP_workspace"
REPORT_REL = "04_report/submission_check.txt"
SECTIONS = ("TO_ADAPT", "TO_EXIST", "TO_ZIP")
TEACHER_PREFIX = "_mLDm_"
EXCLUDED_DIRS = {"__pycache__", ".ipynb_checkpoints", "__macosx"}
EXCLUDED_FILES = (
    ".ds_store", "._*", "thumbs.db", "desktop.ini", "*.pyc", "*.pyo",
    "*~", "*.swp", "*.swo", "submitted_*.zip",
)


class ConfigurationError(Exception):
    """Malformed requirements, unsafe path, or ambiguous ZIP selection."""


class MissingArtefact(Exception):
    """Required local artefact is not present in the expected form."""


@dataclass(frozen=True)
class Finding:
    section: str
    name: str
    status: str
    detail: str = ""


@dataclass(frozen=True)
class Context:
    mode: str
    workspace: Path
    activity: Path
    group: str
    archive_name: str

    @property
    def archive_path(self) -> Path:
        return self.workspace / self.archive_name

    @property
    def report_path(self) -> Path:
        return self.activity / REPORT_REL


# ---------------------------------------------------------------------------
# invocation and installation
# ---------------------------------------------------------------------------
def normalize_group(value: str) -> str:
    match = re.fullmatch(r"(?:[Gg])?([0-9]+)", value)
    if not match:
        raise ConfigurationError(f"Invalid group: {value!r}; expected 1..99 or G01..G99")
    number = int(match.group(1))
    if not 1 <= number <= 99:
        raise ConfigurationError(f"Group out of range (1..99): {value!r}")
    return f"G{number:02d}"


def activity_name_is_valid(name: str) -> bool:
    return ((name.startswith("MoP_") and len(name) > len("MoP_")) or
            (name.startswith("_TeP_") and len(name) > len("_TeP_")))


def is_plain_directory(path: Path, purpose: str) -> bool:
    if path.is_symlink():
        raise ConfigurationError(f"Symbolic link not allowed for {purpose}: {path}")
    return path.is_dir()


def detect_context(arguments: list[str]) -> Context:
    script = Path(__file__).absolute()
    location = script.parent
    if location.name == "02_code":
        if len(arguments) != 1:
            raise ConfigurationError("From 02_code, use: python3 " + SCRIPT_NAME + " GROUP")
        activity = location.parent
        workspace = activity.parent
        mode = "02_code"
    elif location.name == WORKSPACE_NAME:
        if len(arguments) != 2:
            raise ConfigurationError("From workspace, use: python3 " + SCRIPT_NAME + " GROUP ACTIVITY")
        workspace = location
        name = arguments[1]
        if (not activity_name_is_valid(name) or name in (".", "..") or
                "/" in name or "\\" in name or ":" in name):
            raise ConfigurationError(f"Invalid activity folder name: {name!r}")
        activity = workspace / name
        mode = "workspace"
    else:
        raise ConfigurationError(
            f"Place {SCRIPT_NAME} in activity/02_code or at the root of {WORKSPACE_NAME}"
        )

    if workspace.name != WORKSPACE_NAME or not is_plain_directory(workspace, "workspace"):
        raise ConfigurationError(f"Workspace folder must be named {WORKSPACE_NAME}")
    if not activity_name_is_valid(activity.name) or activity.parent != workspace:
        raise ConfigurationError(f"Activity must be a direct MoP_... or _TeP_... child: {activity}")
    if not is_plain_directory(activity, "activity"):
        raise ConfigurationError(f"Activity directory is missing: {activity}")
    for required in ("01_input", "02_code", "03_output"):
        if not is_plain_directory(activity / required, required):
            raise ConfigurationError(f"Required activity directory is missing: {activity / required}")
    group = normalize_group(arguments[0])
    clean_name = activity.name.lstrip("_") if activity.name.startswith("_") else activity.name
    return Context(mode, workspace, activity, group, f"submitted_{group}_{clean_name}.zip")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def install_or_verify_script(ctx: Context) -> None:
    source = ctx.activity / "02_code" / SCRIPT_NAME
    installed = ctx.workspace / SCRIPT_NAME
    if source.is_symlink() or not source.is_file():
        raise ConfigurationError(f"Activity copy of rev01 is missing: {source}")
    if ctx.mode == "workspace":
        if installed.is_symlink() or not installed.is_file():
            raise ConfigurationError("Installed workspace script is missing or is a symbolic link")
        if sha256_file(source) != sha256_file(installed):
            raise ConfigurationError(
                "The workspace and 02_code copies differ. Run the rev01 script "
                "from the activity/02_code first to update the workspace copy."
            )
        return
    if installed.is_symlink():
        raise ConfigurationError(f"Workspace script destination is a symbolic link: {installed}")
    # Always install atomically; invoking the activity's copy is authoritative.
    descriptor, temporary_name = tempfile.mkstemp(prefix=".mldm-rev01-install-", dir=ctx.workspace)
    os.close(descriptor)
    temporary = Path(temporary_name)
    try:
        shutil.copy2(source, temporary)
        os.replace(temporary, installed)
    finally:
        temporary.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# requirements parser and path safety
# ---------------------------------------------------------------------------
def parse_requirements(path: Path) -> tuple[dict[str, list[str]], list[str]]:
    if path.is_symlink() or not path.is_file():
        raise ConfigurationError(f"Requirements file missing or symbolic link: {path}")
    entries: dict[str, list[str]] = {section: [] for section in SECTIONS}
    seen: dict[str, set[str]] = {section: set() for section in SECTIONS}
    warnings: list[str] = []
    section: str | None = None
    with path.open("r", encoding="utf-8-sig") as handle:
        for line_no, raw_line in enumerate(handle, 1):
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("[") and line.endswith("]"):
                section = line[1:-1].strip().upper()
                if section not in SECTIONS:
                    raise ConfigurationError(f"Line {line_no}: unknown section [{section}]")
                continue
            if section is None:
                raise ConfigurationError(f"Line {line_no}: entry before any section: {line!r}")
            if line in seen[section]:
                warnings.append(f"Repeated [{section}] entry ignored: {line}")
                continue
            seen[section].add(line)
            entries[section].append(line)
    return entries, warnings


def normalized_relpath(raw: str) -> str:
    if not raw or raw.strip() != raw or "\x00" in raw:
        raise ConfigurationError(f"Invalid relative path: {raw!r}")
    if "\\" in raw or ntpath.splitdrive(raw)[0] or raw.startswith("/"):
        raise ConfigurationError(f"Absolute/Windows/ambiguous path not allowed: {raw!r}")
    if any(character in raw for character in ("*", "?", "[", "]")):
        raise ConfigurationError(f"Patterns are not supported: {raw!r}")
    if any(ord(char) < 32 for char in raw):
        raise ConfigurationError(f"Control character in path: {raw!r}")
    parts = raw.rstrip("/").split("/")
    if not parts or any(part in ("", ".", "..") for part in parts):
        raise ConfigurationError(f"Empty, dot or traversal component in path: {raw!r}")
    if any(":" in part for part in parts):
        raise ConfigurationError(f"Nonportable ':' in path: {raw!r}")
    return PurePosixPath(*parts).as_posix()


def safe_activity_path(activity: Path, relative: str) -> Path:
    # The relative argument is already normalized and syntactically safe.
    candidate = activity
    for part in PurePosixPath(relative).parts:
        candidate = candidate / part
        if candidate.is_symlink():
            raise ConfigurationError(f"Symbolic link is not allowed: {relative}")
    # Defence in depth, including for previously unencountered path forms.
    try:
        candidate.resolve(strict=False).relative_to(activity.resolve(strict=True))
    except (OSError, ValueError) as exc:
        raise ConfigurationError(f"Path escapes the activity: {relative}") from exc
    return candidate


def excluded_technical(relative: str) -> bool:
    parts = PurePosixPath(relative).parts
    if any(part.casefold() in EXCLUDED_DIRS for part in parts[:-1]):
        return True
    name = parts[-1].casefold()
    return any(fnmatchcase(name, pattern.casefold()) for pattern in EXCLUDED_FILES)


def excluded_directory(relative: str) -> bool:
    return PurePosixPath(relative).name.casefold() in EXCLUDED_DIRS


def reject_explicit_technical(relative: str) -> None:
    if excluded_technical(relative) or excluded_directory(relative):
        raise ConfigurationError(f"Technically excluded artefact cannot be required: {relative}")


def ignored_in_recursive_selection(relative: str) -> bool:
    if excluded_technical(relative):
        return True
    parts = PurePosixPath(relative).parts
    return bool(parts and parts[0] == "02_code" and parts[-1].startswith(TEACHER_PREFIX))


def regular_file(path: Path) -> bool:
    return path.is_file() and not path.is_symlink()


def expand_directory(activity: Path, directory: Path) -> dict[str, Path]:
    """Expand recursively without symlinks, excluding technical files and originals."""
    chosen: dict[str, Path] = {}

    def walk(current: Path) -> None:
        try:
            children = sorted(current.iterdir(), key=lambda x: x.name)
        except OSError as exc:
            raise ConfigurationError(f"Cannot list directory {current}: {exc}") from exc
        for child in children:
            relative = child.relative_to(activity).as_posix()
            if excluded_directory(relative) or excluded_technical(relative):
                continue
            if child.is_symlink():
                raise ConfigurationError(f"Symbolic link in selected directory: {relative}")
            if child.is_dir():
                walk(child)
            elif child.is_file():
                if ignored_in_recursive_selection(relative) or relative == REPORT_REL:
                    continue
                chosen[relative] = child
            else:
                raise ConfigurationError(f"Unsupported filesystem entry in selection: {relative}")

    walk(directory)
    return chosen


def portable_key(name: str) -> str:
    return unicodedata.normalize("NFC", name).casefold()


def validate_archive_map(selected: dict[str, Path]) -> None:
    """Reject nonportable case/Unicode aliases and file/directory collisions."""
    aliases: dict[tuple[str, ...], tuple[str, ...]] = {}
    file_keys: set[tuple[str, ...]] = set()
    for archive_name in sorted(selected):
        parts = PurePosixPath(archive_name).parts
        normalized = tuple(portable_key(part) for part in parts)
        file_keys.add(normalized)
        for length in range(1, len(parts) + 1):
            key = normalized[:length]
            spelling = parts[:length]
            previous = aliases.get(key)
            if previous is not None and previous != spelling:
                raise ConfigurationError(
                    f"Nonportable ZIP name collision: "
                    f"{'/'.join(previous)!r} vs {'/'.join(spelling)!r}"
                )
            aliases[key] = spelling
    for archive_name in selected:
        normalized = tuple(portable_key(part) for part in PurePosixPath(archive_name).parts)
        for length in range(1, len(normalized)):
            if normalized[:length] in file_keys:
                raise ConfigurationError(f"ZIP file/directory collision: {archive_name}")


# ---------------------------------------------------------------------------
# structural checks and archive manifest
# ---------------------------------------------------------------------------
def assess(ctx: Context, entries: dict[str, list[str]], warnings: list[str]) -> tuple[list[Finding], dict[str, Path]]:
    findings: list[Finding] = []
    chosen: dict[str, Path] = {}

    def record(section: str, raw: str, action) -> None:
        try:
            detail = action()
            findings.append(Finding(section, raw, "OK", detail or ""))
        except MissingArtefact as exc:
            findings.append(Finding(section, raw, "MISSING", str(exc)))
        except (ConfigurationError, OSError) as exc:
            findings.append(Finding(section, raw, "ERROR", str(exc)))

    for raw in entries["TO_ADAPT"]:
        def adapt(raw=raw) -> str:
            relative = normalized_relpath(raw)
            reject_explicit_technical(relative)
            path = safe_activity_path(ctx.activity, relative)
            if not path.name.startswith(TEACHER_PREFIX) or len(path.name) <= len(TEACHER_PREFIX):
                raise ConfigurationError("[TO_ADAPT] original filename must start with _mLDm_")
            if not regular_file(path):
                raise ConfigurationError(f"Instructor original missing or not a regular file: {relative}")
            adapted_rel = (PurePosixPath(relative).parent / path.name[len(TEACHER_PREFIX):]).as_posix()
            adapted = safe_activity_path(ctx.activity, adapted_rel)
            reject_explicit_technical(adapted_rel)
            if not regular_file(adapted):
                raise MissingArtefact(f"Adapted copy not found: {adapted_rel}")
            if adapted.samefile(path):
                raise ConfigurationError(f"Adapted copy is the same file as original: {adapted_rel}")
            return f"Adapted copy: {adapted_rel}"
        record("TO_ADAPT", raw, adapt)

    for raw in entries["TO_EXIST"]:
        def exist(raw=raw) -> str:
            relative = normalized_relpath(raw)
            reject_explicit_technical(relative)
            path = safe_activity_path(ctx.activity, relative)
            if not path.exists():
                raise MissingArtefact(f"Not found: {relative}")
            if not (path.is_file() or path.is_dir()):
                raise ConfigurationError(f"Not a regular file or directory: {relative}")
            return "File" if path.is_file() else "Directory"
        record("TO_EXIST", raw, exist)

    for raw in entries["TO_ZIP"]:
        def include(raw=raw) -> str:
            relative = normalized_relpath(raw)
            reject_explicit_technical(relative)
            path = safe_activity_path(ctx.activity, relative)
            if relative == REPORT_REL:
                # The check is generated by this script, even on a first run.
                if path.is_symlink():
                    raise ConfigurationError(f"Generated report is a symbolic link: {relative}")
                return "Automatic report (included once)"
            if not path.exists():
                raise MissingArtefact(f"Not found: {relative}")
            if path.is_file():
                new = {relative: path}
            elif path.is_dir():
                new = expand_directory(ctx.activity, path)
                if not new:
                    raise MissingArtefact(f"Directory has no eligible files: {relative}")
            else:
                raise ConfigurationError(f"Not a regular file or directory: {relative}")
            for archive_name, source in new.items():
                prior = chosen.get(archive_name)
                if prior is not None and prior != source:
                    raise ConfigurationError(f"Different files target the same ZIP name: {archive_name}")
            chosen.update(new)
            return f"{len(new)} eligible file(s)"
        record("TO_ZIP", raw, include)

    chosen[REPORT_REL] = ctx.report_path
    try:
        validate_archive_map(chosen)
    except ConfigurationError as exc:
        findings.append(Finding("ZIP_MANIFEST", "archive paths", "ERROR", str(exc)))

    return findings, dict(sorted(chosen.items()))


def report_text(ctx: Context, findings: list[Finding], warnings: list[str],
                selected: dict[str, Path], status: str) -> str:
    required = len([item for item in findings if item.section in SECTIONS])
    found = sum(item.status == "OK" for item in findings)
    missing = sum(item.status == "MISSING" for item in findings)
    errors = sum(item.status == "ERROR" for item in findings)
    lines = [
        "PTS | MLDM | Submission verification | rev01",
        "=" * 68,
        f"activity: {ctx.activity.name}",
        f"group: {ctx.group}",
        f"requirements: 01_input/{REQUIREMENTS_NAME}",
        f"archive: {ctx.archive_name}",
        "",
    ]
    for section in SECTIONS:
        lines.append(f"[{section}]")
        subset = [item for item in findings if item.section == section]
        if not subset:
            lines.append("  (none)")
        for item in subset:
            detail = f" | {item.detail}" if item.detail else ""
            lines.append(f"  [{item.status}] {item.name}{detail}")
        lines.append("")
    for item in findings:
        if item.section not in SECTIONS:
            lines.append(f"  [{item.status}] {item.section}: {item.detail}")
    if warnings:
        lines.append("Warnings:")
        lines.extend(f"  - {warning}" for warning in warnings)
        lines.append("")
    lines.append("Selected ZIP entries:")
    lines.extend(f"  {name}" for name in selected)
    lines.append("")
    lines.extend([
        f"zip-entries: {len(selected)}",
        f"required: {required}",
        f"found: {found}",
        f"missing: {missing}",
        f"configuration-errors: {errors}",
        f"STATUS: {status}",
        "",
        "Note: This tool checks file presence/structure only, not the semantic",
        "correctness of notebooks, models, datasets, or predictions.",
    ])
    return "\n".join(lines) + "\n"


def write_report(path: Path, body: str) -> None:
    parent = path.parent
    if parent.is_symlink():
        raise ConfigurationError(f"Report directory is a symbolic link: {parent}")
    parent.mkdir(parents=True, exist_ok=True)
    if path.is_symlink():
        raise ConfigurationError(f"Report path is a symbolic link: {path}")
    fd, tmp_name = tempfile.mkstemp(prefix=".submission-check-", suffix=".tmp", dir=parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as output:
            output.write(body)
        os.replace(tmp_name, path)
    finally:
        Path(tmp_name).unlink(missing_ok=True)


def produce_zip(ctx: Context, selected: dict[str, Path]) -> None:
    destination = ctx.archive_path
    fd, temp_name = tempfile.mkstemp(prefix=".mldm-rev01-zip-", suffix=".zip.tmp", dir=ctx.workspace)
    os.close(fd)
    temporary = Path(temp_name)
    try:
        with zipfile.ZipFile(temporary, mode="w", compression=zipfile.ZIP_DEFLATED,
                             compresslevel=6, allowZip64=True) as archive:
            for relative, source in selected.items():
                # Reject swapped-in symlinks and missing files at write time.
                checked_source = safe_activity_path(ctx.activity, relative)
                if checked_source != source or not regular_file(source):
                    raise ConfigurationError(f"Selected source changed or vanished: {relative}")
                archive.write(source, arcname=relative)
        with zipfile.ZipFile(temporary, mode="r") as archive:
            actual = archive.namelist()
            if len(actual) != len(set(actual)) or set(actual) != set(selected):
                raise ConfigurationError("ZIP content mismatch or duplicate archive names")
            if archive.testzip() is not None:
                raise ConfigurationError("ZIP CRC integrity check failed")
            validate_archive_map({name: selected[name] for name in actual})
        os.replace(temporary, destination)
    finally:
        temporary.unlink(missing_ok=True)


def remove_old_zip(ctx: Context) -> None:
    if ctx.archive_path.is_symlink():
        raise ConfigurationError(f"Archive destination is a symbolic link: {ctx.archive_path}")
    if ctx.archive_path.exists():
        if not ctx.archive_path.is_file():
            raise ConfigurationError(f"Archive destination is not a file: {ctx.archive_path}")
        ctx.archive_path.unlink()


def run(ctx: Context) -> bool:
    findings: list[Finding] = []
    warnings: list[str] = []
    selected: dict[str, Path] = {REPORT_REL: ctx.report_path}
    try:
        # Check for conflicting script versions BEFORE any activity validation.
        install_or_verify_script(ctx)
        entries, warnings = parse_requirements(ctx.activity / "01_input" / REQUIREMENTS_NAME)
        findings, selected = assess(ctx, entries, warnings)
    except (ConfigurationError, OSError, UnicodeError) as exc:
        findings.append(Finding("SETUP", "requirements or execution context", "ERROR", str(exc)))

    passed = all(item.status == "OK" for item in findings)
    status = "OK" if passed else "ERROR"
    try:
        write_report(ctx.report_path, report_text(ctx, findings, warnings, selected, status))
    except (ConfigurationError, OSError) as exc:
        print(f"[ERROR] Could not write {REPORT_REL}: {exc}", file=sys.stderr)
        try:
            remove_old_zip(ctx)
        except (ConfigurationError, OSError) as clean_exc:
            print(f"[ERROR] Could not remove old ZIP: {clean_exc}", file=sys.stderr)
        return False

    if not passed:
        try:
            remove_old_zip(ctx)
        except (ConfigurationError, OSError) as exc:
            print(f"[ERROR] Could not remove old ZIP: {exc}", file=sys.stderr)
        for item in findings:
            if item.status != "OK":
                print(f"[{item.status}] {item.section}: {item.name} — {item.detail}", file=sys.stderr)
        print(f"[ERROR] Check {ctx.report_path}", file=sys.stderr)
        return False

    try:
        if ctx.archive_path.is_symlink():
            raise ConfigurationError(f"Archive destination is a symbolic link: {ctx.archive_path}")
        produce_zip(ctx, selected)
    except (ConfigurationError, OSError, zipfile.BadZipFile) as exc:
        findings.append(Finding("ZIP_WRITE", "archive publication", "ERROR", str(exc)))
        try:
            write_report(ctx.report_path, report_text(ctx, findings, warnings, selected, "ERROR"))
            remove_old_zip(ctx)
        except (ConfigurationError, OSError) as clean_exc:
            print(f"[ERROR] Cleanup failed: {clean_exc}", file=sys.stderr)
        print(f"[ERROR] ZIP creation failed: {exc}", file=sys.stderr)
        return False

    print(f"[OK] {ctx.group} | {ctx.activity.name} | {len(selected)} ZIP entries")
    print(f"[OK] {ctx.archive_path}")
    print(f"[OK] {ctx.report_path}")
    return True


def main(argv: list[str]) -> int:
    try:
        ctx = detect_context(argv)
    except ConfigurationError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 2
    return 0 if run(ctx) else 1


# ----------------------------------------------------------------------
if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
# ----------------------------------------------------------------------
