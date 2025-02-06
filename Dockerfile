# Use a slim version of Python for a smaller base image
FROM python:3.10-slim AS builder

# Install system dependencies (only what's necessary)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Copy only the necessary files (like requirements.txt first for caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Use a new image to keep the final image size small
FROM python:3.10-slim AS final

# Install system dependencies in the final image
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory in the final image
WORKDIR /app

# Copy the installed Python packages from the builder stage
COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages

# Copy the application code from the builder stage
COPY --from=builder /app /app

# Ensure the /usr/local/bin directory is in the PATH
ENV PATH="/usr/local/bin:${PATH}"

#Expose Port
Expose 8080
# Command to run your application using python -m to avoid PATH issues
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
