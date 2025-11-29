#!/usr/bin/env python3
"""
Silent Sense - Audio Stream Silence Monitor

Monitors an online radio station's audio stream for silence and sends alerts
to a monitoring system like Uptime Kuma when silence is detected.
"""

import argparse
import logging
import os
import re
import subprocess
import sys
import time
from urllib.parse import urlparse

import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)


def validate_url(url: str) -> bool:
    """Validate that the URL is properly formatted."""
    try:
        result = urlparse(url)
        return all([result.scheme in ('http', 'https'), result.netloc])
    except Exception:
        return False


def send_notification(uptime_kuma_url: str, status: str = "up", msg: str = "") -> bool:
    """
    Send a notification to Uptime Kuma.
    
    Args:
        uptime_kuma_url: The Uptime Kuma push URL
        status: Status to report ("up" or "down")
        msg: Optional message to include
        
    Returns:
        True if notification was sent successfully, False otherwise
    """
    if not uptime_kuma_url:
        logger.debug("No Uptime Kuma URL configured, skipping notification")
        return True
    
    try:
        params = {"status": status}
        if msg:
            params["msg"] = msg
        
        response = requests.get(uptime_kuma_url, params=params, timeout=10)
        response.raise_for_status()
        logger.info(f"Notification sent to Uptime Kuma: status={status}, msg={msg}")
        return True
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to send notification to Uptime Kuma: {e}")
        return False


def monitor_stream(
    stream_url: str,
    silence_threshold_db: float = -60.0,
    silence_timeout_sec: int = 10,
    uptime_kuma_url: str = "",
    check_interval_sec: float = 1.0,
    heartbeat_interval_sec: int = 60
) -> None:
    """
    Monitor an audio stream for silence and send alerts when detected.
    
    Args:
        stream_url: URL of the audio stream to monitor
        silence_threshold_db: Audio level threshold in dB below which is considered silence
        silence_timeout_sec: Duration in seconds of silence before triggering an alert
        uptime_kuma_url: URL for Uptime Kuma push notifications
        check_interval_sec: Interval between audio level checks
        heartbeat_interval_sec: Interval between heartbeat notifications (default 60 seconds)
    """
    if not validate_url(stream_url):
        logger.error(f"Invalid stream URL: {stream_url}")
        sys.exit(1)
    
    logger.info(f"Starting stream monitor for: {stream_url}")
    logger.info(f"Silence threshold: {silence_threshold_db} dB")
    logger.info(f"Silence timeout: {silence_timeout_sec} seconds")
    logger.info(f"Heartbeat interval: {heartbeat_interval_sec} seconds")
    
    silence_start_time = None
    is_silent = False
    alert_sent = False
    last_heartbeat_time = 0
    
    # FFmpeg command to analyze audio levels
    # Using volumedetect filter to get mean and max volume
    ffmpeg_cmd = [
        "ffmpeg",
        "-i", stream_url,
        "-t", str(int(check_interval_sec) + 2),  # Sample duration
        "-af", "volumedetect",
        "-f", "null",
        "-"
    ]
    
    while True:
        try:
            # Run FFmpeg to analyze audio
            result = subprocess.run(
                ffmpeg_cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            # Parse the output for volume information
            output = result.stderr
            
            # Look for mean_volume in FFmpeg output
            mean_volume_match = re.search(r'mean_volume:\s*([-\d.]+)\s*dB', output)
            max_volume_match = re.search(r'max_volume:\s*([-\d.]+)\s*dB', output)
            
            if mean_volume_match:
                mean_volume = float(mean_volume_match.group(1))
                max_volume = float(max_volume_match.group(1)) if max_volume_match else mean_volume
                
                logger.debug(f"Audio levels - Mean: {mean_volume} dB, Max: {max_volume} dB")
                
                # Check if audio is below silence threshold
                current_is_silent = mean_volume < silence_threshold_db
                
                if current_is_silent:
                    if silence_start_time is None:
                        silence_start_time = time.time()
                        logger.warning(f"Silence detected (below {silence_threshold_db} dB)")
                    
                    silence_duration = time.time() - silence_start_time
                    
                    if silence_duration >= silence_timeout_sec and not alert_sent:
                        logger.error(
                            f"ALERT: Silence detected for {silence_duration:.1f} seconds "
                            f"(threshold: {silence_timeout_sec} seconds)"
                        )
                        send_notification(
                            uptime_kuma_url,
                            status="down",
                            msg=f"Silence detected for {silence_duration:.1f} seconds"
                        )
                        alert_sent = True
                else:
                    if silence_start_time is not None:
                        logger.info("Audio resumed - silence ended")
                        if alert_sent:
                            send_notification(
                                uptime_kuma_url,
                                status="up",
                                msg="Audio stream resumed"
                            )
                    silence_start_time = None
                    alert_sent = False
                    
                    # Send heartbeat when audio is playing (throttled)
                    current_time = time.time()
                    if current_time - last_heartbeat_time >= heartbeat_interval_sec:
                        send_notification(uptime_kuma_url, status="up", msg="Stream playing normally")
                        last_heartbeat_time = current_time
            else:
                logger.warning("Could not parse audio levels from FFmpeg output")
                
        except subprocess.TimeoutExpired:
            logger.error("FFmpeg timeout - stream may be unresponsive")
            if not alert_sent:
                send_notification(
                    uptime_kuma_url,
                    status="down",
                    msg="Stream unresponsive (FFmpeg timeout)"
                )
                alert_sent = True
                
        except subprocess.SubprocessError as e:
            logger.error(f"FFmpeg error: {e}")
            if not alert_sent:
                send_notification(
                    uptime_kuma_url,
                    status="down",
                    msg=f"Stream error: {str(e)}"
                )
                alert_sent = True
                
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            
        # Wait before next check
        time.sleep(check_interval_sec)


def main():
    """Main entry point for the Silent Sense monitor."""
    parser = argparse.ArgumentParser(
        description="Monitor an audio stream for silence and alert via Uptime Kuma",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    parser.add_argument(
        "--stream-url",
        type=str,
        default=os.environ.get("STREAM_URL", ""),
        help="URL of the audio stream to monitor (or set STREAM_URL env var)"
    )
    
    parser.add_argument(
        "--silence-threshold",
        type=float,
        default=float(os.environ.get("SILENCE_THRESHOLD", "-60")),
        help="Silence threshold in decibels (or set SILENCE_THRESHOLD env var)"
    )
    
    parser.add_argument(
        "--silence-timeout",
        type=int,
        default=int(os.environ.get("SILENCE_TIMEOUT", "10")),
        help="Seconds of silence before alerting (or set SILENCE_TIMEOUT env var)"
    )
    
    parser.add_argument(
        "--uptime-kuma-url",
        type=str,
        default=os.environ.get("UPTIME_KUMA_URL", ""),
        help="Uptime Kuma push URL for notifications (or set UPTIME_KUMA_URL env var)"
    )
    
    parser.add_argument(
        "--check-interval",
        type=float,
        default=float(os.environ.get("CHECK_INTERVAL", "5")),
        help="Interval in seconds between checks (or set CHECK_INTERVAL env var)"
    )
    
    parser.add_argument(
        "--heartbeat-interval",
        type=int,
        default=int(os.environ.get("HEARTBEAT_INTERVAL", "60")),
        help="Interval in seconds between heartbeat notifications (or set HEARTBEAT_INTERVAL env var)"
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        default=os.environ.get("DEBUG", "").lower() in ("true", "1", "yes"),
        help="Enable debug logging (or set DEBUG env var)"
    )
    
    args = parser.parse_args()
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Debug logging enabled")
    
    if not args.stream_url:
        logger.error("Stream URL is required. Use --stream-url or set STREAM_URL env var")
        sys.exit(1)
    
    if args.silence_threshold > 0:
        logger.error("Silence threshold must be a negative value in decibels")
        sys.exit(1)
    
    if args.silence_timeout < 1:
        logger.error("Silence timeout must be at least 1 second")
        sys.exit(1)
    
    if args.check_interval < 1:
        logger.error("Check interval must be at least 1 second")
        sys.exit(1)
    
    if args.heartbeat_interval < 1:
        logger.error("Heartbeat interval must be at least 1 second")
        sys.exit(1)
    
    try:
        monitor_stream(
            stream_url=args.stream_url,
            silence_threshold_db=args.silence_threshold,
            silence_timeout_sec=args.silence_timeout,
            uptime_kuma_url=args.uptime_kuma_url,
            check_interval_sec=args.check_interval,
            heartbeat_interval_sec=args.heartbeat_interval
        )
    except KeyboardInterrupt:
        logger.info("Monitoring stopped by user")
        sys.exit(0)


if __name__ == "__main__":
    main()
