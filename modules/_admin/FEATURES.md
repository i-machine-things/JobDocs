# Admin Module - Feature Overview

The Admin module provides comprehensive administrative controls for JobDocs, including first-time setup, user management, and global settings control.

## Features Implemented

### 1. First-Time Setup Wizard (OOBE)

**Automatic First Run**
- Automatically launches on first application startup
- Detects if `oobe_completed` flag is not set
- Can be cancelled and re-run later from Admin tab

**Wizard Screens**
1. **Welcome Screen** - Introduction and overview
2. **Directory Configuration** - Set blueprints and customer files directories
3. **Link Type Selection** - Choose between hard link, symbolic link, or copy
4. **Network Sharing** - Optional configuration for team collaboration
5. **User Authentication** - Optional user login system setup
6. **Completion** - Summary and next steps

**Re-runnable**
- "Run Setup Wizard" button in Admin → System Info tab
- Allows reconfiguration at any time
- Preserves existing settings as defaults

### 2. User Management

**Features**
- Create new user accounts with secure password hashing
- Delete existing users (except current user)
- View all users with full names
- Refresh user list
- Integration with existing `_user_auth` module

**Requirements**
- User authentication module must be enabled (rename `_user_auth` to `user_auth`)
- `user_auth_enabled: true` in settings

**UI Components**
- User list with current user indicator
- Create/Delete/Refresh buttons
- Reuses existing `CreateUserDialog` from user_auth module

### 3. Global Settings Management

**Features**
- View all application settings in table format
- Identify which settings are shared vs. local
- Edit network-shared settings file directly
- JSON validation when saving
- Auto-create network settings file if missing

**Settings Priority (Highest to Lowest)**
1. **Personal settings** from local file (ui_style, default_tab) - always local
2. **Network configuration** from local file (network_shared_enabled, paths) - always local
3. **Global settings** from network file - **TAKES PRECEDENCE** over local
4. Non-personal settings from local file - fallback if network unavailable
5. Default settings - baseline

**Table Columns**
- Setting name
- Current value (truncated if long)
- Shared status (Yes/No - Local)

**Requirements**
- Network sharing must be enabled
- Network settings path must be configured

**How It Works**
When network sharing is enabled, global settings in the network file **override** local settings across all users. This ensures team-wide consistency for:
- Directory paths (blueprints_dir, customer_files_dir, etc.)
- Link type
- Blueprint file extensions
- Job folder structure
- All other non-personal settings

Personal settings (UI style, default tab) and network configuration always remain local to each user.

### 4. System Information

**Displays**
- Application info (module count)
- User authentication status and user count
- Network sharing configuration
- Directory paths (blueprints, customer files, ITAR)
- Configuration (link type, extensions, folder structure)
- History statistics (recent jobs, customers)

**Actions**
- Refresh system info
- Run setup wizard button

## File Structure

```
modules/admin/
├── __init__.py           # Module package
├── module.py             # Main admin module (AdminModule class)
├── oobe_wizard.py        # First-time setup wizard (OOBEWizard class)
├── README.md             # Module documentation
├── FEATURES.md           # This file
└── ui/                   # Future UI files (if needed)
```

## Integration Points

### main.py Changes
1. Added `oobe_completed` to DEFAULT_SETTINGS
2. Added `_run_first_time_setup()` method
3. Automatic OOBE launch on first run with QTimer
4. Graceful fallback if admin module not available

### settings_dialog.py Changes
1. Removed experimental features checkbox
2. Removed experimental features from save method
3. Updated docstring

### Module Loading
- Module order: 90 (appears after History and Reporting)
- Auto-discovered by ModuleLoader
- No changes needed to enable/disable

## Usage Flow

### First-Time User
1. Launch JobDocs
2. OOBE wizard appears automatically after 500ms
3. Complete setup wizard or cancel
4. Settings saved and application ready to use

### Existing User - Re-run Setup
1. Go to Admin tab
2. Click "System Info" sub-tab
3. Click "Run Setup Wizard" button
4. Complete wizard to update settings
5. Restart recommended for full effect

### User Management (if enabled)
1. Enable user_auth module (remove underscore)
2. Set `user_auth_enabled: true`
3. Restart application
4. Go to Admin → User Management
5. Create/delete users as needed

### Global Settings Management (if enabled)
1. Enable network sharing in Settings → Advanced
2. Configure network paths
3. Go to Admin → Global Settings
4. View/edit shared settings
5. Changes affect all users

## Security Considerations

1. **Password Storage**: Uses PBKDF2-HMAC-SHA256 with 100k iterations
2. **Network Files**: Hidden to prevent accidental tampering
3. **User Validation**: Cannot delete currently logged-in user
4. **JSON Validation**: Settings file validated before saving
5. **Permission Checks**: User auth module availability checked gracefully

## Future Enhancements

Potential additions:
- User roles and permissions (admin, standard, read-only)
- Audit logging of administrative actions
- Backup/restore settings functionality
- Import/export user accounts
- Password reset functionality
- Session management and timeout
- Multi-factor authentication
- LDAP/Active Directory integration
