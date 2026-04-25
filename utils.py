"""Utility functions for the YouTube Downloader application."""

import os
import re
import shutil
from typing import Optional, Tuple


def is_valid_url(url: str) -> bool:
    """Validate if a URL is properly formatted and supported."""
    pattern = r'^(https?://)?(www\.)?(youtube\.com|youtu\.be|music\.youtube\.com)/'
    return bool(re.match(pattern, url.strip()))


def find_ffmpeg() -> Optional[str]:
    """Search for FFmpeg in common installation paths."""
    paths = [
        r"C:\ffmpeg\bin\ffmpeg.exe",
        r"C:\Program Files\FFmpeg\bin\ffmpeg.exe",
        r"/usr/local/bin/ffmpeg",
        r"/usr/bin/ffmpeg",
        shutil.which("ffmpeg"),
    ]
    
    for path in paths:
        if path and os.path.exists(path):
            return path
    
    # Try to download FFmpeg if not found (optional)
    print("FFmpeg not found. Please install it manually.")
    return None


def get_default_save_path() -> str:
    """Get the default save directory."""
    home = os.path.expanduser("~")
    downloads = os.path.join(home, "Downloads", "YouTube Downloads")
    
    if not os.path.exists(downloads):
        os.makedirs(downloads)
    
    return downloads


def format_quality_string(quality: str) -> str:
    """Format quality string for youtube-dl."""
    quality = quality.strip()
    
    if quality == "Best Quality":
        return 'bestaudio/best'
    
    # Extract bitrate number
    match = re.search(r'(\d+)', quality)
    if match:
        bitrate = int(match.group(1))
        return f'bestaudio[abr<={bitrate}]/bestaudio[abr<=320]/bestaudio/best'
    
    # Handle video qualities
    height_match = re.search(r'(\d+)p', quality)
    if height_match:
        height = int(height_match.group(1))
        return (f'bestvideo[height={height}][ext=mp4]+bestaudio[ext=m4a]/'
                f'bestvideo[height<={height}][ext=mp4]+bestaudio[ext=m4a]/'
                f'bestvideo[height<={height}]+bestaudio/best[height<={height}]/best')
    
    return 'bestvideo+bestaudio/best'


def extract_video_id(url: str) -> Optional[str]:
    """Extract video ID from YouTube URL."""
    patterns = [
        r'(?:youtube\.com\/(?:[^\/]+\/.+\/|(?:v|e(?:mbed)?)\/|.*[?&]v=)|youtu\.be\/)([^"&\W\/]+)',
        r'(?:(?:http)?://)?(www\.)?(?:www\.)?(?:youtube\.com|youtu\.be)/(?:watch\?v=)?([^#\?\&\s]+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1).strip()
    
    return None


def get_ffmpeg_paths() -> dict:
    """Get FFmpeg paths for youtube-dl options."""
    detected_ffmpeg = find_ffmpeg()
    ffmpeg_path = detected_ffmpeg or "ffmpeg"
    ffprobe_path = detected_ffmpeg.replace("ffmpeg", "ffprobe") if detected_ffmpeg else "ffprobe"
    
    return {
        'ffmpeg': ffmpeg_path,
        'ffprobe': ffprobe_path,
    }


def get_default_settings() -> dict:
    """Get default application settings."""
    return {
        'save_path': get_default_save_path(),
        'default_quality': 'Best Quality',
        'auto_audio_for_music': True,
        'show_thumbnails': True,
    }
