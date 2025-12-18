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

## Network-Shared User Accounts (Multi-Machine Support)

JobDocs supports sharing user accounts across multiple machines via a network-shared users file. This allows an admin on one machine to create user accounts that work on all machines in the team.

### How It Works

1. **Admin Machine**: Creates and manages users via Admin tab
2. **Users File**: Stored on network share (e.g., `\\server\shared\jobdocs-users.json`)
3. **User Machines**: Point to the network users file, use centralized accounts

### Configuration

**Via OOBE Wizard** (Recommended for users):
1. Run OOBE wizard on user machine
2. Go to "User Authentication" page
3. Click "🔍 Auto-Search for Shared Users File"
4. Wizard automatically finds and selects the network users file
5. Finish setup - user can now log in with admin-created accounts

**Manual Configuration**:
1. Edit `settings.json`
2. Set `"network_users_path": "\\\\server\\shared\\jobdocs-users.json"`
3. Restart JobDocs
4. Login with credentials created by admin

### Network File Location

The auto-search feature looks for users files in:
- Same directory as `network_settings_path`
- Same directory as `network_history_path`
- Parent directory of `customer_files_dir`
- Common mapped drives (Windows: G:, H:, etc.)

### Admin Workflow (Multi-Machine Team)

1. **Admin sets up first machine**:
   - Enable admin module: `mv modules/_admin modules/admin`
   - Run OOBE wizard, configure directories
   - Enable user authentication
   - Specify network users file path: `\\server\shared\jobdocs-users.json`
   - Create user accounts via Admin tab → Users

2. **Admin distributes settings**:
   - Share network paths with team:
     - Settings: `\\server\shared\jobdocs-settings.json`
     - History: `\\server\shared\jobdocs-history.json`
     - Users: `\\server\shared\jobdocs-users.json`

3. **Users set up their machines**:
   - Install user build (admin module disabled: `_admin`)
   - Run OOBE wizard
   - Enable network sharing (enter network settings/history paths)
   - Enable user authentication
   - Click "Auto-Search" to find network users file
   - Finish wizard, restart, log in with credentials

### Benefits

✓ **Centralized user management**: Admin creates users once, works everywhere
✓ **Automatic discovery**: Users can auto-find the shared users file
✓ **No manual copying**: No need to distribute users.json to each machine
✓ **Password changes sync**: Password changes by admin apply immediately
✓ **Offline fallback**: Local users file used if network unavailable

### Fallback Behavior

When `network_users_path` is configured:

1. **First Try**: Load from network file (preferred)
2. **Fallback**: Load from local file if network unavailable
3. **Saves**: Always save to network file when using network users

This ensures users can still log in if the network is temporarily unavailable (using cached local copy).

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

## User Roles and Access Control

JobDocs implements role-based access control (RBAC) with two user roles:

### Admin Users
- **Can access**: All modules + Admin menu
- **Admin menu includes**:
  - Admin Panel (full Settings & Setup)
  - User Management (create/delete users, set roles)
- **Auto-assigned**: First user created is always admin
- **Display**: Window title shows "(Admin)" indicator

### Regular Users
- **Can access**: All regular modules (Create Job, Search, History, etc.)
- **Cannot access**: Admin Panel, User Management
- **No admin menu**: Admin menu hidden entirely
- **Display**: Window title shows username only

### How It Works

When a user logs in:
1. System checks `is_admin` flag in user record
2. Loads appropriate modules:
   - Admins: All modules (admin accessed via menu, not tabs)
   - Users: Regular modules only (admin module excluded)
3. Shows/hides Admin menu based on role

### Setting User Roles

**First User** (Automatic):
- First user created is automatically an admin
- Happens on first run or when no users exist

**Additional Users** (Via User Management):
- Admin logs in → Admin → User Management
- Create new user → Check "Admin privileges" if needed
- Or edit existing user to promote/demote

**Via Network Users File**:
- Admin edits network users.json directly
- Set `"is_admin": true` or `false` for any user
- Changes apply immediately on next login

## Summary

**user_auth** = Login system (backend, no tab) + Role management
**Admin module** = Configuration + User management (accessible via Admin menu for admins only)

Together they provide:
- Secure login with role-based access
- User account and permission management
- Clean UI (admin features hidden from regular users)
- Prevents accidental configuration damage

Role-based separation:
- Admins: Full access (all modules + Admin menu)
- Users: Regular modules only (no Admin menu)
- First user: Always admin
- Network sync: Roles stored in shared users file
