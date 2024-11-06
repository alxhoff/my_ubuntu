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

# Define paths
current_dir = os.path.abspath(os.path.dirname(__file__))
sdk_manager_host_path = os.path.join(current_dir, "sdk_manager")

# Vendor and Product ID for the target USB device
TARGET_VENDOR_ID = "0955"
TARGET_PRODUCT_ID = "7023"

# Calculate half of the available CPU cores
num_cores = os.cpu_count()
half_cores = max(1, num_cores // 2)
cpu_limit = half_cores / num_cores  # This will be a fraction between 0 and 1

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
    logging.info(f"Committing container to a new image '{UPDATED_IMAGE_NAME}'...")
    try:
        # Get the container ID of the last x11docker container
        container_id = subprocess.check_output(
            ["docker", "ps", "-lq", "--filter", "ancestor=" + IMAGE_NAME]
        ).decode().strip()

        if not container_id:
            logging.error("No running container found to commit.")
            return

        commit_command = ["docker", "commit", container_id, UPDATED_IMAGE_NAME]
        subprocess.run(commit_command, check=True)
        logging.info(f"Container committed successfully as '{UPDATED_IMAGE_NAME}'.")
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to commit container: {e}")

def run_desktop(use_updated_image=False):
    """Run the Docker container using x11docker."""
    image_to_use = UPDATED_IMAGE_NAME if use_updated_image and image_exists(UPDATED_IMAGE_NAME) else IMAGE_NAME
    logging.info(f"Running the Docker container '{image_to_use}' with x11docker in desktop mode...")

    # Create the home directory if it doesn't exist
    home_dir = os.path.join(current_dir, "home")
    os.makedirs(home_dir, exist_ok=True)

    # Build the x11docker command
    run_command = [
        "x11docker",
        "--desktop",
        "--no-entrypoint",
        "--limit=" + str(cpu_limit),
        f"--home={home_dir}",
        f"--user={os.getuid()}:{os.getgid()}",
        "--sudouser=nopasswd",
    ]

    # Add device paths if needed
    device_paths = find_usb_devices()
    if device_paths:
        for device_path in device_paths:
            run_command += [f"--device={device_path}"]

    # Add the image name
    run_command.append(image_to_use)

    try:
        subprocess.run(run_command, check=True)
        logging.info("Container started successfully.")
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to run Docker container with x11docker: {e}")

def main():
    sdk_manager_host_path = os.path.join(current_dir, "sdk_manager")
    os.makedirs(sdk_manager_host_path, exist_ok=True)

    if len(sys.argv) < 2:
        logging.error("Usage: python3 run_docker.py <build|desktop|commit> [optional: package1 package2 ...]")
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
    elif command == "desktop":
        use_updated_image = os.path.exists(f"{current_dir}/updated_image_flag")
        run_desktop(use_updated_image=use_updated_image)
    elif command == "commit":
        commit_container()
        with open(f"{current_dir}/updated_image_flag", "w") as flag_file:
            flag_file.write("use_updated_image")
    else:
        logging.error("Invalid command. Use 'build', 'desktop', or 'commit'.")
        sys.exit(1)

if __name__ == "__main__":
    main()

