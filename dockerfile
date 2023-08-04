# Use an official Python base image with the desired version
FROM python:3.11.4-slim-bullseye

# Set environment variable to avoid interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Set the working directory inside the container
WORKDIR /usr/src/app

# Copy only the requirements.txt file first to leverage Docker layer caching
COPY requirements.txt .

# Install FFmpeg and Firefox without recommended packages
RUN apt-get update && apt-get install -y --no-install-recommends --no-install-suggests \
    ffmpeg \
    firefox-esr \
    fortune-mod \
    # Clean up after package installation
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Install Python dependencies from the requirements.txt file
RUN python -m pip install --upgrade pip \
    && pip install --no-cache-dir --no-compile -r requirements.txt \
    # Clear pip cache after installing requirements
    && pip cache purge 

# Copy the rest of the application files into the working directory
COPY . .

# Run the bot when the container starts
CMD ["python", "main.py"]