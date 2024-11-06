import subprocess
import os
import sys
import re
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Define image and container names
IMAGE_NAME = "my_ubuntu_desktop"
UPDATED_IMAGE_NAME = "my_ubuntu_image_updated"
CONTAINER_NAME = "my_ubuntu_container"

# Define paths
current_dir = os.path.abspath(os.path.dirname(__file__))
volume_host_path = os.path.join(current_dir, "volume")
volume_container_path = "/data"
sdk_manager_host_path = os.path.join(current_dir, "sdk_manager")
sdk_manager_container_path = "/sdk_manager"

# Paths for the specific directories to mount
downloads_host_path = os.path.join(current_dir, "Downloads")
nvidia_host_path = os.path.join(current_dir, "nvidia")
downloads_container_path = "/home/dockeruser/Downloads"
nvidia_container_path = "/home/dockeruser/nvidia"

# Vendor and Product ID for the target USB device
TARGET_VENDOR_ID = "0955"
TARGET_PRODUCT_ID = "7023"

# Calculate half of the available CPU cores
num_cores = os.cpu_count()
half_cores = max(1, num_cores // 2)

def find_usb_devices():
    try:
        lsusb_output = subprocess.check_output(["lsusb"]).decode("utf-8")
        matches = re.finditer(
            rf"Bus (\d{{3}}) Device (\d{{3}}): ID {TARGET_VENDOR_ID}:{TARGET_PRODUCT_ID}", lsusb_output
        )

        device_paths = [f"/dev/bus/usb/{match.group(1)}/{match.group(2)}" for match in matches]
        if device_paths:
            for device_path in device_paths:
                logging.info(f"Found device at {device_path}")
        else:
            logging.warning("No USB devices found.")
        return device_paths
    except subprocess.CalledProcessError as e:
        logging.error(f"Error running lsusb command: {e}")
        return []

def image_exists(image_name):
    try:
        subprocess.run(["docker", "inspect", "--type=image", image_name], check=True, stdout=subprocess.DEVNULL)
        return True
    except subprocess.CalledProcessError:
        return False

def remove_existing_container():
    """Remove the existing container if it's already running."""
    try:
        subprocess.run(["docker", "rm", "-f", CONTAINER_NAME], check=True)
        logging.info(f"Stopped and removed existing container '{CONTAINER_NAME}'.")
    except subprocess.CalledProcessError:
        logging.info(f"No existing container named '{CONTAINER_NAME}' was found.")

def build_image():
    logging.info("Building the Docker image...")
    try:
        logging.info("Removing old updated Docker image if it exists...")
        subprocess.run(["docker", "rmi", "-f", UPDATED_IMAGE_NAME], check=False)

        build_command = [
            "docker", "build",
            "--build-arg", f"USER_ID={os.getuid()}",
            "--build-arg", f"GROUP_ID={os.getgid()}",
            "-t", IMAGE_NAME, "."
        ]
        subprocess.run(build_command, check=True)
        logging.info("Docker image built successfully.")
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to build Docker image: {e}")

def commit_container():
    logging.info(f"Committing container '{CONTAINER_NAME}' to a new image '{UPDATED_IMAGE_NAME}'...")
    try:
        commit_command = ["docker", "commit", CONTAINER_NAME, UPDATED_IMAGE_NAME]
        subprocess.run(commit_command, check=True)
        logging.info(f"Container '{CONTAINER_NAME}' committed successfully as '{UPDATED_IMAGE_NAME}'.")
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to commit container: {e}")

def run_shell(device_paths=None, use_updated_image=False):
    image_to_use = UPDATED_IMAGE_NAME if use_updated_image and image_exists(UPDATED_IMAGE_NAME) else IMAGE_NAME
    logging.info(f"Running the Docker container '{image_to_use}' with volume mounted...")

    run_command = [
        "docker", "run", "--rm", "-it",
        "--privileged",
        "--name", CONTAINER_NAME,
        "-v", f"{volume_host_path}:{volume_container_path}",
        "-v", f"{sdk_manager_host_path}:{sdk_manager_container_path}",
        "-v", f"{downloads_host_path}:{downloads_container_path}",
        "-v", f"{nvidia_host_path}:{nvidia_container_path}",
        f"--cpus={half_cores}",
        image_to_use,
        "bash"
    ]

    if device_paths:
        for device_path in device_paths:
            run_command += ["--device", device_path]

    try:
        subprocess.run(run_command, check=True)
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to run Docker container: {e}")

def run_desktop():
    """Run the Docker container and set up X2Go server."""
    logging.info(f"Running the Docker container '{IMAGE_NAME}' in desktop mode using X2Go...")

    # Ensure no container with the same name is running
    remove_existing_container()

    run_command = [
        "docker", "run",
        "--privileged",
        "--name", CONTAINER_NAME,
        "-v", f"{volume_host_path}:{volume_container_path}",
        "-v", f"{sdk_manager_host_path}:{sdk_manager_container_path}",
        "-v", f"{downloads_host_path}:{downloads_container_path}",
        "-v", f"{nvidia_host_path}:{nvidia_container_path}",
        "-p", "2222:22",
        f"--cpus={half_cores}",
        IMAGE_NAME
    ]

    # Start the container and capture the ID
    try:
        container_id = subprocess.check_output(run_command).decode().strip()
        logging.info(f"Docker container started with ID {container_id}")
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to run Docker container: {e}")
        return

    logging.info("Container started successfully.")
    logging.info("You can connect via X2Go client to localhost on port 2222.")
    logging.info("Use username 'dockeruser' and password 'dockeruser'.")

def main():
    os.makedirs(volume_host_path, exist_ok=True)
    os.makedirs(sdk_manager_host_path, exist_ok=True)
    os.makedirs(downloads_host_path, exist_ok=True)
    os.makedirs(nvidia_host_path, exist_ok=True)

    if len(sys.argv) < 2:
        logging.error("Usage: python3 run_docker.py <build|shell|commit|desktop> [optional: package1 package2 ...]")
        sys.exit(1)

    command = sys.argv[1].lower()
    additional_packages = sys.argv[2:] if len(sys.argv) > 2 else []

    if command == "build":
        if additional_packages:
            requirements_path = os.path.join(current_dir, "requirements.txt")
            with open(requirements_path, "w") as req_file:
                for package in additional_packages:
                    req_file.write(package + "\n")
            logging.info(f"Created requirements.txt with additional packages: {additional_packages}")
        build_image()
    elif command == "shell":
        use_updated_image = os.path.exists(f"{current_dir}/updated_image_flag")
        device_paths = find_usb_devices()
        run_shell(device_paths=device_paths, use_updated_image=use_updated_image)
    elif command == "commit":
        commit_container()
        with open(f"{current_dir}/updated_image_flag", "w") as flag_file:
            flag_file.write("use_updated_image")
    elif command == "desktop":
        run_desktop()
    else:
        logging.error("Invalid command. Use 'build', 'shell', 'commit', or 'desktop'.")
        sys.exit(1)

if __name__ == "__main__":
    main()

