# Use an official Python runtime as a parent image
FROM python:3.10-slim


# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvbin --link
ENV PATH="/uvbin:${PATH}"

# Set the working directory to /app
WORKDIR /app

# Install git and wget (required for pip install and downloading CES lib)
RUN apt-get update && apt-get install -y git wget && rm -rf /var/lib/apt/lists/*

# Install CES Client Library (Pre-requisite) - Cached Layer
RUN URL="https://storage.googleapis.com/gassets-api-ai/" && \
    URL="${URL}ces-client-libraries/v1beta/ces-v1beta-py.tar" && \
    wget $URL && \
    uv pip install --system ces-v1beta-py.tar --quiet && \
    rm ces-v1beta-py.tar

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install dependencies and local CLI wheel
RUN uv pip install --system --no-cache-dir -r requirements.txt &&     uv pip install --system cxas-scrapi

# Copy the agent code into the container
COPY . .

# Set the entrypoint to cxas-scrapi
ENTRYPOINT ["cxas"]
