#!/usr/bin/env python3
"""
JobDocs - Modular Blueprint and Job Management System

Main application entry point using the modular plugin architecture.
"""

import sys
import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QMessageBox, QDialog
)
from PyQt6.QtCore import Qt

from core.module_loader import ModuleLoader
from core.app_context import AppContext
from shared.utils import get_config_dir, get_os_text, get_os_type


class JobDocsMainWindow(QMainWindow):
    """Main application window with modular plugin system"""

    DEFAULT_SETTINGS = {
        'blueprints_dir': '',
        'customer_files_dir': '',
        'itar_blueprints_dir': '',
        'itar_customer_files_dir': '',
        'link_type': 'hard',
        'blueprint_extensions': ['.pdf', '.dwg', '.dxf'],
        'allow_duplicate_jobs': False,
        'ui_style': 'Fusion',
        'job_folder_structure': '{customer}/job documents/{job_folder}',
        'quote_folder_path': 'Quotes',
        'legacy_mode': True,
        'default_tab': 0,
        'disabled_modules': [],  # List of disabled module names
        'network_users_path': '',  # Path to shared users.json on network
        'db_type': 'mssql',
        'db_host': 'localhost',
        'db_port': 1433,
        'db_name': '',
        'db_username': '',
        'db_password': '',
        'network_shared_enabled': False,
        'network_settings_path': '',
        'network_history_path': '',
        'user_auth_enabled': False,
        'oobe_completed': False
    }

    # Personal settings that should never be shared across network
    PERSONAL_SETTINGS = {
        'ui_style',
        'default_tab'
    }

    def __init__(self):
        super().__init__()

        # Configuration
        self.config_dir = get_config_dir()
        self.settings_file = self.config_dir / 'settings.json'
        self.history_file = self.config_dir / 'history.json'
        self.users_file = self.config_dir / 'users.json'

        self.settings = self.load_settings()
        self.history = self.load_history()
        self.modules = []  # Store loaded modules
        self.current_user = None  # Current logged-in user
        self.user_is_admin = False  # Whether current user is admin
        self.user_auth = None  # Will be initialized after OOBE if needed

        # Setup UI first (needed for OOBE wizard)
        self.setWindowTitle("JobDocs")
        self.resize(700, 600)
        self.setMaximumHeight(700)  # Prevent window from exceeding 700px

        # Create tab widget
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        # Create app context for modules
        self.app_context = AppContext(
            settings=self.settings,
            history=self.history,
            config_dir=self.config_dir,
            save_settings_callback=self.save_settings,
            save_history_callback=self.save_history,
            log_message_callback=self.log_message,
            show_error_callback=self.show_error_dialog,
            show_info_callback=self.show_info_dialog,
            get_customer_list_callback=self.get_customer_list,
            add_to_history_callback=self.add_to_history,
            main_window=self
        )

        # Load modules (needed for OOBE)
        self.load_modules()

        # Apply UI style
        self.apply_ui_style()

        # Set default tab
        default_tab = self.settings.get('default_tab', 0)
        if 0 <= default_tab < self.tabs.count():
            self.tabs.setCurrentIndex(default_tab)

        self.statusBar().showMessage("Ready")

        # Check for first-time setup BEFORE user authentication
        # This allows OOBE to configure network_users_path
        if not self.settings.get('oobe_completed', False):
            self._run_first_time_setup()

        # Initialize user authentication AFTER OOBE (requires user_auth module)
        if self.settings.get('user_auth_enabled', False):
            try:
                from modules.user_auth.user_auth import UserAuth

                # Get network users path if configured (may have been set by OOBE)
                network_users_path = self.settings.get('network_users_path', '')
                network_users_file = Path(network_users_path) if network_users_path else None

                self.user_auth = UserAuth(self.users_file, network_users_file)

                # Show login dialog
                if not self._login():
                    # User cancelled login or failed to authenticate
                    sys.exit(0)
            except ImportError:
                # Module not enabled (still has underscore prefix)
                pass

        # Setup menu AFTER user authentication so admin menu shows for admin users
        self.setup_menu()

    # ==================== First-Time Setup ====================

    def _run_first_time_setup(self):
        """Run the first-time setup wizard (OOBE)"""
        try:
            from modules.admin.oobe_wizard import OOBEWizard
            from PyQt6.QtCore import QTimer

            # Show wizard after main window is displayed
            def show_wizard():
                wizard = OOBEWizard(self.app_context, parent=self)
                if wizard.exec():
                    QMessageBox.information(
                        self,
                        "Setup Complete",
                        "JobDocs has been configured.\n\n"
                        "You may need to restart the application for all changes to take effect."
                    )
                else:
                    # User cancelled - ask if they want to continue anyway
                    reply = QMessageBox.question(
                        self,
                        "Setup Cancelled",
                        "Setup was cancelled. You can run it later from the Admin tab.\n\n"
                        "Do you want to continue without setup?",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                    )
                    if reply == QMessageBox.StandardButton.No:
                        self.close()

            # Show wizard after a short delay to ensure window is visible
            QTimer.singleShot(500, show_wizard)

        except ImportError:
            # Admin module not available, skip OOBE
            print("Admin module not available, skipping first-time setup")
            # Mark as completed so we don't keep trying
            self.settings['oobe_completed'] = True
            self.save_settings()

    # ==================== User Authentication ====================

    def _login(self) -> bool:
        """Show login dialog and authenticate user"""
        from modules.user_auth.ui.login_dialog import LoginDialog

        # Check if there are any users
        if not self.user_auth.list_users():
            # No users exist - create first admin user
            QMessageBox.information(
                self,
                "Welcome!",
                "No user accounts exist yet.\n\nLet's create your first admin user account."
            )

            from PyQt6.QtWidgets import QInputDialog, QLineEdit
            username, ok = QInputDialog.getText(self, "Create First Admin User", "Username:")
            if not ok or not username:
                return False

            password, ok = QInputDialog.getText(self, "Create First Admin User", "Password:", QLineEdit.EchoMode.Password)
            if not ok or not password:
                return False

            try:
                # First user is always an admin
                self.user_auth.create_user(username, password, is_admin=True)
                QMessageBox.information(self, "Success", f"Admin user '{username}' created successfully!")
            except ValueError as e:
                QMessageBox.critical(self, "Error", str(e))
                return False

        dialog = LoginDialog(self.user_auth, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.current_user = dialog.get_authenticated_user()
            self.user_is_admin = self.user_auth.is_admin(self.current_user)

            # Record login session
            self.user_auth.login(self.current_user)

            # Update window title with role indicator
            role_text = " (Admin)" if self.user_is_admin else ""
            self.setWindowTitle(f"JobDocs - {self.current_user}{role_text}")

            return True
        return False

    def logout(self):
        """Logout current user and restart to login screen"""
        if not self.user_auth or not self.current_user:
            return

        # Confirm logout
        reply = QMessageBox.question(
            self,
            "Logout",
            f"Are you sure you want to logout?\n\nYou are currently logged in as: {self.current_user}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.log_message(f"User '{self.current_user}' logged out")

            # Remove session tracking
            self.user_auth.logout(self.current_user)

            # Clear current user
            old_user = self.current_user
            self.current_user = None
            self.user_is_admin = False

            # Show login dialog again
            if self._login():
                # Successful login - rebuild menu with new user permissions
                self.menuBar().clear()
                self.setup_menu()
            else:
                # User cancelled login - close application
                self.close()

    # ==================== Settings & History ====================

    def _make_file_hidden(self, file_path: Path):
        """Make a file hidden (cross-platform)"""
        try:
            if get_os_type() == "windows":
                # Windows: Set hidden attribute
                import ctypes
                ctypes.windll.kernel32.SetFileAttributesW(str(file_path), 2)
            else:
                # Linux/macOS: Rename to start with dot if not already
                if not file_path.name.startswith('.'):
                    parent = file_path.parent
                    new_path = parent / f".{file_path.name}"
                    if not new_path.exists():
                        file_path.rename(new_path)
                        return new_path
            return file_path
        except Exception as e:
            print(f"Warning: Could not make file hidden: {e}")
            return file_path

    def load_settings(self) -> Dict[str, Any]:
        """
        Load settings from file, merging network and local settings.

        Priority order (highest to lowest):
        1. Personal settings from local file (ui_style, default_tab)
        2. Network configuration from local file (network_shared_enabled, paths)
        3. Global settings from network file (takes precedence over local)
        4. Non-personal settings from local file
        5. Default settings
        """
        # Start with defaults
        merged = self.DEFAULT_SETTINGS.copy()

        # Load local settings file
        local_settings = {}
        if self.settings_file.exists():
            try:
                with open(self.settings_file, 'r') as f:
                    local_settings = json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Warning: Could not load local settings: {e}")

        # First, merge all local settings (as fallback/base)
        merged.update(local_settings)

        # Check if network sharing is enabled
        network_enabled = local_settings.get('network_shared_enabled', False)
        network_settings_path = local_settings.get('network_settings_path', '')

        # Network config keys that should always come from local
        network_config_keys = {'network_shared_enabled', 'network_settings_path', 'network_history_path'}

        if network_enabled and network_settings_path:
            # Try to load network shared settings
            try:
                network_path = Path(network_settings_path)
                if network_path.exists():
                    with open(network_path, 'r') as f:
                        network_settings = json.load(f)

                        # Network settings take precedence over local (except personal settings)
                        for key, value in network_settings.items():
                            # Skip personal settings and network config - keep local values
                            if key not in self.PERSONAL_SETTINGS and key not in network_config_keys:
                                merged[key] = value

                        print(f"Loaded network shared settings from: {network_settings_path}")
                        print(f"  Global settings take precedence over local settings")
                else:
                    print(f"Warning: Network settings file not found: {network_settings_path}")
            except (json.JSONDecodeError, IOError) as e:
                print(f"Warning: Could not load network settings: {e}")
                print("Falling back to local settings only")

        # Ensure personal settings and network config always use local values
        # (overlay them on top of network settings)
        for key in self.PERSONAL_SETTINGS | network_config_keys:
            if key in local_settings:
                merged[key] = local_settings[key]

        return merged

    def save_settings(self):
        """Save settings to file, handling network shared settings"""
        try:
            # Always save local settings file (includes personal settings and network config)
            with open(self.settings_file, 'w') as f:
                json.dump(self.settings, f, indent=2)

            # If network sharing is enabled, also save shared settings
            network_enabled = self.settings.get('network_shared_enabled', False)
            network_settings_path = self.settings.get('network_settings_path', '')

            if network_enabled and network_settings_path:
                try:
                    # Prepare shared settings (exclude personal settings and network config)
                    shared_settings = {
                        k: v for k, v in self.settings.items()
                        if k not in self.PERSONAL_SETTINGS
                        and k not in {'network_shared_enabled', 'network_settings_path', 'network_history_path'}
                    }

                    network_path = Path(network_settings_path)
                    # Create parent directory if it doesn't exist
                    network_path.parent.mkdir(parents=True, exist_ok=True)

                    with open(network_path, 'w') as f:
                        json.dump(shared_settings, f, indent=2)

                    # Make the file hidden to prevent tampering
                    self._make_file_hidden(network_path)

                    print(f"Saved network shared settings to: {network_settings_path}")
                except IOError as e:
                    print(f"Warning: Could not save network settings: {e}")
                    self.show_error_dialog(
                        "Network Settings Error",
                        f"Failed to save network shared settings:\n{e}\n\nLocal settings were saved successfully."
                    )

        except IOError as e:
            self.show_error_dialog("Error", f"Failed to save settings: {e}")

    def load_history(self) -> Dict[str, Any]:
        """Load history from file, checking network shared history first"""
        default_history = {'customers': {}, 'recent_jobs': []}

        # Check if network sharing is enabled
        network_enabled = self.settings.get('network_shared_enabled', False)
        network_history_path = self.settings.get('network_history_path', '')

        if network_enabled and network_history_path:
            # Try to load network shared history
            try:
                network_path = Path(network_history_path)
                if network_path.exists():
                    with open(network_path, 'r') as f:
                        history = json.load(f)
                        print(f"Loaded network shared history from: {network_history_path}")
                        return history
                else:
                    print(f"Warning: Network history file not found: {network_history_path}")
            except (json.JSONDecodeError, IOError) as e:
                print(f"Warning: Could not load network history: {e}")
                print("Falling back to local history")

        # Fall back to local history
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Warning: Could not load local history: {e}")

        return default_history

    def save_history(self):
        """Save history to file, handling network shared history"""
        # Check if network sharing is enabled
        network_enabled = self.settings.get('network_shared_enabled', False)
        network_history_path = self.settings.get('network_history_path', '')

        if network_enabled and network_history_path:
            # Save to network shared location
            try:
                network_path = Path(network_history_path)
                # Create parent directory if it doesn't exist
                network_path.parent.mkdir(parents=True, exist_ok=True)

                with open(network_path, 'w') as f:
                    json.dump(self.history, f, indent=2)

                # Make the file hidden to prevent tampering
                self._make_file_hidden(network_path)

                print(f"Saved network shared history to: {network_history_path}")
            except IOError as e:
                print(f"Warning: Could not save network history: {e}")
                self.show_error_dialog(
                    "Network History Error",
                    f"Failed to save network shared history:\n{e}\n\nHistory was not saved."
                )
        else:
            # Save to local file
            try:
                with open(self.history_file, 'w') as f:
                    json.dump(self.history, f, indent=2)
            except IOError as e:
                self.show_error_dialog("Error", f"Failed to save history: {e}")

    # ==================== Module Loading ====================

    def load_modules(self):
        """Load all modules using the module loader"""
        modules_dir = Path(__file__).parent / 'modules'
        loader = ModuleLoader(modules_dir)

        try:
            # Load all modules (experimental modules controlled by underscore prefix)
            all_modules = loader.load_all_modules(self.app_context, experimental_enabled=True)

            if not all_modules:
                QMessageBox.warning(
                    self,
                    "No Modules",
                    "No modules were loaded. Check the modules/ directory."
                )
                return

            # Filter modules based on user role
            self.modules = []
            self.admin_module = None

            for module in all_modules:
                module_name = module.get_name()

                # Check if this is the admin module
                if module_name in ["Settings & Setup", "Admin", "Administration"]:
                    # Store admin module separately (will be added to menu, not tabs)
                    self.admin_module = module
                    self.log_message(f"Found admin module: {module_name}")
                    continue

                # Add regular modules to tabs
                self.modules.append(module)

            # Add regular modules as tabs
            for module in self.modules:
                try:
                    widget = module.get_widget()
                    name = module.get_name()
                    self.tabs.addTab(widget, name)
                    self.log_message(f"Loaded module: {name}")
                except Exception as e:
                    self.log_message(f"ERROR: Failed to load module {module.__class__.__name__}: {e}")
                    import traceback
                    traceback.print_exc()

            self.statusBar().showMessage(f"Loaded {len(self.modules)} module(s)")

            # Populate customer lists in all modules
            self.populate_customer_lists()

        except Exception as e:
            QMessageBox.critical(
                self,
                "Module Load Error",
                f"Failed to load modules:\n\n{str(e)}"
            )
            import traceback
            traceback.print_exc()

    # ==================== Menu ====================

    def setup_menu(self):
        """Setup application menu"""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("&File")

        settings_action = file_menu.addAction("&Settings")
        settings_action.triggered.connect(self.open_settings)

        file_menu.addSeparator()

        # Logout option (only if user authentication is enabled)
        if self.user_auth and self.current_user:
            logout_action = file_menu.addAction("&Logout")
            logout_action.triggered.connect(self.logout)
            file_menu.addSeparator()

        exit_action = file_menu.addAction("E&xit")
        exit_action.triggered.connect(self.close)

        # Admin menu (only visible for admin users)
        if self.user_is_admin and self.admin_module:
            admin_menu = menubar.addMenu("&Admin")

            # Setup wizard
            setup_action = admin_menu.addAction("&Setup Wizard")
            setup_action.triggered.connect(self.run_setup_wizard)

            admin_menu.addSeparator()

            # User management
            user_management_action = admin_menu.addAction("&User Management")
            user_management_action.triggered.connect(self.open_user_management)

            admin_menu.addSeparator()

            # Team Settings
            team_settings_action = admin_menu.addAction("&Team Settings")
            team_settings_action.triggered.connect(self.open_team_settings)

        # Help menu
        help_menu = menubar.addMenu("&Help")

        getting_started_action = help_menu.addAction("&Getting Started")
        getting_started_action.triggered.connect(self.show_getting_started)

        help_menu.addSeparator()

        about_action = help_menu.addAction("&About")
        about_action.triggered.connect(self.show_about)

    def open_settings(self):
        """Open settings dialog"""
        # Import here to avoid circular dependency
        from core.settings_dialog import SettingsDialog

        # Discover all available modules for the settings dialog
        modules_dir = Path(__file__).parent / 'modules'
        loader = ModuleLoader(modules_dir)
        available_module_names = loader.discover_modules()

        # Create list of (module_name, display_name) tuples
        available_modules = []
        for module_name in available_module_names:
            try:
                # Try to load the module class to get its display name
                module_class = loader.load_module(module_name)
                instance = module_class()
                display_name = instance.get_name()
                available_modules.append((module_name, display_name))
            except Exception:
                # If we can't load it, just use the module name
                available_modules.append((module_name, module_name))

        dialog = SettingsDialog(self.settings, self, available_modules, self.user_is_admin)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.settings = dialog.settings
            self.save_settings()
            self.populate_customer_lists()
            QMessageBox.information(self, "Settings", "Settings saved. Please restart for all changes to take effect.")

    def show_getting_started(self):
        """Show getting started guide"""
        folder_term = get_os_text('folder_term')
        path_example = get_os_text('path_example')

        content = f"""
<h2>GETTING STARTED</h2>

<p><b>1. Go to File → Settings</b><br>
<b>2. Configure directories:</b><br>
&nbsp;&nbsp;- Blueprints Directory: Central drawing storage<br>
&nbsp;&nbsp;- Customer Files Directory: Where job {folder_term}s are created<br>
<b>3. Choose link type (Hard Link recommended)</b><br>
<b>4. Set blueprint file extensions</b></p>

<p><b>CREATE JOB TAB</b><br>
Enter job information and drop files to create job {folder_term}s.</p>

<p><b>BULK CREATE TAB</b><br>
Create multiple jobs at once using CSV format.</p>

<p><b>SEARCH TAB</b><br>
Search across all customers and jobs.</p>
        """

        msg = QMessageBox(self)
        msg.setWindowTitle("Getting Started")
        msg.setTextFormat(Qt.TextFormat.RichText)
        msg.setText(content)
        msg.exec()

    def run_setup_wizard(self):
        """Run the OOBE setup wizard"""
        if not self.admin_module:
            QMessageBox.warning(self, "Setup Wizard", "Admin module not available")
            return

        try:
            self.admin_module.run_oobe_wizard()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to run setup wizard: {e}")

    def open_team_settings(self):
        """Open team settings editor"""
        if not self.admin_module:
            QMessageBox.warning(self, "Team Settings", "Admin module not available")
            return

        try:
            self.admin_module.show_team_settings_dialog()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open team settings: {e}")

    def open_user_management(self):
        """Open user management dialog"""
        if not self.user_auth:
            QMessageBox.warning(self, "User Management", "User authentication not enabled")
            return

        try:
            from modules.user_auth.ui.user_management_dialog import UserManagementDialog
            dialog = UserManagementDialog(self.user_auth, self.current_user, self)
            dialog.exec()
        except ImportError:
            QMessageBox.warning(self, "User Management", "User management module not available")

    def show_about(self):
        """Show about dialog"""
        folder_term = get_os_text('folder_term')

        content = f"""
<h2>JobDocs</h2>
<p>A modular tool for managing blueprint files and customer job {folder_term}s.</p>

<p><b>Features:</b></p>
<ul>
<li>Plugin-based modular architecture</li>
<li>Quote and job management</li>
<li>Blueprint file organization</li>
<li>ITAR support for controlled documents</li>
<li>Bulk job creation</li>
<li>Advanced search capabilities</li>
</ul>

<p>Built with PyQt6 and the JobDocs Plugin System</p>
        """

        msg = QMessageBox(self)
        msg.setWindowTitle("About JobDocs")
        msg.setTextFormat(Qt.TextFormat.RichText)
        msg.setText(content)
        msg.exec()

    # ==================== UI Helpers ====================

    def apply_ui_style(self):
        """Apply UI style from settings"""
        style = self.settings.get('ui_style', 'Fusion')
        QApplication.setStyle(style)

    def log_message(self, message: str):
        """Log a message to console and status bar"""
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")
        self.statusBar().showMessage(message, 3000)

    def show_error_dialog(self, title: str, message: str):
        """Show error dialog"""
        QMessageBox.critical(self, title, message)

    def show_info_dialog(self, title: str, message: str):
        """Show information dialog"""
        QMessageBox.information(self, title, message)

    # ==================== Data Helpers ====================

    def get_customer_list(self) -> List[str]:
        """Get list of customers from customer files directory"""
        customers = set()
        for dir_key in ['customer_files_dir', 'itar_customer_files_dir']:
            dir_path = self.settings.get(dir_key, '')
            if dir_path and Path(dir_path).exists():
                try:
                    for d in Path(dir_path).iterdir():
                        if d.is_dir():
                            customers.add(d.name)
                except OSError:
                    pass
        return sorted(customers)

    def add_to_history(self, entry_type: str, data: Dict[str, Any]):
        """Add an entry to history"""
        if entry_type == 'job':
            recent_jobs = self.history.get('recent_jobs', [])

            # Add timestamp
            data['date'] = datetime.now().isoformat()

            # Add to front of list
            recent_jobs.insert(0, data)

            # Keep only last 100 entries
            self.history['recent_jobs'] = recent_jobs[:100]

            # Update customer history
            customer = data.get('customer', '')
            if customer:
                if 'customers' not in self.history:
                    self.history['customers'] = {}
                self.history['customers'][customer] = datetime.now().isoformat()

            self.save_history()

    def populate_customer_lists(self):
        """Refresh customer lists in all modules (called after settings change)"""
        # Call populate methods on all loaded modules that have them
        for module in self.modules:
            # Check for populate_*_customer_list methods
            for method_name in dir(module):
                if method_name.startswith('populate_') and method_name.endswith('_customer_list'):
                    method = getattr(module, method_name, None)
                    if callable(method):
                        try:
                            method()
                        except Exception as e:
                            self.log_message(f"Error refreshing {module.get_name()} customer list: {e}")

        self.log_message("Customer lists refreshed")

    def refresh_history(self):
        """Refresh history displays in all modules"""
        # Hook for modules to refresh history displays
        self.log_message("History refreshed")

    # ==================== Job Creation (for Bulk module) ====================

    def create_single_job(self, customer: str, job_number: str, description: str,
                         drawings: List[str], is_itar: bool, quote_files: List[str]) -> bool:
        """
        Create a single job (called by Bulk module).
        This is a simplified version - full implementation would be in Job module.
        """
        try:
            # This is a stub - in reality, the Job module handles job creation
            # The Bulk module calls this to create jobs
            self.add_to_history('job', {
                'customer': customer,
                'job_number': job_number,
                'description': description,
                'drawings': drawings,
                'is_itar': is_itar
            })
            return True
        except Exception as e:
            self.log_message(f"Error creating job {job_number}: {e}")
            return False

    # ==================== Application Cleanup ====================

    def closeEvent(self, event):
        """Handle window close event - ensure proper cleanup"""
        self.log_message("Application closing - cleaning up resources...")

        # Remove user session if logged in
        if self.user_auth and self.current_user:
            self.user_auth.logout(self.current_user)

        # Cleanup all modules
        for module in self.modules:
            try:
                module.cleanup()
            except Exception as e:
                print(f"Error cleaning up module {module.get_name()}: {e}")

        # Save any pending settings/history
        try:
            self.save_settings()
            self.save_history()
        except Exception as e:
            print(f"Error saving on exit: {e}")

        # Accept the close event
        event.accept()

        # Ensure application quits
        QApplication.quit()


def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    app.setApplicationName("JobDocs")
    app.setOrganizationName("JobDocs")

    # Ensure clean shutdown
    app.setQuitOnLastWindowClosed(True)

    print("=" * 60)
    print("JobDocs - Modular Plugin System")
    print("=" * 60)
    print()

    window = JobDocsMainWindow()
    window.show()

    # Run the application
    exit_code = app.exec()

    # Ensure window is properly deleted
    window.deleteLater()

    # Process any remaining events
    app.processEvents()

    return exit_code


if __name__ == '__main__':
    sys.exit(main())
