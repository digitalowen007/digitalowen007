# src/ui/themes.py

LIGHT_THEME_QSS = """
/* Light Theme - Based on system default or a very light custom style */
QMainWindow {
    background-color: #f0f0f0; /* Slightly off-white for main window background */
}

QWidget {
    /* General widget background, can be overridden by specific widgets */
    /* background-color: #ffffff; */
    color: #000000;
}

QTabWidget::pane {
    border-top: 1px solid #c2c7cb;
    background-color: #f0f0f0;
}

QTabBar::tab {
    background: #e1e1e1;
    border: 1px solid #c2c7cb;
    border-bottom-color: #c2c7cb; /* Same as pane border color */
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    min-width: 8ex;
    padding: 5px;
    margin-right: 2px;
}

QTabBar::tab:selected {
    background: #f0f0f0; /* Matches pane background for seamless look */
    border-color: #c2c7cb;
    border-bottom-color: #f0f0f0; /* Make selected tab blend with pane */
}

QTabBar::tab:!selected:hover {
    background: #f5f5f5;
}

QTableView {
    background-color: #ffffff;
    border: 1px solid #d3d3d3;
    gridline-color: #d3d3d3;
}

QHeaderView::section {
    background-color: #e1e1e1;
    padding: 4px;
    border: 1px solid #d3d3d3;
}

QPushButton {
    background-color: #e1e1e1;
    border: 1px solid #adadad;
    padding: 5px 10px;
    border-radius: 4px;
    color: #000000;
}

QPushButton:hover {
    background-color: #f0f0f0;
}

QPushButton:pressed {
    background-color: #c2c2c2;
}

QPushButton:disabled {
    background-color: #d3d3d3;
    color: #a0a0a0;
}

QLineEdit, QComboBox, QSpinBox {
    background-color: #ffffff;
    border: 1px solid #c2c7cb;
    padding: 3px;
    border-radius: 4px;
    color: #000000;
}

QComboBox::drop-down {
    border-left: 1px solid #c2c7cb;
}

QProgressBar {
    border: 1px solid #c2c7cb;
    border-radius: 4px;
    text-align: center;
    color: #000000; /* Text color on progress bar */
}

QProgressBar::chunk {
    background-color: #4CAF50; /* A pleasant green */
    width: 10px; /* Optional: makes the chunk a bit wider */
    margin: 0.5px;
}

QGroupBox {
    border: 1px solid #c2c7cb;
    border-radius: 4px;
    margin-top: 6px; /* Make space for title */
    padding: 10px 5px 5px 5px; /* top, right, bottom, left */
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left; /* position at the top left */
    padding: 0 3px;
    left: 10px; /* Position title slightly to the right */
    background-color: #f0f0f0; /* Match QMainWindow background */
    color: #000000;
}

QLabel {
 color: #000000;
}

QToolTip {
    border: 1px solid #c2c7cb;
    background-color: #ffffdc; /* Light yellow for tooltips */
    color: #000000;
    padding: 2px;
}
"""

DARK_THEME_QSS = """
/* Dark Theme */
QMainWindow {
    background-color: #2e2e2e;
}

QWidget {
    /* General widget background, can be overridden by specific widgets */
    /* background-color: #3c3c3c; */
    color: #e0e0e0; /* Light text for dark backgrounds */
}

QTabWidget::pane {
    border-top: 1px solid #505050;
    background-color: #3c3c3c;
}

QTabBar::tab {
    background: #2e2e2e;
    border: 1px solid #505050;
    border-bottom-color: #505050; 
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    min-width: 8ex;
    padding: 5px;
    margin-right: 2px;
    color: #e0e0e0;
}

QTabBar::tab:selected {
    background: #3c3c3c; 
    border-color: #505050;
    border-bottom-color: #3c3c3c; 
}

QTabBar::tab:!selected:hover {
    background: #4a4a4a;
}

QTableView {
    background-color: #3c3c3c;
    border: 1px solid #505050;
    gridline-color: #505050;
    color: #e0e0e0;
}

QHeaderView::section {
    background-color: #2e2e2e;
    padding: 4px;
    border: 1px solid #505050;
    color: #e0e0e0;
}

QPushButton {
    background-color: #505050;
    border: 1px solid #606060;
    padding: 5px 10px;
    border-radius: 4px;
    color: #e0e0e0;
}

QPushButton:hover {
    background-color: #606060;
}

QPushButton:pressed {
    background-color: #707070;
}

QPushButton:disabled {
    background-color: #404040;
    color: #808080;
}

QLineEdit, QComboBox, QSpinBox {
    background-color: #2e2e2e;
    border: 1px solid #505050;
    padding: 3px;
    border-radius: 4px;
    color: #e0e0e0;
}

QComboBox::drop-down {
    border-left: 1px solid #505050;
}
QComboBox QAbstractItemView { /* Dropdown list style */
    background-color: #3c3c3c;
    border: 1px solid #505050;
    selection-background-color: #505050;
    color: #e0e0e0;
}


QProgressBar {
    border: 1px solid #505050;
    border-radius: 4px;
    text-align: center;
    color: #e0e0e0; /* Text color on progress bar */
    background-color: #2e2e2e; /* Background of the progress bar itself */
}

QProgressBar::chunk {
    background-color: #0078d7; /* A nice blue for dark theme */
    width: 10px; 
    margin: 0.5px;
}

QGroupBox {
    border: 1px solid #505050;
    border-radius: 4px;
    margin-top: 6px; 
    padding: 10px 5px 5px 5px; 
    color: #e0e0e0;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left; 
    padding: 0 3px;
    left: 10px; 
    background-color: #2e2e2e; /* Match QMainWindow background */
    color: #e0e0e0;
}

QLabel {
 color: #e0e0e0;
}

QToolTip {
    border: 1px solid #505050;
    background-color: #3c3c3c; 
    color: #e0e0e0;
    padding: 2px;
}
"""

# To apply a theme from MainWindow:
# import src.ui.themes as themes
# app = QApplication.instance()
# app.setStyleSheet(themes.DARK_THEME_QSS) # or themes.LIGHT_THEME_QSS
# self.settings_manager.set_setting('theme', 'Dark') # or 'Light'
# self.settings_manager.save()
#
# And in load_and_apply_settings():
# current_theme = self.settings_manager.get_setting('theme')
# if current_theme == 'Dark':
#     QApplication.instance().setStyleSheet(themes.DARK_THEME_QSS)
# else:
#     QApplication.instance().setStyleSheet(themes.LIGHT_THEME_QSS) # Or your specific light QSS
# self.current_theme = current_theme # Store it if needed for comparison
