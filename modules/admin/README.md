# Admin Module

The Admin module provides administrative controls for managing JobDocs in a team environment.

## Features

### User Management
- Create new user accounts
- Delete existing users
- View all users in the system
- Change user passwords

### Global Settings Management
- View and edit network-shared settings
- Control which settings are synchronized across the team
- Manage directory paths, link types, and other global configurations
- Preview local vs. shared settings

## Usage

This module is only useful when:
1. User authentication is enabled (`user_auth_enabled: true` in settings)
2. Network shared settings are enabled (`network_shared_enabled: true` in settings)

## Tab Order

Order: 90 (appears after History and Reporting tabs)
