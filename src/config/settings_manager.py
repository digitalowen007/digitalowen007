import json
import os
from PyQt6.QtCore import QStandardPaths
# QSettings not used for JSON, but good to remember for platform-native settings
from ..utils.logger import setup_logger # Added

class SettingsManager:
    def __init__(self, settings_file='config/settings.json'):
        self.logger = setup_logger('SettingsManager', 'application.log') # Setup logger for this class
        
        app_data_path = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppConfigLocation)
        if app_data_path: 
            self.settings_file = os.path.join(app_data_path, "VersaDownloader", "settings.json")
            self.logger.info(f"Using application-specific config path: {self.settings_file}")
        else: 
            if not os.path.isabs(settings_file): # Use provided settings_file if absolute
                 self.settings_file = os.path.join(os.getcwd(), settings_file)
            else:
                 self.settings_file = settings_file
            self.logger.warning(f"AppConfigLocation not available. Using local path: {self.settings_file}")


        self.defaults = {
            'download_dir': QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DownloadLocation) or os.path.join(os.path.expanduser("~"), "Downloads"),
            'conversion_output_dir': QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DocumentsLocation) or os.path.join(os.path.expanduser("~"), "Documents"),
            'max_concurrent_downloads': 3,
            'max_concurrent_conversions': 2,
            'auto_clear_completed': False,
            'theme': 'Light' 
        }
        self.settings = self.defaults.copy()
        self.load_settings()

    def load_settings(self):
        self.logger.info(f"Loading settings from {self.settings_file}")
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r') as f:
                    loaded_settings = json.load(f)
                
                for key, default_value in self.defaults.items():
                    loaded_value = loaded_settings.get(key)
                    if loaded_value is not None and isinstance(loaded_value, type(default_value)):
                        self.settings[key] = loaded_value
                    else:
                        self.settings[key] = default_value
                        if loaded_value is not None: 
                            self.logger.warning(f"Setting '{key}' has incorrect type in settings file. Using default. Found: {type(loaded_value)}, Expected: {type(default_value)}")
                self.logger.info("Settings loaded successfully.")
            else:
                self.logger.warning(f"Settings file not found at {self.settings_file}. Creating with defaults.")
                self.save_settings() # Save defaults if file doesn't exist
        except json.JSONDecodeError as e:
            self.logger.error(f"Error decoding JSON from {self.settings_file}: {e}. Using default settings and attempting to overwrite.", exc_info=False) # exc_info=False to avoid full trace for common json error
            self.settings = self.defaults.copy() 
            self.save_settings() 
        except Exception as e:
            self.logger.error(f"An unexpected error occurred loading settings from {self.settings_file}: {e}. Using default settings.", exc_info=True)
            self.settings = self.defaults.copy() 
            self.save_settings()


    def save_settings(self):
        self.logger.info(f"Saving settings to {self.settings_file}")
        try:
            os.makedirs(os.path.dirname(self.settings_file), exist_ok=True)
            with open(self.settings_file, 'w') as f:
                json.dump(self.settings, f, indent=4)
            self.logger.info("Settings saved successfully.")
        except Exception as e:
            self.logger.error(f"Error saving settings to {self.settings_file}: {e}", exc_info=True)

    def get_setting(self, key):
        # self.logger.debug(f"Getting setting for key: {key}") # Can be too verbose
        return self.settings.get(key, self.defaults.get(key))

    def set_setting(self, key, value):
        # Basic type validation before setting could be useful
        if key in self.defaults and not isinstance(value, type(self.defaults[key])):
            print(f"Warning: Type mismatch for setting '{key}'. Expected {type(self.defaults[key])}, got {type(value)}. Value not set.")
            return
        self.settings[key] = value

    def save(self): # To be called explicitly by the dialog or app
        self.save_settings()

if __name__ == '__main__':
    # Test SettingsManager
    # Create a dummy settings file path for testing to avoid user's actual config
    test_settings_dir = "test_config"
    test_settings_file = os.path.join(test_settings_dir, "test_settings.json")
    
    if not os.path.exists(test_settings_dir):
        os.makedirs(test_settings_dir)
        
    # Clean up old test file if it exists
    if os.path.exists(test_settings_file):
        os.remove(test_settings_file)

    print(f"Using test settings file: {os.path.abspath(test_settings_file)}")
    manager = SettingsManager(settings_file=test_settings_file)
    
    print("Initial (default) settings:", manager.settings)
    
    # Test loading (should load defaults and save them if file didn't exist)
    assert os.path.exists(test_settings_file), "Settings file not created on init."
    
    # Modify a setting
    manager.set_setting('max_concurrent_downloads', 5)
    manager.set_setting('theme', 'Dark')
    print("Modified settings (not saved yet):", manager.settings)
    
    # Save settings
    manager.save()
    print("Settings saved.")
    
    # Create a new manager instance to load the saved settings
    manager2 = SettingsManager(settings_file=test_settings_file)
    print("Settings loaded by new manager:", manager2.settings)
    assert manager2.get_setting('max_concurrent_downloads') == 5
    assert manager2.get_setting('theme') == 'Dark'
    
    # Test loading with a corrupt value (manual file edit would be needed for full test)
    # For now, test setting an invalid type
    manager2.set_setting('max_concurrent_downloads', "not-an-int") # Should print warning and not set
    assert manager2.get_setting('max_concurrent_downloads') == 5 # Should remain unchanged
    
    manager2.set_setting('new_unvalidated_setting', True) # Example of a setting not in defaults
    manager2.save()

    # Load again to see if unvalidated setting persists (it should) and validated ones are correct
    manager3 = SettingsManager(settings_file=test_settings_file)
    print("Settings loaded by manager3:", manager3.settings)
    assert manager3.get_setting('max_concurrent_downloads') == 5
    assert manager3.get_setting('new_unvalidated_setting') is None # It's not in defaults, so get_setting returns None (or default for key)
                                                                 # Current implementation: it will be loaded if it was in the file
                                                                 # but not accessible via get_setting unless key matches a default.
                                                                 # Let's verify if it's in manager3.settings directly:
    assert 'new_unvalidated_setting' in manager3.settings, "Custom setting not loaded!"


    # Test with a intentionally corrupted JSON file
    with open(test_settings_file, 'w') as f:
        f.write("{'max_concurrent_downloads': 10, 'theme': 'Dark', ") # Invalid JSON
    
    print("\nTesting with intentionally corrupted JSON file...")
    manager_corrupt = SettingsManager(settings_file=test_settings_file)
    print("Settings after loading corrupted file:", manager_corrupt.settings)
    # It should have loaded defaults and overwritten the corrupt file with defaults.
    assert manager_corrupt.get_setting('max_concurrent_downloads') == manager_corrupt.defaults['max_concurrent_downloads']
    assert manager_corrupt.get_setting('theme') == manager_corrupt.defaults['theme']
    
    # Verify the file was overwritten with defaults
    with open(test_settings_file, 'r') as f:
        repaired_content = json.load(f)
    assert repaired_content['max_concurrent_downloads'] == manager_corrupt.defaults['max_concurrent_downloads']
    print("Corrupted file test passed, file was repaired with defaults.")

    # Clean up test file
    if os.path.exists(test_settings_file):
        os.remove(test_settings_file)
    if os.path.exists(test_settings_dir):
        os.rmdir(test_settings_dir)
    print("\nTest completed and test files cleaned up.")
