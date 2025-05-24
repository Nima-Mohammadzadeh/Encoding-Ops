from PyQt6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QPushButton, 
    QFrame, QGridLayout, QSpacerItem, QSizePolicy
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QIcon
from theme_manager import THEME_MANAGER

class DashboardView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("dashboardView")

        # 1. Initialize main layout for the view
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(30, 30, 30, 30)
        main_layout.setSpacing(25)

        # 2. Create and configure UI elements, assigning to self where needed by update_theme_stylesheet
        # Welcome Message elements
        self.welcome_frame = QFrame()
        welcome_frame_layout = QVBoxLayout(self.welcome_frame)
        welcome_frame_layout.setContentsMargins(0,0,0,0)
        welcome_frame_layout.setSpacing(8)
        self.welcome_title = QLabel("Welcome to RFID Workflow Manager")
        self.welcome_title.setObjectName("welcomeTitle")
        welcome_title_font = QFont("Segoe UI", 26, QFont.Weight.Bold)
        self.welcome_title.setFont(welcome_title_font)
        welcome_frame_layout.addWidget(self.welcome_title)
        self.welcome_subtitle = QLabel(
            "Manage your RFID jobs and label printing efficiently. Use the tabs above to navigate to "
            "different sections of the application. This dashboard provides an overview of your current "
            "tasks and system status."
        )
        self.welcome_subtitle.setObjectName("welcomeSubtitle")
        welcome_subtitle_font = QFont("Segoe UI", 11)
        self.welcome_subtitle.setFont(welcome_subtitle_font)
        self.welcome_subtitle.setWordWrap(True)
        welcome_frame_layout.addWidget(self.welcome_subtitle)

        # Summary Cards Section elements (layout defined before use in populate_summary_cards)
        self.cards_layout_widget = QWidget()
        self.cards_layout = QHBoxLayout(self.cards_layout_widget)
        self.cards_layout.setContentsMargins(0,0,0,0)
        self.cards_layout.setSpacing(25)
        
        # Quick Actions Section elements
        self.quick_actions_frame = QFrame()
        quick_actions_frame_layout = QVBoxLayout(self.quick_actions_frame)
        quick_actions_frame_layout.setContentsMargins(0,0,0,0)
        quick_actions_frame_layout.setSpacing(12)
        self.quick_actions_title = QLabel("Quick Actions")
        self.quick_actions_title.setObjectName("quickActionsTitle")
        quick_actions_title_font = QFont("Segoe UI", 18, QFont.Weight.DemiBold)
        self.quick_actions_title.setFont(quick_actions_title_font)
        quick_actions_frame_layout.addWidget(self.quick_actions_title)
        
        quick_action_buttons_layout = QHBoxLayout()
        quick_action_buttons_layout.setSpacing(15)
        quick_action_buttons_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.create_new_job_button = self.create_action_button("Create New Job", "➕")
        self.reprint_label_button = self.create_action_button("Reprint Label", "📄")
        self.view_reports_button = self.create_action_button("View Reports", "📊")
        quick_action_buttons_layout.addWidget(self.create_new_job_button)
        quick_action_buttons_layout.addWidget(self.reprint_label_button)
        quick_action_buttons_layout.addWidget(self.view_reports_button)
        quick_action_buttons_layout.addStretch()
        quick_actions_frame_layout.addLayout(quick_action_buttons_layout)

        # 3. Register for theme updates and apply initial theme styles
        # This call will use the self.xxx attributes defined above.
        THEME_MANAGER.register_for_theme_updates(self.update_theme_stylesheet)
        self.update_theme_stylesheet() 

        # 4. Add the created and styled widgets to the main layout
        main_layout.addWidget(self.welcome_frame)
        main_layout.addSpacerItem(QSpacerItem(20, 15, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed))
        main_layout.addWidget(self.cards_layout_widget) # This contains the cards_layout with cards
        main_layout.addSpacerItem(QSpacerItem(20, 25, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed))
        main_layout.addWidget(self.quick_actions_frame)
        main_layout.addStretch()

    def populate_summary_cards(self):
        if not hasattr(self, 'cards_layout') or self.cards_layout is None:
            return # Guard against calls before cards_layout is fully initialized
            
        while self.cards_layout.count():
            item = self.cards_layout.takeAt(0)
            widget = item.widget()
            if widget: widget.deleteLater()

        theme = THEME_MANAGER.current()
        active_jobs_count = 12
        completed_today_count = 35
        system_alerts_count = 2

        self.cards_layout.addWidget(self.create_summary_card(
            "Active Jobs", str(active_jobs_count), "Jobs currently in progress", "📘", 
            icon_color=theme["ICON_COLOR"], value_color=theme["SUCCESS_COLOR"]
        ))
        self.cards_layout.addWidget(self.create_summary_card(
            "Completed Today", str(completed_today_count), "Labels printed successfully", "✅", 
            icon_color=theme["ICON_COLOR"], value_color=theme["SUCCESS_COLOR"]
        ))
        self.cards_layout.addWidget(self.create_summary_card(
            "System Alerts", str(system_alerts_count), "Requires attention", "⚠️", 
            icon_color=theme["ALERT_COLOR"],  # Provide a base icon color (can be alert color)
            value_color=theme["ALERT_COLOR"], # Provide a base value color (will be overridden by alert_color logic for value)
            alert_color=theme["ALERT_COLOR"]
        ))

    def update_theme_stylesheet(self):
        theme = THEME_MANAGER.current()
        self.setStyleSheet(f"""
            QWidget#dashboardView {{
                background-color: {theme["WINDOW_BACKGROUND"]};
            }}
            QFrame#summaryCard {{
                background-color: {theme["CONTENT_BACKGROUND"]};
                border-radius: 8px;
                border: 1px solid {theme["BORDER_COLOR"]};
            }}
            QLabel#welcomeTitle {{
                color: {theme["PRIMARY_TEXT"]};
            }}
            QLabel#welcomeSubtitle {{
                color: {theme["SECONDARY_TEXT"]};
            }}
            QLabel#quickActionsTitle {{
                color: {theme["PRIMARY_TEXT"]};
            }}
            QLabel.cardIcon {{ /* Style applied in create_summary_card */ }}
            QLabel.cardTitle {{
                color: {theme["PRIMARY_TEXT"]};
            }}
            QLabel.cardValue {{ /* Style applied in create_summary_card */ }}
            QLabel.cardSubtitle {{
                color: {theme["MUTED_TEXT"]};
            }}
            QPushButton.actionButton {{
                background-color: {theme["PRIMARY_ACCENT"]};
                color: {theme["PRIMARY_ACCENT_TEXT"]};
                border-radius: 5px;
                padding: 8px 15px;
                text-align: center;
                font-size: 10pt;
                border: none; /* Ensure no default border interferes */
            }}
            QPushButton.actionButton:hover {{ background-color: {theme["PRIMARY_ACCENT_HOVER"]}; }}
            QPushButton.actionButton:pressed {{ background-color: {theme["PRIMARY_ACCENT_PRESSED"]}; }}
        """)
        
        # Ensure dynamic content is repopulated/restyled
        self.populate_summary_cards()
        
        # Re-apply specific stylesheet aspects for buttons
        button_base_style = (
            f"background-color: {theme['PRIMARY_ACCENT']}; color: {theme['PRIMARY_ACCENT_TEXT']}; "
            f"border-radius: 5px; padding: 8px 15px; text-align: center; font-size: 10pt; border: none;"
        )
        button_hover_style = f"background-color: {theme['PRIMARY_ACCENT_HOVER']};"
        button_pressed_style = f"background-color: {theme['PRIMARY_ACCENT_PRESSED']};"

        for btn in [self.create_new_job_button, self.reprint_label_button, self.view_reports_button]:
            btn.setStyleSheet(
                f"""QPushButton {{
                    {button_base_style}
                }}
                QPushButton:hover {{
                    {button_hover_style}
                }}
                QPushButton:pressed {{
                    {button_pressed_style}
                }}"""
            )

    def create_summary_card(self, title_text, value_text, subtitle_text, icon_text, icon_color, value_color, alert_color=None):
        card = QFrame()
        card.setObjectName("summaryCard")
        card.setFixedWidth(260)
        card.setFixedHeight(160)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(20, 20, 20, 20)
        card_layout.setSpacing(12)
        card_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        header_layout = QHBoxLayout()
        header_layout.setSpacing(10)
        icon_label = QLabel(icon_text)
        icon_label.setObjectName("cardIcon")
        icon_font = QFont("Segoe UI", 20)
        icon_label.setFont(icon_font)
        icon_label.setStyleSheet(f"color: {alert_color if alert_color else icon_color}; padding-top: 3px; background-color: transparent;")
        header_layout.addWidget(icon_label)

        card_title_label = QLabel(title_text)
        card_title_label.setObjectName("cardTitle")
        title_font = QFont("Segoe UI", 12, QFont.Weight.Bold)
        card_title_label.setFont(title_font)
        header_layout.addWidget(card_title_label, alignment=Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        header_layout.addStretch()
        card_layout.addLayout(header_layout)

        value_label = QLabel(value_text)
        value_label.setObjectName("cardValue")
        value_font = QFont("Segoe UI", 30, QFont.Weight.Bold)
        value_label.setFont(value_font)
        final_value_color = alert_color if alert_color else value_color
        value_label.setStyleSheet(f"color: {final_value_color}; background-color: transparent;")
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(value_label, alignment=Qt.AlignmentFlag.AlignCenter)

        subtitle_label = QLabel(subtitle_text)
        subtitle_label.setObjectName("cardSubtitle")
        subtitle_font = QFont("Segoe UI", 9)
        subtitle_label.setFont(subtitle_font)
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_label.setWordWrap(True)
        card_layout.addWidget(subtitle_label, alignment=Qt.AlignmentFlag.AlignCenter)
        
        card_layout.addStretch()
        return card

    def create_action_button(self, text, icon_text):
        button = QPushButton(f"{icon_text} {text}")
        button.setObjectName("actionButton") # Used by the main stylesheet in update_theme_stylesheet
        button.setFixedHeight(40)
        return button

    def __del__(self):
        THEME_MANAGER.unregister_for_theme_updates(self.update_theme_stylesheet) 