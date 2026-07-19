#!/usr/bin/env python3
"""Build and validate a Blender-installable Pie Menu Editor ZIP."""

from __future__ import annotations

import argparse
import ast
import fnmatch
from pathlib import Path, PurePosixPath
import sys
import zipfile


ADDON_DIRECTORY = "pie_menu_editor"


class ReleaseIgnore:
    """Match the small rsync-style pattern subset used by .releaseignore."""

    def __init__(self, ignore_file: Path) -> None:
        self.patterns: list[tuple[str, bool, bool]] = []
        for line_number, raw_line in enumerate(
            ignore_file.read_text(encoding="utf-8").splitlines(), start=1
        ):
            pattern = raw_line.strip()
            if not pattern or pattern.startswith("#"):
                continue
            if pattern.startswith("!"):
                raise ValueError(
                    f"{ignore_file}:{line_number}: negated patterns are not supported"
                )
            anchored = pattern.startswith("/")
            directory_only = pattern.endswith("/")
            self.patterns.append((pattern.strip("/"), anchored, directory_only))

    def matches(self, relative_path: PurePosixPath, is_dir: bool) -> bool:
        parts = relative_path.parts
        path_text = relative_path.as_posix()
        for pattern, anchored, directory_only in self.patterns:
            if anchored:
                if directory_only:
                    if path_text == pattern or path_text.startswith(pattern + "/"):
                        return True
                elif fnmatch.fnmatchcase(path_text, pattern):
                    return True
                continue

            if directory_only:
                directory_parts = parts if is_dir else parts[:-1]
                if any(fnmatch.fnmatchcase(part, pattern) for part in directory_parts):
                    return True
            elif fnmatch.fnmatchcase(parts[-1], pattern):
                return True
        return False


def read_addon_version(repo_root: Path) -> str:
    init_file = repo_root / "__init__.py"
    module = ast.parse(init_file.read_text(encoding="utf-8"), filename=str(init_file))
    for statement in module.body:
        if not isinstance(statement, ast.Assign):
            continue
        if not any(isinstance(target, ast.Name) and target.id == "bl_info" for target in statement.targets):
            continue
        bl_info = ast.literal_eval(statement.value)
        version = bl_info.get("version")
        if (
            not isinstance(version, tuple)
            or not version
            or any(not isinstance(item, int) for item in version)
        ):
            break
        return ".".join(str(item) for item in version)
    raise ValueError(f"Unable to read bl_info version from {init_file}")


def collect_files(repo_root: Path) -> list[Path]:
    ignore = ReleaseIgnore(repo_root / ".releaseignore")
    files: list[Path] = []
    for path in sorted(repo_root.rglob("*")):
        relative = PurePosixPath(path.relative_to(repo_root).as_posix())
        if path.is_symlink():
            raise ValueError(f"Release input contains a symlink: {relative}")
        if ignore.matches(relative, path.is_dir()):
            continue
        if path.is_file():
            files.append(path)
    return files


def validate_inputs(repo_root: Path, files: list[Path]) -> None:
    relative_files = {
        PurePosixPath(path.relative_to(repo_root).as_posix()) for path in files
    }
    required_files = {
        PurePosixPath("__init__.py"),
        PurePosixPath("core/__init__.py"),
        PurePosixPath("core/addon.py"),
        PurePosixPath("core/pme.py"),
        PurePosixPath("core/preferences.py"),
        PurePosixPath("LICENSE.md"),
    }
    missing = sorted(required_files - relative_files)
    if missing:
        raise ValueError(f"Missing required add-on file: {missing[0]}")

    root_python_files = sorted(
        path for path in relative_files if len(path.parts) == 1 and path.suffix == ".py"
    )
    if root_python_files != [PurePosixPath("__init__.py")]:
        raise ValueError("The add-on root must contain only __init__.py Python code")


def validate_archive(output: Path) -> int:
    with zipfile.ZipFile(output) as archive:
        members = archive.namelist()
        bad_member = archive.testzip()

    prefix = ADDON_DIRECTORY + "/"
    if not members or any(not member.startswith(prefix) for member in members):
        raise ValueError(f"ZIP must contain exactly one {ADDON_DIRECTORY} root directory")
    if f"{prefix}__init__.py" not in members:
        raise ValueError("ZIP does not contain the add-on entry point")
    if bad_member:
        raise ValueError(f"ZIP CRC validation failed: {bad_member}")

    forbidden_roots = {
        ".git",
        ".github",
        ".agents",
        ".codex",
        ".claude",
        "_dist",
        "build",
        "tools",
    }
    for member in members:
        relative_parts = PurePosixPath(member).parts[1:]
        if relative_parts and relative_parts[0] in forbidden_roots:
            raise ValueError(f"ZIP contains a development path: {member}")
        if "__pycache__" in relative_parts:
            raise ValueError(f"ZIP contains a cache path: {member}")
        if relative_parts and PurePosixPath(member).suffix in {".pyc", ".pyo"}:
            raise ValueError(f"ZIP contains generated Python bytecode: {member}")
    return len(members)


def build_zip(repo_root: Path, output: Path) -> None:
    files = collect_files(repo_root)
    validate_inputs(repo_root, files)

    output.parent.mkdir(parents=True, exist_ok=True)
    output.unlink(missing_ok=True)
    with zipfile.ZipFile(
        output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6
    ) as archive:
        for source in files:
            relative = PurePosixPath(source.relative_to(repo_root).as_posix())
            archive.write(source, (PurePosixPath(ADDON_DIRECTORY) / relative).as_posix())

    try:
        member_count = validate_archive(output)
    except Exception:
        output.unlink(missing_ok=True)
        raise

    size_mib = output.stat().st_size / (1024 * 1024)
    print(f"Built {output} ({size_mib:.2f} MiB, {member_count} files)")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--print-version", action="store_true")
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
    )
    args = parser.parse_args()
    if not args.print_version and args.output is None:
        parser.error("--output is required unless --print-version is used")
    return args


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    if args.print_version:
        print(read_addon_version(repo_root))
        return 0
    build_zip(repo_root, args.output.resolve())
    return 0


if __name__ == "__main__":
    sys.exit(main())
