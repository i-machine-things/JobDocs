"""
Admin Module for JobDocs

Provides administrative controls for user management and global settings.
"""

import json
from pathlib import Path
from typing import Dict, Any
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel,
    QPushButton, QMessageBox, QListWidget, QTextEdit, QTabWidget,
    QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView,
    QScrollArea, QFrame, QCheckBox, QComboBox
)
from PyQt6.QtCore import Qt

from core.base_module import BaseModule


class AdminModule(BaseModule):
    """
    Admin module for managing users and global settings.

    Provides:
    - User account management (create, delete, list)
    - Global settings management for network-shared configurations
    """

    def __init__(self):
        super().__init__()
        self._widget = None

        # UI references
        self.tabs = None
        self.user_list = None
        self.settings_table = None
        self.settings_text = None

    # ==================== REQUIRED METHODS ====================

    def get_name(self) -> str:
        """Return the display name for this module's tab"""
        return "Admin"

    def get_order(self) -> int:
        """Return the display order (after History and Reporting)"""
        return 90

    def initialize(self, app_context):
        """Initialize the module with application context"""
        super().initialize(app_context)
        self.log_message("Admin module initialized")

    def get_widget(self) -> QWidget:
        """Return the widget to display in the tab"""
        if self._widget is None:
            self._widget = self._create_widget()
        return self._widget

    # ==================== WIDGET CREATION ====================

    def _create_widget(self) -> QWidget:
        """Create the admin tab widget"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Header
        header = QLabel("Administrative Controls")
        header.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(header)

        # Create tab widget for different admin sections
        self.tabs = QTabWidget()

        # User Management tab
        self.tabs.addTab(self._create_user_management_tab(), "User Management")

        # Global Settings tab
        self.tabs.addTab(self._create_global_settings_tab(), "Global Settings")

        # Info tab
        self.tabs.addTab(self._create_info_tab(), "System Info")

        layout.addWidget(self.tabs)

        return widget

    def _create_user_management_tab(self) -> QWidget:
        """Create the user management tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Check if user auth is available
        user_auth = self._get_user_auth()

        if not user_auth:
            # User auth not enabled
            info = QLabel(
                "User authentication is not enabled.\n\n"
                "To enable user management:\n"
                "1. Enable user_auth module (remove underscore from _user_auth)\n"
                "2. Set 'user_auth_enabled': true in settings.json\n"
                "3. Restart the application"
            )
            info.setStyleSheet("color: #666; padding: 20px;")
            info.setWordWrap(True)
            layout.addWidget(info)
            return widget

        # User list
        list_group = QGroupBox("Users")
        list_layout = QVBoxLayout(list_group)

        self.user_list = QListWidget()
        list_layout.addWidget(self.user_list)

        layout.addWidget(list_group)

        # Buttons
        button_layout = QHBoxLayout()

        create_btn = QPushButton("Create New User")
        create_btn.clicked.connect(self.create_user)
        button_layout.addWidget(create_btn)

        delete_btn = QPushButton("Delete User")
        delete_btn.clicked.connect(self.delete_user)
        button_layout.addWidget(delete_btn)

        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh_user_list)
        button_layout.addWidget(refresh_btn)

        button_layout.addStretch()

        layout.addLayout(button_layout)

        # Initial load
        self.refresh_user_list()

        return widget

    def _create_global_settings_tab(self) -> QWidget:
        """Create the global settings management tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Check if network sharing is enabled
        network_enabled = self.app_context.get_setting('network_shared_enabled', False)
        network_path = self.app_context.get_setting('network_settings_path', '')

        if not network_enabled or not network_path:
            # Network sharing not enabled
            info = QLabel(
                "Network shared settings are not enabled.\n\n"
                "To enable global settings management:\n"
                "1. Go to File → Settings → Advanced Settings\n"
                "2. Enable 'Network shared settings'\n"
                "3. Configure the shared settings file path\n"
                "4. Save and restart the application"
            )
            info.setStyleSheet("color: #666; padding: 20px;")
            info.setWordWrap(True)
            layout.addWidget(info)
            return widget

        # Network settings info
        info_group = QGroupBox("Network Settings Configuration")
        info_layout = QVBoxLayout(info_group)

        path_label = QLabel(f"<b>Shared Settings File:</b> {network_path}")
        path_label.setWordWrap(True)
        info_layout.addWidget(path_label)

        info_text = QLabel(
            "These settings are synchronized across all users on the network.\n"
            "Personal settings (UI style, default tab) remain local."
        )
        info_text.setStyleSheet("color: #666; font-size: 11px;")
        info_text.setWordWrap(True)
        info_layout.addWidget(info_text)

        layout.addWidget(info_group)

        # Settings editor
        editor_group = QGroupBox("Global Settings")
        editor_layout = QVBoxLayout(editor_group)

        # Table view of settings
        self.settings_table = QTableWidget()
        self.settings_table.setColumnCount(3)
        self.settings_table.setHorizontalHeaderLabels(["Setting", "Value", "Shared"])
        self.settings_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.settings_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.settings_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)

        editor_layout.addWidget(self.settings_table)

        # Buttons
        button_layout = QHBoxLayout()

        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh_settings)
        button_layout.addWidget(refresh_btn)

        edit_btn = QPushButton("Edit Settings File")
        edit_btn.clicked.connect(self.edit_settings_file)
        button_layout.addWidget(edit_btn)

        button_layout.addStretch()

        editor_layout.addLayout(button_layout)

        layout.addWidget(editor_group)

        # Initial load
        self.refresh_settings()

        return widget

    def _create_info_tab(self) -> QWidget:
        """Create the system info tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Setup wizard section
        setup_group = QGroupBox("First-Time Setup")
        setup_layout = QVBoxLayout(setup_group)

        setup_info = QLabel(
            "Run the setup wizard to configure JobDocs directories, "
            "link type, network sharing, and user authentication."
        )
        setup_info.setWordWrap(True)
        setup_layout.addWidget(setup_info)

        oobe_btn = QPushButton("Run Setup Wizard")
        oobe_btn.clicked.connect(self.run_oobe_wizard)
        oobe_btn.setStyleSheet("font-weight: bold;")
        setup_layout.addWidget(oobe_btn)

        layout.addWidget(setup_group)

        # System info section
        info_group = QGroupBox("System Information")
        info_layout = QVBoxLayout(info_group)

        self.info_text = QTextEdit()
        self.info_text.setReadOnly(True)
        info_layout.addWidget(self.info_text)

        layout.addWidget(info_group)

        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh_system_info)
        layout.addWidget(refresh_btn)

        # Initial load
        self.refresh_system_info()

        return widget

    # ==================== USER MANAGEMENT METHODS ====================

    def _get_user_auth(self):
        """Get the UserAuth instance from main window"""
        main_window = self.app_context.main_window
        if main_window and hasattr(main_window, 'user_auth'):
            return main_window.user_auth
        return None

    def refresh_user_list(self):
        """Refresh the user list"""
        if not self.user_list:
            return

        user_auth = self._get_user_auth()
        if not user_auth:
            return

        self.user_list.clear()

        try:
            users = user_auth.list_users()

            # Get current user if available
            main_window = self.app_context.main_window
            current_user = getattr(main_window, 'current_user', None) if main_window else None

            for username in sorted(users):
                user_info = user_auth.get_user_info(username)
                full_name = user_info.get('full_name', '') if user_info else ''

                display = username
                if full_name:
                    display += f" ({full_name})"
                if current_user and username == current_user:
                    display += " [CURRENT]"

                self.user_list.addItem(display)

            self.log_message(f"User list refreshed: {len(users)} users")

        except Exception as e:
            self.show_error("Error", f"Failed to load users:\n{e}")

    def create_user(self):
        """Create a new user"""
        user_auth = self._get_user_auth()
        if not user_auth:
            self.show_error("Error", "User authentication is not available.")
            return

        try:
            from modules._user_auth.ui.user_management_dialog import CreateUserDialog

            dialog = CreateUserDialog(user_auth, parent=self._widget)
            if dialog.exec():
                self.show_info("Success", f"User '{dialog.username}' created successfully.")
                self.refresh_user_list()

        except ImportError:
            self.show_error(
                "Module Not Available",
                "The user_auth module is not available.\n\n"
                "To enable it, rename 'modules/_user_auth' to 'modules/user_auth' and restart."
            )

    def delete_user(self):
        """Delete selected user"""
        if not self.user_list:
            return

        user_auth = self._get_user_auth()
        if not user_auth:
            return

        selected_items = self.user_list.selectedItems()
        if not selected_items:
            self.show_error("Error", "Please select a user to delete.")
            return

        selected_text = selected_items[0].text()
        username = selected_text.split(' ')[0]

        # Check if trying to delete current user
        main_window = self.app_context.main_window
        current_user = getattr(main_window, 'current_user', None) if main_window else None

        if current_user and username == current_user:
            self.show_error("Error", "You cannot delete the currently logged-in user.")
            return

        # Confirm deletion
        reply = QMessageBox.question(
            self._widget,
            "Confirm Delete",
            f"Are you sure you want to delete user '{username}'?\n\nThis cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                if user_auth.delete_user(username):
                    self.show_info("Success", f"User '{username}' deleted.")
                    self.refresh_user_list()
                else:
                    self.show_error("Error", f"Failed to delete user '{username}'.")
            except Exception as e:
                self.show_error("Error", f"Failed to delete user:\n{e}")

    # ==================== GLOBAL SETTINGS METHODS ====================

    def refresh_settings(self):
        """Refresh the settings display"""
        if not self.settings_table:
            return

        self.settings_table.setRowCount(0)

        # Get settings
        settings = self.app_context.settings

        # Personal settings that aren't shared
        personal_settings = getattr(
            self.app_context.main_window,
            'PERSONAL_SETTINGS',
            {'ui_style', 'default_tab'}
        ) if self.app_context.main_window else set()

        # Add each setting to the table
        row = 0
        for key, value in sorted(settings.items()):
            # Skip internal/sensitive settings
            if key in {'network_settings_path', 'network_history_path', 'network_shared_enabled'}:
                continue

            self.settings_table.insertRow(row)

            # Setting name
            self.settings_table.setItem(row, 0, QTableWidgetItem(key))

            # Value (convert to string)
            value_str = str(value)
            if len(value_str) > 100:
                value_str = value_str[:97] + "..."
            self.settings_table.setItem(row, 1, QTableWidgetItem(value_str))

            # Shared status
            is_shared = key not in personal_settings
            shared_item = QTableWidgetItem("Yes" if is_shared else "No (Local)")
            if not is_shared:
                shared_item.setForeground(Qt.GlobalColor.gray)
            self.settings_table.setItem(row, 2, shared_item)

            row += 1

        self.log_message("Settings refreshed")

    def edit_settings_file(self):
        """Open settings file for editing"""
        network_path = self.app_context.get_setting('network_settings_path', '')

        if not network_path:
            self.show_error("Error", "Network settings path is not configured.")
            return

        file_path = Path(network_path)

        if not file_path.exists():
            reply = QMessageBox.question(
                self._widget,
                "File Not Found",
                f"Settings file does not exist:\n{network_path}\n\n"
                "Create it now with current shared settings?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                try:
                    # Create with current shared settings
                    main_window = self.app_context.main_window
                    if main_window:
                        main_window.save_settings()
                        self.show_info("Success", "Settings file created.")
                except Exception as e:
                    self.show_error("Error", f"Failed to create settings file:\n{e}")
                    return
            else:
                return

        # Show editor dialog
        self._show_json_editor(file_path, "Global Settings File")

    def _show_json_editor(self, file_path: Path, title: str):
        """Show a simple JSON editor dialog"""
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QPushButton, QTextEdit

        dialog = QDialog(self._widget)
        dialog.setWindowTitle(title)
        dialog.setMinimumSize(600, 400)

        layout = QVBoxLayout(dialog)

        # Info
        info = QLabel(f"<b>File:</b> {file_path}")
        info.setWordWrap(True)
        layout.addWidget(info)

        # Editor
        editor = QTextEdit()
        editor.setFontFamily("monospace")

        try:
            with open(file_path, 'r') as f:
                content = f.read()
            editor.setPlainText(content)
        except Exception as e:
            self.show_error("Error", f"Failed to read file:\n{e}")
            return

        layout.addWidget(editor)

        # Buttons
        button_layout = QHBoxLayout()

        save_btn = QPushButton("Save")
        def save_file():
            try:
                # Validate JSON
                content = editor.toPlainText()
                json.loads(content)  # Will raise exception if invalid

                # Save
                with open(file_path, 'w') as f:
                    f.write(content)

                self.show_info("Success", "Settings file saved.")
                self.refresh_settings()
                dialog.accept()

            except json.JSONDecodeError as e:
                self.show_error("Invalid JSON", f"JSON syntax error:\n{e}")
            except Exception as e:
                self.show_error("Error", f"Failed to save file:\n{e}")

        save_btn.clicked.connect(save_file)
        button_layout.addWidget(save_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(dialog.reject)
        button_layout.addWidget(cancel_btn)

        layout.addLayout(button_layout)

        dialog.exec()

    # ==================== SYSTEM INFO METHODS ====================

    def refresh_system_info(self):
        """Refresh system information display"""
        if not hasattr(self, 'info_text'):
            return

        info_lines = []

        # Application info
        info_lines.append("=== APPLICATION INFORMATION ===\n")
        info_lines.append(f"Application: JobDocs")
        info_lines.append(f"Module Count: {len(self.app_context.main_window.modules) if self.app_context.main_window else 'N/A'}")

        # User info
        info_lines.append("\n=== USER AUTHENTICATION ===\n")
        user_auth_enabled = self.app_context.get_setting('user_auth_enabled', False)
        info_lines.append(f"User Auth Enabled: {user_auth_enabled}")

        if user_auth_enabled:
            user_auth = self._get_user_auth()
            if user_auth:
                users = user_auth.list_users()
                info_lines.append(f"Total Users: {len(users)}")

                main_window = self.app_context.main_window
                current_user = getattr(main_window, 'current_user', None) if main_window else None
                if current_user:
                    info_lines.append(f"Current User: {current_user}")

        # Network settings info
        info_lines.append("\n=== NETWORK SHARED SETTINGS ===\n")
        network_enabled = self.app_context.get_setting('network_shared_enabled', False)
        info_lines.append(f"Network Sharing Enabled: {network_enabled}")

        if network_enabled:
            settings_path = self.app_context.get_setting('network_settings_path', '')
            history_path = self.app_context.get_setting('network_history_path', '')

            info_lines.append(f"Settings File: {settings_path}")
            if settings_path:
                exists = Path(settings_path).exists()
                info_lines.append(f"  Exists: {exists}")

            info_lines.append(f"History File: {history_path}")
            if history_path:
                exists = Path(history_path).exists()
                info_lines.append(f"  Exists: {exists}")

        # Directory info
        info_lines.append("\n=== CONFIGURED DIRECTORIES ===\n")
        info_lines.append(f"Blueprints: {self.app_context.get_setting('blueprints_dir', 'Not set')}")
        info_lines.append(f"Customer Files: {self.app_context.get_setting('customer_files_dir', 'Not set')}")
        info_lines.append(f"ITAR Blueprints: {self.app_context.get_setting('itar_blueprints_dir', 'Not set') or 'Not set'}")
        info_lines.append(f"ITAR Customer Files: {self.app_context.get_setting('itar_customer_files_dir', 'Not set') or 'Not set'}")

        # Configuration
        info_lines.append("\n=== CONFIGURATION ===\n")
        info_lines.append(f"Link Type: {self.app_context.get_setting('link_type', 'Not set')}")
        info_lines.append(f"Blueprint Extensions: {', '.join(self.app_context.get_setting('blueprint_extensions', []))}")
        info_lines.append(f"Job Folder Structure: {self.app_context.get_setting('job_folder_structure', 'Not set')}")

        # History stats
        info_lines.append("\n=== HISTORY ===\n")
        recent_jobs = self.app_context.history.get('recent_jobs', [])
        customers = self.app_context.history.get('customers', {})
        info_lines.append(f"Recent Jobs: {len(recent_jobs)}")
        info_lines.append(f"Customers: {len(customers)}")

        self.info_text.setPlainText('\n'.join(info_lines))
        self.log_message("System info refreshed")

    # ==================== OOBE WIZARD ====================

    def run_oobe_wizard(self):
        """Run the first-time setup wizard"""
        try:
            from modules.admin.oobe_wizard import OOBEWizard

            wizard = OOBEWizard(self.app_context, parent=self._widget)

            if wizard.exec():
                self.show_info(
                    "Setup Complete",
                    "Settings have been saved.\n\n"
                    "Please restart JobDocs for all changes to take effect."
                )
                self.refresh_settings()
                self.refresh_system_info()

        except Exception as e:
            self.show_error("Error", f"Failed to run setup wizard:\n{e}")
            import traceback
            traceback.print_exc()
