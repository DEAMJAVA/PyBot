import subprocess
import sys
from importlib.metadata import distributions  # Python 3.8+

def uninstall_all_packages():
    protected = {"pip", "wheel"}
    packages = [dist.metadata["Name"] for dist in distributions()]
    packages_to_remove = [pkg for pkg in packages if pkg and pkg not in protected]

    if not packages_to_remove:
        print("No removable packages found.")
        return

    print(f"Uninstalling {len(packages_to_remove)} packages...")
    subprocess.call([sys.executable, "-m", "pip", "uninstall", "-y", *packages_to_remove])

if __name__ == "__main__":
    uninstall_all_packages()
