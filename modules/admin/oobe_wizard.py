"""
OOBE (Out-Of-Box Experience) Wizard for JobDocs

First-time setup wizard to configure essential settings.
"""

from pathlib import Path
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QCheckBox, QFileDialog, QMessageBox, QStackedWidget,
    QWidget, QRadioButton, QButtonGroup, QGroupBox, QTextEdit
)
from PyQt6.QtCore import Qt


class OOBEWizard(QDialog):
    """
    First-time setup wizard for JobDocs.

    Guides users through:
    1. Welcome screen
    2. Directory configuration
    3. Link type selection
    4. Network sharing setup (optional)
    5. User authentication setup (optional)
    6. Completion
    """

    def __init__(self, app_context, parent=None):
        super().__init__(parent)
        self.app_context = app_context
        self.settings = app_context.settings.copy()

        self.setWindowTitle("JobDocs First-Time Setup")
        self.setModal(True)
        self.setMinimumSize(700, 500)

        self.current_page = 0
        self.pages = []

        self.setup_ui()

    def setup_ui(self):
        """Setup the wizard UI"""
        layout = QVBoxLayout(self)

        # Title
        self.title_label = QLabel()
        self.title_label.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(self.title_label)

        # Stacked widget for pages
        self.stack = QStackedWidget()

        # Create pages
        self.pages = [
            self._create_welcome_page(),
            self._create_directories_page(),
            self._create_link_type_page(),
            self._create_network_sharing_page(),
            self._create_user_auth_page(),
            self._create_completion_page()
        ]

        for page in self.pages:
            self.stack.addWidget(page)

        layout.addWidget(self.stack)

        # Navigation buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.back_button = QPushButton("< Back")
        self.back_button.clicked.connect(self.go_back)
        self.back_button.setEnabled(False)
        button_layout.addWidget(self.back_button)

        self.next_button = QPushButton("Next >")
        self.next_button.clicked.connect(self.go_next)
        button_layout.addWidget(self.next_button)

        self.finish_button = QPushButton("Finish")
        self.finish_button.clicked.connect(self.finish)
        self.finish_button.setVisible(False)
        button_layout.addWidget(self.finish_button)

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)

        layout.addLayout(button_layout)

        # Show first page
        self.update_page()

    def _create_welcome_page(self) -> QWidget:
        """Create welcome page"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        welcome = QLabel(
            "<h2>Welcome to JobDocs!</h2>"
            "<p>This wizard will help you configure JobDocs for first-time use.</p>"
            "<p>We'll guide you through:</p>"
            "<ul>"
            "<li>Setting up directory paths for blueprints and customer files</li>"
            "<li>Choosing how files should be linked</li>"
            "<li>Optional: Network sharing for team collaboration</li>"
            "<li>Optional: User authentication</li>"
            "</ul>"
            "<p><b>You can re-run this setup wizard at any time from the Admin tab.</b></p>"
        )
        welcome.setWordWrap(True)
        welcome.setTextFormat(Qt.TextFormat.RichText)
        layout.addWidget(welcome)

        layout.addStretch()

        return widget

    def _create_directories_page(self) -> QWidget:
        """Create directories configuration page"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        intro = QLabel(
            "<b>Configure Directory Paths</b><br>"
            "Set up where JobDocs will store blueprints and customer files."
        )
        intro.setWordWrap(True)
        intro.setTextFormat(Qt.TextFormat.RichText)
        layout.addWidget(intro)

        # Blueprints directory
        bp_group = QGroupBox("Blueprints Directory")
        bp_layout = QVBoxLayout(bp_group)

        bp_layout.addWidget(QLabel("Central storage for all blueprint files (PDF, DWG, DXF, etc.)"))

        bp_input_layout = QHBoxLayout()
        self.bp_dir_edit = QLineEdit(self.settings.get('blueprints_dir', ''))
        self.bp_dir_edit.setPlaceholderText("Select blueprints directory...")
        bp_input_layout.addWidget(self.bp_dir_edit)

        bp_browse_btn = QPushButton("Browse...")
        bp_browse_btn.clicked.connect(lambda: self._browse_directory(self.bp_dir_edit))
        bp_input_layout.addWidget(bp_browse_btn)

        bp_layout.addLayout(bp_input_layout)
        layout.addWidget(bp_group)

        # Customer files directory
        cf_group = QGroupBox("Customer Files Directory")
        cf_layout = QVBoxLayout(cf_group)

        cf_layout.addWidget(QLabel("Where job folders will be created for each customer"))

        cf_input_layout = QHBoxLayout()
        self.cf_dir_edit = QLineEdit(self.settings.get('customer_files_dir', ''))
        self.cf_dir_edit.setPlaceholderText("Select customer files directory...")
        cf_input_layout.addWidget(self.cf_dir_edit)

        cf_browse_btn = QPushButton("Browse...")
        cf_browse_btn.clicked.connect(lambda: self._browse_directory(self.cf_dir_edit))
        cf_input_layout.addWidget(cf_browse_btn)

        cf_layout.addLayout(cf_input_layout)
        layout.addWidget(cf_group)

        layout.addStretch()

        return widget

    def _create_link_type_page(self) -> QWidget:
        """Create link type selection page"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        intro = QLabel(
            "<b>Choose Link Type</b><br>"
            "How should JobDocs handle files when creating job folders?"
        )
        intro.setWordWrap(True)
        intro.setTextFormat(Qt.TextFormat.RichText)
        layout.addWidget(intro)

        self.link_type_group = QButtonGroup()

        # Hard link (recommended)
        hard_radio = QRadioButton("Hard Link (Recommended)")
        hard_radio.setToolTip(
            "Creates a hard link. Saves disk space by sharing the same file data.\n"
            "Files must be on the same volume/drive."
        )
        self.link_type_group.addButton(hard_radio, 0)
        layout.addWidget(hard_radio)

        hard_desc = QLabel(
            "  • Saves disk space - files share the same data on disk\n"
            "  • Changes to one file affect the other\n"
            "  • Both files must be on the same drive/volume\n"
            "  • Best option for most users"
        )
        hard_desc.setStyleSheet("color: #666; margin-left: 20px; margin-bottom: 10px;")
        layout.addWidget(hard_desc)

        # Symbolic link
        symbolic_radio = QRadioButton("Symbolic Link")
        symbolic_radio.setToolTip(
            "Creates a symbolic link (shortcut).\n"
            "May require administrator privileges on Windows."
        )
        self.link_type_group.addButton(symbolic_radio, 1)
        layout.addWidget(symbolic_radio)

        symbolic_desc = QLabel(
            "  • Creates a reference/shortcut to the original file\n"
            "  • Can work across different drives\n"
            "  • May require admin rights on Windows\n"
            "  • If original is deleted, link becomes broken"
        )
        symbolic_desc.setStyleSheet("color: #666; margin-left: 20px; margin-bottom: 10px;")
        layout.addWidget(symbolic_desc)

        # Copy
        copy_radio = QRadioButton("Copy")
        copy_radio.setToolTip(
            "Creates an independent copy of the file.\n"
            "Uses more disk space but files are completely independent."
        )
        self.link_type_group.addButton(copy_radio, 2)
        layout.addWidget(copy_radio)

        copy_desc = QLabel(
            "  • Creates a complete independent copy\n"
            "  • Works across different drives\n"
            "  • Uses more disk space\n"
            "  • Files are completely independent"
        )
        copy_desc.setStyleSheet("color: #666; margin-left: 20px; margin-bottom: 10px;")
        layout.addWidget(copy_desc)

        # Set current selection
        link_type = self.settings.get('link_type', 'hard')
        if link_type == 'hard':
            hard_radio.setChecked(True)
        elif link_type == 'symbolic':
            symbolic_radio.setChecked(True)
        else:
            copy_radio.setChecked(True)

        layout.addStretch()

        return widget

    def _create_network_sharing_page(self) -> QWidget:
        """Create network sharing configuration page"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        intro = QLabel(
            "<b>Network Shared Settings (Optional)</b><br>"
            "Enable this if multiple users need to share the same settings and history."
        )
        intro.setWordWrap(True)
        intro.setTextFormat(Qt.TextFormat.RichText)
        layout.addWidget(intro)

        self.enable_network_check = QCheckBox("Enable network shared settings")
        self.enable_network_check.setChecked(self.settings.get('network_shared_enabled', False))
        self.enable_network_check.toggled.connect(self._toggle_network_fields)
        layout.addWidget(self.enable_network_check)

        # Network paths
        network_group = QGroupBox("Network Paths")
        network_layout = QVBoxLayout(network_group)

        # Settings file
        network_layout.addWidget(QLabel("Shared Settings File:"))
        settings_input_layout = QHBoxLayout()
        self.network_settings_edit = QLineEdit(self.settings.get('network_settings_path', ''))
        self.network_settings_edit.setPlaceholderText(r"\\server\share\jobdocs\shared-settings.json")
        settings_input_layout.addWidget(self.network_settings_edit)

        settings_browse_btn = QPushButton("Browse...")
        settings_browse_btn.clicked.connect(lambda: self._browse_file(
            self.network_settings_edit,
            "jobdocs-settings.json"
        ))
        settings_input_layout.addWidget(settings_browse_btn)

        network_layout.addLayout(settings_input_layout)

        # History file
        network_layout.addWidget(QLabel("Shared History File:"))
        history_input_layout = QHBoxLayout()
        self.network_history_edit = QLineEdit(self.settings.get('network_history_path', ''))
        self.network_history_edit.setPlaceholderText(r"\\server\share\jobdocs\shared-history.json")
        history_input_layout.addWidget(self.network_history_edit)

        history_browse_btn = QPushButton("Browse...")
        history_browse_btn.clicked.connect(lambda: self._browse_file(
            self.network_history_edit,
            "jobdocs-history.json"
        ))
        history_input_layout.addWidget(history_browse_btn)

        network_layout.addLayout(history_input_layout)

        layout.addWidget(network_group)
        self.network_group = network_group

        note = QLabel(
            "<i>Note: Personal settings (UI style, default tab) will remain local to each user.</i>"
        )
        note.setWordWrap(True)
        note.setTextFormat(Qt.TextFormat.RichText)
        note.setStyleSheet("color: #666; font-size: 11px;")
        layout.addWidget(note)

        self._toggle_network_fields(self.enable_network_check.isChecked())

        layout.addStretch()

        return widget

    def _create_user_auth_page(self) -> QWidget:
        """Create user authentication setup page"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        intro = QLabel(
            "<b>User Authentication (Optional)</b><br>"
            "Enable user accounts to track who is using JobDocs."
        )
        intro.setWordWrap(True)
        intro.setTextFormat(Qt.TextFormat.RichText)
        layout.addWidget(intro)

        # Check if user_auth module is available
        user_auth_available = self._check_user_auth_available()

        if not user_auth_available:
            warning = QLabel(
                "<b>User Authentication Module Not Available</b><br><br>"
                "The user_auth module is not currently enabled.<br><br>"
                "To enable it:<br>"
                "1. Rename 'modules/_user_auth' to 'modules/user_auth'<br>"
                "2. Restart JobDocs<br>"
                "3. Re-run this setup wizard"
            )
            warning.setWordWrap(True)
            warning.setTextFormat(Qt.TextFormat.RichText)
            warning.setStyleSheet("color: #b36200; padding: 10px; background: #fff3cd; border: 1px solid #ffc107;")
            layout.addWidget(warning)

            self.enable_user_auth_check = QCheckBox("Enable user authentication (requires module)")
            self.enable_user_auth_check.setEnabled(False)
            self.enable_user_auth_check.setChecked(False)
            layout.addWidget(self.enable_user_auth_check)
        else:
            self.enable_user_auth_check = QCheckBox("Enable user authentication")
            self.enable_user_auth_check.setChecked(self.settings.get('user_auth_enabled', False))
            layout.addWidget(self.enable_user_auth_check)

            info = QLabel(
                "When enabled:<br>"
                "• Users must log in to use JobDocs<br>"
                "• You can manage users from the Admin tab<br>"
                "• User actions can be tracked and audited"
            )
            info.setWordWrap(True)
            info.setTextFormat(Qt.TextFormat.RichText)
            info.setStyleSheet("color: #666; margin-left: 20px;")
            layout.addWidget(info)

        layout.addStretch()

        return widget

    def _create_completion_page(self) -> QWidget:
        """Create completion page"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        completion = QLabel(
            "<h2>Setup Complete!</h2>"
            "<p>JobDocs is now configured and ready to use.</p>"
            "<p><b>What's next?</b></p>"
            "<ul>"
            "<li>Start creating jobs from the 'Create Job' tab</li>"
            "<li>Import blueprints using the 'Import Blueprints' tab</li>"
            "<li>Search for jobs using the 'Search' tab</li>"
            "<li>Manage users and settings from the 'Admin' tab</li>"
            "</ul>"
            "<p><i>You can always change these settings later from File → Settings</i></p>"
        )
        completion.setWordWrap(True)
        completion.setTextFormat(Qt.TextFormat.RichText)
        layout.addWidget(completion)

        layout.addStretch()

        return widget

    # ==================== NAVIGATION ====================

    def update_page(self):
        """Update the current page display"""
        self.stack.setCurrentIndex(self.current_page)

        # Update title
        titles = [
            "Welcome",
            "Directory Configuration",
            "Link Type Selection",
            "Network Sharing",
            "User Authentication",
            "Setup Complete"
        ]
        self.title_label.setText(f"Step {self.current_page + 1} of {len(self.pages)}: {titles[self.current_page]}")

        # Update buttons
        self.back_button.setEnabled(self.current_page > 0)

        is_last_page = self.current_page == len(self.pages) - 1
        self.next_button.setVisible(not is_last_page)
        self.finish_button.setVisible(is_last_page)

    def go_next(self):
        """Go to next page"""
        # Validate current page
        if not self._validate_page():
            return

        if self.current_page < len(self.pages) - 1:
            self.current_page += 1
            self.update_page()

    def go_back(self):
        """Go to previous page"""
        if self.current_page > 0:
            self.current_page -= 1
            self.update_page()

    def _validate_page(self) -> bool:
        """Validate current page before proceeding"""
        if self.current_page == 1:  # Directories page
            bp_dir = self.bp_dir_edit.text().strip()
            cf_dir = self.cf_dir_edit.text().strip()

            if not bp_dir or not cf_dir:
                QMessageBox.warning(
                    self,
                    "Required Fields",
                    "Please configure both Blueprints and Customer Files directories."
                )
                return False

            # Save to settings
            self.settings['blueprints_dir'] = bp_dir
            self.settings['customer_files_dir'] = cf_dir

        elif self.current_page == 2:  # Link type page
            selected = self.link_type_group.checkedId()
            if selected == 0:
                self.settings['link_type'] = 'hard'
            elif selected == 1:
                self.settings['link_type'] = 'symbolic'
            else:
                self.settings['link_type'] = 'copy'

        elif self.current_page == 3:  # Network sharing page
            self.settings['network_shared_enabled'] = self.enable_network_check.isChecked()
            if self.enable_network_check.isChecked():
                self.settings['network_settings_path'] = self.network_settings_edit.text().strip()
                self.settings['network_history_path'] = self.network_history_edit.text().strip()

        elif self.current_page == 4:  # User auth page
            self.settings['user_auth_enabled'] = self.enable_user_auth_check.isChecked()

        return True

    def finish(self):
        """Finish the wizard"""
        if not self._validate_page():
            return

        # Save all settings
        self.app_context.settings.update(self.settings)
        self.app_context.save_settings()

        # Mark OOBE as completed
        self.settings['oobe_completed'] = True
        self.app_context.settings['oobe_completed'] = True
        self.app_context.save_settings()

        self.accept()

    # ==================== HELPERS ====================

    def _browse_directory(self, line_edit: QLineEdit):
        """Browse for a directory"""
        dir_path = QFileDialog.getExistingDirectory(self, "Select Directory")
        if dir_path:
            line_edit.setText(dir_path)

    def _browse_file(self, line_edit: QLineEdit, default_filename: str = ""):
        """
        Browse for a file with optional default filename.

        Args:
            line_edit: The line edit to populate with the selected path
            default_filename: Default filename to suggest (e.g., "jobdocs-settings.json")
        """
        # Get current value from line edit or use default filename
        current_value = line_edit.text().strip()

        # If there's a current value, use its directory
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
            "JSON Files (*.json);;All Files (*)"
        )
        if file_path:
            # Ensure .json extension
            if not file_path.endswith('.json'):
                file_path += '.json'
            line_edit.setText(file_path)

    def _toggle_network_fields(self, enabled: bool):
        """Enable/disable network path fields"""
        self.network_group.setEnabled(enabled)

    def _check_user_auth_available(self) -> bool:
        """Check if user_auth module is available"""
        try:
            from modules.user_auth.user_auth import UserAuth
            return True
        except ImportError:
            try:
                from modules._user_auth.user_auth import UserAuth
                return False  # Module exists but has underscore prefix
            except ImportError:
                return False
