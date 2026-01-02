# JobDocs

A modular tool for managing blueprint files and customer job directories with support for file linking, ITAR compliance, and comprehensive job tracking.

## Features

- **First-Time Setup Wizard** - Guided OOBE (Out-Of-Box Experience) for easy initial configuration
- **Admin Module** - Centralized user management, global settings control, and system information
- **Modular Plugin Architecture** - Extensible system with drop-in modules
- **Single and Bulk Job Creation** - Create individual jobs or import multiple jobs from CSV
- **Quote Management** - Create quotes that can be converted to jobs
- **Auto-Generate Numbers** - Automatically generate next sequential job/quote number (starting at 10000)
- **Blueprint File Management** - Centralized blueprint storage with hard linking to save disk space
- **ITAR Support** - Separate directories and workflows for ITAR-controlled projects
- **Advanced Search** - Find jobs by customer, job number, description, or drawing number
- **File Organization** - Automatic folder structure creation and file management
- **Import Tools** - Direct import of files to blueprint folders
- **History Tracking** - Keep track of recent jobs and customer information
- **Network Shared Settings** - Global settings take precedence across all users for team consistency
- **User Authentication** - Optional user accounts with secure password storage
  - **Session Tracking** - Monitor which users are currently logged in
  - **Active Session Monitoring** - View logged-in users from the login screen
- **Cross-Platform** - Works on Windows, macOS, and Linux

## Installation

### Requirements
- Python 3.8 or higher
- PyQt6

### Install Dependencies

#### On Debian/Ubuntu:
```bash
sudo apt install python3-pyqt6
```

#### On Arch Linux:
```bash
sudo pacman -S python-pyqt6
```

#### Using pip:
```bash
pip install -r requirements.txt
```

Or install PyQt6 directly:
```bash
pip install PyQt6
```

## Usage

Run the application:

```bash
python main.py
```

### First Time Setup

**Automatic Setup Wizard (Recommended)**

On first launch, JobDocs will automatically present a setup wizard that guides you through:
1. Directory configuration (blueprints and customer files)
2. Link type selection (hard link, symbolic link, or copy)
3. Optional: Network sharing for team collaboration
4. Optional: User authentication

You can re-run the setup wizard anytime from **Admin → System Info → Run Setup Wizard**.

**Manual Setup**

Alternatively, configure settings manually:
1. Go to **File → Settings**
2. Configure your directories:
   - **Blueprints Directory**: Central storage for all blueprint files
   - **Customer Files Directory**: Where job folders will be created
   - **ITAR Directories**: Optional separate directories for ITAR-controlled projects
3. Choose your link type (Hard Link recommended to save disk space)
4. Set blueprint file extensions (default: .pdf, .dwg, .dxf)

### Network Shared Settings (For Teams)

For teams working on multiple machines, JobDocs supports centralized settings management:

**Setup:**
1. Run the **Setup Wizard** and enable network sharing (or go to **File → Settings → Advanced Settings**)
2. Enable **Network Shared Settings**
3. Configure network paths:
   - **Shared Settings File**: `\\server\share\jobdocs-settings.json`
   - **Shared History File**: `\\server\share\jobdocs-history.json`
4. Click Save and restart

**How It Works:**
- **Global settings** (directories, link type, extensions) are stored in the network file
- **Global settings take precedence** over individual user settings
- Administrators edit the network file → all users get updates instantly
- **Personal settings** (UI style, default tab) stay local to each user
- **Network configuration** (paths to network files) stays local to each user

**Benefits:**
- Centralized control - admins manage team-wide settings
- Consistency - everyone uses same directories and configurations
- No misconfiguration - users can't accidentally use wrong paths
- Easy onboarding - new users point to network file and get correct settings

See [docs/SETTINGS_PRIORITY.md](docs/SETTINGS_PRIORITY.md) for detailed priority explanation.

### Creating Quotes

1. Go to the **Create Quote** tab
2. Enter customer name (auto-completes from existing customers)
3. Enter quote number(s):
   - Click **Auto** button to auto-generate next number (starts at 10000)
   - Or manually enter - supports ranges like Q12345-Q12350
4. Enter description
5. Optionally add drawing numbers (comma-separated)
6. Add files by dragging/dropping
7. Click **Create Quote**
8. Use **Copy From...** to copy information from existing quotes or jobs

### Creating Jobs

#### Single Job Creation
1. Go to the **Create Job** tab
2. Enter customer name (auto-completes from history)
3. Enter job number(s):
   - Click **Auto** button to auto-generate next number (starts at 10000)
   - Or manually enter - supports:
     - Single: `12345`
     - Multiple: `12345, 12346, 12347`
     - Range: `12345-12350`
4. Enter description
5. Optionally add drawing numbers (comma-separated)
6. Add files by dragging/dropping or browsing
7. Click **Create Job**
8. Use **Copy From...** to copy information from existing quotes or jobs

#### Bulk Job Creation
1. Go to the **Bulk Create** tab
2. Enter jobs in CSV format (one per line):
   ```
   Customer Name, Job Number, Description, Drawing1, Drawing2...
   ```
3. Click **Validate** to check for errors
4. Click **Create All Jobs**
   - Automatically detects and skips duplicate jobs
   - Shows warning if duplicates are found

Or import from CSV file using the **Import CSV** button.

### Managing Existing Jobs

Use the **Add to Job** tab to:
- Browse existing job folders
- Add files to existing jobs
- Filter by customer or ITAR status
- Choose destination (blueprints only, job folder only, or both)

### Importing Blueprints

Use the **Import Blueprints** tab to:
- Import blueprint files directly to the blueprints directory
- Select customer name
- Choose ITAR or standard blueprints directory
- Automatically creates customer folders

### Searching

The **Search** tab provides powerful search capabilities:
- Search by customer name, job number, description, or drawing
- Two search modes:
  - **Search All Folders** (Legacy mode): Full recursive search through all folders
    - Handles inconsistent folder structures from legacy files
    - Optional: Also search blueprints directories
    - Slower but comprehensive
  - **Strict Format** (Faster): Only searches properly formatted job folders
    - Filter by specific fields (customer, job #, description, drawings)
    - Much faster for well-organized structures
- Double-click results to open job folders
- Right-click for context menu (copy path, open location)

### Administration

The **Admin** tab provides centralized management:

#### User Management
- Create and delete user accounts
- View all registered users in the system
- Secure password storage with PBKDF2-HMAC-SHA256
- Session tracking - monitor active user sessions
- View currently logged-in users from the Login screen (Users tab)
- Automatic session timeout (60 minutes of inactivity)
- **Requirements:** Enable user authentication in setup wizard or settings

#### Global Settings Management
- View all application settings in table format
- Edit network-shared settings file directly
- JSON validation when saving
- See which settings are shared vs. local
- **Requirements:** Network sharing must be enabled

#### System Information
- View application info (module count)
- Check user authentication status
- Review network sharing configuration
- Inspect directory paths and configuration
- View history statistics

#### Setup Wizard
- Re-run first-time setup anytime
- Reconfigure directories, link type, network sharing, and user auth
- Updates all settings at once

## File Structure

JobDocs creates the following directory structure:

```
Customer Files Directory/
├── Customer Name/
│   ├── 12345_Job Description/
│   │   └── job documents/
│   │       ├── blueprint1.pdf (hard link)
│   │       └── other_file.doc (copy)
│   ├── 12346_Another Job/
│   │   └── ...
│   └── Quotes/
│       └── Q12345_Quote Description/
│           ├── blueprint1.pdf (hard link)
│           └── ...

Blueprints Directory/
└── Customer Name/
    ├── blueprint1.pdf (original)
    ├── blueprint2.dwg
    └── ...
```

## Configuration

Configuration files are stored in platform-specific locations:
- **Windows**: `C:\Users\<Username>\AppData\Local\JobDocs`
- **macOS**: `~/Library/Application Support/JobDocs`
- **Linux**: `~/.local/share/JobDocs`

Files stored:
- `settings.json` - Application settings (local and network configuration)
- `history.json` - Recent jobs and customer history (local fallback)
- `users.json` - User accounts (if user authentication is enabled)
- `sessions.json` - Active user sessions (if user authentication is enabled)

### Network Shared Configuration

When network sharing is enabled:
- **Global settings** from network file take precedence over local settings
- **Personal settings** (UI style, default tab) always remain local
- Shared settings stored at configured network path (e.g., `\\server\share\jobdocs-settings.json`)
- Shared history stored at configured network path (e.g., `\\server\share\jobdocs-history.json`)
- Local settings file maintains personal preferences and network paths
- See [docs/SETTINGS_PRIORITY.md](docs/SETTINGS_PRIORITY.md) for priority details

### Settings Priority

When network sharing is enabled, settings are applied in this order (highest to lowest):
1. **Personal settings** from local file (ui_style, default_tab)
2. **Network configuration** from local file (network paths)
3. **Global settings** from network file ⭐ **TAKES PRECEDENCE**
4. Non-personal settings from local file (fallback)
5. Default settings (baseline)

This ensures team-wide consistency while preserving individual preferences.

## Link Types

### Hard Link (Recommended)
- Same file appears in multiple locations
- Takes no extra disk space
- Files stay in sync automatically
- **Limitation**: Only works on same drive/partition

### Symbolic Link
- Creates a shortcut/reference to original file
- Works across different drives
- Original file must not be moved

### Copy
- Duplicates the file
- Uses double disk space
- Files are independent

## Modular Architecture

JobDocs uses a plugin-based architecture:

### Available Modules
1. **Create Quote** - Quote creation and management
2. **Create Job** - Job folder creation with duplicate detection
3. **Add to Job** - Add files to existing jobs
4. **Bulk Create** - Bulk job creation from CSV
5. **Search** - Advanced job search
6. **Import Blueprints** - Import blueprints to customer folders
7. **History** - View recent job history
8. **Admin** - Administrative controls and system management
   - **User Management** - Create/delete user accounts (requires user_auth module)
   - **Global Settings** - View and edit network-shared settings
   - **System Info** - View application and configuration information
   - **Setup Wizard** - Re-run first-time setup anytime
9. **Reporting** (Experimental) - Generate and export reports

### Creating Custom Modules

See [MODULAR_SYSTEM.md](docs/MODULAR_SYSTEM.md) for details on creating custom modules.

## Development

### Project Structure
```
JobDocs/
├── main.py              # Main application
├── core/                # Core framework
│   ├── base_module.py   # Module base class
│   ├── app_context.py   # Shared application context
│   └── module_loader.py # Auto module discovery
├── shared/              # Shared utilities
│   ├── utils.py         # File operations, parsing
│   └── widgets.py       # Custom UI widgets
├── modules/             # Plugin modules
│   ├── quote/           # Quote module
│   ├── job/             # Job module
│   ├── bulk/            # Bulk creation module
│   ├── admin/           # Admin module
│   │   ├── module.py    # Admin functionality
│   │   └── oobe_wizard.py # First-time setup wizard
│   ├── user_auth/       # User authentication module
│   │   ├── user_auth.py # Authentication & session tracking
│   │   └── ui/          # Login dialog and user management UI
│   └── ...
├── settings_dialog.py   # Settings UI
├── docs/                # Documentation
│   ├── SETTINGS_PRIORITY.md  # Settings priority explanation
│   ├── OOBE_IMPROVEMENTS.md  # OOBE wizard improvements
│   └── ...
├── old/                 # Legacy code (archived)
├── requirements.txt     # Python dependencies
└── README.md            # This file
```

### Building

See [BUILD.md](docs/BUILD.md) for instructions on creating standalone executables.

### Testing

See [TESTING.md](docs/TESTING.md) for testing instructions.

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Support

For issues or questions, please visit:
https://github.com/i-machine-things/JobDocs

## Contributing

Contributions are welcome! Feel free to submit issues or pull requests.

### Development Notes
- The modular architecture allows for easy extension and customization
- Each module is self-contained and can be developed independently
- Use `modules/_template/` as a starting point for new modules

---

**Note**: ITAR (International Traffic in Arms Regulations) compliance is the user's responsibility. This tool only provides organizational separation of ITAR and non-ITAR files.

## Acknowledgments

This project was developed with assistance from Claude (Anthropic), an AI assistant that helped with code architecture, documentation, testing, and packaging solutions.
