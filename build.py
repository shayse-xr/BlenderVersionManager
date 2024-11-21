import PyInstaller.__main__
import platform
import os
from pathlib import Path
import sys
import shutil
import subprocess
from PIL import Image
import tempfile

def create_icns(png_path, output_dir):
    """Convert PNG to ICNS format"""
    try:
        # Create temporary iconset directory
        iconset_dir = Path(output_dir) / "icon.iconset"
        iconset_dir.mkdir(parents=True, exist_ok=True)
        
        # Open original PNG
        img = Image.open(png_path)
        
        # Generate different sizes
        sizes = [16, 32, 64, 128, 256, 512, 1024]
        for size in sizes:
            # Regular size
            resized = img.resize((size, size), Image.Resampling.LANCZOS)
            resized.save(iconset_dir / f"icon_{size}x{size}.png")
            
            # @2x size
            if size <= 512:
                resized = img.resize((size * 2, size * 2), Image.Resampling.LANCZOS)
                resized.save(iconset_dir / f"icon_{size}x{size}@2x.png")
        
        # Convert iconset to icns
        icns_path = Path(output_dir) / "icon.icns"
        subprocess.run(['iconutil', '-c', 'icns', str(iconset_dir)], check=True)
        
        # Clean up iconset directory
        shutil.rmtree(iconset_dir)
        
        return icns_path
        
    except Exception as e:
        print(f"Failed to create ICNS: {str(e)}")
        return None

def build(version="1.0.0"):
    try:
        # Get current platform
        system = platform.system().lower()
        print(f"Building for platform: {system}")
        
        # Get absolute paths
        current_dir = Path.cwd()
        logo_path = current_dir / "logo.png"
        build_dir = current_dir / "build"
        dist_dir = current_dir / "dist"
        
        # Clean previous builds
        if build_dir.exists():
            shutil.rmtree(build_dir)
        if dist_dir.exists():
            shutil.rmtree(dist_dir)
            
        build_dir.mkdir()
        dist_dir.mkdir()
        
        # Convert PNG to ICNS for macOS
        icon_path = logo_path
        if system == 'darwin':
            print("Converting PNG to ICNS format...")
            icon_path = create_icns(logo_path, build_dir)
            if not icon_path:
                print("Failed to create ICNS file. Continuing without icon...")
                icon_path = logo_path
        
        # Base PyInstaller arguments
        args = [
            'main.py',
            '--name=Blenders',
            '--windowed',
            '--onefile',
            f'--icon={str(icon_path)}',
            f'--add-data={str(logo_path)}:.',
            '--clean',
            '--noconfirm',
            f'--distpath={str(dist_dir)}',
            f'--workpath={str(build_dir)}',
            f'--specpath={str(build_dir)}'
        ]
        
        # Platform-specific arguments
        if system == 'darwin':
            args.extend([
                '--osx-bundle-identifier=com.shaysegal.blenders'
            ])
        elif system == 'windows':
            args.extend([
                '--version-file=version.txt'
            ])
        
        # Run PyInstaller
        PyInstaller.__main__.run(args)
        
        # Create DMG for macOS
        if system == 'darwin':
            app_path = dist_dir / "Blenders.app"
            if app_path.exists():
                dmg_name = f"Blenders-{version}-macos-arm64.dmg"
                dmg_path = dist_dir / dmg_name
                
                # Remove existing DMG if it exists
                if dmg_path.exists():
                    dmg_path.unlink()
                
                # Create DMG
                subprocess.run([
                    'hdiutil', 'create',
                    '-volname', 'Blenders',
                    '-srcfolder', str(app_path),
                    '-ov', '-format', 'UDZO',
                    str(dmg_path)
                ], check=True)
                
                print(f"\nCreated DMG: {dmg_path}")
            
        print("\nBuild completed successfully!")
        
    except Exception as e:
        print(f"Build failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    build() 

