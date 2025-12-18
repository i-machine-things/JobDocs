"""
Login Dialog for JobDocs

Provides user authentication UI.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox, QCheckBox
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

        # Title
        title = QLabel("JobDocs - User Login")
        title.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Username
        username_layout = QHBoxLayout()
        username_layout.addWidget(QLabel("Username:"))
        self.username_edit = QLineEdit()
        self.username_edit.setPlaceholderText("Enter username")
        self.username_edit.returnPressed.connect(self.login)
        username_layout.addWidget(self.username_edit)
        layout.addLayout(username_layout)

        # Password
        password_layout = QHBoxLayout()
        password_layout.addWidget(QLabel("Password:"))
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_edit.setPlaceholderText("Enter password")
        self.password_edit.returnPressed.connect(self.login)
        password_layout.addWidget(self.password_edit)
        layout.addLayout(password_layout)

        # Show password checkbox
        self.show_password_check = QCheckBox("Show password")
        self.show_password_check.toggled.connect(self.toggle_password_visibility)
        layout.addWidget(self.show_password_check)

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

        layout.addLayout(button_layout)

        # Info message
        if not self.user_auth.list_users():
            info = QLabel("No users found. Create the first user to get started.")
            info.setStyleSheet("color: #666; font-style: italic; margin-top: 10px;")
            info.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(info)

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
