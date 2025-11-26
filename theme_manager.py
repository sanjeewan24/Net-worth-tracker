"""
Theme Manager for Net Worth Tracker
Handles dark and light themes with Claude.ai-inspired typography
"""


class ThemeManager:
    """Manages application themes and styling"""
    
    def __init__(self):
        self.dark_theme = self._create_dark_theme()
        self.light_theme = self._create_light_theme()
    
    def get_dark_theme(self):
        """Return dark theme stylesheet"""
        return self.dark_theme
    
    def get_light_theme(self):
        """Return light theme stylesheet"""
        return self.light_theme
    
    def _create_dark_theme(self):
        """Create dark theme stylesheet with complete coverage"""
        return """
            /* Main Window */
            QMainWindow {
                background-color: #0f172a;
                color: #e2e8f0;
            }
            
            /* All Widgets - Base Styling */
            QWidget {
                background-color: #0f172a;
                color: #e2e8f0;
                font-family: -apple-system, BlinkMacSystemFont, 'Inter', 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
                font-size: 14px;
                letter-spacing: -0.01em;
            }
            
            /* Labels - CRITICAL FIX */
            QLabel {
                color: #e2e8f0;
                background-color: transparent;
                font-weight: 400;
            }
            
            /* Form Labels */
            QFormLayout QLabel {
                color: #e2e8f0;
                background-color: transparent;
            }
            
            /* Buttons */
            QPushButton {
                background-color: #1e293b;
                color: #e2e8f0;
                border: 1px solid #334155;
                border-radius: 8px;
                padding: 10px 20px;
                font-weight: 500;
                font-size: 14px;
                letter-spacing: -0.01em;
            }
            
            QPushButton:hover {
                background-color: #2d3b52;
                border: 1px solid #475569;
            }
            
            QPushButton:pressed {
                background-color: #475569;
            }
            
            QPushButton:disabled {
                background-color: #1e293b;
                color: #64748b;
                border: 1px solid #1e293b;
            }
            
            /* Input Fields */
            QLineEdit, QTextEdit, QSpinBox, QDoubleSpinBox {
                background-color: #1e293b;
                color: #e2e8f0;
                border: 1px solid #334155;
                border-radius: 8px;
                padding: 10px 14px;
                font-size: 14px;
                selection-background-color: #3b82f6;
            }
            
            QLineEdit:focus, QTextEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {
                border: 2px solid #3b82f6;
                background-color: #1e2936;
            }
            
            /* ComboBox - COMPLETE FIX */
            QComboBox {
                background-color: #1e293b;
                color: #e2e8f0;
                border: 1px solid #334155;
                border-radius: 8px;
                padding: 10px 14px;
                font-size: 14px;
                selection-background-color: #3b82f6;
            }
            
            QComboBox:hover {
                background-color: #2d3b52;
                border: 1px solid #475569;
            }
            
            QComboBox:focus {
                border: 2px solid #3b82f6;
                background-color: #1e2936;
            }
            
            QComboBox::drop-down {
                border: none;
                background-color: transparent;
                width: 35px;
            }
            
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #e2e8f0;
                margin-right: 8px;
            }
            
            QComboBox QAbstractItemView {
                background-color: #1e293b;
                color: #e2e8f0;
                selection-background-color: #3b82f6;
                selection-color: white;
                border: 1px solid #334155;
                border-radius: 8px;
                padding: 4px;
                outline: none;
            }
            
            QComboBox QAbstractItemView::item {
                color: #e2e8f0;
                background-color: transparent;
                padding: 8px 12px;
                border-radius: 4px;
            }
            
            QComboBox QAbstractItemView::item:hover {
                background-color: #2d3b52;
                color: #ffffff;
            }
            
            QComboBox QAbstractItemView::item:selected {
                background-color: #3b82f6;
                color: white;
            }
            
            /* Table Widget */
            QTableWidget {
                background-color: #1e293b;
                alternate-background-color: #192433;
                color: #e2e8f0;
                gridline-color: #2d3b52;
                border: 1px solid #334155;
                border-radius: 12px;
                font-size: 13px;
            }
            
            QTableWidget::item {
                padding: 12px 16px;
                border: none;
                color: #e2e8f0;
            }
            
            QTableWidget::item:selected {
                background-color: #3b82f6;
                color: white;
            }
            
            QHeaderView::section {
                background-color: #2d3b52;
                color: #cbd5e1;
                padding: 14px 16px;
                border: none;
                font-weight: 600;
                font-size: 13px;
                text-transform: uppercase;
                letter-spacing: 0.05em;
            }
            
            /* Scrollbars */
            QScrollBar:vertical {
                background-color: #1e293b;
                width: 14px;
                border-radius: 7px;
                margin: 2px;
            }
            
            QScrollBar::handle:vertical {
                background-color: #475569;
                border-radius: 7px;
                min-height: 30px;
            }
            
            QScrollBar::handle:vertical:hover {
                background-color: #5a6b82;
            }
            
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            
            QScrollBar:horizontal {
                background-color: #1e293b;
                height: 14px;
                border-radius: 7px;
                margin: 2px;
            }
            
            QScrollBar::handle:horizontal {
                background-color: #475569;
                border-radius: 7px;
                min-width: 30px;
            }
            
            QScrollBar::handle:horizontal:hover {
                background-color: #5a6b82;
            }
            
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                width: 0px;
            }
            
            /* Tab Widget */
            QTabWidget::pane {
                border: 1px solid #334155;
                border-radius: 12px;
                background-color: #0f172a;
                padding: 4px;
            }
            
            QTabBar::tab {
                background-color: transparent;
                color: #94a3b8;
                padding: 12px 24px;
                margin-right: 4px;
                border-radius: 8px;
                font-weight: 500;
            }
            
            QTabBar::tab:selected {
                background-color: #3b82f6;
                color: white;
            }
            
            QTabBar::tab:hover {
                background-color: #2d3b52;
                color: #e2e8f0;
            }
            
            /* Progress Bar */
            QProgressBar {
                border: none;
                border-radius: 12px;
                background-color: #1e293b;
                text-align: center;
                height: 28px;
                font-weight: 600;
                color: #e2e8f0;
            }
            
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                        stop:0 #10b981, stop:1 #34d399);
                border-radius: 12px;
            }
            
            /* Dialogs */
            QDialog {
                background-color: #0f172a;
                color: #e2e8f0;
                border-radius: 16px;
            }
            
            QMessageBox {
                background-color: #0f172a;
                color: #e2e8f0;
            }
            
            QMessageBox QLabel {
                color: #e2e8f0;
            }
            
            QMessageBox QPushButton {
                min-width: 100px;
                padding: 10px 24px;
            }
            
            /* Status Bar */
            QStatusBar {
                background-color: #1e293b;
                color: #94a3b8;
                border-top: 1px solid #334155;
                font-size: 13px;
                padding: 6px 12px;
            }
            
            QStatusBar QLabel {
                color: #94a3b8;
            }
            
            /* Menu Bar */
            QMenuBar {
                background-color: #1e293b;
                color: #e2e8f0;
                border-bottom: 1px solid #334155;
                padding: 4px;
            }
            
            QMenuBar::item {
                padding: 8px 16px;
                border-radius: 6px;
                color: #e2e8f0;
            }
            
            QMenuBar::item:selected {
                background-color: #2d3b52;
            }
            
            QMenu {
                background-color: #1e293b;
                color: #e2e8f0;
                border: 1px solid #334155;
                border-radius: 10px;
                padding: 6px;
            }
            
            QMenu::item {
                padding: 10px 20px;
                border-radius: 6px;
                color: #e2e8f0;
            }
            
            QMenu::item:selected {
                background-color: #3b82f6;
                color: white;
            }
            
            /* Date Edit */
            QDateEdit {
                background-color: #1e293b;
                color: #e2e8f0;
                border: 1px solid #334155;
                border-radius: 8px;
                padding: 10px 14px;
                font-size: 14px;
            }
            
            QDateEdit::drop-down {
                border: none;
                background-color: transparent;
                width: 35px;
            }
            
            QDateEdit::down-arrow {
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #e2e8f0;
                margin-right: 8px;
            }
            
            QCalendarWidget {
                background-color: #1e293b;
                color: #e2e8f0;
                border-radius: 12px;
            }
            
            QCalendarWidget QToolButton {
                background-color: #2d3b52;
                color: #e2e8f0;
                border-radius: 6px;
                padding: 8px;
                font-weight: 500;
            }
            
            QCalendarWidget QToolButton:hover {
                background-color: #3b82f6;
            }
            
            QCalendarWidget QMenu {
                background-color: #1e293b;
                color: #e2e8f0;
            }
            
            QCalendarWidget QSpinBox {
                background-color: #2d3b52;
                color: #e2e8f0;
                border-radius: 6px;
                padding: 6px;
            }
            
            QCalendarWidget QAbstractItemView {
                background-color: #1e293b;
                color: #e2e8f0;
                selection-background-color: #3b82f6;
                selection-color: white;
                border-radius: 6px;
            }
            
            /* Sidebar */
            QWidget[objectName="sidebar"] {
                background-color: #1e293b;
                border-right: 1px solid #334155;
                padding: 16px 8px;
            }
            
            QWidget[objectName="sidebar"] QLabel {
                color: #e2e8f0;
            }
            
            QWidget[objectName="sidebar"] QPushButton {
                text-align: left;
                padding-left: 20px;
                margin: 4px 0;
                font-size: 14px;
                color: #e2e8f0;
            }
            
            QWidget[objectName="sidebar"] QPushButton:hover {
                background-color: #2d3b52;
            }
            
            /* Cards */
            QWidget[objectName="card"] {
                background-color: #1e293b;
                border: 1px solid #334155;
                border-radius: 16px;
                padding: 24px;
            }

            QLabel[objectName="muted"] {
                color: #94a3b8;
            }

            QPushButton[objectName="primary"] {
                background-color: #10b981;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-weight: 600;
            }
            QPushButton[objectName="primary"]:hover {
                background-color: #34d399;
            }
            
            /* Checkbox */
            QCheckBox {
                spacing: 8px;
                color: #e2e8f0;
                font-size: 14px;
            }
            
            QCheckBox::indicator {
                width: 20px;
                height: 20px;
                border-radius: 6px;
                border: 2px solid #334155;
                background-color: #1e293b;
            }
            
            QCheckBox::indicator:checked {
                background-color: #3b82f6;
                border-color: #3b82f6;
            }
            
            QCheckBox::indicator:hover {
                border-color: #3b82f6;
            }
            
            /* Spin Box Buttons */
            QSpinBox::up-button, QDoubleSpinBox::up-button {
                background-color: #2d3b52;
                border: none;
                border-radius: 4px;
            }
            
            QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover {
                background-color: #3b82f6;
            }
            
            QSpinBox::down-button, QDoubleSpinBox::down-button {
                background-color: #2d3b52;
                border: none;
                border-radius: 4px;
            }
            
            QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover {
                background-color: #3b82f6;
            }
            
            QSpinBox::up-arrow, QDoubleSpinBox::up-arrow {
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-bottom: 5px solid #e2e8f0;
            }
            
            QSpinBox::down-arrow, QDoubleSpinBox::down-arrow {
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 5px solid #e2e8f0;
            }
        """
        
    def _create_light_theme(self):
        """Create light theme stylesheet with complete coverage"""
        return """
            /* Main Window */
            QMainWindow {
                background-color: #ffffff;
                color: #1e293b;
            }
            
            /* All Widgets */
            QWidget {
                background-color: #ffffff;
                color: #1e293b;
                font-family: -apple-system, BlinkMacSystemFont, 'Inter', 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
                font-size: 14px;
                letter-spacing: -0.01em;
            }
            
            /* Labels */
            QLabel {
                color: #1e293b;
                background-color: transparent;
                font-weight: 400;
            }
            
            QFormLayout QLabel {
                color: #1e293b;
                background-color: transparent;
            }
            
            /* Buttons */
            QPushButton {
                background-color: #f8fafc;
                color: #1e293b;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                padding: 10px 20px;
                font-weight: 500;
                font-size: 14px;
            }
            
            QPushButton:hover {
                background-color: #f1f5f9;
                border: 1px solid #cbd5e1;
            }
            
            QPushButton:pressed {
                background-color: #e2e8f0;
            }
            
            QPushButton:disabled {
                background-color: #f8fafc;
                color: #94a3b8;
            }
            
            /* Input Fields */
            QLineEdit, QTextEdit, QSpinBox, QDoubleSpinBox {
                background-color: #ffffff;
                color: #1e293b;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                padding: 10px 14px;
                font-size: 14px;
                selection-background-color: #bfdbfe;
            }
            
            QLineEdit:focus, QTextEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {
                border: 2px solid #3b82f6;
                background-color: #f8fafc;
            }
            
            /* ComboBox */
            QComboBox {
                background-color: #ffffff;
                color: #1e293b;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                padding: 10px 14px;
                font-size: 14px;
            }
            
            QComboBox:hover {
                background-color: #f8fafc;
                border: 1px solid #cbd5e1;
            }
            
            QComboBox:focus {
                border: 2px solid #3b82f6;
            }
            
            QComboBox::drop-down {
                border: none;
                background-color: transparent;
                width: 35px;
            }
            
            QComboBox::down-arrow {
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #1e293b;
                margin-right: 8px;
            }
            
            QComboBox QAbstractItemView {
                background-color: #ffffff;
                color: #1e293b;
                selection-background-color: #3b82f6;
                selection-color: white;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                padding: 4px;
            }
            
            QComboBox QAbstractItemView::item {
                color: #1e293b;
                background-color: transparent;
                padding: 8px 12px;
                border-radius: 4px;
            }
            
            QComboBox QAbstractItemView::item:hover {
                background-color: #f1f5f9;
            }
            
            QComboBox QAbstractItemView::item:selected {
                background-color: #3b82f6;
                color: white;
            }
            
            /* Table */
            QTableWidget {
                background-color: #ffffff;
                alternate-background-color: #f8fafc;
                color: #1e293b;
                gridline-color: #f1f5f9;
                border: 1px solid #e2e8f0;
                border-radius: 12px;
                font-size: 13px;
            }
            
            QTableWidget::item {
                padding: 12px 16px;
                border: none;
                color: #1e293b;
            }
            
            QTableWidget::item:selected {
                background-color: #3b82f6;
                color: white;
            }
            
            QHeaderView::section {
                background-color: #f8fafc;
                color: #475569;
                padding: 14px 16px;
                border: none;
                font-weight: 600;
                font-size: 13px;
            }
            
            /* Scrollbars */
            QScrollBar:vertical {
                background-color: #f8fafc;
                width: 14px;
                border-radius: 7px;
            }
            
            QScrollBar::handle:vertical {
                background-color: #cbd5e1;
                border-radius: 7px;
                min-height: 30px;
            }
            
            QScrollBar::handle:vertical:hover {
                background-color: #94a3b8;
            }
            
            QScrollBar:horizontal {
                background-color: #f8fafc;
                height: 14px;
                border-radius: 7px;
            }
            
            QScrollBar::handle:horizontal {
                background-color: #cbd5e1;
                border-radius: 7px;
                min-width: 30px;
            }
            
            QScrollBar::handle:horizontal:hover {
                background-color: #94a3b8;
            }
            
            /* Tabs */
            QTabWidget::pane {
                border: 1px solid #e2e8f0;
                border-radius: 12px;
                background-color: #ffffff;
            }
            
            QTabBar::tab {
                background-color: transparent;
                color: #64748b;
                padding: 12px 24px;
                border-radius: 8px;
                font-weight: 500;
            }
            
            QTabBar::tab:selected {
                background-color: #3b82f6;
                color: white;
            }
            
            QTabBar::tab:hover {
                background-color: #f1f5f9;
                color: #1e293b;
            }
            
            /* Progress Bar */
            QProgressBar {
                border: none;
                border-radius: 12px;
                background-color: #f1f5f9;
                text-align: center;
                height: 28px;
                font-weight: 600;
                color: #1e293b;
            }
            
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                        stop:0 #10b981, stop:1 #34d399);
                border-radius: 12px;
            }
            
            /* Dialogs */
            QDialog {
                background-color: #ffffff;
                color: #1e293b;
            }
            
            QMessageBox {
                background-color: #ffffff;
                color: #1e293b;
            }
            
            QMessageBox QLabel {
                color: #1e293b;
            }
            
            /* Status Bar */
            QStatusBar {
                background-color: #f8fafc;
                color: #64748b;
                border-top: 1px solid #e2e8f0;
                font-size: 13px;
                padding: 6px 12px;
            }
            
            /* Sidebar */
            QWidget[objectName="sidebar"] {
                background-color: #f8fafc;
                border-right: 1px solid #e2e8f0;
                padding: 16px 8px;
            }
            
            QWidget[objectName="sidebar"] QLabel {
                color: #1e293b;
            }
            
            QWidget[objectName="sidebar"] QPushButton {
                text-align: left;
                padding-left: 20px;
                margin: 4px 0;
                color: #1e293b;
            }
            
            QWidget[objectName="sidebar"] QPushButton:hover {
                background-color: #f1f5f9;
            }

            QWidget[objectName="card"] {
                background-color: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 16px;
                padding: 24px;
            }

            QLabel[objectName="muted"] {
                color: #64748b;
            }

            QPushButton[objectName="primary"] {
                background-color: #10b981;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-weight: 600;
            }
            QPushButton[objectName="primary"]:hover {
                background-color: #34d399;
            }
            
            /* Date Edit */
            QDateEdit {
                background-color: #ffffff;
                color: #1e293b;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                padding: 10px 14px;
            }
            
            QCalendarWidget {
                background-color: #ffffff;
                color: #1e293b;
            }
            
            /* Checkbox */
            QCheckBox {
                color: #1e293b;
                spacing: 8px;
            }
            
            QCheckBox::indicator {
                width: 20px;
                height: 20px;
                border-radius: 6px;
                border: 2px solid #cbd5e1;
                background-color: #ffffff;
            }
            
            QCheckBox::indicator:checked {
                background-color: #3b82f6;
                border-color: #3b82f6;
            }
            
            /* Spin Box Buttons */
            QSpinBox::up-button, QDoubleSpinBox::up-button,
            QSpinBox::down-button, QDoubleSpinBox::down-button {
                background-color: #f1f5f9;
                border: none;
                border-radius: 4px;
            }
            
            QSpinBox::up-arrow, QDoubleSpinBox::up-arrow {
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-bottom: 5px solid #1e293b;
            }
            
            QSpinBox::down-arrow, QDoubleSpinBox::down-arrow {
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 5px solid #1e293b;
            }
        """

    def get_color_palette(self, theme='dark'):
        """Return color palette for charts and visualizations"""
        if theme == 'dark':
            return {
                'primary': '#3b82f6',
                'success': '#10b981',
                'warning': '#f59e0b',
                'danger': '#ef4444',
                'info': '#06b6d4',
                'purple': '#8b5cf6',
                'pink': '#ec4899',
                'background': '#0f172a',
                'surface': '#1e293b',
                'card': '#2d3b52',
                'text': '#e2e8f0',
                'text_secondary': '#94a3b8',
                'border': '#334155'
            }
        else:
            return {
                'primary': '#3b82f6',
                'success': '#10b981',
                'warning': '#f59e0b',
                'danger': '#ef4444',
                'info': '#06b6d4',
                'purple': '#8b5cf6',
                'pink': '#ec4899',
                'background': '#ffffff',
                'surface': '#f8fafc',
                'card': '#ffffff',
                'text': '#1e293b',
                'text_secondary': '#64748b',
                'border': '#e2e8f0'
            }
