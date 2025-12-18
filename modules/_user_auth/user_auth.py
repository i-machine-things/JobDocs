"""
User Authentication System for JobDocs

Provides secure user authentication with password hashing.
Does NOT store passwords in plaintext.
"""

import json
import hashlib
import secrets
from pathlib import Path
from typing import Dict, Optional, Tuple


class UserAuth:
    """Manages user authentication with secure password storage"""

    def __init__(self, users_file: Path):
        """
        Initialize user authentication system

        Args:
            users_file: Path to the users database file (JSON)
        """
        self.users_file = users_file
        self.users = self._load_users()

    def _load_users(self) -> Dict:
        """Load users from file"""
        if self.users_file.exists():
            try:
                with open(self.users_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Warning: Could not load users: {e}")
        return {}

    def _save_users(self):
        """Save users to file"""
        try:
            # Create parent directory if needed
            self.users_file.parent.mkdir(parents=True, exist_ok=True)

            with open(self.users_file, 'w') as f:
                json.dump(self.users, f, indent=2)
        except IOError as e:
            raise RuntimeError(f"Failed to save users: {e}")

    def _hash_password(self, password: str, salt: str) -> str:
        """
        Hash a password using PBKDF2-HMAC-SHA256

        Args:
            password: Plain text password
            salt: Random salt (hex string)

        Returns:
            Hashed password (hex string)
        """
        # Use PBKDF2 with 100,000 iterations (OWASP recommended minimum)
        password_bytes = password.encode('utf-8')
        salt_bytes = bytes.fromhex(salt)

        hash_bytes = hashlib.pbkdf2_hmac(
            'sha256',
            password_bytes,
            salt_bytes,
            100000  # iterations
        )

        return hash_bytes.hex()

    def create_user(self, username: str, password: str, full_name: str = "") -> bool:
        """
        Create a new user with hashed password

        Args:
            username: Username (case-insensitive, will be lowercased)
            password: Plain text password (will be hashed)
            full_name: User's full name (optional)

        Returns:
            True if user created successfully

        Raises:
            ValueError: If username already exists or password is too weak
        """
        username = username.lower().strip()

        if not username:
            raise ValueError("Username cannot be empty")

        if username in self.users:
            raise ValueError(f"User '{username}' already exists")

        if len(password) < 4:
            raise ValueError("Password must be at least 4 characters")

        # Generate random salt (32 bytes = 256 bits)
        salt = secrets.token_hex(32)

        # Hash the password
        password_hash = self._hash_password(password, salt)

        # Store user data
        self.users[username] = {
            'password_hash': password_hash,
            'salt': salt,
            'full_name': full_name,
            'created': None,  # Could add timestamp if needed
            'last_login': None
        }

        self._save_users()
        return True

    def verify_user(self, username: str, password: str) -> bool:
        """
        Verify a user's credentials

        Args:
            username: Username
            password: Plain text password

        Returns:
            True if credentials are valid
        """
        username = username.lower().strip()

        if username not in self.users:
            # Use constant-time comparison to prevent username enumeration
            # Hash a dummy password to keep timing consistent
            dummy_salt = secrets.token_hex(32)
            self._hash_password(password, dummy_salt)
            return False

        user_data = self.users[username]
        salt = user_data['salt']
        stored_hash = user_data['password_hash']

        # Hash the provided password with the stored salt
        password_hash = self._hash_password(password, salt)

        # Constant-time comparison to prevent timing attacks
        return secrets.compare_digest(password_hash, stored_hash)

    def change_password(self, username: str, old_password: str, new_password: str) -> bool:
        """
        Change a user's password

        Args:
            username: Username
            old_password: Current password
            new_password: New password

        Returns:
            True if password changed successfully

        Raises:
            ValueError: If old password is incorrect or new password is too weak
        """
        if not self.verify_user(username, old_password):
            raise ValueError("Current password is incorrect")

        if len(new_password) < 4:
            raise ValueError("New password must be at least 4 characters")

        username = username.lower().strip()

        # Generate new salt
        salt = secrets.token_hex(32)
        password_hash = self._hash_password(new_password, salt)

        # Update user data
        self.users[username]['password_hash'] = password_hash
        self.users[username]['salt'] = salt

        self._save_users()
        return True

    def delete_user(self, username: str) -> bool:
        """
        Delete a user

        Args:
            username: Username to delete

        Returns:
            True if user deleted successfully
        """
        username = username.lower().strip()

        if username not in self.users:
            return False

        del self.users[username]
        self._save_users()
        return True

    def get_user_info(self, username: str) -> Optional[Dict]:
        """
        Get user information (without password)

        Args:
            username: Username

        Returns:
            Dict with user info (full_name, etc.) or None if user doesn't exist
        """
        username = username.lower().strip()

        if username not in self.users:
            return None

        user_data = self.users[username].copy()
        # Remove sensitive data
        user_data.pop('password_hash', None)
        user_data.pop('salt', None)

        return user_data

    def list_users(self) -> list:
        """
        Get list of all usernames

        Returns:
            List of usernames
        """
        return list(self.users.keys())

    def user_exists(self, username: str) -> bool:
        """
        Check if a user exists

        Args:
            username: Username to check

        Returns:
            True if user exists
        """
        return username.lower().strip() in self.users

    def update_last_login(self, username: str):
        """
        Update the last login time for a user

        Args:
            username: Username
        """
        username = username.lower().strip()

        if username in self.users:
            from datetime import datetime
            self.users[username]['last_login'] = datetime.now().isoformat()
            self._save_users()
