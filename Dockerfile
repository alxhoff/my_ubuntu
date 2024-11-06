# Start with the Ubuntu base image
FROM ubuntu:20.04

# Set environment variable for noninteractive installs
ENV DEBIAN_FRONTEND=noninteractive

# Install necessary packages for XFCE4, X2Go server, and general development tools
RUN apt-get update && \
    apt-get install -y software-properties-common && \
    add-apt-repository -y ppa:x2go/stable && \
    apt-get update && \
    apt-get install -y \
        xfce4 \
        xfce4-goodies \
        x2goserver x2goserver-xsession \
        openssh-server \
        openssh-client \
        x11vnc \
        xvfb \
        gnome-terminal \
        firefox \
        curl \
        vim \
        git \
        build-essential \
        binutils \
        libxml2-utils \
        cpio \
        usbutils \
        python3 \
        python3-pip \
        python3-yaml \
        python3-uinput \
        python3-opengl \
        sudo \
        libgconf-2-4 \
        libxshmfence1 \
        libx11-6 \
        libxcb1 \
        libxrender1 \
        libxtst6 \
        libxfixes3 \
        libxi6 \
        libfontconfig1 \
        libgl1-mesa-glx \
        x11-xserver-utils \
        libnss3 \
        libatk-bridge2.0-0 \
        libgtk-3-0 \
        libgbm1 \
    && rm -rf /var/lib/apt/lists/*

# Create a new user with sudo privileges
ARG USER_ID=1000
ARG GROUP_ID=1000

RUN groupadd -g $GROUP_ID dockeruser && \
    useradd -m -u $USER_ID -g $GROUP_ID -s /bin/bash dockeruser && \
    echo "dockeruser:dockeruser" | chpasswd && \
    adduser dockeruser sudo

# Switch to dockeruser for specific tasks
USER dockeruser

# Set up X2Go session
RUN echo "xfce4-session" > /home/dockeruser/.xsession

# Ensure Downloads and nvidia directories exist
RUN mkdir -p /home/dockeruser/Downloads /home/dockeruser/nvidia

# Switch back to root user
USER root

# Ensure ownership of /home/dockeruser is correct
RUN chown -R dockeruser:dockeruser /home/dockeruser

# Copy and install NVIDIA SDK Manager from sdk_manager folder
COPY ./sdk_manager /tmp/sdk_manager
RUN if [ -f /tmp/sdk_manager/*.deb ]; then \
        apt-get update && \
        apt-get install -y /tmp/sdk_manager/*.deb && \
        rm -f /tmp/sdk_manager/*.deb; \
    else \
        echo "No SDK Manager .deb files found"; \
    fi

# Expose SSH port
EXPOSE 22

# Generate SSH host keys
RUN ssh-keygen -A

# Set correct permissions for SSH directories and keys
RUN chmod 700 /etc/ssh && \
    chmod 600 /etc/ssh/ssh_host_*_key

# Set correct permissions for sshd_config
RUN chmod 644 /etc/ssh/sshd_config && \
    chown root:root /etc/ssh/sshd_config

# Set up SSH
RUN mkdir -p /var/run/sshd && \
    echo 'PasswordAuthentication yes' >> /etc/ssh/sshd_config && \
    echo 'X11Forwarding yes' >> /etc/ssh/sshd_config && \
    echo 'X11UseLocalhost no' >> /etc/ssh/sshd_config

# Set the working directory
WORKDIR /home/dockeruser

# Start SSH service
CMD ["/usr/sbin/sshd", "-D", "-e"]

