"""
User Authentication Module for JobDocs

Provides secure user authentication system with password hashing.
This is an EXPERIMENTAL feature.

To enable:
1. Rename this directory from _user_auth to user_auth (remove underscore)
2. Enable experimental features in Settings
3. Enable user authentication in Advanced Settings
4. Restart JobDocs
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QDialog
from core.base_module import BaseModule
from core.app_context import AppContext


class UserAuthModule(BaseModule):
    """User authentication management module"""

    def __init__(self, app_context: AppContext):
        super().__init__(app_context)
        self.user_auth = None
        self.current_user = None

    def get_name(self) -> str:
        return "User Management"

    def get_widget(self) -> QWidget:
        """Return the module's main widget"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Info label
        info = QLabel(
            "User Authentication Module\n\n"
            "This module provides secure user authentication.\n"
            "Passwords are hashed using PBKDF2-HMAC-SHA256.\n\n"
            "Manage users using the User Management button below."
        )
        layout.addWidget(info)

        # User management button
        manage_btn = QPushButton("Manage Users")
        manage_btn.clicked.connect(self.open_user_management)
        layout.addWidget(manage_btn)

        layout.addStretch()

        return widget

    def open_user_management(self):
        """Open user management dialog"""
        # Get user auth from main window
        main_window = self.app_context.main_window
        if not hasattr(main_window, 'user_auth') or not main_window.user_auth:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(
                self.app_context.main_window,
                "Not Available",
                "User authentication is not initialized.\n\n"
                "This feature requires a restart after enabling."
            )
            return

        from modules._user_auth.ui.user_management_dialog import UserManagementDialog
        dialog = UserManagementDialog(
            main_window.user_auth,
            main_window.current_user,
            self.app_context.main_window
        )
        dialog.exec()
