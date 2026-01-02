"""
Login Dialog for JobDocs

Provides user authentication UI.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox, QCheckBox, QTabWidget, QListWidget, QWidget
)
from PyQt6.QtCore import Qt
from modules.user_auth.user_auth import UserAuth


class LoginDialog(QDialog):
    """User login dialog"""

    def __init__(self, user_auth: UserAuth, parent=None):
        super().__init__(parent)
        self.user_auth = user_auth
        self.authenticated_user = None
        self.setWindowTitle("JobDocs Login")
        self.setModal(True)
        self.setMinimumWidth(350)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Create tab widget
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        # Login tab
        login_tab = QWidget()
        login_layout = QVBoxLayout(login_tab)

        # Title
        title = QLabel("JobDocs - User Login")
        title.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        login_layout.addWidget(title)

        # Username
        username_layout = QHBoxLayout()
        username_layout.addWidget(QLabel("Username:"))
        self.username_edit = QLineEdit()
        self.username_edit.setPlaceholderText("Enter username")
        self.username_edit.returnPressed.connect(self.login)
        username_layout.addWidget(self.username_edit)
        login_layout.addLayout(username_layout)

        # Password
        password_layout = QHBoxLayout()
        password_layout.addWidget(QLabel("Password:"))
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_edit.setPlaceholderText("Enter password")
        self.password_edit.returnPressed.connect(self.login)
        password_layout.addWidget(self.password_edit)
        login_layout.addLayout(password_layout)

        # Show password checkbox
        self.show_password_check = QCheckBox("Show password")
        self.show_password_check.toggled.connect(self.toggle_password_visibility)
        login_layout.addWidget(self.show_password_check)

        # Buttons
        button_layout = QHBoxLayout()

        self.login_btn = QPushButton("Login")
        self.login_btn.clicked.connect(self.login)
        self.login_btn.setDefault(True)
        button_layout.addWidget(self.login_btn)

        # Only show "Create User" if no users exist
        if not self.user_auth.list_users():
            create_user_btn = QPushButton("Create First User")
            create_user_btn.clicked.connect(self.create_first_user)
            button_layout.addWidget(create_user_btn)

        login_layout.addLayout(button_layout)

        # Info message
        if not self.user_auth.list_users():
            info = QLabel("No users found. Create the first user to get started.")
            info.setStyleSheet("color: #666; font-style: italic; margin-top: 10px;")
            info.setAlignment(Qt.AlignmentFlag.AlignCenter)
            login_layout.addWidget(info)

        # Add login tab
        self.tabs.addTab(login_tab, "Login")

        # Users tab
        users_tab = QWidget()
        users_layout = QVBoxLayout(users_tab)

        # Users list
        users_title = QLabel("Currently Logged In Users")
        users_title.setStyleSheet("font-size: 14px; font-weight: bold; margin: 10px;")
        users_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        users_layout.addWidget(users_title)

        self.users_list = QListWidget()
        self.users_list.setSelectionMode(QListWidget.SelectionMode.NoSelection)
        users_layout.addWidget(self.users_list)

        # Refresh button
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh_logged_in_users)
        users_layout.addWidget(refresh_btn)

        # Add users tab
        self.tabs.addTab(users_tab, "Users")

        # Populate users list initially
        self.refresh_logged_in_users()

        # Focus username field
        self.username_edit.setFocus()

    def toggle_password_visibility(self, checked: bool):
        """Toggle password visibility"""
        if checked:
            self.password_edit.setEchoMode(QLineEdit.EchoMode.Normal)
        else:
            self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)

    def login(self):
        """Attempt to log in"""
        username = self.username_edit.text().strip()
        password = self.password_edit.text()

        if not username or not password:
            QMessageBox.warning(
                self,
                "Login Failed",
                "Please enter both username and password."
            )
            return

        if self.user_auth.verify_user(username, password):
            self.authenticated_user = username
            self.user_auth.update_last_login(username)
            self.accept()
        else:
            QMessageBox.warning(
                self,
                "Login Failed",
                "Invalid username or password."
            )
            self.password_edit.clear()
            self.password_edit.setFocus()

    def create_first_user(self):
        """Create the first user (only shown when no users exist)"""
        from modules.user_auth.ui.user_management_dialog import CreateUserDialog

        dialog = CreateUserDialog(self.user_auth, is_first_user=True, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            QMessageBox.information(
                self,
                "User Created",
                f"User '{dialog.username}' created successfully!\n\nYou can now log in."
            )
            self.username_edit.setText(dialog.username)
            self.password_edit.setFocus()

    def get_authenticated_user(self) -> str:
        """Get the authenticated username"""
        return self.authenticated_user

    def refresh_logged_in_users(self):
        """Refresh the list of currently logged-in users"""
        self.users_list.clear()

        # Get logged-in users from UserAuth
        logged_in = self.user_auth.get_logged_in_users(timeout_minutes=60)

        if not logged_in:
            item_text = "No users currently logged in"
            self.users_list.addItem(item_text)
        else:
            for user_info in logged_in:
                username = user_info['username']
                full_name = user_info['full_name']
                login_time = user_info['login_time']

                # Format the display text
                if full_name:
                    display_text = f"{username} ({full_name})"
                else:
                    display_text = username

                # Add login time if available
                if login_time:
                    try:
                        from datetime import datetime
                        dt = datetime.fromisoformat(login_time)
                        time_str = dt.strftime("%I:%M %p")
                        display_text += f" - logged in at {time_str}"
                    except ValueError:
                        pass

                self.users_list.addItem(display_text)
