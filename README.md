# Docker Build and Run with Persistent Volume

This project provides a Python script, `run_docker.py`, to automate building a Docker image from a `Dockerfile` and running a container with a persistent volume. The volume allows all changes made inside the container to be saved on the host system, making it ideal for development environments.

## Files

- `Dockerfile`: Defines the environment and dependencies for the Docker image.
- `volume/`: A folder used for persistent storage, shared between the host and container. All changes in `/data` inside the container will be saved here.
- `run_docker.py`: Python script that builds the Docker image and launches the container with the volume mounted.

## Requirements

- **Docker**: Make sure Docker is installed and running on your system. You can verify by running `docker --version`.
- **Python 3**: The script requires Python 3 to run.

## Usage

1. **Clone or Download the Repository**:
   Ensure that the `Dockerfile`, `volume/` folder, and `run_docker.py` script are in the same directory.

2. **Prepare the Volume Directory**:
   Make sure there is a `volume/` folder in the same directory as `run_docker.py` and the `Dockerfile`. If the folder doesn’t exist, the script will create it automatically.

3. **Run the Python Script**:
   The script supports two commands: `build` and `shell`.

   - **Build the Docker Image**:

     Use the `build` command to build the Docker image from the `Dockerfile`:

     ```bash
     python3 run_docker.py build
     ```

     This command will create a Docker image named `my_ubuntu_image`.

   - **Start a Shell in the Docker Container**:

     Use the `shell` command to start a Docker container with the volume mounted and open an interactive Bash shell:

     ```bash
     python3 run_docker.py shell
     ```

     This command will:
     - Start a container named `my_ubuntu_container` from the `my_ubuntu_image` image.
     - Mount the `volume/` folder on the host to `/data` in the container, making changes persistent.
     - Open an interactive Bash shell in the container.

4. **Working with the Persistent Volume**:
   Inside the container, you can save files and changes to `/data`. All changes will be saved to the `volume/` folder on your host system, ensuring persistence across container sessions.

5. **Exiting the Container**:
   - To exit the container, type `exit`.
   - The container will automatically stop and be removed (due to the `--rm` flag in the script).
   - The data in `volume/` remains unaffected on the host.

## Customization

- **Image Name**: Change the `IMAGE_NAME` variable in `run_docker.py` to use a custom image name.
- **Container Name**: Adjust `CONTAINER_NAME` to set a different container name.
- **Volume Mount Path**: Modify the `volume_host_path` or `volume_container_path` variables to change the source or target of the volume mount.

## Example

After running the `shell` command, you can create files in `/data` inside the container:

```bash
# Inside the container's Bash shell
echo "Hello, persistent volume!" > /data/hello.txt

