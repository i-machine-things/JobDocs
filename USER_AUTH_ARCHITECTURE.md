# User Authentication Architecture

## Overview

JobDocs uses a two-module approach for user authentication:

1. **user_auth module** - Backend authentication (NO UI tab)
2. **Admin module** (_admin) - User account management (UI tab, disabled by default)

## How It Works

### user_auth Module (Backend Only)

**Location**: `modules/user_auth/`

**Purpose**: Provides login functionality

**Key Points**:
- ✅ Shows login dialog at startup (if enabled in settings)
- ✅ Handles password verification
- ✅ Manages user sessions
- ❌ Does NOT create a visible tab
- ❌ Does NOT provide user management UI

**Why no module.py?**
- The module loader looks for `module.py` to load tab modules
- Since user_auth is NOT a tab, it has NO `module.py` file
- This prevents it from being loaded as a tab
- It's still importable as a Python package via `from modules.user_auth.user_auth import UserAuth`

**Files**:
```
modules/user_auth/
├── __init__.py                    # Package marker
├── user_auth.py                   # Authentication backend
└── ui/
    ├── login_dialog.py            # Login UI shown at startup
    └── user_management_dialog.py  # UI used by Admin module
```

### Admin Module (Tab with User Management)

**Location**: `modules/_admin/` (disabled by default)

**Purpose**: Administrative controls including user account management

**Key Points**:
- ✅ Creates a visible "Settings & Setup" tab (when enabled)
- ✅ Provides setup wizard
- ✅ Manages user accounts (create, delete users)
- ✅ Manages team settings
- ❌ Disabled by default (underscore prefix)

**User Management Features** (in Admin module):
- View all user accounts
- Create new users
- Delete users (cannot delete currently logged-in user)
- See user details

**Files**:
```
modules/_admin/
├── module.py              # Admin tab module
├── oobe_wizard.py         # Setup wizard
└── ...
```

## Configuration Scenarios

### Scenario 1: No Authentication (Default)
**Configuration**:
- `user_auth_enabled: false` in settings
- Admin module disabled (`_admin`)

**Behavior**:
- ✅ No login required
- ✅ All users have full access
- ❌ Cannot track who makes changes
- ❌ No admin tab visible

**Use Case**: Single user or trusted environment

### Scenario 2: User Authentication Only
**Configuration**:
- `user_auth_enabled: true` in settings
- Admin module disabled (`_admin`)

**Behavior**:
- ✅ Login required at startup
- ✅ User sessions tracked
- ❌ NO way to manage users (must use admin build)
- ❌ No admin tab visible

**Use Case**: User build after initial setup by admin

### Scenario 3: Authentication + Admin (Full Access)
**Configuration**:
- `user_auth_enabled: true` in settings
- Admin module enabled (`admin` - no underscore)

**Behavior**:
- ✅ Login required at startup
- ✅ User sessions tracked
- ✅ Can create/delete users via Admin tab
- ✅ Full configuration access via Admin tab

**Use Case**: Admin build for initial setup and management

## Workflow

### Initial Deployment (Admin)

1. **Build admin version**: `mv modules/_admin modules/admin`
2. **Run application**: `python main.py`
3. **Run setup wizard** (from Admin tab):
   - Configure folder locations
   - Enable user authentication
   - Create first user account
4. **Deploy settings** to network share (if using team sharing)
5. **Build user version**: `mv modules/admin modules/_admin`
6. **Distribute user build** to all workstations

### Daily Use (Users)

1. **Launch JobDocs**: User build (no admin tab)
2. **Login prompt appears** (if user_auth enabled)
3. **Enter credentials**: Username and password
4. **Work normally**: Create jobs, search, etc.
5. **No access to**:
   - Folder location changes
   - User management
   - Critical settings

### User Management (Admin Only)

1. **Launch admin build**: Admin has admin module enabled
2. **Login as admin**
3. **Go to Admin tab → Users sub-tab**
4. **Manage users**:
   - Add new users
   - Remove users
   - View user list

## Enable/Disable Guide

### To Enable User Authentication

**Via OOBE Wizard** (Admin build):
1. Run setup wizard from Admin tab
2. Go to "User Accounts" page
3. Check "Enable user accounts"
4. Finish wizard and restart

**Via Settings File** (Manual):
1. Edit `~/.local/share/JobDocs/settings.json`
2. Set `"user_auth_enabled": true`
3. Restart JobDocs
4. Login dialog appears (create first user if none exist)

### To Disable User Authentication

1. Edit `settings.json`
2. Set `"user_auth_enabled": false`
3. Restart JobDocs
4. No login required

## Security Model

### What's Protected
- Login required before using JobDocs
- Passwords securely hashed (PBKDF2-HMAC-SHA256)
- Cannot guess passwords from hash
- User activity tracked (username in window title)

### What's NOT Protected
- User can access files directly on disk (no file encryption)
- Admin rights on computer bypass authentication
- Settings file can be edited manually

### Recommendations
- Use user authentication for accountability
- Use admin/user builds to prevent accidental configuration changes
- Combine with network shares for team environments
- Use file system permissions to protect sensitive directories

## Build Types Recap

### User Build (Production)
```bash
# Ensure admin is disabled
ls modules/ | grep admin
# Should show: _admin

# Result:
# - No Admin tab
# - Login required (if enabled)
# - Cannot manage users
# - Cannot change folder locations
# - Safe for regular users
```

### Admin Build (Setup/Management)
```bash
# Enable admin
mv modules/_admin modules/admin

# Result:
# - Admin tab visible ("Settings & Setup")
# - Login required (if enabled)
# - CAN manage users
# - CAN change folder locations
# - CAN configure everything
# - For IT staff only
```

## Troubleshooting

### "user_auth module not found"
- Check: `modules/user_auth/user_auth.py` exists
- Check: Directory name is `user_auth` (no underscore)
- The module doesn't need `module.py` to work

### "Cannot manage users"
- This is expected in user build
- Enable admin module: `mv modules/_admin modules/admin`
- Restart application
- Go to Admin tab → Users

### "Login dialog doesn't appear"
- Check: `user_auth_enabled: true` in settings.json
- Check: `modules/user_auth/` exists (no underscore)
- Restart application

### "Admin tab doesn't appear"
- Check: `modules/admin/` exists (no underscore)
- User build has `_admin` (disabled) by design
- This is the intended behavior for user builds

## Summary

**user_auth** = Login system (backend, no tab)
**Admin** = Configuration + User management (tab, disabled by default)

Together they provide:
- Secure login
- User account management
- Build separation (user vs admin)
- Prevents accidental configuration damage

Separately they can be:
- user_auth only: Login without management (requires admin build for setup)
- Admin only: Configuration without authentication
- Both disabled: Open access, simplest setup
- Both enabled: Full control (admin build)
