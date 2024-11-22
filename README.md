# Blenders - Blender Version Manager

The simplest way to download, install, and switch between Blender versions.

![](blenders.mp4)

## Features

- Install and manage multiple Blender versions
- Easy switching between versions
- Clean uninstallation of versions
- Cross-platform support (Windows, macOS, Linux)
- Automatic version detection and updates

## Download the App

The Blenders application is available for download on various platforms. It allows users to manage multiple Blender installations seamlessly.

### Download Links
- [Download for macOS](https://github.com/yourusername/blenders/releases/latest)
- [Download for Windows - COMING SOON](https://github.com/yourusername/blenders/releases/latest)
- [Download for Linux - COMING SOON](https://github.com/yourusername/blenders/releases/latest)

### Installation Instructions
1. Download the installer for your platform.
2. Follow the on-screen instructions to complete the installation.

## Building from Source

### Prerequisites
- Python 3.8 or higher
- pip (Python package installer)

### Setup
1. Clone the repository:
```bash
git clone git@github.com:shayse-xr/BlenderVersionManager.git
cd blenders
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
python main.py
```

## Usage

### Installing a Blender Version
1. Launch the application
2. Browse the available versions
3. Click "Install" next to your desired version
4. Wait for the download and installation to complete

### Launching Blender
- Click "Launch" next to any installed version to start that version of Blender

### Uninstalling
- Click the trash icon next to any installed version to remove it
- Confirm the uninstallation when prompted

## Configuration

The application stores its configuration in:
- Windows: `%USERPROFILE%\.blender_manager`
- macOS/Linux: `~/.blender_manager`

## Development

### Project Structure
```
blender-version-manager/
├── main.py
├── blender_manager.py
├── version_row.py
├── styles.py
├── requirements.txt
└── README.md
```

## Contributing

Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Blender Foundation for their 3D software
- PyQt6 for the GUI framework

## Support

If you encounter any issues or have questions, please:
1. Check the [Issues](https://github.com/shayse-xr/BlenderVersionManager/issues) page
2. Create a new issue if your problem isn't already listed

---

Made with <3 by @shayse-xr / [shaysegal.co](https://shaysegal.co)

