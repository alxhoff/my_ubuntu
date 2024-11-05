import subprocess
import os
import sys
import re
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Define image and container names
IMAGE_NAME = "my_ubuntu_image"
CONTAINER_NAME = "my_ubuntu_container"

# Define paths
current_dir = os.path.abspath(os.path.dirname(__file__))
volume_host_path = os.path.join(current_dir, "volume")  # Host path to "volume" folder
volume_container_path = "/data"  # Path inside the container

# Define paths for SDK Manager volume
sdk_manager_host_path = os.path.join(current_dir, "sdk_manager")  # Host path to "sdk_manager" folder
sdk_manager_container_path = "/sdk_manager"  # Path inside the container

# Vendor and Product ID for the target USB device
TARGET_VENDOR_ID = "0955"
TARGET_PRODUCT_ID = "7023"

def find_usb_devices():
    """Find the USB devices paths based on Vendor and Product ID."""
    try:
        # Run lsusb to find the devices by Vendor ID and Product ID
        lsusb_output = subprocess.check_output(["lsusb"]).decode("utf-8")

        # Search for all matching devices
        matches = re.finditer(
            rf"Bus (\d{{3}}) Device (\d{{3}}): ID {TARGET_VENDOR_ID}:{TARGET_PRODUCT_ID}", lsusb_output
        )

        device_paths = []
        for match in matches:
            bus = match.group(1)
            device = match.group(2)
            device_path = f"/dev/bus/usb/{bus}/{device}"
            logging.info(f"Found device at {device_path}")
            device_paths.append(device_path)

        if not device_paths:
            logging.warning("No USB devices found.")

        return device_paths
    except subprocess.CalledProcessError as e:
        logging.error(f"Error running lsusb command: {e}")
        return []

def build_image():
    """Build the Docker image."""
    logging.info("Building the Docker image...")
    try:
        build_command = ["docker", "build", "-t", IMAGE_NAME, "."]
        subprocess.run(build_command, check=True)
        logging.info("Docker image built successfully.")
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to build Docker image: {e}")

def run_shell(device_paths=None):
    """Run the Docker container with volume mounted, USB devices (if found), and start an interactive shell."""
    logging.info("Running the Docker container with volume mounted...")
    run_command = [
        "docker", "run", "--rm", "-it",
        "--name", CONTAINER_NAME,
        "-v", f"{volume_host_path}:{volume_container_path}",  # Mount volume
        "-v", f"{sdk_manager_host_path}:{sdk_manager_container_path}",  # Mount SDK Manager volume
    ]

    # Add the USB devices if found
    if device_paths:
        for device_path in device_paths:
            run_command += ["--device", device_path]

    run_command.append(IMAGE_NAME)
    run_command.append("bash")  # Launches into a terminal in the container

    try:
        subprocess.run(run_command, check=True)
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to run Docker container: {e}")

def main():
    # Ensure the volume directory exists
    if not os.path.isdir(volume_host_path):
        os.makedirs(volume_host_path)
        logging.info(f"Created missing volume directory at {volume_host_path}")

    # Ensure the sdk_manager directory exists
    if not os.path.isdir(sdk_manager_host_path):
        os.makedirs(sdk_manager_host_path)
        logging.info(f"Created missing sdk_manager directory at {sdk_manager_host_path}")

    # Check for arguments
    if len(sys.argv) < 2:
        logging.error("Usage: python3 run_docker.py <build|shell> [optional: package1 package2 ...]")
        sys.exit(1)

    # Parse the argument
    command = sys.argv[1].lower()

    # Install additional packages if provided
    additional_packages = sys.argv[2:] if len(sys.argv) > 2 else []

    if command == "build":
        if additional_packages:
            # Create requirements.txt for additional packages
            requirements_path = os.path.join(current_dir, "requirements.txt")
            with open(requirements_path, "w") as req_file:
                for package in additional_packages:
                    req_file.write(package + "\n")
            logging.info(f"Created requirements.txt with additional packages: {additional_packages}")

        build_image()
    elif command == "shell":
        device_paths = find_usb_devices()
        run_shell(device_paths)
    else:
        logging.error("Invalid command. Use 'build' to build the image or 'shell' to start a shell.")
        sys.exit(1)

if __name__ == "__main__":
    main()

