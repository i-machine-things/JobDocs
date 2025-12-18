# Settings Priority in JobDocs

## Overview

JobDocs supports both local and network-shared settings for team collaboration. This document explains how settings are loaded and which values take precedence.

## Settings Priority Order

When network sharing is enabled, settings are loaded in this priority (highest to lowest):

```
┌─────────────────────────────────────────────────────────────┐
│  1. PERSONAL SETTINGS (from local file)                     │
│     - ui_style                                               │
│     - default_tab                                            │
│     Always stays local - never shared                        │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│  2. NETWORK CONFIGURATION (from local file)                 │
│     - network_shared_enabled                                 │
│     - network_settings_path                                  │
│     - network_history_path                                   │
│     Always stays local - controls network access             │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│  3. GLOBAL SETTINGS (from network file) ⭐ TAKES PRECEDENCE │
│     - blueprints_dir                                         │
│     - customer_files_dir                                     │
│     - itar_blueprints_dir                                    │
│     - itar_customer_files_dir                                │
│     - link_type                                              │
│     - blueprint_extensions                                   │
│     - job_folder_structure                                   │
│     - quote_folder_path                                      │
│     - allow_duplicate_jobs                                   │
│     - legacy_mode                                            │
│     - oobe_completed                                         │
│     - user_auth_enabled                                      │
│     Network settings OVERRIDE local for these                │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│  4. LOCAL SETTINGS (from local file)                        │
│     Used as fallback if network unavailable                  │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│  5. DEFAULT SETTINGS (hardcoded in main.py)                 │
│     Baseline values if nothing else is set                   │
└─────────────────────────────────────────────────────────────┘
```

## How It Works

### Without Network Sharing

When `network_shared_enabled = false`:

1. Load defaults
2. Apply local settings
3. Done!

**All settings come from local file.**

### With Network Sharing

When `network_shared_enabled = true`:

1. Load defaults
2. Apply local settings (as base/fallback)
3. **Apply network settings (OVERRIDES local for shared settings)**
4. Re-apply personal settings from local (to ensure they stay local)
5. Re-apply network config from local (to ensure it stays local)

**Result**: Global settings from network file take precedence across all users.

## Example Scenario

### User A's Local Settings

```json
{
  "ui_style": "Fusion",
  "default_tab": 2,
  "blueprints_dir": "/home/userA/blueprints",
  "link_type": "copy",
  "network_shared_enabled": true,
  "network_settings_path": "//server/share/jobdocs-settings.json"
}
```

### User B's Local Settings

```json
{
  "ui_style": "Windows",
  "default_tab": 0,
  "blueprints_dir": "/home/userB/my-prints",
  "link_type": "symbolic",
  "network_shared_enabled": true,
  "network_settings_path": "//server/share/jobdocs-settings.json"
}
```

### Network Shared Settings

```json
{
  "blueprints_dir": "//server/company/blueprints",
  "customer_files_dir": "//server/company/customers",
  "link_type": "hard",
  "blueprint_extensions": [".pdf", ".dwg", ".dxf"],
  "job_folder_structure": "{customer}/{job_folder}/job documents"
}
```

### Resulting Settings

**User A sees:**
- `ui_style`: "Fusion" (from User A local - personal)
- `default_tab`: 2 (from User A local - personal)
- `blueprints_dir`: "//server/company/blueprints" (**from network** ✓)
- `customer_files_dir`: "//server/company/customers" (**from network** ✓)
- `link_type`: "hard" (**from network**, not "copy" ✓)

**User B sees:**
- `ui_style`: "Windows" (from User B local - personal)
- `default_tab`: 0 (from User B local - personal)
- `blueprints_dir`: "//server/company/blueprints" (**from network** ✓)
- `customer_files_dir`: "//server/company/customers" (**from network** ✓)
- `link_type`: "hard" (**from network**, not "symbolic" ✓)

**Both users use the same global settings, but keep their own UI preferences!**

## Benefits

### For Teams
- **Centralized control**: Admin changes network settings file → all users get updates
- **Consistency**: Everyone uses same directories, link type, extensions
- **No individual misconfiguration**: Users can't accidentally use wrong paths
- **Easy onboarding**: New users just point to network file, get correct settings

### For Individuals
- **Personal preferences respected**: UI style and default tab stay local
- **Flexible network setup**: Each user configures their own network paths
- **Graceful fallback**: Works offline with local settings if network unavailable

## Admin Controls

Administrators can:

1. **Edit network settings file** via Admin → Global Settings → "Edit Settings File"
2. **View current values** in the settings table
3. **See which settings are shared** (marked "Yes" in Shared column)
4. **Create network file** if it doesn't exist

## Implementation Details

### Code Location

Settings loading logic: `main.py` → `JobDocsMainWindow.load_settings()`

```python
def load_settings(self) -> Dict[str, Any]:
    # 1. Load defaults
    merged = self.DEFAULT_SETTINGS.copy()

    # 2. Load local settings (base)
    merged.update(local_settings)

    # 3. Load network settings (OVERRIDE for shared keys)
    if network_enabled:
        for key, value in network_settings.items():
            if key not in PERSONAL_SETTINGS and key not in network_config_keys:
                merged[key] = value  # Network wins!

    # 4. Re-apply personal settings (always local)
    for key in PERSONAL_SETTINGS | network_config_keys:
        if key in local_settings:
            merged[key] = local_settings[key]

    return merged
```

### Personal Settings List

Defined in `main.py`:

```python
PERSONAL_SETTINGS = {
    'ui_style',
    'default_tab'
}
```

To add more personal settings, just add them to this set!

## Testing

Run the test script to verify settings priority:

```bash
python3 test_settings_priority.py
```

Expected output:
```
=== SETTINGS PRIORITY TEST ===

PERSONAL SETTINGS (should be from LOCAL):
  ✓ Personal settings correctly preserved from local

NETWORK CONFIG (should be from LOCAL):
  ✓ Network configuration correctly preserved from local

GLOBAL SETTINGS (should be from NETWORK):
  ✓ Global settings correctly use network values

=== ALL TESTS PASSED ===
```

## Troubleshooting

### "Network settings aren't applying"

**Check:**
1. Is `network_shared_enabled: true` in local settings?
2. Is `network_settings_path` correct and accessible?
3. Does the network file exist at that path?
4. Can the application read the network file? (permissions)
5. Is the network file valid JSON? (check syntax)

**Debug:**
- Look at console output when app starts
- Should see: "Loaded network shared settings from: ..."
- Should see: "Global settings take precedence over local settings"

### "Personal settings are being shared"

**Check:**
1. Is the setting in `PERSONAL_SETTINGS`? (check `main.py`)
2. If not, it WILL be shared - this is intentional
3. To make a setting personal, add it to `PERSONAL_SETTINGS` set

### "Can't edit network settings"

**Check:**
1. Do you have write permissions to the network file?
2. Is the file locked by another user?
3. Is the network path accessible?

**Solution:**
- Use Admin → Global Settings → "Edit Settings File"
- Edit on the server directly (requires file access)
- Ask your system admin to update permissions

## Security Considerations

- **Network files are hidden**: Prevents accidental tampering
- **JSON validation**: Settings file validated before saving
- **Graceful fallback**: Uses local settings if network unavailable
- **No passwords stored**: Sensitive data not in settings files
- **Read-only for users**: Most users won't edit network file directly

## Future Enhancements

Potential improvements:
- Setting-level override permissions
- Audit log of network settings changes
- Push notifications when settings change
- Settings versioning and rollback
- Per-group settings (not just global)
