import sys
import os
import json
import requests
import platform
import subprocess
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import re
from urllib.parse import urljoin

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QProgressBar, QScrollArea, QMessageBox,
    QStatusBar
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QUrl
from PyQt6.QtGui import QIcon, QPixmap, QDesktopServices

from version_row import VersionRow
from styles import (
    get_window_style, get_header_style, COLORS, FONTS, LAYOUT
)

class DownloadWorker(QThread):
    # Signal definitions for communication with main thread
    progress = pyqtSignal(int)      # Reports download progress (0-100)
    finished = pyqtSignal()         # Signals when download is complete
    error = pyqtSignal(str)         # Signals if an error occurs

    def __init__(self, url: str, save_path: str):
        super().__init__()
        self.url = url
        self.save_path = save_path
        print(f"Initializing download: {url} -> {save_path}")  

    def run(self):
        try:
            print(f"Starting download from: {self.url}")  
            response = requests.get(self.url, stream=True)
            response.raise_for_status()  
            
            total_size = int(response.headers.get('content-length', 0))
            print(f"Total file size: {total_size} bytes") 
            
            block_size = 1024
            downloaded = 0

            # Download file in chunks and update progress
            with open(self.save_path, 'wb') as f:
                for data in response.iter_content(block_size):
                    downloaded += len(data)
                    f.write(data)
                    if total_size:
                        progress = int((downloaded / total_size) * 100)
                        self.progress.emit(progress)
            
            # Verify the downloaded file
            if Path(self.save_path).stat().st_size == 0:
                raise Exception("Downloaded file is empty")
                
            print(f"Download completed. File size: {Path(self.save_path).stat().st_size} bytes") 
            self.finished.emit()
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Download failed: {str(e)}"
            print(error_msg)  
            self.error.emit(error_msg)
        except Exception as e:
            error_msg = f"Error during download: {str(e)}"
            print(error_msg) 
            self.error.emit(error_msg)

class BlenderManager(QMainWindow):
    def __init__(self):
        super().__init__()
        self.selected_version = None
        self.setWindowTitle("Blenders")
        self.setStyleSheet(get_window_style())
        
        # Fixed window size with 3:2 aspect ratio
        self.setFixedSize(600, 400)
        
        # Set application icon
        icon_path = Path(__file__).parent / 'logo.png'
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))
        
        # Set up configuration directories
        self.config_dir = Path.home() / '.blender_manager'
        self.config_file = self.config_dir / 'config.json'
        self.install_dir = self.config_dir / 'versions'
        
        # Create necessary directories
        self.config_dir.mkdir(exist_ok=True)
        self.install_dir.mkdir(exist_ok=True)
        
        # Initialize configuration and UI
        self.load_config()
        self.init_ui()

    def load_config(self):
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                self.config = json.load(f)
                # Verify installations when loading config
                self.verify_installations()
        else:
            # Create default configuration
            self.config = {
                'installed_versions': {},
                'active_version': None,
                'last_check': None
            }
            self.save_config()

    def save_config(self):
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Header
        header_widget = QWidget()
        header_widget.setObjectName("header")
        header_widget.setStyleSheet(get_header_style())
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(LAYOUT['PADDING']['HEADER'], 0, 
                                       LAYOUT['PADDING']['HEADER'], 0)
        header_layout.setSpacing(0)
        
        # Add logo
        logo_label = QLabel()
        logo_pixmap = QIcon('logo.png').pixmap(24, 24)
        logo_label.setPixmap(logo_pixmap)
        logo_label.setStyleSheet("margin-right: 1px;")
        header_layout.addWidget(logo_label)
        
        title = QLabel("Blender Version Manager")
        title.setStyleSheet(f"""
            color: {COLORS['TEXT_PRIMARY']};
            font-size: {FONTS['TITLE']['size']}px;
            font-weight: {FONTS['TITLE']['weight']};
            font-family: {FONTS['TITLE']['family']};
            margin-left: 2px;
        """)
        header_layout.addWidget(title)
        
        # Add stretch to push logo and title to the left
        header_layout.addStretch()
        
        updated_at = QLabel(f"Updated at {datetime.now().strftime('%d %B %Y %H:%M')}")
        updated_at.setStyleSheet(f"""
            color: {COLORS['TEXT_SECONDARY']};
            font-size: {FONTS['CAPTION']['size']}px;
            font-family: {FONTS['CAPTION']['family']};
        """)
        header_layout.addWidget(updated_at)
        
        main_layout.addWidget(header_widget)

        # Progress bar (hidden by default)
        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: {COLORS['HEADER_BG']};
                border: none;
                border-radius: 4px;
                height: 6px;
                text-align: center;
                margin: 0 {LAYOUT['PADDING']['HEADER']}px;
            }}
            QProgressBar::chunk {{
                background-color: {COLORS['BUTTON_PRIMARY']};
                border-radius: 4px;
            }}
        """)
        self.progress_bar.hide()
        main_layout.addWidget(self.progress_bar)

        # Scroll area for versions
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                background-color: transparent;
                width: 8px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background-color: #3A3A3C;
                min-height: 30px;
                border-radius: 4px;
            }
            QScrollBar::add-line:vertical, 
            QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)
        
        scroll_content = QWidget()
        scroll_content.setStyleSheet(f"background-color: {COLORS['WINDOW_BG']};")
        self.versions_layout = QVBoxLayout(scroll_content)
        self.versions_layout.setSpacing(1)
        self.versions_layout.setContentsMargins(
            LAYOUT['PADDING']['WINDOW'], 
            LAYOUT['PADDING']['WINDOW'], 
            LAYOUT['PADDING']['WINDOW'], 
            LAYOUT['PADDING']['WINDOW']
        )
        scroll.setWidget(scroll_content)
        
        main_layout.addWidget(scroll)
        
        # Status bar
        self.status_bar = QStatusBar()
        self.status_bar.setStyleSheet(f"""
            QStatusBar {{
                background-color: {COLORS['HEADER_BG']};
                color: {COLORS['TEXT_SECONDARY']};
                font-size: {FONTS['CAPTION']['size']}px;
                padding: 4px {LAYOUT['PADDING']['HEADER']}px;
            }}
        """)
        self.setStatusBar(self.status_bar)
        
        # Credit label 
        credit_label = QLabel("<a href='https://shaysegal.co' style='color: #999999; text-decoration: none;'>Created by shaysegal.co</a>")
        credit_label.setStyleSheet(f"""
            color: rgba(255, 255, 255, 0.5);  /* Softer white color with 50% opacity */
            font-size: {FONTS['CAPTION']['size']}px;
            padding-left: {LAYOUT['PADDING']['HEADER']}px;
        """)
        credit_label.setOpenExternalLinks(True)
        self.status_bar.addWidget(credit_label)
        
        # Initial version load
        self.refresh_versions()

    def get_blender_versions(self) -> List[Dict[str, str]]:
        try:
            # Base URL for Blender downloads
            base_url = "https://download.blender.org/release/"
            versions = []
            
            # Latest versions 
            latest_versions = [
                {
                    'version': '4.3.0',
                    'url': 'https://download.blender.org/release/Blender4.3/',
                    'directory': 'Blender4.3/',
                    'release_year': '2024'
                },
                {
                    'version': '4.2.4',
                    'url': 'https://download.blender.org/release/Blender4.2/',
                    'directory': 'Blender4.2/',
                    'release_year': '2024'
                },
                {
                    'version': '4.2.3',
                    'url': 'https://download.blender.org/release/Blender4.2/',
                    'directory': 'Blender4.2/',
                    'release_year': '2024'
                },
                {
                    'version': '4.2.2',
                    'url': 'https://download.blender.org/release/Blender4.2/',
                    'directory': 'Blender4.2/',
                    'release_year': '2024'
                },
                {
                    'version': '4.2.1',
                    'url': 'https://download.blender.org/release/Blender4.2/',
                    'directory': 'Blender4.2/',
                    'release_year': '2024'
                },
                {
                    'version': '4.2.0',
                    'url': 'https://download.blender.org/release/Blender4.2/',
                    'directory': 'Blender4.2/',
                    'release_year': '2023'
                },
                {
                    'version': '3.6.5',
                    'url': 'https://download.blender.org/release/Blender3.6/',
                    'directory': 'Blender3.6/',
                    'release_year': '2023'
                },
                {
                    'version': '3.5.1',
                    'url': 'https://download.blender.org/release/Blender3.5/',
                    'directory': 'Blender3.5/',
                    'release_year': '2023'
                },
                {
                    'version': '3.4.1',
                    'url': 'https://download.blender.org/release/Blender3.4/',
                    'directory': 'Blender3.4/',
                    'release_year': '2022'
                },
                {
                    'version': '3.3.1',
                    'url': 'https://download.blender.org/release/Blender3.3/',
                    'directory': 'Blender3.3/',
                    'release_year': '2022'
                },
                {
                    'version': '3.2.2',
                    'url': 'https://download.blender.org/release/Blender3.2/',
                    'directory': 'Blender3.2/',
                    'release_year': '2022'
                },
                {
                    'version': '3.0.1',
                    'url': 'https://download.blender.org/release/Blender3.0/',
                    'directory': 'Blender3.0/',
                    'release_year': '2022'
                }
            ]
            versions.extend(latest_versions)
            
            # Get older versions (if needed)
            response = requests.get(base_url)
            version_pattern = r'href="(Blender\d+\.\d+\.\d+(/|\.\d+/?))"'
            
            for match in re.finditer(version_pattern, response.text):
                version_dir = match.group(1)
                version_url = urljoin(base_url, version_dir)
                
                try:
                    version_match = re.search(r'Blender(\d+\.\d+\.\d+)', version_dir)
                    if version_match:
                        version_num = version_match.group(1)
                        # Skip versions we already added manually
                        if not any(v['version'] == version_num for v in latest_versions):
                            versions.append({
                                'version': version_num,
                                'url': version_url,
                                'directory': version_dir
                            })
                except (AttributeError, IndexError):
                    continue
            
            return sorted(versions, 
                        key=lambda x: [int(n) for n in x['version'].split('.')],
                        reverse=True)
        except Exception as e:
            self.handle_error(f"Failed to fetch Blender versions: {str(e)}")
            return []

    def refresh_versions(self):
        """Refresh the list of available Blender versions"""
        # Clear existing rows
        for i in reversed(range(self.versions_layout.count())): 
            widget = self.versions_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        # Verify installations before refreshing
        self.verify_installations()
        
        # Fetch actual versions
        versions = self.get_blender_versions()
        
        # Create version rows
        for version_info in versions:
            version = version_info['version']
            release_year = version_info.get('release_year')  # Use .get() to handle cases where release_year isn't present
            is_installed = version in self.config['installed_versions'] and \
                          Path(self.config['installed_versions'][version]).exists()
            is_selected = version == self.selected_version
            
            version_row = VersionRow(version, is_installed, is_selected, release_year)
            
            # Use functools.partial to properly bind the version parameter
            from functools import partial
            
            if is_installed:
                version_row.button.clicked.connect(
                    partial(self.launch_version, version)
                )
                version_row.uninstall_button.clicked.connect(
                    partial(self.uninstall_version, version)
                )
            else:
                version_row.button.clicked.connect(
                    partial(self.handle_version_click, version, version_info['url'])
                )
                
            self.versions_layout.addWidget(version_row)

        self.versions_layout.addStretch()

    def handle_version_click(self, version: str, base_url: str):
        """Handle clicks on version row buttons (Install/Launch)"""
        if version in self.config['installed_versions']:
            self.launch_version(version)
        else:
            self.install_version(version, base_url)

    def install_version(self, version: str, base_url: str):
        """Start the download and installation process for a Blender version."""
        try:
            system = platform.system().lower()
            
            # Convert version number to include .0 if needed
            version_parts = version.split('.')
            if len(version_parts) == 2:
                full_version = f"{version}.0"
            else:
                full_version = version
            
            # Determine correct filename based on system
            if system == 'darwin':
                # Check if we're on Apple Silicon
                is_arm = platform.processor() == 'arm'
                filename = f"blender-{full_version}-macos-{'arm64' if is_arm else 'x64'}"
            elif system == 'windows':
                filename = f"blender-{full_version}-windows-x64"
            else:  # Linux
                filename = f"blender-{full_version}-linux-x64"

            # Set appropriate extension
            if system == 'darwin':
                extension = '.dmg'
            elif system == 'windows':
                extension = '.zip'
            else:
                extension = '.tar.xz'

            download_url = urljoin(base_url, filename + extension)
            save_path = self.install_dir / f"{filename}{extension}"
            
            print(f"Attempting to download from: {download_url}")  
            print(f"Saving to: {save_path}") 

            # Show progress bar and start download
            self.progress_bar.show()
            self.progress_bar.setValue(0)

            # Store version for use in callbacks
            self._current_version = version

            # Create and start download worker
            self.current_download_worker = DownloadWorker(download_url, str(save_path))
            
            # Connect signals using lambda to preserve context
            self.current_download_worker.progress.connect(
                lambda value: self.update_progress(value)
            )
            self.current_download_worker.finished.connect(
                lambda: self.handle_download_finished(version)
            )
            self.current_download_worker.error.connect(
                lambda error: self.handle_error(error)
            )
            
            # Start the download
            self.current_download_worker.start()

        except Exception as e:
            self.handle_error(f"Failed to start download: {str(e)}")

    def handle_download_finished(self, version: str):
        try:
            # Verify download completed successfully
            full_version = f"{version}.0" if version.count('.') == 1 else version
            system = platform.system().lower()
            
            if system == 'darwin':
                is_arm = platform.processor() == 'arm'
                filename = f"blender-{full_version}-macos-{'arm64' if is_arm else 'x64'}.dmg"
            elif system == 'windows':
                filename = f"blender-{full_version}-windows-x64.zip"
            else:
                filename = f"blender-{full_version}-linux-x64.tar.xz"
            
            downloaded_file = self.install_dir / filename
            
            if not downloaded_file.exists():
                raise Exception(f"Download failed: {filename} not found")
            
            if downloaded_file.stat().st_size == 0:
                raise Exception(f"Download failed: {filename} is empty")
            
            print(f"Download completed successfully: {downloaded_file}")
            
            # Proceed with installation
            self.finish_installation(version)
            
        except Exception as e:
            self.handle_error(f"Download verification failed: {str(e)}")

    def update_progress(self, value: int):
        """Update progress bar with current download progress"""
        self.progress_bar.setValue(value)

    def finish_installation(self, version: str):
        """Complete the installation process after successful download"""
        try:
            self.progress_bar.hide()
            system = platform.system().lower()
            full_version = f"{version}.0" if version.count('.') == 1 else version
            
            if system == 'darwin':
                # Check for ARM or Intel DMG
                dmg_path = self.install_dir / f"blender-{full_version}-macos-arm64.dmg"
                if not dmg_path.exists():
                    dmg_path = self.install_dir / f"blender-{full_version}-macos-x64.dmg"
                
                # Verify DMG exists
                if not dmg_path.exists():
                    raise Exception(f"DMG file not found at {dmg_path}")
                
                print(f"Installing from DMG: {dmg_path}")
                print(f"DMG exists: {dmg_path.exists()}")
                print(f"DMG size: {dmg_path.stat().st_size} bytes")
                
                mount_point = "/Volumes/Blender"
                
                # First, ensure the mount point is not already in use
                try:
                    detach_result = subprocess.run(
                        ['hdiutil', 'detach', mount_point], 
                        capture_output=True,
                        text=True,
                        check=False
                    )
                    print(f"Detach result: {detach_result.stdout} {detach_result.stderr}")
                except Exception as e:
                    print(f"Detach exception: {str(e)}")
                
                # Mount the DMG with more detailed error handling
                try:
                    print(f"Attempting to mount: {dmg_path}")
                    mount_process = subprocess.run(
                        ['hdiutil', 'attach', str(dmg_path)],
                        capture_output=True,
                        text=True,
                        check=True
                    )
                    print(f"Mount output: {mount_process.stdout}")
                    
                    # Wait for mount
                    import time
                    time.sleep(2)
                    
                    # Create installation directory
                    install_path = self.install_dir / f"Blender {version}"
                    install_path.mkdir(exist_ok=True)
                    print(f"Created install path: {install_path}")
                    
                    # Check mount point contents
                    mount_contents = list(Path(mount_point).glob('*'))
                    print(f"Mount point contents: {mount_contents}")
                    
                    # Verify Blender.app exists
                    blender_app = Path(f"{mount_point}/Blender.app")
                    if not blender_app.exists():
                        raise Exception(f"Blender.app not found in {mount_point}")
                    
                    print(f"Found Blender.app at: {blender_app}")
                    
                    # Copy Blender.app
                    copy_result = subprocess.run(
                        ['cp', '-R', str(blender_app), str(install_path)],
                        capture_output=True,
                        text=True,
                        check=True
                    )
                    print(f"Copy result: {copy_result.stdout}")
                    
                    # Unmount
                    detach_result = subprocess.run(
                        ['hdiutil', 'detach', mount_point],
                        capture_output=True,
                        text=True,
                        check=True
                    )
                    print(f"Final detach result: {detach_result.stdout}")
                    
                    # Cleanup
                    dmg_path.unlink()
                    
                    # Update config
                    self.config['installed_versions'][version] = str(install_path / "Blender.app")
                    print(f"Installation completed successfully")
                    
                except subprocess.CalledProcessError as e:
                    raise Exception(f"DMG operation failed: {e.stderr}")
                except Exception as e:
                    raise Exception(f"Installation error: {str(e)}")
                
            elif system == 'windows':
                # Handle Windows zip/msi installation
                pass
                
            else:  # Linux
                # Handle Linux tar.xz installation
                pass
            
            self.save_config()
            self.refresh_versions()
            self.status_bar.showMessage(f"Blender {version} installed successfully")
            
        except Exception as e:
            self.handle_error(f"Installation failed: {str(e)}")
            # Cleanup
            install_path = self.install_dir / f"Blender {version}"
            if install_path.exists():
                import shutil
                shutil.rmtree(install_path)
            
            if system == 'darwin':
                try:
                    subprocess.run(
                        ['hdiutil', 'detach', mount_point], 
                        capture_output=True,
                        check=False
                    )
                except:
                    pass

    def handle_error(self, error_msg: str):
        """Display error message to user and clean up UI"""
        self.progress_bar.hide()
        QMessageBox.critical(self, "Error", f"Installation failed: {error_msg}")

    def launch_version(self, version: str):
        """Launch an installed version of Blender"""
        try:
            install_path = Path(self.config['installed_versions'][version])
            system = platform.system().lower()
            
            if system == 'darwin':
                subprocess.Popen(['open', str(install_path)])
            elif system == 'windows':
                subprocess.Popen([str(install_path / 'blender.exe')])
            else:  # Linux
                subprocess.Popen([str(install_path / 'blender')])
            
            self.status_bar.showMessage(f"Launched Blender {version}")
        except Exception as e:
            self.handle_error(f"Failed to launch Blender: {str(e)}")

    def get_os_suffix(self) -> str:
        """Get the appropriate OS suffix for download URLs"""
        system = platform.system().lower()
        if system == 'darwin':
            return 'macos-x64'
        elif system == 'windows':
            return 'windows-x64'
        else:  # linux
            return 'linux-x64'

    def handle_row_click(self, version: str):
        """Handle clicks on version rows (selection)"""
        self.selected_version = version
        self.refresh_versions()

    def verify_installations(self):
        """Verify all installed versions actually exist and clean up invalid entries"""
        invalid_versions = []
        
        for version, path in self.config['installed_versions'].items():
            app_path = Path(path)
            if not app_path.exists():
                print(f"Found invalid installation: {version} at {path}")
                invalid_versions.append(version)
        
        # Remove invalid entries from config
        for version in invalid_versions:
            print(f"Removing invalid installation from config: {version}")
            del self.config['installed_versions'][version]
        
        # Save cleaned config if any changes were made
        if invalid_versions:
            self.save_config()
            print("Config cleaned up")

    def list_installed_versions(self):
        """Print all installed versions and their paths"""
        print("\nInstalled Blender Versions:")
        print("-" * 50)
        
        # First verify installations to clean up any invalid entries
        self.verify_installations()
        
        if not self.config['installed_versions']:
            print("No Blender versions currently installed.")
            return
        
        for version, path in self.config['installed_versions'].items():
            app_path = Path(path)
            status = "✓ Valid" if app_path.exists() else "✗ Invalid"
            size = "N/A"
            if app_path.exists():
                try:
                    # Get size in MB
                    size = f"{app_path.stat().st_size / (1024 * 1024):.1f} MB"
                except:
                    pass
            print(f"Version: {version}")
            print(f"Path: {path}")
            print(f"Status: {status}")
            print(f"Size: {size}")
            print("-" * 50)

    def uninstall_version(self, version: str):
        """Uninstall a Blender version"""
        try:
            # Get installation path from config
            install_path = Path(self.config['installed_versions'][version])
            
            # Get the parent directory that contains the Blender version folder
            version_dir = self.install_dir / f"Blender {version}"
            
            # Confirm uninstallation
            msg_box = QMessageBox(self)
            msg_box.setIcon(QMessageBox.Icon.Warning)
            msg_box.setText(f'Are you sure you want to uninstall Blender {version}?')
            msg_box.setStandardButtons(
                QMessageBox.StandardButton.Yes | 
                QMessageBox.StandardButton.No
            )
            msg_box.setDefaultButton(QMessageBox.StandardButton.No)
            
            reply = msg_box.exec()
            
            if reply == QMessageBox.StandardButton.Yes:
                # Remove installation directory
                if version_dir.exists():
                    if platform.system() == 'Windows':
                        os.system(f'rmdir /S /Q "{version_dir}"')
                    else:
                        import shutil
                        shutil.rmtree(str(version_dir))
                
                # Remove from config
                del self.config['installed_versions'][version]
                self.save_config()
                
                # Update UI
                self.refresh_versions()
                self.status_bar.showMessage(f'Uninstalled Blender {version}')
                
        except Exception as e:
            self.handle_error(f"Failed to uninstall version {version}: {str(e)}")