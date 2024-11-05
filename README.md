# Run Docker Utility - README

## Overview
This Python script (`run_docker.py`) helps you manage Docker images and containers for your development environment. It provides functionalities for building Docker images, running interactive shells within Docker containers, and saving any changes made to containers by committing them to new images.

### Features:
- **Build Docker Image**: Create the initial Docker image from a Dockerfile.
- **Run Container Shell**: Start an interactive shell inside a Docker container, including options to mount volumes and use GUI support.
- **Commit Changes to New Image**: Save the current state of the container as a new Docker image, making any changes persistent.

## Requirements
- Docker installed and running.
- Python 3 installed.
- The script and Dockerfile are in the same directory.

## Usage
The `run_docker.py` script supports the following commands:

### 1. Build the Docker Image
Use this command to build the initial Docker image as defined in your Dockerfile.

```sh
python3 run_docker.py build [optional: package1 package2 ...]
```
- **Optional Packages**: You can specify additional Python packages to be installed during the build process by providing their names.

### 2. Run the Docker Container with Shell Access
Launch an interactive shell inside the Docker container. If a newer image has been created using the `commit` command, it will use that version.

```sh
python3 run_docker.py shell
```
- **Volume Mounting**: By default, the script will mount a host directory (`volume`) to `/data` inside the container and an SDK Manager folder to `/sdk_manager`.
- **USB Device Detection**: Automatically detects USB devices with specific Vendor and Product IDs and mounts them inside the container.
- **GUI Support**: The container supports GUI applications using X11 forwarding.

### 3. Commit the Current Container State
After making changes inside a running container, use the `commit` command to save those changes to a new Docker image (`my_ubuntu_image_updated`). This will allow the next `shell` session to use this updated image.

```sh
python3 run_docker.py commit
```
- **Commit Changes**: This command commits the current container to a new Docker image and sets a flag so that future `shell` commands use this updated image.

## Detailed Workflow
1. **Build the Docker Image**
   - Run the following command to build your Docker image:
     ```sh
     python3 run_docker.py build
     ```
   - Optionally, specify additional packages to be installed during the build.

2. **Start the Container and Make Changes**
   - Use the following command to start a container and access an interactive shell:
     ```sh
     python3 run_docker.py shell
     ```
   - Make any desired changes inside the container (e.g., install additional software, modify configurations).

3. **Save Changes by Committing**
   - Once you've made changes that you want to persist, use the following command to commit the current state of the container to a new image:
     ```sh
     python3 run_docker.py commit
     ```
   - The next time you run `python3 run_docker.py shell`, the updated image (`my_ubuntu_image_updated`) will be used.

## Additional Information
- **Privileged Mode**: The container is run in privileged mode to handle namespace changes and to properly support some tools like SDK Manager.
- **Flag for Updated Image**: The script uses a flag file (`updated_image_flag`) to determine whether to use the updated image or the original one when running the container.

## Example Workflow
1. Build the image:
   ```sh
   python3 run_docker.py build
   ```
2. Run the container and modify it as needed:
   ```sh
   python3 run_docker.py shell
   ```
3. After making changes, commit the container:
   ```sh
   python3 run_docker.py commit
   ```
4. Run the updated container with:
   ```sh
   python3 run_docker.py shell
   ```

## Troubleshooting
- **Namespace Errors**: The script runs containers with `--privileged` mode to handle namespace requirements.
- **X Server Permissions**: Make sure to run `xhost +local:docker` on your host to allow the Docker container to use your display server. Don't forget to revoke permissions with `xhost -local:docker` when you're done.

