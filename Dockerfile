# Start with the Ubuntu base image
FROM ubuntu:focal
ENV SHELL=/bin/bash

# Handle proxy settings if needed
RUN bash -c 'if test -n "$http_proxy"; then echo "Acquire::http::proxy \"$http_proxy\";" > /etc/apt/apt.conf.d/99proxy; else echo "Using direct network connection."; fi'

# Desktop stuff
RUN apt-get update && \
    env DEBIAN_FRONTEND=noninteractive apt-get install -y \
      dbus-x11 \
      procps \
      psmisc && \
    env DEBIAN_FRONTEND=noninteractive apt-get install -y \
      xdg-utils \
      xdg-user-dirs \
      menu-xdg \
      mime-support \
      desktop-file-utils \
      bash-completion && \
    env DEBIAN_FRONTEND=noninteractive apt-get install -y \
      mesa-utils-extra \
      libxv1 \
      sudo \
      lsb-release

# My stuff
RUN apt-get update && \
    env DEBIAN_FRONTEND=noninteractive apt-get install -y \
    apt-utils

ENV LANG en_US.UTF-8
RUN echo $LANG UTF-8 > /etc/locale.gen && \
    env DEBIAN_FRONTEND=noninteractive apt-get install -y \
     locales && locale-gen $LANG || update-locale --reset LANG=$LANG

# Ubuntu MATE desktop
RUN env DEBIAN_FRONTEND=noninteractive apt-get install -y \
      ubuntu-mate-desktop^;

# Remove screensaver
RUN env DEBIAN_FRONTEND=noninteractive apt-get purge -y mate-screensaver && \
    env DEBIAN_FRONTEND=noninteractive apt-get autoremove --purge -y && \
    rm -rf /var/lib/apt/lists/*

# Copy and install NVIDIA SDK Manager from sdk_manager folder
COPY ./sdk_manager /tmp/sdk_manager
RUN if ls /tmp/sdk_manager/*.deb 1> /dev/null 2>&1; then \
        apt-get update && \
        apt-get install -y /tmp/sdk_manager/*.deb && \
        rm -f /tmp/sdk_manager/*.deb && \
        rm -rf /var/lib/apt/lists/*; \
    else \
        echo "No SDK Manager .deb files found"; \
    fi

# # Create a new user with sudo privileges
# ARG USER_ID=1000
# ARG GROUP_ID=1000
# RUN groupadd -g $GROUP_ID dockeruser && \
#     useradd -m -u $USER_ID -g $GROUP_ID -s /bin/bash dockeruser && \
#     echo "dockeruser:dockeruser" | chpasswd && \
#     adduser dockeruser sudo && \
#     echo "dockeruser ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers
#
# # Set the working directory
# WORKDIR /home/dockeruser
#
# # Switch to the new user
# USER dockeruser

# Start the MATE desktop session
CMD ["mate-session"]

