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

        # Friendly header
        header = QLabel("Settings & Setup")
        header.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 5px;")
        layout.addWidget(header)

        # Subtitle
        subtitle = QLabel("Configure JobDocs and manage users")
        subtitle.setStyleSheet("color: #666; margin-bottom: 15px;")
        layout.addWidget(subtitle)

        # Create tab widget for different admin sections
        self.tabs = QTabWidget()

        # Setup tab (first and most important)
        self.tabs.addTab(self._create_setup_tab(), "Setup")

        # Team Settings tab (renamed from Global Settings)
        self.tabs.addTab(self._create_global_settings_tab(), "Team Settings")

        # User Management tab
        self.tabs.addTab(self._create_user_management_tab(), "Users")

        # Info tab
        self.tabs.addTab(self._create_info_tab(), "About")

        layout.addWidget(self.tabs)

        return widget

    def _create_setup_tab(self) -> QWidget:
        """Create the main setup tab with quick access to common tasks"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)

        # Welcome section
        welcome_box = QGroupBox("Welcome to JobDocs")
        welcome_layout = QVBoxLayout(welcome_box)

        welcome_text = QLabel(
            "JobDocs helps you organize blueprints and job folders. "
            "Use the setup wizard below to get started, or manage specific settings from the other tabs."
        )
        welcome_text.setWordWrap(True)
        welcome_text.setStyleSheet("color: #444; padding: 10px;")
        welcome_layout.addWidget(welcome_text)

        layout.addWidget(welcome_box)

        # Quick Setup section
        setup_box = QGroupBox("Quick Setup")
        setup_layout = QVBoxLayout(setup_box)

        setup_desc = QLabel(
            "First time using JobDocs? Run the setup wizard to configure everything you need:"
        )
        setup_desc.setWordWrap(True)
        setup_layout.addWidget(setup_desc)

        wizard_btn = QPushButton("Run Setup Wizard")
        wizard_btn.setStyleSheet(
            "QPushButton { font-size: 14px; font-weight: bold; padding: 10px; "
            "background-color: #0078d4; color: white; border-radius: 5px; }"
            "QPushButton:hover { background-color: #005a9e; }"
        )
        wizard_btn.clicked.connect(self.run_oobe_wizard)
        setup_layout.addWidget(wizard_btn)

        wizard_info = QLabel(
            "The wizard will help you:\n"
            "  • Set up folder locations for blueprints and customer files\n"
            "  • Choose how to link files (saves disk space)\n"
            "  • Configure team sharing (optional)\n"
            "  • Set up user accounts (optional)"
        )
        wizard_info.setWordWrap(True)
        wizard_info.setStyleSheet("color: #666; margin-top: 10px; padding: 5px;")
        setup_layout.addWidget(wizard_info)

        layout.addWidget(setup_box)

        # Common Settings section
        common_box = QGroupBox("Settings")
        common_layout = QVBoxLayout(common_box)

        common_desc = QLabel(
            "Most settings can be changed from the File → Settings menu.\n"
            "Folder locations and other critical settings require the setup wizard."
        )
        common_desc.setWordWrap(True)
        common_desc.setStyleSheet("color: #666; margin-bottom: 10px;")
        common_layout.addWidget(common_desc)

        # Add button to open main settings
        settings_btn = QPushButton("Open Settings Menu")
        settings_btn.setToolTip("Open the settings dialog for file types, link preferences, etc.")
        settings_btn.clicked.connect(self._open_main_settings)
        common_layout.addWidget(settings_btn)

        layout.addWidget(common_box)

        # Status section
        status_box = QGroupBox("Current Configuration")
        status_layout = QVBoxLayout(status_box)

        self.status_label = QLabel()
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet("padding: 10px; background-color: #f5f5f5; border-radius: 5px;")
        status_layout.addWidget(self.status_label)

        refresh_status_btn = QPushButton("Refresh Status")
        refresh_status_btn.clicked.connect(self._update_setup_status)
        status_layout.addWidget(refresh_status_btn)

        layout.addWidget(status_box)

        layout.addStretch()

        # Initial status update
        self._update_setup_status()

        return widget

    def _update_setup_status(self):
        """Update the setup status display"""
        if not hasattr(self, 'status_label'):
            return

        status_lines = []

        # Check directory configuration
        bp_dir = self.app_context.get_setting('blueprints_dir', '')
        cf_dir = self.app_context.get_setting('customer_files_dir', '')

        if bp_dir and cf_dir:
            status_lines.append("✓ Folders configured")
        else:
            status_lines.append("⚠ Folders not configured - run setup wizard")

        # Check link type
        link_type = self.app_context.get_setting('link_type', 'hard')
        link_name = {'hard': 'Hard Link', 'symbolic': 'Symbolic Link', 'copy': 'Copy'}
        status_lines.append(f"✓ File linking: {link_name.get(link_type, link_type)}")

        # Check network sharing
        if self.app_context.get_setting('network_shared_enabled', False):
            status_lines.append("✓ Team sharing enabled")
        else:
            status_lines.append("○ Team sharing disabled")

        # Check user auth
        if self.app_context.get_setting('user_auth_enabled', False):
            user_auth = self._get_user_auth()
            if user_auth:
                user_count = len(user_auth.list_users())
                status_lines.append(f"✓ User accounts enabled ({user_count} users)")
            else:
                status_lines.append("⚠ User accounts enabled but not available")
        else:
            status_lines.append("○ User accounts disabled")

        self.status_label.setText("\n".join(status_lines))

    def _open_main_settings(self):
        """Open the main settings dialog"""
        if self.app_context.main_window:
            self.app_context.main_window.open_settings()

    def _create_user_management_tab(self) -> QWidget:
        """Create the user management tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)

        # Check if user auth is available
        user_auth = self._get_user_auth()

        if not user_auth:
            # User auth not enabled - show friendly message
            info_box = QGroupBox("User Accounts")
            info_layout = QVBoxLayout(info_box)

            icon_label = QLabel("👥")
            icon_label.setStyleSheet("font-size: 48px;")
            icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            info_layout.addWidget(icon_label)

            info = QLabel(
                "User accounts are not currently enabled.\n\n"
                "User accounts let you track who is using JobDocs and control access."
            )
            info.setStyleSheet("color: #666; padding: 20px;")
            info.setWordWrap(True)
            info.setAlignment(Qt.AlignmentFlag.AlignCenter)
            info_layout.addWidget(info)

            enable_info = QLabel(
                "<b>To enable user accounts:</b><br>"
                "1. Run the Setup Wizard from the Setup tab<br>"
                "2. Enable 'User Authentication' in the wizard<br>"
                "3. Restart JobDocs"
            )
            enable_info.setTextFormat(Qt.TextFormat.RichText)
            enable_info.setWordWrap(True)
            enable_info.setStyleSheet("padding: 10px; background-color: #f0f8ff; border-radius: 5px;")
            info_layout.addWidget(enable_info)

            layout.addWidget(info_box)
            layout.addStretch()
            return widget

        # User list header
        header = QLabel("Manage User Accounts")
        header.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(header)

        desc = QLabel("Add, remove, or view user accounts for this JobDocs installation.")
        desc.setStyleSheet("color: #666; margin-bottom: 10px;")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        # User list
        list_group = QGroupBox("User Accounts")
        list_layout = QVBoxLayout(list_group)

        self.user_list = QListWidget()
        self.user_list.setStyleSheet("QListWidget { font-size: 13px; padding: 5px; }")
        list_layout.addWidget(self.user_list)

        layout.addWidget(list_group)

        # Buttons
        button_layout = QHBoxLayout()

        create_btn = QPushButton("Add New User")
        create_btn.setToolTip("Create a new user account")
        create_btn.setStyleSheet("padding: 8px; font-weight: bold;")
        create_btn.clicked.connect(self.create_user)
        button_layout.addWidget(create_btn)

        delete_btn = QPushButton("Remove User")
        delete_btn.setToolTip("Delete the selected user account")
        delete_btn.clicked.connect(self.delete_user)
        button_layout.addWidget(delete_btn)

        refresh_btn = QPushButton("Refresh List")
        refresh_btn.setToolTip("Reload the user list")
        refresh_btn.clicked.connect(self.refresh_user_list)
        button_layout.addWidget(refresh_btn)

        button_layout.addStretch()

        layout.addLayout(button_layout)

        # Help text
        help_text = QLabel(
            "💡 Tip: You cannot delete the user account you're currently logged in with."
        )
        help_text.setStyleSheet("color: #666; font-size: 11px; font-style: italic; margin-top: 10px;")
        help_text.setWordWrap(True)
        layout.addWidget(help_text)

        # Initial load
        self.refresh_user_list()

        return widget

    def _create_global_settings_tab(self) -> QWidget:
        """Create the global settings management tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)

        # Check if network sharing is enabled
        network_enabled = self.app_context.get_setting('network_shared_enabled', False)
        network_path = self.app_context.get_setting('network_settings_path', '')

        if not network_enabled or not network_path:
            # Network sharing not enabled - show friendly message
            info_box = QGroupBox("Team Settings")
            info_layout = QVBoxLayout(info_box)

            icon_label = QLabel("🌐")
            icon_label.setStyleSheet("font-size: 48px;")
            icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            info_layout.addWidget(icon_label)

            info = QLabel(
                "Team settings are not currently enabled.\n\n"
                "Team settings let multiple people share the same configuration across the network."
            )
            info.setStyleSheet("color: #666; padding: 20px;")
            info.setWordWrap(True)
            info.setAlignment(Qt.AlignmentFlag.AlignCenter)
            info_layout.addWidget(info)

            enable_info = QLabel(
                "<b>To enable team settings:</b><br>"
                "1. Run the Setup Wizard from the Setup tab<br>"
                "2. Enable 'Network Shared Settings' in the wizard<br>"
                "3. Choose a shared network location for the settings file<br>"
                "4. Save and restart JobDocs"
            )
            enable_info.setTextFormat(Qt.TextFormat.RichText)
            enable_info.setWordWrap(True)
            enable_info.setStyleSheet("padding: 10px; background-color: #f0f8ff; border-radius: 5px;")
            info_layout.addWidget(enable_info)

            layout.addWidget(info_box)
            layout.addStretch()
            return widget

        # Header
        header = QLabel("Team Settings")
        header.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(header)

        desc = QLabel(
            "These settings are shared across all team members. "
            "Changes here will affect everyone using this JobDocs installation."
        )
        desc.setStyleSheet("color: #666; margin-bottom: 10px;")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        # Network settings info
        info_group = QGroupBox("Configuration")
        info_layout = QVBoxLayout(info_group)

        path_label = QLabel(f"<b>Shared Settings File:</b><br>{network_path}")
        path_label.setWordWrap(True)
        info_layout.addWidget(path_label)

        info_text = QLabel(
            "💡 Note: Your personal preferences (like UI theme) stay on your computer and won't affect others."
        )
        info_text.setStyleSheet("color: #666; font-size: 11px; font-style: italic; margin-top: 5px;")
        info_text.setWordWrap(True)
        info_layout.addWidget(info_text)

        layout.addWidget(info_group)

        # Settings viewer
        viewer_group = QGroupBox("Current Team Settings")
        viewer_layout = QVBoxLayout(viewer_group)

        viewer_desc = QLabel(
            "Below are the settings that are shared across your team. "
            "Settings marked as 'Local' are personal to each user."
        )
        viewer_desc.setWordWrap(True)
        viewer_desc.setStyleSheet("color: #666; font-size: 12px; margin-bottom: 5px;")
        viewer_layout.addWidget(viewer_desc)

        # Table view of settings
        self.settings_table = QTableWidget()
        self.settings_table.setColumnCount(3)
        self.settings_table.setHorizontalHeaderLabels(["Setting Name", "Value", "Shared?"])
        self.settings_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.settings_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.settings_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.settings_table.setAlternatingRowColors(True)
        self.settings_table.setStyleSheet("QTableWidget { gridline-color: #e0e0e0; }")

        viewer_layout.addWidget(self.settings_table)

        layout.addWidget(viewer_group)

        # Buttons
        button_layout = QHBoxLayout()

        refresh_btn = QPushButton("Refresh")
        refresh_btn.setToolTip("Reload the settings from the shared file")
        refresh_btn.clicked.connect(self.refresh_settings)
        button_layout.addWidget(refresh_btn)

        edit_btn = QPushButton("Advanced: Edit Settings File")
        edit_btn.setToolTip("Edit the raw settings file (for advanced users)")
        edit_btn.setStyleSheet("color: #cc6600;")
        edit_btn.clicked.connect(self.edit_settings_file)
        button_layout.addWidget(edit_btn)

        button_layout.addStretch()

        layout.addLayout(button_layout)

        # Warning
        warning = QLabel(
            "⚠️ Caution: Editing the settings file directly can cause issues if not done correctly. "
            "Most settings can be changed from the main Settings dialog (File → Settings)."
        )
        warning.setWordWrap(True)
        warning.setStyleSheet(
            "color: #cc6600; font-size: 11px; padding: 8px; "
            "background-color: #fff3cd; border-left: 3px solid #ffc107; margin-top: 5px;"
        )
        layout.addWidget(warning)

        # Initial load
        self.refresh_settings()

        return widget

    def _create_info_tab(self) -> QWidget:
        """Create the system info tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)

        # Header
        header = QLabel("About JobDocs")
        header.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(header)

        # App info section
        app_info_box = QGroupBox("Application Information")
        app_info_layout = QVBoxLayout(app_info_box)

        app_desc = QLabel(
            "<b>JobDocs</b><br>"
            "A tool for managing blueprint files and customer job folders.<br><br>"
            "JobDocs helps you organize drawings, create job folders, and keep track of customer files."
        )
        app_desc.setTextFormat(Qt.TextFormat.RichText)
        app_desc.setWordWrap(True)
        app_desc.setStyleSheet("padding: 10px;")
        app_info_layout.addWidget(app_desc)

        layout.addWidget(app_info_box)

        # System info section
        info_group = QGroupBox("System Details")
        info_layout = QVBoxLayout(info_group)

        info_desc = QLabel("Technical information about your JobDocs installation:")
        info_desc.setStyleSheet("color: #666; font-size: 12px; margin-bottom: 5px;")
        info_layout.addWidget(info_desc)

        self.info_text = QTextEdit()
        self.info_text.setReadOnly(True)
        self.info_text.setStyleSheet(
            "QTextEdit { background-color: #f8f8f8; border: 1px solid #ddd; "
            "padding: 10px; font-family: monospace; font-size: 12px; }"
        )
        info_layout.addWidget(self.info_text)

        layout.addWidget(info_group)

        refresh_btn = QPushButton("Refresh Information")
        refresh_btn.setToolTip("Reload the system information")
        refresh_btn.clicked.connect(self.refresh_system_info)
        layout.addWidget(refresh_btn)

        # Help text
        help_text = QLabel(
            "💡 Need help? Check the Help menu for getting started guides and documentation."
        )
        help_text.setStyleSheet("color: #666; font-size: 11px; font-style: italic; margin-top: 10px;")
        help_text.setWordWrap(True)
        layout.addWidget(help_text)

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
            from modules.user_auth.ui.user_management_dialog import CreateUserDialog

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

    def show_team_settings_dialog(self):
        """Show team settings in a user-friendly dialog"""
        # Check if network sharing is enabled
        network_enabled = self.app_context.get_setting('network_shared_enabled', False)
        network_path = self.app_context.get_setting('network_settings_path', '')

        if not network_enabled or not network_path:
            self.show_info(
                "Team Settings",
                "Team settings are not currently enabled.\n\n"
                "To enable team settings, run the Setup Wizard from Admin → Setup Wizard."
            )
            return

        # Create dialog
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QPushButton

        dialog = QDialog(self._widget if self._widget else self.app_context.main_window)
        dialog.setWindowTitle("Team Settings")
        dialog.setMinimumSize(700, 500)

        layout = QVBoxLayout(dialog)

        # Settings table
        table = QTableWidget()
        table.setColumnCount(3)
        table.setHorizontalHeaderLabels(["Setting Name", "Value", "Shared?"])
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        table.setAlternatingRowColors(True)

        # Populate table
        settings = self.app_context.settings
        personal_settings = getattr(
            self.app_context.main_window,
            'PERSONAL_SETTINGS',
            {'ui_style', 'default_tab'}
        ) if self.app_context.main_window else set()

        row = 0
        for key, value in sorted(settings.items()):
            # Skip internal/sensitive settings
            if key in {'network_settings_path', 'network_history_path', 'network_shared_enabled'}:
                continue

            table.insertRow(row)
            table.setItem(row, 0, QTableWidgetItem(key))

            value_str = str(value)
            if len(value_str) > 100:
                value_str = value_str[:97] + "..."
            table.setItem(row, 1, QTableWidgetItem(value_str))

            is_shared = key not in personal_settings
            shared_item = QTableWidgetItem("Yes" if is_shared else "No (Local)")
            if not is_shared:
                shared_item.setForeground(Qt.GlobalColor.gray)
            table.setItem(row, 2, shared_item)

            row += 1

        layout.addWidget(table)

        # Info message
        info_msg = QLabel(
            "💡 To change most settings, use File → Settings.\n"
            "Advanced users can edit the JSON file directly using the button below."
        )
        info_msg.setStyleSheet("color: #666; font-size: 11px; font-style: italic; margin-top: 5px;")
        info_msg.setWordWrap(True)
        layout.addWidget(info_msg)

        # Buttons
        button_layout = QHBoxLayout()

        edit_json_btn = QPushButton("Advanced: Edit JSON File")
        edit_json_btn.setToolTip("Edit the raw settings file (for advanced users)")
        edit_json_btn.setStyleSheet("color: #cc6600;")
        edit_json_btn.clicked.connect(lambda: self._edit_json_from_dialog(dialog))
        button_layout.addWidget(edit_json_btn)

        button_layout.addStretch()

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.accept)
        button_layout.addWidget(close_btn)

        layout.addLayout(button_layout)

        dialog.exec()

    def _edit_json_from_dialog(self, parent_dialog):
        """Edit JSON file from within the settings dialog"""
        parent_dialog.accept()  # Close the parent dialog
        self.edit_settings_file()  # Open JSON editor

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
        dialog.setMaximumHeight(700)  # Prevent window from exceeding 700px

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
        info_lines.append("APPLICATION")
        info_lines.append("─" * 50)
        module_count = len(self.app_context.main_window.modules) if self.app_context.main_window else 0
        info_lines.append(f"Active Modules: {module_count}")
        info_lines.append("")

        # User info
        info_lines.append("USER ACCOUNTS")
        info_lines.append("─" * 50)
        user_auth_enabled = self.app_context.get_setting('user_auth_enabled', False)
        if user_auth_enabled:
            user_auth = self._get_user_auth()
            if user_auth:
                users = user_auth.list_users()
                info_lines.append(f"Status: Enabled")
                info_lines.append(f"Total Users: {len(users)}")

                main_window = self.app_context.main_window
                current_user = getattr(main_window, 'current_user', None) if main_window else None
                if current_user:
                    info_lines.append(f"Logged In As: {current_user}")
            else:
                info_lines.append(f"Status: Enabled (but not available)")
        else:
            info_lines.append("Status: Disabled")
        info_lines.append("")

        # Network settings info
        info_lines.append("TEAM SHARING")
        info_lines.append("─" * 50)
        network_enabled = self.app_context.get_setting('network_shared_enabled', False)
        if network_enabled:
            info_lines.append("Status: Enabled")
            settings_path = self.app_context.get_setting('network_settings_path', '')
            history_path = self.app_context.get_setting('network_history_path', '')

            if settings_path:
                exists = Path(settings_path).exists()
                status = "✓ Found" if exists else "✗ Not found"
                info_lines.append(f"Settings File: {status}")
                info_lines.append(f"  {settings_path}")

            if history_path:
                exists = Path(history_path).exists()
                status = "✓ Found" if exists else "✗ Not found"
                info_lines.append(f"History File: {status}")
                info_lines.append(f"  {history_path}")
        else:
            info_lines.append("Status: Disabled")
        info_lines.append("")

        # Directory info
        info_lines.append("FOLDER LOCATIONS")
        info_lines.append("─" * 50)

        bp_dir = self.app_context.get_setting('blueprints_dir', '')
        if bp_dir:
            exists = Path(bp_dir).exists() if bp_dir else False
            status = "✓" if exists else "✗"
            info_lines.append(f"Blueprints {status}: {bp_dir}")
        else:
            info_lines.append("Blueprints: Not configured")

        cf_dir = self.app_context.get_setting('customer_files_dir', '')
        if cf_dir:
            exists = Path(cf_dir).exists() if cf_dir else False
            status = "✓" if exists else "✗"
            info_lines.append(f"Customer Files {status}: {cf_dir}")
        else:
            info_lines.append("Customer Files: Not configured")

        itar_bp = self.app_context.get_setting('itar_blueprints_dir', '')
        if itar_bp:
            exists = Path(itar_bp).exists()
            status = "✓" if exists else "✗"
            info_lines.append(f"ITAR Blueprints {status}: {itar_bp}")

        itar_cf = self.app_context.get_setting('itar_customer_files_dir', '')
        if itar_cf:
            exists = Path(itar_cf).exists()
            status = "✓" if exists else "✗"
            info_lines.append(f"ITAR Customer Files {status}: {itar_cf}")
        info_lines.append("")

        # Configuration
        info_lines.append("SETTINGS")
        info_lines.append("─" * 50)
        link_type = self.app_context.get_setting('link_type', 'hard')
        link_name = {'hard': 'Hard Link', 'symbolic': 'Symbolic Link', 'copy': 'Copy'}
        info_lines.append(f"File Link Type: {link_name.get(link_type, link_type)}")

        extensions = self.app_context.get_setting('blueprint_extensions', [])
        info_lines.append(f"Blueprint File Types: {', '.join(extensions) if extensions else 'None'}")

        structure = self.app_context.get_setting('job_folder_structure', '')
        if structure:
            info_lines.append(f"Job Folder Pattern: {structure}")
        info_lines.append("")

        # History stats
        info_lines.append("DATABASE")
        info_lines.append("─" * 50)
        recent_jobs = self.app_context.history.get('recent_jobs', [])
        customers = self.app_context.history.get('customers', {})
        info_lines.append(f"Recent Jobs Tracked: {len(recent_jobs)}")
        info_lines.append(f"Customers: {len(customers)}")

        self.info_text.setPlainText('\n'.join(info_lines))
        self.log_message("System information refreshed")

    # ==================== OOBE WIZARD ====================

    def run_oobe_wizard(self):
        """Run the first-time setup wizard"""
        try:
            # Check if already configured
            bp_dir = self.app_context.get_setting('blueprints_dir', '')
            cf_dir = self.app_context.get_setting('customer_files_dir', '')

            if bp_dir and cf_dir:
                # Already configured - show warning
                reply = QMessageBox.question(
                    self._widget,
                    "Run Setup Wizard?",
                    "JobDocs is already configured.\n\n"
                    "The setup wizard will let you change folder locations and other critical settings.\n\n"
                    "⚠️ Changing folder locations can affect how JobDocs finds your files.\n\n"
                    "Do you want to continue?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No
                )

                if reply == QMessageBox.StandardButton.No:
                    return

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
                self._update_setup_status()

        except Exception as e:
            self.show_error("Error", f"Failed to run setup wizard:\n{e}")
            import traceback
            traceback.print_exc()
