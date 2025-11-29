FROM python:3.11-slim

# Install ffmpeg
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application
COPY silent_sense.py .

# Set default environment variables
ENV STREAM_URL=""
ENV SILENCE_THRESHOLD="-60"
ENV SILENCE_TIMEOUT="10"
ENV UPTIME_KUMA_URL=""
ENV CHECK_INTERVAL="5"
ENV DEBUG="false"

# Run the script
ENTRYPOINT ["python", "silent_sense.py"]
