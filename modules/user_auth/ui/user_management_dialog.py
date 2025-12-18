"""
User Management Dialog for JobDocs

Provides UI for managing users (create, delete, change password).
Part of experimental features.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox, QListWidget, QGroupBox, QCheckBox
)
from PyQt6.QtCore import Qt
from modules.user_auth.user_auth import UserAuth


class CreateUserDialog(QDialog):
    """Dialog for creating a new user"""

    def __init__(self, user_auth: UserAuth, is_first_user: bool = False, parent=None):
        super().__init__(parent)
        self.user_auth = user_auth
        self.is_first_user = is_first_user
        self.username = None
        self.setWindowTitle("Create New User")
        self.setModal(True)
        self.setMinimumWidth(400)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        if self.is_first_user:
            info = QLabel("Create the first user account.\nThis user will have access to user management.")
            info.setStyleSheet("font-weight: bold; margin-bottom: 10px;")
            layout.addWidget(info)

        # Username
        layout.addWidget(QLabel("Username:"))
        self.username_edit = QLineEdit()
        self.username_edit.setPlaceholderText("Enter username (lowercase)")
        layout.addWidget(self.username_edit)

        # Full name
        layout.addWidget(QLabel("Full Name (optional):"))
        self.fullname_edit = QLineEdit()
        self.fullname_edit.setPlaceholderText("Enter full name")
        layout.addWidget(self.fullname_edit)

        # Password
        layout.addWidget(QLabel("Password:"))
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_edit.setPlaceholderText("Enter password (min 4 characters)")
        layout.addWidget(self.password_edit)

        # Confirm password
        layout.addWidget(QLabel("Confirm Password:"))
        self.confirm_edit = QLineEdit()
        self.confirm_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_edit.setPlaceholderText("Re-enter password")
        layout.addWidget(self.confirm_edit)

        # Show password
        self.show_password_check = QCheckBox("Show passwords")
        self.show_password_check.toggled.connect(self.toggle_password_visibility)
        layout.addWidget(self.show_password_check)

        # Buttons
        button_layout = QHBoxLayout()
        create_btn = QPushButton("Create User")
        create_btn.clicked.connect(self.create_user)
        create_btn.setDefault(True)
        button_layout.addWidget(create_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        layout.addLayout(button_layout)

    def toggle_password_visibility(self, checked: bool):
        """Toggle password visibility"""
        mode = QLineEdit.EchoMode.Normal if checked else QLineEdit.EchoMode.Password
        self.password_edit.setEchoMode(mode)
        self.confirm_edit.setEchoMode(mode)

    def create_user(self):
        """Create the user"""
        username = self.username_edit.text().strip()
        password = self.password_edit.text()
        confirm = self.confirm_edit.text()
        full_name = self.fullname_edit.text().strip()

        if not username:
            QMessageBox.warning(self, "Error", "Username cannot be empty.")
            return

        if not password:
            QMessageBox.warning(self, "Error", "Password cannot be empty.")
            return

        if password != confirm:
            QMessageBox.warning(self, "Error", "Passwords do not match.")
            return

        try:
            self.user_auth.create_user(username, password, full_name)
            self.username = username
            self.accept()
        except ValueError as e:
            QMessageBox.warning(self, "Error", str(e))


class UserManagementDialog(QDialog):
    """Dialog for managing users"""

    def __init__(self, user_auth: UserAuth, current_user: str, parent=None):
        super().__init__(parent)
        self.user_auth = user_auth
        self.current_user = current_user
        self.setWindowTitle("User Management")
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)
        self.setup_ui()
        self.refresh_user_list()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Current user info
        current_user_label = QLabel(f"Logged in as: {self.current_user}")
        current_user_label.setStyleSheet("font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(current_user_label)

        # User list
        list_group = QGroupBox("Users")
        list_layout = QVBoxLayout(list_group)

        self.user_list = QListWidget()
        self.user_list.itemSelectionChanged.connect(self.update_buttons)
        list_layout.addWidget(self.user_list)

        layout.addWidget(list_group)

        # Buttons
        button_layout = QHBoxLayout()

        self.create_btn = QPushButton("Create New User")
        self.create_btn.clicked.connect(self.create_user)
        button_layout.addWidget(self.create_btn)

        self.delete_btn = QPushButton("Delete User")
        self.delete_btn.clicked.connect(self.delete_user)
        self.delete_btn.setEnabled(False)
        button_layout.addWidget(self.delete_btn)

        self.change_password_btn = QPushButton("Change My Password")
        self.change_password_btn.clicked.connect(self.change_password)
        button_layout.addWidget(self.change_password_btn)

        layout.addLayout(button_layout)

        # Close button
        close_layout = QHBoxLayout()
        close_layout.addStretch()
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        close_layout.addWidget(close_btn)
        layout.addLayout(close_layout)

    def refresh_user_list(self):
        """Refresh the user list"""
        self.user_list.clear()
        for username in sorted(self.user_auth.list_users()):
            user_info = self.user_auth.get_user_info(username)
            full_name = user_info.get('full_name', '')
            display = f"{username}"
            if full_name:
                display += f" ({full_name})"
            if username == self.current_user:
                display += " [YOU]"
            self.user_list.addItem(display)

    def update_buttons(self):
        """Update button states based on selection"""
        selected_items = self.user_list.selectedItems()
        if selected_items:
            selected_text = selected_items[0].text()
            # Extract username from display text
            username = selected_text.split(' ')[0]
            # Can't delete yourself
            self.delete_btn.setEnabled(username != self.current_user)
        else:
            self.delete_btn.setEnabled(False)

    def create_user(self):
        """Create a new user"""
        dialog = CreateUserDialog(self.user_auth, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            QMessageBox.information(
                self,
                "Success",
                f"User '{dialog.username}' created successfully."
            )
            self.refresh_user_list()

    def delete_user(self):
        """Delete selected user"""
        selected_items = self.user_list.selectedItems()
        if not selected_items:
            return

        selected_text = selected_items[0].text()
        username = selected_text.split(' ')[0]

        if username == self.current_user:
            QMessageBox.warning(self, "Error", "You cannot delete yourself.")
            return

        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete user '{username}'?\n\nThis cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            if self.user_auth.delete_user(username):
                QMessageBox.information(self, "Success", f"User '{username}' deleted.")
                self.refresh_user_list()

    def change_password(self):
        """Change current user's password"""
        dialog = ChangePasswordDialog(self.user_auth, self.current_user, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            QMessageBox.information(
                self,
                "Success",
                "Password changed successfully."
            )


class ChangePasswordDialog(QDialog):
    """Dialog for changing password"""

    def __init__(self, user_auth: UserAuth, username: str, parent=None):
        super().__init__(parent)
        self.user_auth = user_auth
        self.username = username
        self.setWindowTitle("Change Password")
        self.setModal(True)
        self.setMinimumWidth(400)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel(f"Change password for: {self.username}"))

        # Current password
        layout.addWidget(QLabel("Current Password:"))
        self.current_password_edit = QLineEdit()
        self.current_password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.current_password_edit)

        # New password
        layout.addWidget(QLabel("New Password:"))
        self.new_password_edit = QLineEdit()
        self.new_password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.new_password_edit.setPlaceholderText("Min 4 characters")
        layout.addWidget(self.new_password_edit)

        # Confirm new password
        layout.addWidget(QLabel("Confirm New Password:"))
        self.confirm_password_edit = QLineEdit()
        self.confirm_password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.confirm_password_edit)

        # Show passwords
        self.show_password_check = QCheckBox("Show passwords")
        self.show_password_check.toggled.connect(self.toggle_password_visibility)
        layout.addWidget(self.show_password_check)

        # Buttons
        button_layout = QHBoxLayout()
        change_btn = QPushButton("Change Password")
        change_btn.clicked.connect(self.change_password)
        change_btn.setDefault(True)
        button_layout.addWidget(change_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        layout.addLayout(button_layout)

    def toggle_password_visibility(self, checked: bool):
        """Toggle password visibility"""
        mode = QLineEdit.EchoMode.Normal if checked else QLineEdit.EchoMode.Password
        self.current_password_edit.setEchoMode(mode)
        self.new_password_edit.setEchoMode(mode)
        self.confirm_password_edit.setEchoMode(mode)

    def change_password(self):
        """Change the password"""
        current = self.current_password_edit.text()
        new = self.new_password_edit.text()
        confirm = self.confirm_password_edit.text()

        if not current or not new:
            QMessageBox.warning(self, "Error", "All fields are required.")
            return

        if new != confirm:
            QMessageBox.warning(self, "Error", "New passwords do not match.")
            return

        try:
            self.user_auth.change_password(self.username, current, new)
            self.accept()
        except ValueError as e:
            QMessageBox.warning(self, "Error", str(e))
            self.current_password_edit.clear()
            self.current_password_edit.setFocus()
