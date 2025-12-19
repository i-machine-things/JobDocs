# Version Management Tools

This directory contains scripts for managing JobDocs version numbers.

## Quick Usage

**Show current version:**
```bash
./version/bump_version.sh
```

**Bump version:**
```bash
./version/bump_version.sh patch    # 0.2.0 → 0.2.1
./version/bump_version.sh minor    # 0.2.0 → 0.3.0
./version/bump_version.sh major    # 0.2.0 → 1.0.0
```

**Set specific version:**
```bash
./version/bump_version.sh set 1.0.0
./version/bump_version.sh set 1.0.0-beta
```

## Files

- `update_version.py` - Core Python version management script
- `bump_version.sh` - Shell wrapper for Linux/macOS
- `bump_version.bat` - Batch wrapper for Windows

## Documentation

See [docs/VERSION_MANAGEMENT.md](../docs/VERSION_MANAGEMENT.md) for complete documentation.
