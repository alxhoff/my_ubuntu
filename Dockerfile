# Start with the Ubuntu base image
FROM ubuntu:22.04

# Set environment variables if needed
ENV DEBIAN_FRONTEND=noninteractive

# Update and install necessary packages
RUN apt-get update && \
    apt-get install -y \
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
    sudo \
    libgconf-2-4 \
    && rm -rf /var/lib/apt/lists/*

# Copy and install NVIDIA SDK Manager from sdk_manager folder
COPY ./sdk_manager/*.deb /tmp/sdkmanager.deb
RUN apt-get update && apt-get install -y /tmp/sdkmanager.deb && rm /tmp/sdkmanager.deb

# Create a persistent data directory
RUN mkdir -p /data

# Create a new user (e.g., 'dockeruser') with sudo privileges
RUN useradd -m -s /bin/bash dockeruser && \
    echo "dockeruser:dockeruser" | chpasswd && \
    adduser dockeruser sudo

# Set working directory
WORKDIR /data

# Change ownership of the working directory to the new user
RUN chown -R dockeruser:dockeruser /data

# Switch to the new user
USER dockeruser

# Set default entrypoint to bash
CMD ["bash"]
