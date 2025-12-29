"""
Setup script to download FFmpeg binaries required for OpenCV video playback.
Run this once after cloning the repository.
"""

import os
import sys
import urllib.request
import zipfile
import shutil

def download_file(url, filename):
    """Download a file with progress indicator"""
    print(f"Downloading {filename}...")
    try:
        urllib.request.urlretrieve(url, filename)
        print(f"✓ Downloaded {filename}")
        return True
    except Exception as e:
        print(f"✗ Failed to download {filename}: {e}")
        return False

def extract_zip(zip_path, extract_to):
    """Extract zip file"""
    print(f"Extracting {zip_path}...")
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
        print(f"✓ Extracted to {extract_to}")
        return True
    except Exception as e:
        print(f"✗ Failed to extract: {e}")
        return False

def setup_ffmpeg():
    """Download and setup FFmpeg binaries"""
    print("="*60)
    print("FFmpeg Setup for Focus Timer")
    print("="*60)
    
    # Check if already exists
    if os.path.exists("ffmpeg.exe") and os.path.exists("ffplay.exe") and os.path.exists("ffprobe.exe"):
        print("FFmpeg binaries already exist. Setup complete!")
        return True
    
    print("\nFFmpeg is required for video background playback.")
    print("This script will download FFmpeg binaries (~100MB).")
    
    response = input("\nContinue? (y/n): ").lower()
    if response != 'y':
        print("Setup cancelled.")
        return False
    
    # FFmpeg download URL (Windows essentials build)
    ffmpeg_url = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
    zip_filename = "ffmpeg.zip"
    
    # Download FFmpeg
    if not download_file(ffmpeg_url, zip_filename):
        return False
    
    # Extract
    extract_folder = "ffmpeg_temp"
    if not extract_zip(zip_filename, extract_folder):
        return False
    
    # Find and copy the executables
    print("\nCopying executables...")
    try:
        # Find the bin folder (structure: ffmpeg-X.X.X-essentials_build/bin/)
        for root, dirs, files in os.walk(extract_folder):
            if 'bin' in dirs:
                bin_path = os.path.join(root, 'bin')
                
                # Copy executables
                for exe in ['ffmpeg.exe', 'ffplay.exe', 'ffprobe.exe']:
                    src = os.path.join(bin_path, exe)
                    if os.path.exists(src):
                        shutil.copy2(src, exe)
                        print(f"✓ Copied {exe}")
                
                break
        
        print("✓ Setup complete!")
        
    except Exception as e:
        print(f"✗ Error copying files: {e}")
        return False
    
    finally:
        # Cleanup
        print("\nCleaning up temporary files...")
        if os.path.exists(zip_filename):
            os.remove(zip_filename)
            print(f"✓ Removed {zip_filename}")
        
        if os.path.exists(extract_folder):
            shutil.rmtree(extract_folder)
            print(f"✓ Removed {extract_folder}")
    
    print("\n" + "="*60)
    print("FFmpeg setup completed successfully!")
    print("You can now run the application.")
    print("="*60)
    
    return True

if __name__ == "__main__":
    try:
        success = setup_ffmpeg()
        if not success:
            print("\nSetup failed. You can:")
            print("1. Run this script again")
            print("2. Manually download FFmpeg from: https://ffmpeg.org/download.html")
            print("3. Extract and copy ffmpeg.exe, ffplay.exe, ffprobe.exe to the project folder")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\nSetup cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        sys.exit(1)