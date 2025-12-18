# User Authentication Module (Experimental)

This module provides secure user authentication for JobDocs using industry-standard password hashing.

## Security Features

- **PBKDF2-HMAC-SHA256** password hashing with 100,000 iterations (OWASP recommended)
- **Random salts** (256-bit) for each password
- **NO plaintext passwords** stored anywhere
- **Constant-time comparisons** to prevent timing attacks
- **Secure password requirements**: Minimum 4 characters (configurable)

## How to Enable

1. **Rename this directory** from `_user_auth` to `user_auth` (remove the underscore)
2. **Restart JobDocs**
3. Go to **File → Settings → Advanced Settings**
4. Enable **"Enable experimental features (Reporting)"**
5. Enable **"User Authentication"** checkbox (will appear after step 4)
6. Click **Save** and restart JobDocs again

## First Time Setup

When you enable user authentication and restart JobDocs:

1. A login dialog will appear
2. Since no users exist, click **"Create First User"**
3. Enter a username, optional full name, and password
4. Click **"Create User"**
5. Log in with your new credentials

## Features

### User Management

Access via the **User Management** module tab:
- **Create New User**: Add additional users to the system
- **Delete User**: Remove users (cannot delete yourself)
- **Change My Password**: Update your own password

### Login System

- Username and password authentication
- Optional "show password" checkbox
- Remembers last login time for each user
- Window title shows currently logged-in user

### Password Security

Passwords are hashed using PBKDF2-HMAC-SHA256:
- **Salt**: Random 256-bit salt per password
- **Iterations**: 100,000 (slows down brute force attacks)
- **Output**: 256-bit hash

Example of stored user data (in `~/.local/share/JobDocs/users.json`):
```json
{
  "john": {
    "password_hash": "a1b2c3...",
    "salt": "d4e5f6...",
    "full_name": "John Doe",
    "created": null,
    "last_login": "2025-01-15T10:30:00"
  }
}
```

**Note**: Even with access to this file, passwords cannot be recovered - they can only be verified against the hash.

## Use Cases

### Single User
If you're the only user, you may not need this module. The login adds an extra step each time you start JobDocs.

### Multiple Users on Same Machine
Track who makes changes and prevent unauthorized access to JobDocs.

### Network Shared Settings
When combined with network shared settings, each user logs in with their own credentials while sharing configuration and history.

## Technical Details

### File Structure

```
modules/user_auth/
├── __init__.py              # Module package marker
├── module.py                # JobDocs module integration
├── user_auth.py             # Authentication backend
├── ui/
│   ├── __init__.py
│   ├── login_dialog.py      # Login UI
│   └── user_management_dialog.py  # User management UI
└── README.md                # This file
```

### Authentication Flow

1. User enters username and password
2. System looks up user by username
3. Password is hashed with stored salt
4. Hash is compared with stored hash using constant-time comparison
5. On success: user is authenticated and last_login is updated
6. On failure: generic error message (doesn't reveal if username exists)

### Password Hashing

```python
def _hash_password(password: str, salt: str) -> str:
    password_bytes = password.encode('utf-8')
    salt_bytes = bytes.fromhex(salt)

    hash_bytes = hashlib.pbkdf2_hmac(
        'sha256',           # Hash function
        password_bytes,      # Password
        salt_bytes,          # Salt
        100000               # Iterations
    )

    return hash_bytes.hex()
```

## Security Considerations

### What This Module Protects Against

- ✅ Casual unauthorized access
- ✅ Password database theft (passwords are hashed)
- ✅ Timing attacks (constant-time comparisons)
- ✅ Rainbow table attacks (random salts)
- ✅ Brute force attacks (100,000 iterations makes it slow)

### What This Module Does NOT Protect Against

- ❌ Physical access to the computer (user can access files directly)
- ❌ Keyloggers or screen capture malware
- ❌ Someone with admin/root access to the system
- ❌ Social engineering attacks

### Best Practices

1. **Choose strong passwords**: Use a mix of letters, numbers, and symbols
2. **Don't share credentials**: Each user should have their own account
3. **Regular password changes**: Update passwords periodically
4. **Protect users.json**: This file contains hashed passwords - protect it with file permissions
5. **Backup strategy**: If you lose access, there's no password recovery (by design)

## Limitations

- **No password recovery**: If you forget your password, you cannot recover it
  - Workaround: Another user can delete your account and you can create a new one
  - Or manually delete `users.json` to start fresh (loses all user accounts)
- **Minimum password length**: Currently hardcoded to 4 characters
  - Can be modified in `user_auth.py` if needed
- **No password complexity requirements**: Users can choose weak passwords
  - This is intentional for simplicity - add validation if needed
- **No account lockout**: Unlimited login attempts
  - Could add rate limiting if needed

## FAQ

### Can I skip the login?
No, once enabled, you must log in to use JobDocs. Disable the feature to remove the login requirement.

### Can I recover a forgotten password?
No. By design, passwords cannot be recovered. Another user can delete the account or you can manually delete `users.json`.

### Where are passwords stored?
In `~/.local/share/JobDocs/users.json` (Linux) or equivalent on Windows/macOS. Passwords are hashed, not in plaintext.

### Is this secure enough for production?
This module uses industry-standard password hashing (PBKDF2-HMAC-SHA256). It's suitable for protecting against casual unauthorized access, not for high-security environments.

### Can I integrate with LDAP/Active Directory?
Not currently. This is a self-contained authentication system. LDAP integration would require significant additional development.

## Development Notes

### Adding Features

To add features to this module:

1. Modify backend logic in `user_auth.py`
2. Add UI in `ui/login_dialog.py` or `ui/user_management_dialog.py`
3. Update `module.py` if adding new module tabs
4. Document changes in this README

### Password Requirements

To change minimum password length, edit `user_auth.py`:

```python
if len(password) < 8:  # Change from 4 to 8
    raise ValueError("Password must be at least 8 characters")
```

### Adding Password Complexity

Add validation in `create_user()` method:

```python
if not any(c.isdigit() for c in password):
    raise ValueError("Password must contain at least one number")
if not any(c.isupper() for c in password):
    raise ValueError("Password must contain at least one uppercase letter")
```

## License

Part of JobDocs - MIT License
