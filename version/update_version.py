#!/usr/bin/env python3
"""
Version Update Script for JobDocs

This script helps manage version numbers in the VERSION file.
Supports semantic versioning (MAJOR.MINOR.PATCH) with optional pre-release tags.

Usage:
    python update_version.py                    # Show current version
    python update_version.py patch              # Bump patch version (0.2.0 -> 0.2.1)
    python update_version.py minor              # Bump minor version (0.2.0 -> 0.3.0)
    python update_version.py major              # Bump major version (0.2.0 -> 1.0.0)
    python update_version.py set 1.0.0          # Set specific version
    python update_version.py set 1.0.0-beta     # Set version with pre-release tag
"""

import sys
import re
from pathlib import Path


class VersionManager:
    """Manages version numbering for JobDocs"""

    def __init__(self, version_file: Path = None):
        """Initialize version manager"""
        if version_file is None:
            # VERSION file is in parent directory (JobDocs root)
            version_file = Path(__file__).parent.parent / "VERSION"

        self.version_file = version_file
        self.current_version = self._read_version()

    def _read_version(self) -> str:
        """Read current version from VERSION file"""
        if not self.version_file.exists():
            return "0.1.0"

        return self.version_file.read_text().strip()

    def _write_version(self, version: str):
        """Write version to VERSION file"""
        self.version_file.write_text(f"{version}\n")
        print(f"✓ Version updated: {self.current_version} → {version}")
        self.current_version = version

    def _parse_version(self, version: str) -> dict:
        """
        Parse version string into components.

        Format: MAJOR.MINOR.PATCH[-PRERELEASE]
        Examples: 1.0.0, 0.2.1-alpha, 1.0.0-beta.2
        """
        pattern = r'^(\d+)\.(\d+)\.(\d+)(?:-([a-zA-Z0-9.-]+))?$'
        match = re.match(pattern, version)

        if not match:
            raise ValueError(f"Invalid version format: {version}")

        major, minor, patch, prerelease = match.groups()

        return {
            'major': int(major),
            'minor': int(minor),
            'patch': int(patch),
            'prerelease': prerelease or ''
        }

    def _format_version(self, parts: dict) -> str:
        """Format version components into string"""
        version = f"{parts['major']}.{parts['minor']}.{parts['patch']}"
        if parts['prerelease']:
            version += f"-{parts['prerelease']}"
        return version

    def get_current(self) -> str:
        """Get current version"""
        return self.current_version

    def bump_major(self):
        """Bump major version (1.2.3 -> 2.0.0)"""
        parts = self._parse_version(self.current_version)
        parts['major'] += 1
        parts['minor'] = 0
        parts['patch'] = 0
        parts['prerelease'] = ''  # Remove pre-release tag on major bump

        new_version = self._format_version(parts)
        self._write_version(new_version)

    def bump_minor(self):
        """Bump minor version (1.2.3 -> 1.3.0)"""
        parts = self._parse_version(self.current_version)
        parts['minor'] += 1
        parts['patch'] = 0
        parts['prerelease'] = ''  # Remove pre-release tag on minor bump

        new_version = self._format_version(parts)
        self._write_version(new_version)

    def bump_patch(self):
        """Bump patch version (1.2.3 -> 1.2.4)"""
        parts = self._parse_version(self.current_version)
        parts['patch'] += 1
        parts['prerelease'] = ''  # Remove pre-release tag on patch bump

        new_version = self._format_version(parts)
        self._write_version(new_version)

    def set_version(self, version: str):
        """Set specific version"""
        # Validate format
        self._parse_version(version)
        self._write_version(version)

    def show_info(self):
        """Show current version information"""
        parts = self._parse_version(self.current_version)

        print("=" * 60)
        print("JobDocs Version Information")
        print("=" * 60)
        print(f"Current Version: {self.current_version}")
        print(f"  Major: {parts['major']}")
        print(f"  Minor: {parts['minor']}")
        print(f"  Patch: {parts['patch']}")
        if parts['prerelease']:
            print(f"  Pre-release: {parts['prerelease']}")
        print("=" * 60)
        print("\nNext versions:")

        # Show what bumps would result in
        major_parts = parts.copy()
        major_parts['major'] += 1
        major_parts['minor'] = 0
        major_parts['patch'] = 0
        major_parts['prerelease'] = ''
        print(f"  Major bump:  {self._format_version(major_parts)}")

        minor_parts = parts.copy()
        minor_parts['minor'] += 1
        minor_parts['patch'] = 0
        minor_parts['prerelease'] = ''
        print(f"  Minor bump:  {self._format_version(minor_parts)}")

        patch_parts = parts.copy()
        patch_parts['patch'] += 1
        patch_parts['prerelease'] = ''
        print(f"  Patch bump:  {self._format_version(patch_parts)}")
        print("=" * 60)


def main():
    """Main entry point"""
    manager = VersionManager()

    if len(sys.argv) == 1:
        # No arguments - show current version info
        manager.show_info()
        return

    command = sys.argv[1].lower()

    try:
        if command == "major":
            manager.bump_major()
        elif command == "minor":
            manager.bump_minor()
        elif command == "patch":
            manager.bump_patch()
        elif command == "set":
            if len(sys.argv) < 3:
                print("Error: 'set' command requires a version argument")
                print("Example: python update_version.py set 1.0.0")
                sys.exit(1)
            version = sys.argv[2]
            manager.set_version(version)
        elif command in ["show", "info", "current"]:
            manager.show_info()
        elif command in ["help", "-h", "--help"]:
            print(__doc__)
        else:
            print(f"Error: Unknown command '{command}'")
            print("\nValid commands: major, minor, patch, set, show, help")
            print("Run with --help for more information")
            sys.exit(1)

    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
