# Silent Sense - Radio Stream Silence Monitor

A containerized tool for monitoring online radio streams to detect silence (no audio being played) and alert monitoring systems like Uptime Kuma.

## Features

- **Continuous Monitoring**: Monitors audio streams in real-time using FFmpeg
- **Configurable Thresholds**: Set silence detection threshold (in decibels) and timeout duration
- **Uptime Kuma Integration**: Sends HTTP notifications when silence is detected or audio resumes
- **Docker Support**: Easily deploy anywhere with Docker
- **Robust Error Handling**: Handles stream interruptions and invalid inputs gracefully
- **Comprehensive Logging**: Debug and monitor the tool's operation

## Requirements

- Docker (recommended) OR
- Python 3.8+ and FFmpeg installed locally

## Quick Start with Docker

### Build the Docker Image

```bash
docker build -t silent-sense .
```

### Run the Container

```bash
docker run -d \
  --name silent-sense \
  -e STREAM_URL="https://radio.gayphx.com/listen/gayphx/radio.mp3" \
  -e SILENCE_THRESHOLD="-60" \
  -e SILENCE_TIMEOUT="10" \
  -e UPTIME_KUMA_URL="https://your-uptime-kuma-instance/api/push/your-monitor-id" \
  -e CHECK_INTERVAL="5" \
  silent-sense
```

### View Logs

```bash
docker logs -f silent-sense
```

## Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `STREAM_URL` | URL of the audio stream to monitor | - | Yes |
| `SILENCE_THRESHOLD` | Audio level threshold in dB (negative value) | `-60` | No |
| `SILENCE_TIMEOUT` | Seconds of silence before alerting | `10` | No |
| `UPTIME_KUMA_URL` | Uptime Kuma push URL for notifications | - | No |
| `CHECK_INTERVAL` | Interval in seconds between audio checks | `5` | No |
| `DEBUG` | Enable debug logging (`true`/`false`) | `false` | No |

### Command Line Arguments

You can also pass arguments directly to the script:

```bash
python silent_sense.py \
  --stream-url "https://radio.gayphx.com/listen/gayphx/radio.mp3" \
  --silence-threshold -60 \
  --silence-timeout 10 \
  --uptime-kuma-url "https://your-uptime-kuma-instance/api/push/your-monitor-id" \
  --check-interval 5 \
  --debug
```

| Argument | Description |
|----------|-------------|
| `--stream-url` | URL of the audio stream to monitor |
| `--silence-threshold` | Silence threshold in decibels |
| `--silence-timeout` | Seconds of silence before alerting |
| `--uptime-kuma-url` | Uptime Kuma push URL |
| `--check-interval` | Interval between checks in seconds |
| `--debug` | Enable debug logging |

## Running Locally (Without Docker)

### Prerequisites

1. Install Python 3.8 or higher
2. Install FFmpeg:
   - **Ubuntu/Debian**: `sudo apt-get install ffmpeg`
   - **macOS**: `brew install ffmpeg`
   - **Windows**: Download from [FFmpeg website](https://ffmpeg.org/download.html)

### Installation

```bash
# Clone the repository
git clone https://github.com/bilyfoster/radio-monitor.git
cd radio-monitor

# Install Python dependencies
pip install -r requirements.txt

# Run the monitor
python silent_sense.py --stream-url "https://radio.gayphx.com/listen/gayphx/radio.mp3"
```

## Uptime Kuma Integration

### Setting Up Uptime Kuma

1. In Uptime Kuma, create a new monitor of type **Push**
2. Copy the Push URL (e.g., `https://your-instance.com/api/push/abcd1234`)
3. Set the Push URL as the `UPTIME_KUMA_URL` environment variable or command line argument

### How It Works

- When audio is playing normally, Silent Sense sends `status=up` to Uptime Kuma
- When silence is detected beyond the timeout, it sends `status=down` with a message
- When audio resumes after silence, it sends `status=up` to indicate recovery

## Example Use Cases

### Monitor a Radio Station

```bash
docker run -d \
  --name radio-monitor \
  -e STREAM_URL="https://radio.gayphx.com/listen/gayphx/radio.mp3" \
  -e SILENCE_THRESHOLD="-50" \
  -e SILENCE_TIMEOUT="30" \
  -e UPTIME_KUMA_URL="https://uptime.example.com/api/push/radio-monitor" \
  silent-sense
```

### Monitor with Debug Logging

```bash
docker run -d \
  --name radio-monitor \
  -e STREAM_URL="https://radio.gayphx.com/listen/gayphx/radio.mp3" \
  -e DEBUG="true" \
  silent-sense
```

## Docker Compose

Create a `docker-compose.yml` file:

```yaml
version: '3.8'

services:
  silent-sense:
    build: .
    container_name: silent-sense
    restart: unless-stopped
    environment:
      - STREAM_URL=https://radio.gayphx.com/listen/gayphx/radio.mp3
      - SILENCE_THRESHOLD=-60
      - SILENCE_TIMEOUT=10
      - UPTIME_KUMA_URL=https://your-uptime-kuma-instance/api/push/your-monitor-id
      - CHECK_INTERVAL=5
```

Run with:

```bash
docker-compose up -d
```

## Troubleshooting

### Stream Connection Issues

If the monitor reports frequent errors connecting to the stream:
- Verify the stream URL is accessible
- Check if the stream requires authentication
- Ensure your network allows outbound HTTP/HTTPS connections

### FFmpeg Errors

If you see FFmpeg-related errors:
- Ensure FFmpeg is installed correctly
- Verify FFmpeg can access the stream: `ffmpeg -i "your-stream-url" -t 5 -f null -`

### Debug Mode

Enable debug mode to see detailed logging:
```bash
docker run -e DEBUG=true -e STREAM_URL="..." silent-sense
```

## License

MIT License
