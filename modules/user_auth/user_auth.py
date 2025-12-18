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

    def __init__(self, users_file: Path, network_users_file: Optional[Path] = None):
        """
        Initialize user authentication system

        Args:
            users_file: Path to the local users database file (JSON)
            network_users_file: Optional path to network-shared users file
        """
        self.users_file = users_file
        self.network_users_file = network_users_file
        self.using_network = False
        self.users = self._load_users()

    def _load_users(self) -> Dict:
        """Load users from network file (preferred) or local file (fallback)"""
        # Try network file first if configured
        if self.network_users_file:
            try:
                network_path = Path(self.network_users_file)
                if network_path.exists():
                    with open(network_path, 'r') as f:
                        users = json.load(f)
                    self.using_network = True
                    print(f"[UserAuth] Loaded users from network: {network_path}")
                    return users
            except (json.JSONDecodeError, IOError) as e:
                print(f"Warning: Could not load network users ({self.network_users_file}): {e}")
                print(f"[UserAuth] Falling back to local users file")

        # Fall back to local file
        if self.users_file.exists():
            try:
                with open(self.users_file, 'r') as f:
                    users = json.load(f)
                self.using_network = False
                print(f"[UserAuth] Loaded users from local file: {self.users_file}")
                return users
            except (json.JSONDecodeError, IOError) as e:
                print(f"Warning: Could not load local users: {e}")

        self.using_network = False
        return {}

    def _save_users(self):
        """Save users to network file (if using network) or local file"""
        target_file = self.network_users_file if self.using_network and self.network_users_file else self.users_file

        try:
            # Create parent directory if needed
            Path(target_file).parent.mkdir(parents=True, exist_ok=True)

            with open(target_file, 'w') as f:
                json.dump(self.users, f, indent=2)

            location = "network" if self.using_network else "local"
            print(f"[UserAuth] Saved users to {location} file: {target_file}")
        except IOError as e:
            raise RuntimeError(f"Failed to save users to {target_file}: {e}")

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

    def create_user(self, username: str, password: str, full_name: str = "", is_admin: bool = False) -> bool:
        """
        Create a new user with hashed password

        Args:
            username: Username (case-insensitive, will be lowercased)
            password: Plain text password (will be hashed)
            full_name: User's full name (optional)
            is_admin: Whether user has admin privileges (default: False)

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
            'is_admin': is_admin,
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

    def is_admin(self, username: str) -> bool:
        """
        Check if a user has admin privileges

        Args:
            username: Username to check

        Returns:
            True if user is an admin
        """
        username = username.lower().strip()
        if username not in self.users:
            return False
        return self.users[username].get('is_admin', False)

    def set_admin(self, username: str, is_admin: bool) -> bool:
        """
        Set admin status for a user

        Args:
            username: Username
            is_admin: Whether user should be admin

        Returns:
            True if successful
        """
        username = username.lower().strip()
        if username not in self.users:
            return False

        self.users[username]['is_admin'] = is_admin
        self._save_users()
        return True

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
