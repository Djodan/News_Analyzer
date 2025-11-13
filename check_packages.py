"""
Package Dependency Checker and Installer for News Analyzer
This module checks for all required packages and installs missing ones.
Should be called before importing any other project modules.
"""

import subprocess
import sys
import importlib.util

def is_package_installed(package_name):
    """Check if a package is installed."""
    spec = importlib.util.find_spec(package_name)
    return spec is not None

def install_package(package_name, import_name=None):
    """
    Install a package using pip.
    
    Args:
        package_name: The name to use with pip install
        import_name: The name to use with import (if different from package_name)
    """
    if import_name is None:
        import_name = package_name
    
    print(f"Installing {package_name}...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
        print(f"✓ {package_name} installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to install {package_name}: {e}")
        return False

def check_and_install_packages():
    """Check all required packages and install missing ones."""
    
    # Dictionary of required packages
    # Format: 'import_name': 'pip_package_name'
    # If import_name == pip_package_name, just use the name
    required_packages = {
        'pytz': 'pytz',
        'openai': 'openai',
    }
    
    print("=" * 60)
    print("NEWS ANALYZER - PACKAGE DEPENDENCY CHECK")
    print("=" * 60)
    
    missing_packages = []
    installed_packages = []
    
    # Check each package
    for import_name, pip_name in required_packages.items():
        if is_package_installed(import_name):
            print(f"✓ {import_name} is already installed")
            installed_packages.append(import_name)
        else:
            print(f"✗ {import_name} is NOT installed")
            missing_packages.append((import_name, pip_name))
    
    # Install missing packages
    if missing_packages:
        print("\n" + "=" * 60)
        print(f"Installing {len(missing_packages)} missing package(s)...")
        print("=" * 60)
        
        failed_installations = []
        for import_name, pip_name in missing_packages:
            success = install_package(pip_name, import_name)
            if not success:
                failed_installations.append(pip_name)
        
        # Report results
        if failed_installations:
            print("\n" + "=" * 60)
            print("⚠ WARNING: Some packages failed to install:")
            for pkg in failed_installations:
                print(f"  - {pkg}")
            print("=" * 60)
            print("Please install them manually using:")
            print(f"  pip install {' '.join(failed_installations)}")
            print("=" * 60)
            return False
        else:
            print("\n" + "=" * 60)
            print("✓ All missing packages installed successfully!")
            print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("✓ All required packages are already installed")
        print("=" * 60)
    
    return True

if __name__ == "__main__":
    # Can be run standalone for testing
    success = check_and_install_packages()
    if not success:
        sys.exit(1)
