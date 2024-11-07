# x11docker Ubuntu MATE Desktop with SDK Manager Support

This repository provides a setup for running an Ubuntu MATE desktop environment in a Docker container using `x11docker`. It includes support for custom desktop applications and USB device access, as well as the option to install NVIDIA SDK Manager for embedded development. The setup uses `run_docker.py` as a launch script to manage Docker image building, container starting, and committing changes.

## Requirements

- Docker
- x11docker
- Python 3

## Setup

1. **Clone the Repository:**
   ```bash
   git clone <repository-url>
   cd <repository-folder>
   ```

2. **Add NVIDIA SDK Manager `.deb` (Optional):**
   - Place the SDK Manager `.deb` file in the `sdk_manager` directory if required.

## Usage

The main interface is the `run_docker.py` script, which accepts the following commands:

### Commands

1. **Build the Docker Image**:
   ```bash
   python3 run_docker.py build [package1 package2 ...]
   ```
   - Builds the Docker image with the Ubuntu MATE desktop and installs additional specified packages.
   - Creates a `requirements.txt` file if additional packages are specified, storing package names for tracking.

2. **Run the Desktop Environment**:
   ```bash
   python3 run_docker.py desktop
   ```
   - Starts the Ubuntu MATE desktop environment in a Docker container using `x11docker`.
   - Uses `x11docker` flags for secure desktop mode with optional device support for NVIDIA SDK tools.

3. **Commit the Container**:
   ```bash
   python3 run_docker.py commit
   ```
   - Commits the current running container state as a new Docker image (`my_ubuntu_image_updated`), allowing you to save modifications.
   - Sets a flag file to use this updated image on subsequent runs.

### Dockerfile

The Dockerfile sets up an Ubuntu Focal environment with:

- MATE desktop environment.
- Proxy settings support.
- Utilities and dependencies required for running desktop applications and NVIDIA SDK Manager (optional).

### Launch Script (run_docker.py)

The `run_docker.py` script automates the setup and management of the container with the following main features:

- **USB Device Detection**: Finds and connects USB devices matching the specified Vendor and Product ID for the target hardware.
- **Conditional Image Update**: Builds and commits the container as an updated image if the `commit` command is used.
- **x11docker Integration**: Runs the container using `x11docker` with user and desktop options, allowing graphical desktop access and efficient resource utilization.

#### Notable Flags and Options

- **`--desktop`**: Runs in desktop mode with `x11docker`.
- **`--no-entrypoint`**: Avoids Docker entrypoint conflicts.
- **`--limit`**: Limits CPU usage to half of available cores.
- **`--home`**: Mounts a persistent home directory within the container.
- **USB Device Paths**: Detects and attaches specific USB devices to the container.
- **Optional Privileges**: Uses `--privileged` and `--newprivileges` as required by SDK Manager.

## Example Usage

1. **Build the Image with Extra Packages**:
   ```bash
   python3 run_docker.py build vim curl
   ```

2. **Run the Desktop**:
   ```bash
   python3 run_docker.py desktop
   ```

3. **Commit Changes to Image**:
   ```bash
   python3 run_docker.py commit
   ```

4. **Run Updated Desktop**:
   ```bash
   python3 run_docker.py desktop
   ```

## Notes

- **NVIDIA SDK Manager**: If using SDK Manager, ensure that the `.deb` file is placed in the `sdk_manager` folder before building.
- **Permissions**: Ensure proper permissions for the specified USB device and user access within the container.

## Troubleshooting

- **Error Running SDK Manager**: If you encounter namespace permission errors, ensure `x11docker` is run with `--privileged` or specific `--cap-add` flags as needed.
- **No USB Devices Detected**: Ensure the target USB device is connected and that its Vendor and Product ID match `TARGET_VENDOR_ID` and `TARGET_PRODUCT_ID`.


