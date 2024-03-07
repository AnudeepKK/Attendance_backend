# Use an official Python runtime as a parent image
FROM python:3.8-slim

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        cmake \
        build-essential \
        libboost-all-dev \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip, setuptools
RUN pip install --upgrade pip setuptools

# Install additional Python packages
RUN pip install cmake dlib face_recognition

# Copy requirements.txt to the container
COPY requirements.txt .

# Install Python dependencies from requirements.txt
RUN pip install -r requirements.txt

# Set the working directory in the container
WORKDIR /usr/src/app

# Copy the rest of the application code to the container
COPY . .

# Command to run your application
CMD ["python", "app.py"]
