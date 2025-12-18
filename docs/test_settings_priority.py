#!/usr/bin/env python3
"""
Test script to verify settings priority logic.

This demonstrates how global (network) settings take precedence over local settings.
"""

import json
import tempfile
from pathlib import Path


def test_settings_priority():
    """Test that network settings take precedence over local settings"""

    # Personal settings that should remain local
    PERSONAL_SETTINGS = {'ui_style', 'default_tab'}

    # Network config that should remain local
    NETWORK_CONFIG_KEYS = {'network_shared_enabled', 'network_settings_path', 'network_history_path'}

    # Create temporary files
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        local_file = tmpdir / 'local_settings.json'
        network_file = tmpdir / 'network_settings.json'

        # Simulate local settings
        local_settings = {
            # Personal (should be preserved from local)
            'ui_style': 'Fusion',
            'default_tab': 2,

            # Network config (should be preserved from local)
            'network_shared_enabled': True,
            'network_settings_path': str(network_file),
            'network_history_path': str(tmpdir / 'history.json'),

            # Shared settings (should be OVERRIDDEN by network)
            'blueprints_dir': '/local/blueprints',
            'customer_files_dir': '/local/customers',
            'link_type': 'copy',
            'blueprint_extensions': ['.pdf'],
        }

        # Simulate network (global) settings
        network_settings = {
            # Shared settings (these should WIN)
            'blueprints_dir': '/network/blueprints',
            'customer_files_dir': '/network/customers',
            'link_type': 'hard',
            'blueprint_extensions': ['.pdf', '.dwg', '.dxf'],

            # Even if network has personal settings, they should be ignored
            'ui_style': 'Windows',  # Should be ignored
            'default_tab': 5,       # Should be ignored
        }

        # Write files
        with open(local_file, 'w') as f:
            json.dump(local_settings, f)
        with open(network_file, 'w') as f:
            json.dump(network_settings, f)

        # Simulate the loading logic from main.py
        merged = {}

        # Start with local settings
        merged.update(local_settings)

        # Load network settings
        network_enabled = local_settings.get('network_shared_enabled', False)
        network_path = local_settings.get('network_settings_path', '')

        if network_enabled and network_path:
            # Network settings take precedence (except personal and network config)
            for key, value in network_settings.items():
                if key not in PERSONAL_SETTINGS and key not in NETWORK_CONFIG_KEYS:
                    merged[key] = value

        # Ensure personal settings and network config use local values
        for key in PERSONAL_SETTINGS | NETWORK_CONFIG_KEYS:
            if key in local_settings:
                merged[key] = local_settings[key]

        # Verify results
        print("=== SETTINGS PRIORITY TEST ===\n")

        print("PERSONAL SETTINGS (should be from LOCAL):")
        print(f"  ui_style: {merged['ui_style']} (expected: Fusion)")
        assert merged['ui_style'] == 'Fusion', "Personal setting not preserved!"
        print(f"  default_tab: {merged['default_tab']} (expected: 2)")
        assert merged['default_tab'] == 2, "Personal setting not preserved!"
        print("  ✓ Personal settings correctly preserved from local\n")

        print("NETWORK CONFIG (should be from LOCAL):")
        print(f"  network_shared_enabled: {merged['network_shared_enabled']} (expected: True)")
        assert merged['network_shared_enabled'] == True, "Network config not preserved!"
        print("  ✓ Network configuration correctly preserved from local\n")

        print("GLOBAL SETTINGS (should be from NETWORK):")
        print(f"  blueprints_dir: {merged['blueprints_dir']}")
        print(f"    (expected: /network/blueprints)")
        assert merged['blueprints_dir'] == '/network/blueprints', "Network setting didn't override!"

        print(f"  customer_files_dir: {merged['customer_files_dir']}")
        print(f"    (expected: /network/customers)")
        assert merged['customer_files_dir'] == '/network/customers', "Network setting didn't override!"

        print(f"  link_type: {merged['link_type']} (expected: hard)")
        assert merged['link_type'] == 'hard', "Network setting didn't override!"

        print(f"  blueprint_extensions: {merged['blueprint_extensions']}")
        print(f"    (expected: ['.pdf', '.dwg', '.dxf'])")
        assert merged['blueprint_extensions'] == ['.pdf', '.dwg', '.dxf'], "Network setting didn't override!"

        print("  ✓ Global settings correctly use network values\n")

        print("=== ALL TESTS PASSED ===")
        print("\nSummary:")
        print("  ✓ Personal settings stay local")
        print("  ✓ Network configuration stays local")
        print("  ✓ Global settings use network values (take precedence)")


if __name__ == '__main__':
    test_settings_priority()
