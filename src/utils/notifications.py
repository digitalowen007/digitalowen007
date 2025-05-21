# import logging # No longer needed directly here if setup_logger handles basicConfig
from plyer import notification 
from .logger import setup_logger # Use relative import if logger.py is in the same package/directory

# Setup logger for this module using the standardized setup_logger
# The log_file 'application.log' ensures these logs go to the main app log.
notif_logger = setup_logger('Notifications', 'application.log', console_out=False)


def send_system_notification(title, message, app_name="VersaDownloader", timeout=10):
    """
    Sends a system notification.
    (Args documentation remains the same)
    """
    try:
        notif_logger.info(f"Attempting to send notification: Title='{title}', Message='{message}'")
        notification.notify(
            title=title,
            message=message,
            app_name=app_name,
            timeout=timeout
            # app_icon can be added here
        )
        notif_logger.info("Notification send attempt finished.") # More neutral as actual display is system-dependent
    except NotImplementedError:
        notif_logger.warning("System notifications are not implemented for this platform/environment (plyer).")
    except Exception as e:
        # Log with exc_info=True for more details on unexpected errors.
        notif_logger.error(f"Failed to send system notification: {e}", exc_info=True)
        notif_logger.info("This might be due to missing plyer backend dependencies or other system issues. Check plyer documentation for platform requirements.")

if __name__ == '__main__':
    # This block is for direct testing of this module.
    # For this test, we'll set up a temporary console logger for immediate feedback.
    test_logger = setup_logger('NotificationsTest', 'test_notifications.log', console_out=True)
    test_logger.info("Running notification example from __main__...")
    
    send_system_notification("Test Notification", "This is a test message from VersaDownloader notifications module.")
    send_system_notification("Update Available", "A new version of MyOtherApp is ready!", app_name="MyOtherApp")
    
    test_logger.info("Notification examples attempted. Check your system's notification area/logs and 'test_notifications.log'.")
