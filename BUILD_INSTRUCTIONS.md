# JobDocs Build Instructions

This document explains how to create user and admin builds of JobDocs.

## Understanding the Module System

JobDocs uses a simple naming convention for module control:
- **Enabled modules**: Normal directory names (e.g., `modules/admin/`)
- **Disabled modules**: Directory names starting with underscore (e.g., `modules/_admin/`)

The module loader automatically **skips** any module directory that starts with an underscore.

## Build Types

### User Build (Default)
**For regular users - NO admin access**

Admin module is disabled: `modules/_admin/`

This build:
- ✓ Users can create jobs, search, import blueprints
- ✓ Users can access File → Settings for basic preferences
- ✗ Users CANNOT access the Admin tab
- ✗ Users CANNOT change folder locations
- ✗ Users CANNOT manage user accounts
- ✗ Users CANNOT access team settings

**Current Status**: ✓ This is the current configuration

### Admin Build
**For administrators - FULL access including setup**

Admin module is enabled: `modules/admin/`

This build:
- ✓ Everything from user build
- ✓ Admin tab with setup wizard
- ✓ Can change folder locations (with warnings)
- ✓ Can manage user accounts
- ✓ Can configure team settings
- ✓ Can view system information

## How to Switch Between Builds

### Method 1: Manual (Simple)

**To create USER BUILD** (current):
```bash
# Admin module should have underscore prefix
mv modules/admin modules/_admin  # If it exists
```

**To create ADMIN BUILD**:
```bash
# Remove underscore prefix from admin module
mv modules/_admin modules/admin
```

### Method 2: Build Script (Recommended)

Create a `build.sh` script in the project root:

```bash
#!/bin/bash
# JobDocs Build Script

if [ "$1" = "user" ]; then
    echo "Creating USER build..."
    [ -d "modules/admin" ] && mv modules/admin modules/_admin
    echo "✓ User build ready (admin disabled)"

elif [ "$1" = "admin" ]; then
    echo "Creating ADMIN build..."
    [ -d "modules/_admin" ] && mv modules/_admin modules/admin
    echo "✓ Admin build ready (admin enabled)"

else
    echo "Usage: ./build.sh [user|admin]"
    echo "  user  - Create user build (no admin access)"
    echo "  admin - Create admin build (full admin access)"
    exit 1
fi

echo ""
echo "Module status:"
ls -1 modules/ | grep -E "^_?admin"
```

Make it executable:
```bash
chmod +x build.sh
```

Usage:
```bash
./build.sh user   # For user build
./build.sh admin  # For admin build
```

## Building Executable with PyInstaller

After switching to the desired build type:

```bash
# Build the executable
pyinstaller jobdocs.spec

# The executable will be in:
# dist/jobdocs (on Linux/macOS)
# dist/jobdocs.exe (on Windows)
```

The PyInstaller spec file (`jobdocs.spec`) automatically includes all enabled modules and excludes disabled ones (those starting with underscore).

## Testing Builds

### Testing User Build (Current)
```bash
# Ensure admin is disabled
ls modules/ | grep admin
# Should show: _admin

# Run the application
python main.py

# Verify: Admin tab should NOT appear
```

### Testing Admin Build
```bash
# Enable admin module
mv modules/_admin modules/admin

# Run the application
python main.py

# Verify:
# - Admin tab should appear (renamed to "Settings & Setup")
# - Click "Run Setup Wizard" - should show warning if already configured
# - Can manage user accounts, team settings, etc.

# After testing, switch back to user build
mv modules/admin modules/_admin
```

## Deployment Recommendations

### For End Users (Production)
- **Always use USER BUILD**
- Ship with `modules/_admin/` (disabled)
- Users cannot accidentally break the system by changing folder locations
- Simpler, safer interface

### For Administrators/IT Staff
- **Use ADMIN BUILD**
- Ship with `modules/admin/` (enabled)
- Can configure JobDocs during initial deployment
- Can reconfigure if server paths change
- Can manage user accounts

### Hybrid Approach (Recommended)
1. Deploy **ADMIN BUILD** to one designated admin workstation
2. Deploy **USER BUILD** to all other workstations
3. Admin uses their build to configure network shared settings
4. All users benefit from shared configuration
5. Regular users cannot change critical settings

## Current Status Check

Run this to check current build type:
```bash
if [ -d "modules/admin" ]; then
    echo "Current build: ADMIN BUILD"
else
    echo "Current build: USER BUILD"
fi
```

## Quick Reference

| Action | Command |
|--------|---------|
| Switch to user build | `mv modules/admin modules/_admin` |
| Switch to admin build | `mv modules/_admin modules/admin` |
| Check current build | `ls modules/ \| grep admin` |
| Build executable | `pyinstaller jobdocs.spec` |
| Run for testing | `python main.py` |

---

**Note**: The module naming convention (underscore prefix for disabled) applies to ALL modules, not just admin. This same method can be used to enable/disable reporting, user_auth, or any other experimental features.
