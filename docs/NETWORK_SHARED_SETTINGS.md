# Network Shared Settings

JobDocs supports sharing global settings and history across multiple users on multiple machines over a network. This feature is useful for teams working in a shared environment where consistent configuration and shared history is beneficial.

## Overview

When enabled, JobDocs will:
- Load global settings from a network location
- Save global settings changes to the network location
- Load and save history to a network location
- Keep personal preferences (theme, default tab) stored locally

## Configuration

### Enabling Network Shared Settings

1. Open **File → Settings**
2. Expand **Advanced Settings**
3. Scroll to **Network Shared Settings** section
4. Check **Enable network shared settings**
5. Configure the following paths:
   - **Shared Settings File**: Network path to the shared settings file (e.g., `\\server\share\jobdocs\shared_settings.json`)
   - **Shared History File**: Network path to the shared history file (e.g., `\\server\share\jobdocs\shared_history.json`)
6. Click **Save**

### Network Path Examples

**Windows:**
```
\\server\share\jobdocs\shared_settings.json
\\server\share\jobdocs\shared_history.json
```
Note: On Windows, these files will have the hidden attribute set automatically.

**Linux/macOS:**
```
/mnt/network/jobdocs/shared_settings.json
/mnt/network/jobdocs/shared_history.json
```
Note: On Linux/macOS, if you name the files without a leading dot, they will be automatically renamed to `.shared_settings.json` and `.shared_history.json` to make them hidden.

## How It Works

### Shared Settings

The following settings are shared across all users when network sharing is enabled:

- **Directories**
  - Blueprints directory
  - Customer files directory
  - ITAR blueprints directory
  - ITAR customer files directory

- **File Handling**
  - Link type (hard link, symbolic link, or copy)
  - Blueprint file extensions
  - Allow duplicate jobs setting

- **Folder Structure**
  - Job folder structure template
  - Quote folder path
  - Legacy mode setting

- **Experimental Features**
  - Experimental features toggle
  - Database configuration (type, host, port, name, username, password)

### Personal Settings (NOT Shared)

These settings remain local to each user's machine:

- **UI Style**: Each user can have their own theme preference
- **Default Tab**: Each user can set which tab opens by default

### Shared History

When network sharing is enabled, all users share:
- Customer list and autocomplete data
- Recent jobs list

This ensures everyone has access to the same customer database and can see recently created jobs.

## Fallback Behavior

JobDocs is designed to be resilient to network issues:

### Loading Settings
1. If network sharing is enabled, JobDocs attempts to load from the network path
2. If the network file doesn't exist or can't be accessed, it falls back to local settings
3. Personal preferences are always loaded from local settings

### Saving Settings
1. Local settings are always saved (for personal preferences and network configuration)
2. If network sharing is enabled, shared settings are saved to the network location
3. If the network save fails, an error dialog appears but local settings are still saved

### Loading History
1. If network sharing is enabled, JobDocs attempts to load from the network path
2. If the network file doesn't exist or can't be accessed, it falls back to local history
3. If no local history exists, starts with empty history

### Saving History
1. If network sharing is enabled, history is saved to the network location only
2. If the network save fails, an error dialog appears
3. If network sharing is disabled, history is saved locally

## Setup Recommendations

### For Teams

1. **Designate a network location**: Create a shared folder on your file server (e.g., `\\fileserver\shared\jobdocs\`)

2. **Set up initial configuration**: Have one person:
   - Configure all the directory paths and settings
   - Enable network sharing
   - Set the network paths
   - Save settings

3. **Share the network paths**: Distribute the network paths to all team members:
   ```
   Shared Settings: \\fileserver\shared\jobdocs\shared_settings.json
   Shared History: \\fileserver\shared\jobdocs\shared_history.json
   ```

4. **Team members enable sharing**: Each team member:
   - Opens JobDocs settings
   - Enables network shared settings
   - Enters the network paths
   - Saves settings
   - Restarts JobDocs

### For Individual Users

If you're the only user, you can keep network sharing disabled. All settings and history will be stored locally.

## Troubleshooting

### "Network settings file not found"

**Cause**: The network path doesn't exist yet.

**Solution**:
- The file will be created automatically when you first save settings
- Ensure the parent directory exists and you have write permissions

### "Could not load network settings"

**Cause**: Network connection issue or permission problem.

**Solution**:
- Check that the network share is accessible
- Verify you have read permissions to the network files
- Check network connectivity
- JobDocs will fall back to local settings automatically

### "Failed to save network shared settings"

**Cause**: Permission issue or network connectivity problem.

**Solution**:
- Verify you have write permissions to the network location
- Check that no other process has locked the file
- Check network connectivity
- Note: Local settings were still saved successfully

### Settings not syncing between machines

**Checklist**:
1. Is network sharing enabled on both machines?
2. Are both machines pointing to the same network paths?
3. Have you saved settings on the first machine?
4. Have you restarted JobDocs on the second machine after enabling network sharing?
5. Can both machines access the network paths?

## Security Considerations

- Network shared files are stored in plain JSON format
- **Files are automatically hidden** to prevent accidental tampering:
  - On Windows: Hidden file attribute is set
  - On Linux/macOS: Files are prefixed with a dot (e.g., `.shared_settings.json`)
- Database passwords in the experimental features section are stored in plain text
- Ensure the network location has appropriate access controls
- Only share with trusted users on your network
- Consider network file permissions to restrict access
- Users with malicious intent can still access hidden files - this is not a security measure, only a protection against accidental modifications

## Performance

- Settings are loaded once at startup
- Settings are saved when you click "Save" in the settings dialog
- History is loaded once at startup
- History is saved after each job operation
- Network file access is fast on local networks
- If network access is slow, you may experience delays when saving history

## Disabling Network Sharing

To revert to local-only settings:

1. Open **File → Settings**
2. Expand **Advanced Settings**
3. Uncheck **Enable network shared settings**
4. Click **Save**
5. Restart JobDocs

Your local settings and history will be used from now on. The network files remain unchanged.
