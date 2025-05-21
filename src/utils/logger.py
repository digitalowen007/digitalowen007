import logging
import os

# Ensure the logs directory exists
LOGS_DIR = "logs"
if not os.path.exists(LOGS_DIR):
    os.makedirs(LOGS_DIR)

# Keep existing formatter format, it's good.
LOG_FORMAT = '%(asctime)s - %(levelname)s - %(name)s - %(filename)s:%(lineno)d - %(message)s'

def setup_logger(name, log_file, level=logging.INFO, console_out=False, logger_name_prefix="VersaDownloader"):
    """
    Sets up a logger that writes to a specified file in the 'logs' directory
    and optionally to the console.

    Args:
        name (str): Core name of the logger (e.g., 'app_main', 'MainWindow').
        log_file (str): Filename for the log file (e.g., 'application.log').
        level (int, optional): Logging level. Defaults to logging.INFO.
        console_out (bool, optional): If True, logs to console. Defaults to False.
        logger_name_prefix (str, optional): Prefix for the logger's full name.
                                            If None, 'name' is used directly.
                                            Defaults to "VersaDownloader".

    Returns:
        logging.Logger: Configured logger instance.
    """
    full_logger_name = f"{logger_name_prefix}.{name}" if logger_name_prefix else name
    logger = logging.getLogger(full_logger_name)
    
    # Prevent adding multiple handlers if called repeatedly with the same logger name
    if logger.hasHandlers():
        # If handlers exist, assume it's configured.
        # For more dynamic reconfiguration (e.g., changing console_out on the fly),
        # one might clear existing handlers and re-add, or modify existing ones.
        # For this project, simple "configure once" is fine.
        return logger

    logger.setLevel(level)
    formatter = logging.Formatter(LOG_FORMAT)

    # File Handler (always active)
    file_path = os.path.join(LOGS_DIR, log_file)
    file_handler = logging.FileHandler(file_path)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Console Handler (optional)
    if console_out:
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)
        
    logger.propagate = False # Prevent log duplication if root logger is also configured

    return logger

if __name__ == '__main__':
    # Example Usage:
    logger1 = setup_logger('my_app', 'app.log', level=logging.DEBUG, console_out=True)
    logger1.debug("This is a debug message for app.")
    logger1.info("This is an info message for app.")

    logger2 = setup_logger('another_module', 'module.log', console_out=False)
    logger2.info("This is an info message for another_module, only to file.")
    logger2.warning("This is a warning message for another_module.")
    
    # Test that calling setup_logger again doesn't add more handlers
    logger1_again = setup_logger('my_app', 'app.log', level=logging.DEBUG, console_out=True)
    logger1_again.info("Testing logger1 again, should not duplicate handlers or messages in console.")
    # Note: With the current simple check, if console_out changed, it wouldn't reconfigure.
    # A more complex setup might remove old handlers and add new ones if config changes.
    
    print(f"Log files should be in the '{os.path.abspath(LOGS_DIR)}' directory.")
