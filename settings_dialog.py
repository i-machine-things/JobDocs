"""
Settings Dialog for JobDocs

Provides a UI for configuring application settings including:
- Directory paths
- Link types
- File extensions
- Advanced options
"""

from typing import Dict, Any, List
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
    QGroupBox, QLabel, QLineEdit, QPushButton, QCheckBox,
    QRadioButton, QButtonGroup, QComboBox, QScrollArea,
    QWidget, QFrame, QDialogButtonBox, QFileDialog, QMessageBox,
    QStyleFactory
)

from shared.utils import get_os_type, get_os_text


class SettingsDialog(QDialog):
    """Settings dialog"""

    def __init__(self, settings: Dict[str, Any], parent=None, available_modules: List[tuple] = None, is_admin: bool = True):
        super().__init__(parent)
        self.settings = settings.copy()
        self.available_modules = available_modules or []  # List of (module_name, display_name) tuples
        self.module_checkboxes = {}  # Store module checkboxes
        self.is_admin = is_admin  # Track if user is admin
        self.setWindowTitle("Settings")
        self.setMinimumWidth(600)
        self.setup_ui()

    def setup_ui(self):
        # Main dialog layout
        main_layout = QVBoxLayout(self)

        # Create scroll area for content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        # Container for scrollable content
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)

        # Admin-only notice for regular users
        if not self.is_admin:
            notice = QLabel("⚠ Directory and file path settings are managed by your administrator.")
            notice.setStyleSheet("color: #666; font-style: italic; padding: 10px; background-color: #f0f0f0; border-radius: 3px;")
            notice.setWordWrap(True)
            scroll_layout.addWidget(notice)

        # Directories group (admin only)
        if self.is_admin:
            dir_group = QGroupBox("Directories")
            dir_layout = QGridLayout(dir_group)

            # Blueprints
            dir_layout.addWidget(QLabel("Blueprints Directory:"), 0, 0)
            self.blueprints_edit = QLineEdit(self.settings.get('blueprints_dir', ''))
            dir_layout.addWidget(self.blueprints_edit, 0, 1)
            bp_btn = QPushButton("Browse...")
            bp_btn.clicked.connect(lambda: self.browse_dir(self.blueprints_edit))
            dir_layout.addWidget(bp_btn, 0, 2)

            # Customer files
            dir_layout.addWidget(QLabel("Customer Files Directory:"), 1, 0)
            self.customer_files_edit = QLineEdit(self.settings.get('customer_files_dir', ''))
            dir_layout.addWidget(self.customer_files_edit, 1, 1)
            cf_btn = QPushButton("Browse...")
            cf_btn.clicked.connect(lambda: self.browse_dir(self.customer_files_edit))
            dir_layout.addWidget(cf_btn, 1, 2)

            scroll_layout.addWidget(dir_group)
        else:
            # Create dummy edits for non-admin to avoid errors in get_settings()
            self.blueprints_edit = QLineEdit(self.settings.get('blueprints_dir', ''))
            self.customer_files_edit = QLineEdit(self.settings.get('customer_files_dir', ''))

        # ITAR directories group (admin only)
        if self.is_admin:
            itar_group = QGroupBox("ITAR Directories (optional)")
            itar_layout = QGridLayout(itar_group)

            itar_layout.addWidget(QLabel("ITAR Blueprints:"), 0, 0)
            self.itar_blueprints_edit = QLineEdit(self.settings.get('itar_blueprints_dir', ''))
            itar_layout.addWidget(self.itar_blueprints_edit, 0, 1)
            itar_bp_btn = QPushButton("Browse...")
            itar_bp_btn.clicked.connect(lambda: self.browse_dir(self.itar_blueprints_edit))
            itar_layout.addWidget(itar_bp_btn, 0, 2)

            itar_layout.addWidget(QLabel("ITAR Customer Files:"), 1, 0)
            self.itar_customer_files_edit = QLineEdit(self.settings.get('itar_customer_files_dir', ''))
            itar_layout.addWidget(self.itar_customer_files_edit, 1, 1)
            itar_cf_btn = QPushButton("Browse...")
            itar_cf_btn.clicked.connect(lambda: self.browse_dir(self.itar_customer_files_edit))
            itar_layout.addWidget(itar_cf_btn, 1, 2)

            scroll_layout.addWidget(itar_group)
        else:
            # Create dummy edits for non-admin to avoid errors in get_settings()
            self.itar_blueprints_edit = QLineEdit(self.settings.get('itar_blueprints_dir', ''))
            self.itar_customer_files_edit = QLineEdit(self.settings.get('itar_customer_files_dir', ''))

        # Link type group (admin only)
        if self.is_admin:
            link_group = QGroupBox("Link Type")
            link_layout = QHBoxLayout(link_group)

            self.link_type_group = QButtonGroup(self)
            self.hard_radio = QRadioButton("Hard Link")
            self.symbolic_radio = QRadioButton("Symbolic Link")
            self.copy_radio = QRadioButton("Copy")

            self.link_type_group.addButton(self.hard_radio, 0)
            self.link_type_group.addButton(self.symbolic_radio, 1)
            self.link_type_group.addButton(self.copy_radio, 2)

            link_type = self.settings.get('link_type', 'hard')
            if link_type == 'hard':
                self.hard_radio.setChecked(True)
            elif link_type == 'symbolic':
                self.symbolic_radio.setChecked(True)
            else:
                self.copy_radio.setChecked(True)

            link_layout.addWidget(self.hard_radio)
            link_layout.addWidget(self.symbolic_radio)
            link_layout.addWidget(self.copy_radio)
            link_layout.addStretch()

            # Add OS-specific tooltips
            if get_os_type() == "windows":
                self.hard_radio.setToolTip("Creates a hard link. Saves disk space. Files must be on same volume.")
                self.symbolic_radio.setToolTip("Creates a symbolic link. Requires admin or Developer Mode.")
                self.copy_radio.setToolTip("Creates independent copy. Use if on different drives.")
            else:
                self.hard_radio.setToolTip("Creates a hard link. Recommended - saves disk space.")
                self.symbolic_radio.setToolTip("Creates a symbolic link.")
                self.copy_radio.setToolTip("Creates an independent copy.")

            scroll_layout.addWidget(link_group)
        else:
            # Create dummy radio buttons for non-admin
            self.link_type_group = QButtonGroup(self)
            self.hard_radio = QRadioButton("Hard Link")
            self.symbolic_radio = QRadioButton("Symbolic Link")
            self.copy_radio = QRadioButton("Copy")
            link_type = self.settings.get('link_type', 'hard')
            if link_type == 'hard':
                self.hard_radio.setChecked(True)
            elif link_type == 'symbolic':
                self.symbolic_radio.setChecked(True)
            else:
                self.copy_radio.setChecked(True)

        # Blueprint extensions (admin only)
        if self.is_admin:
            ext_group = QGroupBox("Blueprint File Types")
            ext_layout = QVBoxLayout(ext_group)

            ext_layout.addWidget(QLabel("Files with these extensions go to blueprints folder:"))
            self.extensions_edit = QLineEdit(
                ', '.join(self.settings.get('blueprint_extensions', ['.pdf', '.dwg', '.dxf']))
            )
            ext_layout.addWidget(self.extensions_edit)
            ext_layout.addWidget(QLabel("(comma-separated, e.g., .pdf, .dwg, .dxf)"))

            scroll_layout.addWidget(ext_group)
        else:
            # Create dummy edit for non-admin
            self.extensions_edit = QLineEdit(
                ', '.join(self.settings.get('blueprint_extensions', ['.pdf', '.dwg', '.dxf']))
            )

        # Options
        options_group = QGroupBox("Options")
        options_layout = QVBoxLayout(options_group)

        # Allow duplicates (admin only)
        if self.is_admin:
            self.allow_duplicates_check = QCheckBox("Allow duplicate job numbers (not recommended)")
            self.allow_duplicates_check.setChecked(self.settings.get('allow_duplicate_jobs', False))
            options_layout.addWidget(self.allow_duplicates_check)
        else:
            # Create dummy checkbox for non-admin
            self.allow_duplicates_check = QCheckBox("Allow duplicate job numbers (not recommended)")
            self.allow_duplicates_check.setChecked(self.settings.get('allow_duplicate_jobs', False))

        # Default tab setting
        default_tab_layout = QHBoxLayout()
        default_tab_layout.addWidget(QLabel("Default opening tab:"))
        self.default_tab_combo = QComboBox()
        self.default_tab_combo.addItems([
            "Quote",
            "Job",
            "Add to Job",
            "Bulk Create",
            "Search",
            "Import Blueprints",
            "History"
        ])
        current_default = self.settings.get('default_tab', 0)
        if 0 <= current_default < self.default_tab_combo.count():
            self.default_tab_combo.setCurrentIndex(current_default)
        default_tab_layout.addWidget(self.default_tab_combo)
        default_tab_layout.addStretch()
        options_layout.addLayout(default_tab_layout)

        scroll_layout.addWidget(options_group)

        # Modules section
        if self.available_modules:
            modules_group = QGroupBox("Modules")
            modules_layout = QVBoxLayout(modules_group)

            modules_layout.addWidget(QLabel("Enable or disable modules (requires restart):"))

            disabled_modules = self.settings.get('disabled_modules', [])

            for module_name, display_name in sorted(self.available_modules, key=lambda x: x[1]):
                checkbox = QCheckBox(display_name)
                checkbox.setChecked(module_name not in disabled_modules)
                self.module_checkboxes[module_name] = checkbox
                modules_layout.addWidget(checkbox)

            scroll_layout.addWidget(modules_group)

        # Appearance
        appearance_group = QGroupBox("Appearance")
        appearance_layout = QGridLayout(appearance_group)

        appearance_layout.addWidget(QLabel("UI Style:"), 0, 0)
        self.style_combo = QComboBox()
        available_styles = QStyleFactory.keys()
        self.style_combo.addItems(available_styles)
        current_style = self.settings.get('ui_style', 'Fusion')
        if current_style in available_styles:
            self.style_combo.setCurrentText(current_style)
        appearance_layout.addWidget(self.style_combo, 0, 1)
        appearance_layout.addWidget(QLabel("(restart required)"), 0, 2)

        scroll_layout.addWidget(appearance_group)

        # Advanced Settings (collapsible)
        self.advanced_group = QGroupBox("Advanced Settings")
        self.advanced_group.setCheckable(True)
        self.advanced_group.setChecked(False)
        advanced_layout = QVBoxLayout(self.advanced_group)

        self.advanced_content = QWidget()
        advanced_content_layout = QVBoxLayout(self.advanced_content)
        advanced_content_layout.setContentsMargins(0, 0, 0, 0)

        path_example = get_os_text('path_example')
        path_sep = get_os_text('path_sep')
        legacy_example = f"{{customer}}{path_sep}job documents{path_sep}{{job_folder}}"

        # Job folder structure (admin only)
        if self.is_admin:
            advanced_content_layout.addWidget(QLabel("Job Folder Structure:"))
            advanced_content_layout.addWidget(QLabel("Available placeholders: {customer}, {job_folder}"))
            advanced_content_layout.addWidget(QLabel(f"Default: {path_example}"))
            advanced_content_layout.addWidget(QLabel(f"Legacy: {legacy_example}"))

            self.job_structure_edit = QLineEdit(
                self.settings.get('job_folder_structure', '{customer}/{job_folder}/job documents')
            )
            advanced_content_layout.addWidget(self.job_structure_edit)

            advanced_content_layout.addWidget(QLabel(""))

            advanced_content_layout.addWidget(QLabel("Quote Folder Path:"))
            self.quote_folder_edit = QLineEdit(self.settings.get('quote_folder_path', 'Quotes'))
            advanced_content_layout.addWidget(self.quote_folder_edit)
        else:
            # Create dummy edits for non-admin
            self.job_structure_edit = QLineEdit(
                self.settings.get('job_folder_structure', '{customer}/{job_folder}/job documents')
            )
            self.quote_folder_edit = QLineEdit(self.settings.get('quote_folder_path', 'Quotes'))

        advanced_content_layout.addWidget(QLabel(""))

        self.legacy_mode_check = QCheckBox("Enable legacy mode (shows 'Search All Folders' option)")
        self.legacy_mode_check.setChecked(self.settings.get('legacy_mode', True))
        advanced_content_layout.addWidget(self.legacy_mode_check)

        advanced_content_layout.addWidget(QLabel(""))

        # Network shared settings (admin only)
        if self.is_admin:
            network_label = QLabel("Network Shared Settings:")
            network_label.setStyleSheet("font-weight: bold;")
            advanced_content_layout.addWidget(network_label)

            advanced_content_layout.addWidget(QLabel(
                "Share global settings and history across multiple users/machines.\n"
                "Personal settings (theme, visible tabs, start tab) remain local.\n"
                "Note: Files will be hidden to prevent accidental tampering."
            ))

            self.enable_network_check = QCheckBox("Enable network shared settings")
            self.enable_network_check.setChecked(self.settings.get('network_shared_enabled', False))
            self.enable_network_check.toggled.connect(self.toggle_network_fields)
            advanced_content_layout.addWidget(self.enable_network_check)

            network_paths_layout = QGridLayout()

            network_paths_layout.addWidget(QLabel("Shared Settings File:"), 0, 0)
            self.network_settings_edit = QLineEdit(self.settings.get('network_settings_path', ''))
            self.network_settings_edit.setPlaceholderText(r"\\server\share\jobdocs\shared_settings.json")
            network_paths_layout.addWidget(self.network_settings_edit, 0, 1)
            network_settings_btn = QPushButton("Browse...")
            network_settings_btn.clicked.connect(lambda: self.browse_file(
                self.network_settings_edit,
                "JSON Files (*.json)",
                "jobdocs-settings.json"
            ))
            network_paths_layout.addWidget(network_settings_btn, 0, 2)

            network_paths_layout.addWidget(QLabel("Shared History File:"), 1, 0)
            self.network_history_edit = QLineEdit(self.settings.get('network_history_path', ''))
            self.network_history_edit.setPlaceholderText(r"\\server\share\jobdocs\shared_history.json")
            network_paths_layout.addWidget(self.network_history_edit, 1, 1)
            network_history_btn = QPushButton("Browse...")
            network_history_btn.clicked.connect(lambda: self.browse_file(
                self.network_history_edit,
                "JSON Files (*.json)",
                "jobdocs-history.json"
            ))
            network_paths_layout.addWidget(network_history_btn, 1, 2)

            advanced_content_layout.addLayout(network_paths_layout)

            # Store widgets for toggling
            self.network_widgets = [
                self.network_settings_edit, network_settings_btn,
                self.network_history_edit, network_history_btn
            ]
            self.toggle_network_fields(self.enable_network_check.isChecked())
        else:
            # Create dummy widgets for non-admin
            self.enable_network_check = QCheckBox("Enable network shared settings")
            self.enable_network_check.setChecked(self.settings.get('network_shared_enabled', False))
            self.network_settings_edit = QLineEdit(self.settings.get('network_settings_path', ''))
            self.network_history_edit = QLineEdit(self.settings.get('network_history_path', ''))
            self.network_widgets = []

        advanced_layout.addWidget(self.advanced_content)

        self.advanced_content.setVisible(False)
        self.advanced_group.toggled.connect(self.advanced_content.setVisible)

        scroll_layout.addWidget(self.advanced_group)

        # Set scroll widget and add to main layout
        scroll.setWidget(scroll_widget)
        main_layout.addWidget(scroll)

        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.save)
        button_box.rejected.connect(self.reject)
        main_layout.addWidget(button_box)

    def browse_dir(self, line_edit: QLineEdit):
        dir_path = QFileDialog.getExistingDirectory(self, "Select Directory")
        if dir_path:
            line_edit.setText(dir_path)

    def browse_file(self, line_edit: QLineEdit, file_filter: str, default_filename: str = ""):
        """
        Browse for a file with optional default filename.

        Args:
            line_edit: The line edit to populate with the selected path
            file_filter: File filter for the dialog (e.g., "JSON Files (*.json)")
            default_filename: Default filename to suggest (e.g., "jobdocs-settings.json")
        """
        # Get current value from line edit or use default filename
        current_value = line_edit.text().strip()

        # If there's a current value, use it as initial path
        # Otherwise, suggest the default filename
        if current_value:
            initial_path = current_value
        elif default_filename:
            initial_path = default_filename
        else:
            initial_path = ""

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Select File Location",
            initial_path,
            file_filter
        )
        if file_path:
            # Ensure .json extension for JSON files
            if "JSON" in file_filter and not file_path.endswith('.json'):
                file_path += '.json'
            line_edit.setText(file_path)

    def toggle_network_fields(self, enabled: bool):
        """Enable/disable network path fields based on checkbox"""
        for widget in self.network_widgets:
            widget.setEnabled(enabled)

    def save(self):
        self.settings['blueprints_dir'] = self.blueprints_edit.text()
        self.settings['customer_files_dir'] = self.customer_files_edit.text()
        self.settings['itar_blueprints_dir'] = self.itar_blueprints_edit.text()
        self.settings['itar_customer_files_dir'] = self.itar_customer_files_edit.text()

        if self.hard_radio.isChecked():
            self.settings['link_type'] = 'hard'
        elif self.symbolic_radio.isChecked():
            self.settings['link_type'] = 'symbolic'
        else:
            self.settings['link_type'] = 'copy'

        extensions = [ext.strip().lower() for ext in self.extensions_edit.text().split(',') if ext.strip()]
        extensions = [ext if ext.startswith('.') else f'.{ext}' for ext in extensions]
        self.settings['blueprint_extensions'] = extensions

        self.settings['job_folder_structure'] = self.job_structure_edit.text().strip()
        self.settings['quote_folder_path'] = self.quote_folder_edit.text().strip()
        self.settings['legacy_mode'] = self.legacy_mode_check.isChecked()
        self.settings['allow_duplicate_jobs'] = self.allow_duplicates_check.isChecked()
        self.settings['ui_style'] = self.style_combo.currentText()
        self.settings['default_tab'] = self.default_tab_combo.currentIndex()

        # Network shared settings
        self.settings['network_shared_enabled'] = self.enable_network_check.isChecked()
        self.settings['network_settings_path'] = self.network_settings_edit.text().strip()
        self.settings['network_history_path'] = self.network_history_edit.text().strip()

        # Save disabled modules
        disabled_modules = []
        for module_name, checkbox in self.module_checkboxes.items():
            if not checkbox.isChecked():
                disabled_modules.append(module_name)
        self.settings['disabled_modules'] = disabled_modules

        self.accept()
