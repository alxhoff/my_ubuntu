import subprocess
import os
import sys
import re
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Define image and container names
IMAGE_NAME = "my_ubuntu_image"
UPDATED_IMAGE_NAME = "my_ubuntu_image_updated"
CONTAINER_NAME = "my_ubuntu_container"

# Define paths
current_dir = os.path.abspath(os.path.dirname(__file__))
volume_host_path = os.path.join(current_dir, "volume")  # Host path to "volume" folder
volume_container_path = "/data"  # Path inside the container
docker_home_host_path = os.path.join(current_dir, "docker_home")

# Define paths for SDK Manager volume
sdk_manager_host_path = os.path.join(current_dir, "sdk_manager")  # Host path to "sdk_manager" folder
sdk_manager_container_path = "/sdk_manager"  # Path inside the container

# Vendor and Product ID for the target USB device
TARGET_VENDOR_ID = "0955"
TARGET_PRODUCT_ID = "7023"

# Calculate half of the available CPU cores
num_cores = os.cpu_count()
half_cores = max(1, num_cores // 2)  # Ensure at least 1 core

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

def image_exists(image_name):
    """Check if a Docker image exists locally."""
    try:
        subprocess.run(["docker", "inspect", "--type=image", image_name], check=True, stdout=subprocess.DEVNULL)
        return True
    except subprocess.CalledProcessError:
        return False

def build_image():
    """Build the Docker image."""
    logging.info("Building the Docker image...")
    try:
        # Remove old updated image if it exists
        logging.info("Removing old updated Docker image if it exists...")
        subprocess.run(["docker", "rmi", "-f", UPDATED_IMAGE_NAME], check=False)

        build_command = ["docker", "build", "-t", IMAGE_NAME, "."]
        subprocess.run(build_command, check=True)
        logging.info("Docker image built successfully.")
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to build Docker image: {e}")

def commit_container():
    """Commit the running Docker container to a new image."""
    logging.info(f"Committing container '{CONTAINER_NAME}' to a new image '{UPDATED_IMAGE_NAME}'...")
    try:
        commit_command = ["docker", "commit", CONTAINER_NAME, UPDATED_IMAGE_NAME]
        subprocess.run(commit_command, check=True)
        logging.info(f"Container '{CONTAINER_NAME}' committed successfully as '{UPDATED_IMAGE_NAME}'.")
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to commit container: {e}")

def run_shell(device_paths=None, use_updated_image=False):
    """Run the Docker container with volume mounted, USB devices (if found), and start an interactive shell."""
    # Determine which image to use based on the availability of the updated image
    if use_updated_image and image_exists(UPDATED_IMAGE_NAME):
        image_to_use = UPDATED_IMAGE_NAME
    else:
        image_to_use = IMAGE_NAME

    logging.info(f"Running the Docker container '{image_to_use}' with volume mounted and GUI support...")

    run_command = [
        "docker", "run", "--rm", "-it",
        "--privileged",  # Add this to give the container additional permissions
        "--name", CONTAINER_NAME,
        "-v", f"{volume_host_path}:{volume_container_path}",  # Mount volume
        "-v", f"{sdk_manager_host_path}:{sdk_manager_container_path}",  # Mount SDK Manager volume
        "-v", f"{docker_home_host_path}:/home/dockeruser",  # Mount the container's home directory
        "-e", "DISPLAY",  # Pass display environment variable
        "-v", "/tmp/.X11-unix:/tmp/.X11-unix",  # Mount X11 socket
        f"--cpus={half_cores}",  # Limit container to half the available cores
    ]

    # Add the USB devices if found
    if device_paths:
        for device_path in device_paths:
            run_command += ["--device", device_path]

    run_command.append(image_to_use)
    run_command.append("bash")  # Launches into a terminal in the container

    try:
        # Allow local connections to the X server
        subprocess.run(["xhost", "+local:docker"], check=True)
        subprocess.run(run_command, check=True)
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to run Docker container: {e}")
    finally:
        # Revoke X server permissions after container stops
        subprocess.run(["xhost", "-local:docker"], check=True)

def run_desktop():
    """Run the Docker container and start the desktop environment with VNC support."""
    logging.info(f"Running the Docker container '{IMAGE_NAME}' in desktop mode...")

    run_command = [
        "docker", "run", "--rm", "-it",
        "--privileged",
        "--name", CONTAINER_NAME,
        "-v", f"{volume_host_path}:{volume_container_path}",
        "-v", f"{sdk_manager_host_path}:{sdk_manager_container_path}",
        "-v", f"{docker_home_host_path}:/home/dockeruser",
        "-e", "DISPLAY=:0",
        f"--cpus={half_cores}",  # Limit container to half the available cores
        "-p", "5900:5900",  # Expose VNC port
        IMAGE_NAME,
        "bash", "-c", "Xvfb :0 -screen 0 1024x768x24 & x11vnc -display :0 -forever -passwdfile /etc/vnc/passwd & gnome-session"
    ]

    try:
        subprocess.run(run_command, check=True)
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to run Docker container in desktop mode: {e}")

def main():
    # Ensure the volume directories exist
    os.makedirs(volume_host_path, exist_ok=True)
    os.makedirs(sdk_manager_host_path, exist_ok=True)
    os.makedirs(docker_home_host_path, exist_ok=True)

    # Check for arguments
    if len(sys.argv) < 2:
        logging.error("Usage: python3 run_docker.py <build|shell|commit|desktop> [optional: package1 package2 ...]")
        sys.exit(1)

    # Parse the argument
    command = sys.argv[1].lower()

    # Install additional packages if provided
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

