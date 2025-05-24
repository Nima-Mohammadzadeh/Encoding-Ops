from PyQt6.QtGui import QPalette, QColor, QFont
from PyQt6.QtWidgets import QApplication

LIGHT_THEME = {
    "WINDOW_BACKGROUND": "#f8f9fa",
    "CONTENT_BACKGROUND": "#ffffff",
    "PRIMARY_TEXT": "#212529",
    "SECONDARY_TEXT": "#495057",
    "MUTED_TEXT": "#6c757d",
    "PRIMARY_ACCENT": "#007bff",
    "PRIMARY_ACCENT_HOVER": "#0056b3",
    "PRIMARY_ACCENT_PRESSED": "#004085",
    "PRIMARY_ACCENT_TEXT": "#ffffff",
    "BORDER_COLOR": "#e0e0e0",
    "ICON_COLOR": "#007bff",
    "ALERT_COLOR": "#dc3545",
    "SUCCESS_COLOR": "#28a745",
    "NAV_BACKGROUND": "#ffffff",
    "NAV_TEXT": "#495057",
    "NAV_TEXT_HOVER": "#007bff",
    "NAV_ITEM_HOVER_BACKGROUND": "rgba(0, 123, 255, 0.1)",
    "LOGO_ICON_COLOR": "#007bff",
    "USER_PROFILE_ICON_BG": "#6c757d",
    "USER_PROFILE_ICON_TEXT": "#ffffff",
    "CARD_BACKGROUND": "#ffffff",
    "CARD_SHADOW": "rgba(0, 0, 0, 0.1)",
    "ACCENT_GRADIENT_START": "#007bff",
    "ACCENT_GRADIENT_END": "#0056b3",
}

DARK_THEME = {
    "WINDOW_BACKGROUND": "#1a1a1a",
    "CONTENT_BACKGROUND": "#2d2d2d",
    "PRIMARY_TEXT": "#e0e0e0",
    "SECONDARY_TEXT": "#b8b8b8",
    "MUTED_TEXT": "#888888",
    "PRIMARY_ACCENT": "#1e88e5",
    "PRIMARY_ACCENT_HOVER": "#42a5f5",
    "PRIMARY_ACCENT_PRESSED": "#1565c0",
    "PRIMARY_ACCENT_TEXT": "#ffffff",
    "BORDER_COLOR": "#404040",
    "ICON_COLOR": "#1e88e5",
    "ALERT_COLOR": "#e57373",
    "SUCCESS_COLOR": "#81c784",
    "NAV_BACKGROUND": "#2d2d2d",
    "NAV_TEXT": "#e0e0e0",
    "NAV_TEXT_HOVER": "#42a5f5",
    "NAV_ITEM_HOVER_BACKGROUND": "rgba(30, 136, 229, 0.15)",
    "LOGO_ICON_COLOR": "#1e88e5",
    "USER_PROFILE_ICON_BG": "#606060",
    "USER_PROFILE_ICON_TEXT": "#e0e0e0",
    "CARD_BACKGROUND": "#2d2d2d",
    "CARD_SHADOW": "rgba(0, 0, 0, 0.3)",
    "ACCENT_GRADIENT_START": "#1e88e5",
    "ACCENT_GRADIENT_END": "#1565c0",
}

class ThemeManager:
    _instance = None
    current_theme_name = "light"
    themes = {"light": LIGHT_THEME, "dark": DARK_THEME}
    
    # Signals or callbacks could be added here to notify widgets of theme changes
    theme_changed_callbacks = []

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ThemeManager, cls).__new__(cls)
        return cls._instance

    def current(self):
        return self.themes[self.current_theme_name]

    def toggle_theme(self):
        if self.current_theme_name == "light":
            self.current_theme_name = "dark"
        else:
            self.current_theme_name = "light"
        self.apply_theme_to_app()
        for callback in self.theme_changed_callbacks:
            callback()

    def apply_theme_to_app(self):
        app = QApplication.instance()
        if not app:
            return

        theme_colors = self.current()
        
        # Set global palette (affects some standard Qt widgets)
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(theme_colors["WINDOW_BACKGROUND"]))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(theme_colors["PRIMARY_TEXT"]))
        palette.setColor(QPalette.ColorRole.Base, QColor(theme_colors["CONTENT_BACKGROUND"]))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(theme_colors["WINDOW_BACKGROUND"])) # e.g. for table alternate rows
        palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(theme_colors["CONTENT_BACKGROUND"]))
        palette.setColor(QPalette.ColorRole.ToolTipText, QColor(theme_colors["PRIMARY_TEXT"]))
        palette.setColor(QPalette.ColorRole.Text, QColor(theme_colors["PRIMARY_TEXT"]))
        palette.setColor(QPalette.ColorRole.Button, QColor(theme_colors["CONTENT_BACKGROUND"]))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(theme_colors["PRIMARY_TEXT"]))
        palette.setColor(QPalette.ColorRole.BrightText, QColor(theme_colors["ALERT_COLOR"])) # Often used for errors
        palette.setColor(QPalette.ColorRole.Link, QColor(theme_colors["PRIMARY_ACCENT"]))
        palette.setColor(QPalette.ColorRole.Highlight, QColor(theme_colors["PRIMARY_ACCENT"]))
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor(theme_colors["PRIMARY_ACCENT_TEXT"]))
        app.setPalette(palette)

        # Note: QPalette is limited. Most detailed styling will still come from stylesheets.
        # We need to trigger a stylesheet refresh for all relevant widgets.

    def get_stylesheet(self, widget_name):
        # This is a placeholder. Each major widget (navbar, views) will need its own method
        # to generate its specific stylesheet based on the current theme.
        # For now, we just signal that the theme changed, and widgets should update themselves.
        pass

    def register_for_theme_updates(self, callback):
        if callback not in self.theme_changed_callbacks:
            self.theme_changed_callbacks.append(callback)

    def unregister_for_theme_updates(self, callback):
        if callback in self.theme_changed_callbacks:
            self.theme_changed_callbacks.remove(callback)

# Initialize a singleton instance
THEME_MANAGER = ThemeManager() 