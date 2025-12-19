#!/usr/bin/env python3
"""
Test OOBE (Out-of-Box Experience) Wizard

This script launches the OOBE wizard for testing purposes without:
- Loading real settings from disk
- Saving settings to disk
- Modifying any existing configuration

Perfect for testing the first-run experience.
"""

import sys
from pathlib import Path
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import QTimer


class MockAppContext:
    """Mock application context for OOBE testing"""

    def __init__(self):
        # Start with default settings (fresh install simulation)
        self.settings = {
            'blueprints_dir': '',
            'customer_files_dir': '',
            'itar_blueprints_dir': '',
            'itar_customer_files_dir': '',
            'link_type': 'hard',
            'blueprint_extensions': ['.pdf', '.dwg', '.dxf'],
            'allow_duplicate_jobs': False,
            'ui_style': 'Fusion',
            'job_folder_structure': '{customer}/{job_folder}/job documents',
            'quote_folder_path': 'Quotes',
            'legacy_mode': True,
            'default_tab': 0,
            'disabled_modules': [],
            'network_users_path': '',
            'network_shared_enabled': False,
            'network_settings_path': '',
            'network_history_path': '',
            'user_auth_enabled': False,
            'oobe_completed': False
        }

        self.config_dir = Path.home() / '.local' / 'share' / 'JobDocs'
        self.history = {
            'recent_jobs': [],
            'customers': []
        }
        self.main_window = None

    def save_settings_callback(self):
        """Mock save - prints what would be saved instead of actually saving"""
        print("\n" + "="*60)
        print("OOBE COMPLETED - Settings that would be saved:")
        print("="*60)
        for key, value in sorted(self.settings.items()):
            if value:  # Only show non-empty values
                print(f"  {key}: {value}")
        print("="*60)
        print("\nNOTE: Settings were NOT actually saved (test mode)")
        print("="*60 + "\n")

    def save_history_callback(self):
        """Mock save - does nothing"""
        pass

    def log_message_callback(self, message):
        """Mock log - prints to console"""
        print(f"[LOG] {message}")

    def show_error_callback(self, title, message):
        """Mock error - prints to console"""
        print(f"[ERROR] {title}: {message}")

    def show_info_callback(self, title, message):
        """Mock info - prints to console"""
        print(f"[INFO] {title}: {message}")

    def get_customer_list_callback(self):
        """Mock customer list"""
        return []

    def add_to_history_callback(self, job_data):
        """Mock add to history"""
        pass


def run_oobe_test():
    """Run the OOBE wizard in test mode"""

    app = QApplication(sys.argv)

    print("\n" + "="*60)
    print("JobDocs OOBE Test Mode")
    print("="*60)
    print("This will launch the first-time setup wizard.")
    print("Settings will NOT be saved to disk.")
    print("="*60 + "\n")

    # Create mock app context
    app_context = MockAppContext()

    # Import and create OOBE wizard
    try:
        from modules.admin.oobe_wizard import OOBEWizard

        # Create wizard
        wizard = OOBEWizard(app_context)

        # Show wizard
        result = wizard.exec()

        if result:
            print("\n✓ OOBE Wizard completed successfully!")
            print("\nUpdated settings:")
            print("-" * 60)

            # Show what changed from defaults
            changed_settings = {}
            for key, value in app_context.settings.items():
                # Compare with default mock settings
                default_value = MockAppContext().settings.get(key)
                if value != default_value:
                    changed_settings[key] = value

            if changed_settings:
                for key, value in sorted(changed_settings.items()):
                    print(f"  {key}: {value}")
            else:
                print("  (No settings were changed)")

            print("-" * 60)
        else:
            print("\n✗ OOBE Wizard was cancelled")

    except ImportError as e:
        QMessageBox.critical(
            None,
            "Error",
            f"Failed to load OOBE wizard:\n{e}\n\n"
            f"Make sure the admin module is enabled:\n"
            f"  mv modules/_admin modules/admin"
        )
        sys.exit(1)
    except Exception as e:
        QMessageBox.critical(
            None,
            "Error",
            f"Error running OOBE wizard:\n{e}"
        )
        import traceback
        traceback.print_exc()
        sys.exit(1)

    sys.exit(0)


if __name__ == '__main__':
    run_oobe_test()
