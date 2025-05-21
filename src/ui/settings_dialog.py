import os
from PyQt6.QtWidgets import (
    QDialog, QFormLayout, QLineEdit, QPushButton, QSpinBox, 
    QCheckBox, QComboBox, QDialogButtonBox, QFileDialog, QMessageBox
)
from PyQt6.QtCore import Qt

class SettingsDialog(QDialog):
    def __init__(self, settings_manager, parent=None):
        super().__init__(parent)
        self.settings_manager = settings_manager
        
        self.setWindowTitle("Settings")
        self.setMinimumWidth(400)

        layout = QFormLayout(self)

        # Download Directory
        self.download_dir_edit = QLineEdit()
        self.browse_download_dir_button = QPushButton("Browse...")
        download_dir_layout = self.create_browse_layout(self.download_dir_edit, self.browse_download_dir_button)
        layout.addRow("Download Directory:", download_dir_layout)

        # Conversion Directory
        self.conversion_dir_edit = QLineEdit()
        self.browse_conversion_dir_button = QPushButton("Browse...")
        conversion_dir_layout = self.create_browse_layout(self.conversion_dir_edit, self.browse_conversion_dir_button)
        layout.addRow("Conversion Output Directory:", conversion_dir_layout)

        # Max Downloads
        self.max_downloads_spinbox = QSpinBox()
        self.max_downloads_spinbox.setRange(1, 10)
        layout.addRow("Max Concurrent Downloads:", self.max_downloads_spinbox)

        # Max Conversions
        self.max_conversions_spinbox = QSpinBox()
        self.max_conversions_spinbox.setRange(1, 10)
        layout.addRow("Max Concurrent Conversions:", self.max_conversions_spinbox)

        # Auto-clear
        self.auto_clear_checkbox = QCheckBox("Automatically clear completed tasks")
        layout.addRow(self.auto_clear_checkbox)

        # Theme
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Light", "Dark"]) # System theme is more complex, deferring
        layout.addRow("Theme:", self.theme_combo)

        # Dialog Buttons
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        layout.addRow(self.button_box)

        # Load initial settings
        self.load_initial_settings()

        # Connect signals
        self.browse_download_dir_button.clicked.connect(lambda: self.browse_directory(self.download_dir_edit))
        self.browse_conversion_dir_button.clicked.connect(lambda: self.browse_directory(self.conversion_dir_edit))
        self.button_box.accepted.connect(self.apply_settings_and_accept)
        self.button_box.rejected.connect(self.reject)

    def create_browse_layout(self, line_edit, button):
        from PyQt6.QtWidgets import QHBoxLayout, QWidget # Local import if not already global
        h_layout = QHBoxLayout()
        h_layout.addWidget(line_edit)
        h_layout.addWidget(button)
        # Set margins to 0 to make it compact within the QFormLayout row
        h_layout.setContentsMargins(0,0,0,0) 
        widget = QWidget() # QLayouts need to be set on a QWidget to be added to another QLayout
        widget.setLayout(h_layout)
        return widget

    def load_initial_settings(self):
        self.download_dir_edit.setText(self.settings_manager.get_setting('download_dir'))
        self.conversion_dir_edit.setText(self.settings_manager.get_setting('conversion_output_dir'))
        self.max_downloads_spinbox.setValue(self.settings_manager.get_setting('max_concurrent_downloads'))
        self.max_conversions_spinbox.setValue(self.settings_manager.get_setting('max_concurrent_conversions'))
        self.auto_clear_checkbox.setChecked(self.settings_manager.get_setting('auto_clear_completed'))
        
        current_theme = self.settings_manager.get_setting('theme')
        theme_index = self.theme_combo.findText(current_theme, Qt.MatchFlag.MatchFixedString)
        if theme_index >= 0:
            self.theme_combo.setCurrentIndex(theme_index)
        else: # Fallback if saved theme is not in combo (e.g. "System" if we add it later but not in this version)
            self.theme_combo.setCurrentIndex(0) # Default to first item (Light)

    def browse_directory(self, line_edit_widget):
        current_path = line_edit_widget.text()
        if not current_path or not os.path.isdir(current_path):
            # If current path is invalid or empty, default to a sensible location
            # For download_dir_edit, use settings_manager's default download_dir
            if line_edit_widget == self.download_dir_edit:
                current_path = self.settings_manager.defaults['download_dir']
            # For conversion_dir_edit, use settings_manager's default conversion_output_dir
            elif line_edit_widget == self.conversion_dir_edit:
                current_path = self.settings_manager.defaults['conversion_output_dir']
            else: # General fallback if widget is unknown
                current_path = os.path.expanduser("~")


        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Directory",
            current_path
        )
        if directory:
            line_edit_widget.setText(directory)

    def apply_settings_and_accept(self):
        # Validate paths before saving (optional, but good practice)
        if not os.path.isdir(self.download_dir_edit.text()):
            QMessageBox.warning(self, "Invalid Path", "Download directory path is invalid. Please select a valid directory.")
            return # Prevent dialog from closing
        
        if not os.path.isdir(self.conversion_dir_edit.text()):
            QMessageBox.warning(self, "Invalid Path", "Conversion output directory path is invalid. Please select a valid directory.")
            return

        self.settings_manager.set_setting('download_dir', self.download_dir_edit.text())
        self.settings_manager.set_setting('conversion_output_dir', self.conversion_dir_edit.text())
        self.settings_manager.set_setting('max_concurrent_downloads', self.max_downloads_spinbox.value())
        self.settings_manager.set_setting('max_concurrent_conversions', self.max_conversions_spinbox.value())
        self.settings_manager.set_setting('auto_clear_completed', self.auto_clear_checkbox.isChecked())
        self.settings_manager.set_setting('theme', self.theme_combo.currentText())
        
        self.settings_manager.save()
        self.accept()

if __name__ == '__main__':
    # Example Usage:
    from PyQt6.QtWidgets import QApplication
    import sys
    # Need a dummy SettingsManager for testing if settings_manager.py is not in PYTHONPATH
    # For this test, assume settings_manager.py is in a reachable path (e.g. src.config)
    # Or, provide a mock.
    
    # --- Mock SettingsManager for standalone testing ---
    class MockSettingsManager:
        def __init__(self):
            from PyQt6.QtCore import QStandardPaths # Re-import for mock
            self.defaults = {
                'download_dir': QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DownloadLocation) or os.path.join(os.path.expanduser("~"), "Downloads"),
                'conversion_output_dir': QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DocumentsLocation) or os.path.join(os.path.expanduser("~"), "Documents"),
                'max_concurrent_downloads': 2,
                'max_concurrent_conversions': 1,
                'auto_clear_completed': True,
                'theme': 'Dark'
            }
            self.settings = self.defaults.copy()
            print("MockSettingsManager initialized with:", self.settings)

        def get_setting(self, key):
            return self.settings.get(key, self.defaults.get(key))

        def set_setting(self, key, value):
            self.settings[key] = value
            print(f"Mock: Set {key} to {value}")

        def save(self):
            print("Mock: Settings saved:", self.settings)
    # --- End Mock SettingsManager ---

    app = QApplication(sys.argv)
    
    # Use the mock manager for testing
    # In the real app, this would be the actual SettingsManager instance
    # from src.config.settings_manager import SettingsManager
    # manager = SettingsManager() # Real manager
    
    mock_manager = MockSettingsManager()
    
    dialog = SettingsDialog(mock_manager)
    if dialog.exec():
        print("Settings dialog accepted.")
        print("Current settings in mock manager:", mock_manager.settings)
    else:
        print("Settings dialog cancelled.")
    
    # sys.exit(app.exec()) # Not needed if just testing dialog logic
    print("Dialog test finished.")
