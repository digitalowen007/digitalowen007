import sys
from PyQt6.QtWidgets import QApplication
from src.ui.main_window import MainWindow
from src.utils.logger import setup_logger # Added

# Setup main application logger
main_logger = setup_logger('app_main', 'application.log', console_out=True)

def main():
    main_logger.info("Application starting...")
    app = QApplication(sys.argv)
    
    try:
        window = MainWindow() # Pass logger if MainWindow expects it, or it sets up its own
        window.show()
        exit_code = app.exec()
        main_logger.info(f"Application shutting down with exit code: {exit_code}")
        sys.exit(exit_code)
    except Exception as e:
        main_logger.critical("Unhandled exception in main application loop", exc_info=True)
        sys.exit(1) # Exit with error code

if __name__ == '__main__':
    main()
