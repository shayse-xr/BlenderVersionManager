from PyQt6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QLabel
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QIcon
from styles import COLORS, FONTS

class VersionRow(QWidget):
    def __init__(self, version: str, is_installed: bool, is_selected: bool, release_year: str = None):
        super().__init__()
        self.setObjectName("VersionRow")
        # Enable background styling for the widget
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
            
        # Horizontal layout with padding
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 12, 8, 12)
        
        # Version label with release year
        version_text = f"{version} ({release_year})" if release_year else version
        version_label = QLabel(version_text)
        version_label.setStyleSheet(f"""
            color: {COLORS['TEXT_PRIMARY']};
            font-size: {FONTS['BODY']['size']}px;
            font-family: {FONTS['BODY']['family']};
            background: transparent;
        """)
        layout.addWidget(version_label)
        
        # Add flexible space between label and buttons
        layout.addStretch()
        
        # Create button container for installed versions
        if is_installed:
            button_container = QWidget()
            button_layout = QHBoxLayout(button_container)
            button_layout.setContentsMargins(0, 0, 0, 0)
            button_layout.setSpacing(8)
            
            # Uninstall button
            self.uninstall_button = QPushButton()
            self.uninstall_button.setFixedSize(32, 32)
            self.uninstall_button.setIcon(QIcon.fromTheme("trash"))  
            self.uninstall_button.setToolTip("Uninstall")
            self.uninstall_button.setStyleSheet("""
                QPushButton {
                    background-color: #1E1E1E;  /* Match the row background */
                    border: none;
                    padding: 6px;
                    border-radius: 3px;
                }
                QPushButton:hover {
                    background-color: #3A3A3C;  /* Lighter hover state */
                }
                QPushButton:pressed {
                    background-color: #3A3A3C;
                }
            """)
            button_layout.addWidget(self.uninstall_button)
            
            # Launch button
            self.button = QPushButton("Launch")
            self.button.setFixedWidth(100)
            self.button.setStyleSheet(self._get_button_style("#f17702", "#eb8728"))
            button_layout.addWidget(self.button)
            
            layout.addWidget(button_container)
        else:
            # Install button for non-installed versions
            self.button = QPushButton("Install")
            self.button.setFixedWidth(100)
            self.button.setStyleSheet(self._get_button_style("#525c75", "#0066D6"))
            layout.addWidget(self.button)

        self.setStyleSheet(self._get_row_style(is_selected))

    def _get_button_style(self, base_color: str, hover_color: str) -> str:
        return f"""
            QPushButton {{
                background-color: {base_color};
                color: white;
                border: none;
                padding: 6px;
                border-radius: 3px;
            }}
            QPushButton:hover {{
                background-color: {hover_color};
            }}
            QPushButton:pressed {{
                background-color: {hover_color};
            }}
        """

    def _get_row_style(self, is_selected: bool) -> str:
        base_style = f"""
            #VersionRow {{
                background-color: {("#3A3A3C" if is_selected else "#1E1E1E")};
                border-radius: 3px;
                border-top: 1px solid #2D2D2D;
            }}
            #VersionLabel {{
                color: white;
                background: transparent;
            }}
        """
        if not is_selected:
            base_style += """
            #VersionRow:hover {
                background-color: #2D2D2D;
                border-top: 1px solid #3D3D3D;
            }
            """
        return base_style