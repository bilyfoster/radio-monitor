# Silent Sense - Radio Stream Silence Monitor

Silent Sense is a tool for monitoring online radio streams to detect silence (no audio being played) and alert a monitoring system like Uptime Kuma.

## Features

- **Continuous Monitoring**: Monitors audio streams in real-time using FFmpeg
- **Configurable Thresholds**: Set custom silence detection threshold (in decibels)
- **Configurable Timeout**: Define how long silence must persist before alerting
- **Uptime Kuma Integration**: Send notifications to Uptime Kuma push endpoints
- **Docker Support**: Easy deployment via Docker container
- **Robust Error Handling**: Handles stream interruptions and connection issues
- **Detailed Logging**: Comprehensive logging for debugging and monitoring

## Requirements

### Running with Docker (Recommended)

- Docker

### Running Locally

- Python 3.8+
- FFmpeg
- Python packages: `requests`

## Quick Start

### Using Docker

1. **Build the Docker image:**

   ```bash
   docker build -t silent-sense .
   ```

2. **Run the container:**

   ```bash
   docker run -d --name silent-sense \
     -e STREAM_URL="https://radio.gayphx.com/listen/gayphx/radio.mp3" \
     -e SILENCE_THRESHOLD="-60" \
     -e SILENCE_TIMEOUT="10" \
     -e UPTIME_KUMA_URL="https://your-uptime-kuma.com/api/push/YOUR_PUSH_TOKEN" \
     silent-sense
   ```

### Running Locally

1. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

2. **Ensure FFmpeg is installed:**

   ```bash
   # Ubuntu/Debian
   sudo apt-get install ffmpeg

   # macOS
   brew install ffmpeg

   # Windows
   # Download from https://ffmpeg.org/download.html
   ```

3. **Run the script:**

   ```bash
   python silent_sense.py --stream-url "https://radio.gayphx.com/listen/gayphx/radio.mp3"
   ```

## Configuration

Silent Sense can be configured using command-line arguments or environment variables.

### Command-Line Arguments

| Argument | Description | Default |
|----------|-------------|---------|
| `--stream-url` | URL of the audio stream to monitor | Required |
| `--threshold` | Silence threshold in decibels | -60 dB |
| `--timeout` | Silence duration before alerting (seconds) | 10 |
| `--uptime-kuma-url` | Uptime Kuma push URL for notifications | None |
| `--check-interval` | Audio check interval (seconds) | 1 |
| `--debug` | Enable debug logging | False |

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `STREAM_URL` | URL of the audio stream to monitor | Required |
| `SILENCE_THRESHOLD` | Silence threshold in decibels | -60 |
| `SILENCE_TIMEOUT` | Silence duration before alerting (seconds) | 10 |
| `UPTIME_KUMA_URL` | Uptime Kuma push URL for notifications | None |
| `CHECK_INTERVAL` | Audio check interval (seconds) | 1 |
| `DEBUG` | Enable debug logging (true/false) | false |

### Understanding the Silence Threshold

The silence threshold is measured in decibels (dB). Lower values mean quieter sounds:

- `-60 dB`: Very quiet (good default for detecting complete silence)
- `-50 dB`: Quiet
- `-40 dB`: Moderate
- `-30 dB`: Fairly loud

Adjust this based on your stream's characteristics. If you're getting false positives, try lowering the threshold (e.g., -70 dB).

## Examples

### Basic Monitoring

```bash
python silent_sense.py --stream-url "https://radio.gayphx.com/listen/gayphx/radio.mp3"
```

### With Custom Threshold and Timeout

```bash
python silent_sense.py \
  --stream-url "https://radio.gayphx.com/listen/gayphx/radio.mp3" \
  --threshold -50 \
  --timeout 15
```

### With Uptime Kuma Integration

```bash
python silent_sense.py \
  --stream-url "https://radio.gayphx.com/listen/gayphx/radio.mp3" \
  --uptime-kuma-url "https://uptime.example.com/api/push/abc123"
```

### Docker with All Options

```bash
docker run -d --name silent-sense \
  -e STREAM_URL="https://radio.gayphx.com/listen/gayphx/radio.mp3" \
  -e SILENCE_THRESHOLD="-50" \
  -e SILENCE_TIMEOUT="15" \
  -e UPTIME_KUMA_URL="https://uptime.example.com/api/push/abc123" \
  -e CHECK_INTERVAL="2" \
  -e DEBUG="true" \
  --restart unless-stopped \
  silent-sense
```

### Docker Compose

Create a `docker-compose.yml`:

```yaml
version: '3.8'

services:
  silent-sense:
    build: .
    container_name: silent-sense
    environment:
      - STREAM_URL=https://radio.gayphx.com/listen/gayphx/radio.mp3
      - SILENCE_THRESHOLD=-60
      - SILENCE_TIMEOUT=10
      - UPTIME_KUMA_URL=https://uptime.example.com/api/push/abc123
    restart: unless-stopped
```

Then run:

```bash
docker-compose up -d
```

## Uptime Kuma Integration

To integrate with Uptime Kuma:

1. In Uptime Kuma, create a new monitor of type "Push"
2. Copy the Push URL provided
3. Use this URL as the `--uptime-kuma-url` argument or `UPTIME_KUMA_URL` environment variable

Silent Sense will:
- Send a `status=down` notification when silence is detected beyond the timeout
- Send a `status=up` notification when audio resumes after a silence event

## Logging

Silent Sense provides detailed logging to stdout:

- **INFO**: Normal operation, stream status changes
- **WARNING**: Silence detected, potential issues
- **ERROR**: Alerts, connection failures, timeout exceeded
- **DEBUG**: Detailed audio level information (enable with `--debug`)

To view Docker container logs:

```bash
docker logs -f silent-sense
```

## Troubleshooting

### FFmpeg Not Found

Ensure FFmpeg is installed and available in your PATH:

```bash
ffmpeg -version
```

### Stream Connection Issues

- Verify the stream URL is accessible
- Check network connectivity
- Some streams may require specific user agents or headers

### High CPU Usage

- Increase the `--check-interval` to reduce monitoring frequency
- This will slightly delay silence detection but reduce resource usage

## License

MIT License
