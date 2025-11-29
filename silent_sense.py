#!/usr/bin/env python3
"""
Silent Sense - Radio Stream Silence Monitor

This script monitors an audio stream for silence and sends notifications
to Uptime Kuma when silence is detected beyond the configured timeout.
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
    """Validate that the provided URL is properly formatted."""
    try:
        result = urlparse(url)
        return all([result.scheme in ('http', 'https'), result.netloc])
    except Exception:
        return False


def send_uptime_kuma_notification(push_url: str, status: str = "up", msg: str = "") -> bool:
    """
    Send a notification to Uptime Kuma push endpoint.
    
    Args:
        push_url: The Uptime Kuma push URL
        status: Either "up" or "down"
        msg: Optional message to include
        
    Returns:
        True if notification was sent successfully, False otherwise
    """
    if not push_url:
        logger.debug("No Uptime Kuma URL configured, skipping notification")
        return True
        
    try:
        params = {"status": status}
        if msg:
            params["msg"] = msg
            
        response = requests.get(push_url, params=params, timeout=10)
        response.raise_for_status()
        logger.info(f"Sent notification to Uptime Kuma: status={status}, msg={msg}")
        return True
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to send notification to Uptime Kuma: {e}")
        return False


def monitor_stream(
    stream_url: str,
    silence_threshold_db: float = -60.0,
    silence_timeout_seconds: float = 10.0,
    uptime_kuma_url: str = "",
    check_interval_seconds: float = 1.0
) -> None:
    """
    Continuously monitor an audio stream for silence.
    
    Args:
        stream_url: URL of the audio stream to monitor
        silence_threshold_db: Audio level threshold in dB below which is considered silence
        silence_timeout_seconds: Duration of silence (in seconds) before triggering alert
        uptime_kuma_url: Uptime Kuma push URL for notifications
        check_interval_seconds: How often to check audio levels
    """
    logger.info(f"Starting stream monitor for: {stream_url}")
    logger.info(f"Silence threshold: {silence_threshold_db} dB")
    logger.info(f"Silence timeout: {silence_timeout_seconds} seconds")
    
    silence_start_time = None
    is_silent = False
    consecutive_errors = 0
    max_consecutive_errors = 5
    
    while True:
        try:
            # Use ffmpeg to capture a short segment and analyze audio levels
            # The volumedetect filter outputs mean and max volume levels
            cmd = [
                "ffmpeg",
                "-i", stream_url,
                "-t", str(check_interval_seconds),
                "-af", "volumedetect",
                "-f", "null",
                "-"
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            # Parse the output for volume information
            # ffmpeg outputs volume info to stderr
            output = result.stderr
            
            # Look for mean_volume in the output
            # Example: [Parsed_volumedetect_0 @ 0x...] mean_volume: -25.3 dB
            mean_volume_match = re.search(r'mean_volume:\s*([-\d.]+)\s*dB', output)
            
            if mean_volume_match:
                mean_volume = float(mean_volume_match.group(1))
                logger.debug(f"Current mean volume: {mean_volume} dB")
                consecutive_errors = 0
                
                if mean_volume < silence_threshold_db:
                    # Audio is below threshold (silence detected)
                    if silence_start_time is None:
                        silence_start_time = time.time()
                        logger.warning(f"Silence detected (volume: {mean_volume} dB)")
                    
                    silence_duration = time.time() - silence_start_time
                    
                    if silence_duration >= silence_timeout_seconds and not is_silent:
                        is_silent = True
                        logger.error(
                            f"ALERT: Silence exceeded timeout! "
                            f"Duration: {silence_duration:.1f}s, Volume: {mean_volume} dB"
                        )
                        send_uptime_kuma_notification(
                            uptime_kuma_url,
                            status="down",
                            msg=f"Silence detected for {silence_duration:.1f}s (volume: {mean_volume} dB)"
                        )
                else:
                    # Audio is present
                    if silence_start_time is not None:
                        silence_duration = time.time() - silence_start_time
                        logger.info(
                            f"Audio resumed after {silence_duration:.1f}s silence "
                            f"(current volume: {mean_volume} dB)"
                        )
                    
                    if is_silent:
                        # Was silent, now recovered
                        logger.info("Audio recovered, sending recovery notification")
                        send_uptime_kuma_notification(
                            uptime_kuma_url,
                            status="up",
                            msg="Audio stream recovered"
                        )
                    
                    silence_start_time = None
                    is_silent = False
                    
            else:
                # Could not parse volume, might be a stream issue
                consecutive_errors += 1
                logger.warning(f"Could not parse audio levels from stream (error {consecutive_errors}/{max_consecutive_errors})")
                
                if consecutive_errors >= max_consecutive_errors:
                    logger.error("Too many consecutive errors, treating as silence/stream failure")
                    if not is_silent:
                        is_silent = True
                        send_uptime_kuma_notification(
                            uptime_kuma_url,
                            status="down",
                            msg="Stream connection issues - unable to read audio levels"
                        )
                        
        except subprocess.TimeoutExpired:
            consecutive_errors += 1
            logger.error(f"FFmpeg timed out while analyzing stream (error {consecutive_errors}/{max_consecutive_errors})")
            
            if consecutive_errors >= max_consecutive_errors and not is_silent:
                is_silent = True
                send_uptime_kuma_notification(
                    uptime_kuma_url,
                    status="down",
                    msg="Stream connection timeout"
                )
                
        except subprocess.SubprocessError as e:
            consecutive_errors += 1
            logger.error(f"FFmpeg error: {e} (error {consecutive_errors}/{max_consecutive_errors})")
            
            if consecutive_errors >= max_consecutive_errors and not is_silent:
                is_silent = True
                send_uptime_kuma_notification(
                    uptime_kuma_url,
                    status="down",
                    msg=f"Stream processing error: {str(e)}"
                )
                
        except Exception as e:
            consecutive_errors += 1
            logger.error(f"Unexpected error: {e} (error {consecutive_errors}/{max_consecutive_errors})")
            
        # Small sleep to prevent tight looping
        time.sleep(0.1)


def main():
    """Main entry point for the Silent Sense monitor."""
    parser = argparse.ArgumentParser(
        description="Silent Sense - Monitor audio streams for silence",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --stream-url https://radio.example.com/stream.mp3
  %(prog)s --stream-url https://radio.example.com/stream.mp3 --threshold -50 --timeout 15
  %(prog)s --stream-url https://radio.example.com/stream.mp3 --uptime-kuma-url https://uptime.example.com/api/push/xxx
        """
    )
    
    parser.add_argument(
        "--stream-url",
        type=str,
        default=os.environ.get("STREAM_URL", ""),
        help="URL of the audio stream to monitor (or set STREAM_URL env var)"
    )
    
    parser.add_argument(
        "--threshold",
        type=float,
        default=float(os.environ.get("SILENCE_THRESHOLD", "-60")),
        help="Silence threshold in decibels (default: -60 dB)"
    )
    
    parser.add_argument(
        "--timeout",
        type=float,
        default=float(os.environ.get("SILENCE_TIMEOUT", "10")),
        help="Silence duration in seconds before alerting (default: 10 seconds)"
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
        default=float(os.environ.get("CHECK_INTERVAL", "1")),
        help="Audio check interval in seconds (default: 1 second)"
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        default=os.environ.get("DEBUG", "").lower() in ("true", "1", "yes"),
        help="Enable debug logging"
    )
    
    args = parser.parse_args()
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Debug logging enabled")
    
    # Validate inputs
    if not args.stream_url:
        logger.error("Stream URL is required. Use --stream-url or set STREAM_URL environment variable.")
        sys.exit(1)
        
    if not validate_url(args.stream_url):
        logger.error(f"Invalid stream URL: {args.stream_url}")
        sys.exit(1)
        
    if args.uptime_kuma_url and not validate_url(args.uptime_kuma_url):
        logger.error(f"Invalid Uptime Kuma URL: {args.uptime_kuma_url}")
        sys.exit(1)
        
    if args.threshold > 0:
        logger.warning(f"Silence threshold ({args.threshold} dB) is positive, this may cause unexpected behavior")
        
    if args.timeout <= 0:
        logger.error("Silence timeout must be positive")
        sys.exit(1)
        
    if args.check_interval <= 0:
        logger.error("Check interval must be positive")
        sys.exit(1)
    
    # Start monitoring
    try:
        monitor_stream(
            stream_url=args.stream_url,
            silence_threshold_db=args.threshold,
            silence_timeout_seconds=args.timeout,
            uptime_kuma_url=args.uptime_kuma_url,
            check_interval_seconds=args.check_interval
        )
    except KeyboardInterrupt:
        logger.info("Monitoring stopped by user")
        sys.exit(0)


if __name__ == "__main__":
    main()
