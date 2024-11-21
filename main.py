from blender_manager import BlenderManager
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from pathlib import Path
import sys

if __name__ == '__main__':
    # Initialize the Qt application
    app = QApplication(sys.argv)
    
    # Set application icon
    icon_path = Path(__file__).parent / 'logo.png'
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))
    
    # Create and show the main window
    window = BlenderManager()
    window.show()
    
    # Start the event loop and exit when done
    sys.exit(app.exec()) 