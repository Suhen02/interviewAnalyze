# Use a stable Debian-based Python image. Python 3.10 is often more compatible
# for libraries like OpenCV than very new versions like 3.13 due to pre-built wheels.
FROM python:3.10-slim-buster

# Set environment variables for non-interactive apt-get and Python unbuffered output
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100

# Install system dependencies required for ffmpeg, OpenCV, and MediaPipe to build/run.
# build-essential: For compiling Python packages.
# libgl1-mesa-glx: OpenGL library for OpenCV (headless version might still need it for some operations).
# libsm6, libxext6: X11 libraries often required by OpenCV based on underlying dependencies.
# ffmpeg: The core multimedia tool.
# libpq-dev: PostgreSQL client libraries, needed by psycopg2 (used by dj-database-url).
RUN apt-get update && apt-get install -y \
    build-essential \
    libgl1-mesa-glx \
    libsm6 \
    libxext6 \
    ffmpeg \
    libpq-dev \
    git \
    --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*

# Set the working directory in the container
WORKDIR /app

# Copy requirements.txt first to leverage Docker cache
# This means if requirements.txt doesn't change, this step and subsequent pip install
# will use the cached layer, speeding up builds.
COPY requirements.txt /app/

# Install Python dependencies
# Use --no-warn-script-location to avoid warnings about pip scripts not being in PATH
RUN pip install --no-warn-script-location -r requirements.txt

# Copy the rest of your application code
COPY . /app

# Ensure correct permissions for the media directory (where user uploads will go)
# This directory will be created by Django if it doesn't exist, but we ensure permissions
# in case Render's underlying filesystem needs it.
RUN mkdir -p /app/media && chmod -R 775 /app/media

# Expose the port that Gunicorn will listen on
EXPOSE 8000

# Run Django migrations and collect static files during the build process
# Render's "Build Command" in UI will also do this, but adding here makes Dockerfile self-contained.
# python manage.py collectstatic --noinput should be run as part of the build process.
# python manage.py migrate will also run.

# Define the command to run your Django application with Gunicorn
# Render will inject its $PORT environment variable, so Gunicorn binds correctly.
CMD ["gunicorn", "interview_analyzer.wsgi:application", "--bind", "0.0.0.0:$PORT"]

# No Procfile is needed when using a Dockerfile, as the CMD instruction handles the start command.