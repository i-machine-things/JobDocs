# OOBE and Settings Dialog Improvements

## Issue Fixed

When browsing for network settings and history file locations in both the OOBE wizard and Settings dialog, the file browser did not suggest default filenames. Users had to type the filename manually.

## Solution

Updated both dialogs to suggest sensible default filenames when the Browse button is clicked.

## Changes Made

### 1. OOBE Wizard ([modules/admin/oobe_wizard.py](../modules/admin/oobe_wizard.py))

**Updated `_browse_file()` method:**
- Now accepts optional `default_filename` parameter
- Suggests default filename if no current value exists
- Automatically adds `.json` extension if missing

**Default filenames:**
- Settings file: `jobdocs-settings.json`
- History file: `jobdocs-history.json`

**Browse button connections updated:**
```python
# Settings file browse button
settings_browse_btn.clicked.connect(lambda: self._browse_file(
    self.network_settings_edit,
    "jobdocs-settings.json"
))

# History file browse button
history_browse_btn.clicked.connect(lambda: self._browse_file(
    self.network_history_edit,
    "jobdocs-history.json"
))
```

### 2. Settings Dialog ([settings_dialog.py](../settings_dialog.py))

**Updated `browse_file()` method:**
- Now accepts optional `default_filename` parameter (3rd argument)
- Suggests default filename if no current value exists
- Automatically adds `.json` extension for JSON files

**Browse button connections updated:**
```python
# Settings file browse button
network_settings_btn.clicked.connect(lambda: self.browse_file(
    self.network_settings_edit,
    "JSON Files (*.json)",
    "jobdocs-settings.json"
))

# History file browse button
network_history_btn.clicked.connect(lambda: self.browse_file(
    self.network_history_edit,
    "JSON Files (*.json)",
    "jobdocs-history.json"
))
```

## User Experience Improvements

### Before
1. User clicks "Browse..." button
2. File dialog opens with empty filename field
3. User must navigate to folder AND type filename
4. User must remember to add `.json` extension

### After
1. User clicks "Browse..." button
2. File dialog opens with suggested filename (e.g., `jobdocs-settings.json`)
3. User only needs to navigate to desired folder
4. Filename is pre-filled and ready to save
5. Extension automatically added if forgotten

## Behavior Details

### When field is empty:
- Suggests default filename (e.g., `jobdocs-settings.json`)
- User can accept default or change it

### When field has existing value:
- Uses existing path as starting point
- Preserves user's previous selection

### Extension handling:
- Automatically adds `.json` if user forgets
- Prevents files without proper extension

## Testing

### OOBE Wizard Test
1. Launch JobDocs for first time (OOBE appears)
2. Navigate to "Network Sharing" page
3. Check "Enable network shared settings"
4. Click "Browse..." for Settings File
5. **Verify:** Dialog shows `jobdocs-settings.json` as filename
6. Select a folder and save
7. Click "Browse..." for History File
8. **Verify:** Dialog shows `jobdocs-history.json` as filename

### Settings Dialog Test
1. Go to File → Settings
2. Expand "Advanced Settings"
3. Check "Enable network shared settings"
4. Click "Browse..." for Shared Settings File
5. **Verify:** Dialog shows `jobdocs-settings.json` as filename
6. Click "Browse..." for Shared History File
7. **Verify:** Dialog shows `jobdocs-history.json` as filename

## Benefits

1. **Faster setup:** Users don't need to type filenames
2. **Consistency:** Same filenames used across all users
3. **Fewer errors:** No typos in filenames
4. **Better UX:** Conforms to standard file dialog behavior
5. **Discoverability:** Users learn the recommended filenames

## Files Modified

- [modules/admin/oobe_wizard.py](../modules/admin/oobe_wizard.py)
  - Updated `_browse_file()` method (lines 509-539)
  - Updated browse button connections (lines 286-290, 303-307)

- [settings_dialog.py](../settings_dialog.py)
  - Updated `browse_file()` method (lines 298-329)
  - Updated browse button connections (lines 246-250, 258-262)

## Related Documentation

- [OOBE Features](../modules/admin/FEATURES.md)
- [Settings Priority](SETTINGS_PRIORITY.md)
