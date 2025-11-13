import sys
import os
import re
import requests

API_BASE = "https://pybotapi.javanodes.in"


def get_version_components():
    with open("main.py", "r", encoding='utf-8') as f:
        content = f.read()

    match = re.search(r"current_version\s*=\s*'V(\d+\.\d+)-dev-(\d+)\.(\d+)'", content)
    if not match:
        raise ValueError("Version string not found or invalid format in main.py")

    main_version, dev_major, dev_minor = match.groups()
    return main_version, int(dev_major), int(dev_minor), content


def update_version(flag):
    main_version, dev_major, dev_minor, content = get_version_components()

    main_major, main_minor = map(int, main_version.split('.'))

    if flag == "-d":  # Increment dev minor version
        dev_minor += 1
    elif flag == "-D":  # Increment dev major version, reset dev minor
        dev_major += 1
        dev_minor = 0
    elif flag == "-m":  # Increment main stream minor version, reset dev
        main_minor += 1
        dev_major = 0
        dev_minor = 0
    elif flag == "-M":  # Increment main stream major version, reset minor and dev
        main_major += 1
        main_minor = 0
        dev_major = 0
        dev_minor = 0
    else:
        return  # No version bump requested

    new_main_version = f"{main_major}.{main_minor}"
    new_version = f"V{new_main_version}-dev-{dev_major}.{dev_minor}"

    new_content = re.sub(r"current_version\s*=\s*'[^']+'",
                         f"current_version = '{new_version}'",
                         content)

    with open("main.py", "w", encoding='utf-8') as f:
        f.write(new_content)

    print(f"[VERSION] Updated version to: {new_version}")
    return new_version


def upload_file(file_path, endpoint):
    if not os.path.exists(file_path):
        print(f"[ERROR] File not found: {file_path}")
        return
    with open(file_path, "rb") as f:
        files = {'file': (os.path.basename(file_path), f)}
        response = requests.post(f"{API_BASE}{endpoint}", files=files)
    if response.ok:
        print(f"[OK] Uploaded: {file_path} -> {endpoint}")
    else:
        print(f"[ERROR] Failed to upload {file_path} -> {endpoint}")
        print(response.text)



def strip_dev_suffix(content):
    """Remove -dev-x.y from version string for release builds."""
    return re.sub(r"-dev-\d+\.\d+", "", content)

def upload_content(content: str, filename: str, endpoint: str):
    files = {'file': (filename, content.encode("utf-8"))}
    response = requests.post(f"{API_BASE}{endpoint}", files=files)
    if response.ok:
        print(f"[OK] Uploaded: {filename} -> {endpoint}")
    else:
        print(f"[ERROR] Failed to upload {filename} -> {endpoint}")
        print(response.text)



def main():
    args = sys.argv[1:]
    push_release = "-r" in args
    plugin_name = None
    version_bump_flag = next((arg for arg in args if arg in ("-M", "-m", "-d", "-D")), None)

    # ✅ Always apply version bump if provided
    if version_bump_flag:
        update_version(version_bump_flag)

    # Detect plugin argument
    for arg in args:
        if arg.startswith("-p:"):
            plugin_name = arg.split(":", 1)[1]
        elif arg == "-pall":
            plugin_name = "all"

    # ✅ Only extract version string if pushing release
    version = None
    if push_release:
        main_version, _, _, _ = get_version_components()
        version = f"V{main_version}"

    # Upload logic
    if not plugin_name:
        if push_release:
            _, _, _, content = get_version_components()
            release_content = strip_dev_suffix(content)
            upload_content(release_content, "main.py", f"/release/{version}")
        else:
            upload_file("main.py", "/upload")
    elif plugin_name == "all":
        plugin_dirs = ["plugins"]
        if not push_release and os.path.exists("dev-plugins"):
            plugin_dirs.append("dev-plugins")

        for plugin_dir in plugin_dirs:
            for fname in os.listdir(plugin_dir):
                if fname.endswith(".py"):
                    path = os.path.join(plugin_dir, fname)
                    endpoint = f"/release_plugin/{version}" if push_release else "/upload_plugin"
                    upload_file(path, endpoint)
    else:
        if not push_release and os.path.exists(f"dev-plugins/{plugin_name}.py"):
            path = f"dev-plugins/{plugin_name}.py"
        else:
            path = f"plugins/{plugin_name}.py"

        endpoint = f"/release_plugin/{version}" if push_release else "/upload_plugin"
        upload_file(path, endpoint)


if __name__ == "__main__":
    main()
