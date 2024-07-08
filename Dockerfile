FROM python:3.10.12

# stdout and stderr streams directly
ENV PYTHONUNBUFFERED=1
# Do not write .pyc bytecode files to disk
ENV PYTHONDONTWRITEBYTECODE=1

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libegl1 \
    libopencv-dev \
    build-essential \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libxkbcommon0 \
    libwayland-client0 \
    libwayland-cursor0 \
    libwayland-egl1 \
    qtwayland5 \
    dbus-x11 \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory in the container
WORKDIR /focuser160

ENV QT_DEBUG_PLUGINS=1

# Install dependencies
COPY requirements.txt /focuser160/
RUN pip install --no-cache-dir -r requirements.txt

ENV LIBGL_ALWAYS_INDIRECT=1
# Copy the rest of the application code to the container
COPY . /focuser160/

# Set the command to run your application
CMD ["python", "main.py"]