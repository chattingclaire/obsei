"""
Video Processing Tool
Download, process, and extract metadata/frames from videos using ffmpeg and yt-dlp
"""

import os
import logging
from typing import Dict, List, Optional, Any
import subprocess
import json
from urllib.parse import urlparse, parse_qs

import yt_dlp

logger = logging.getLogger(__name__)


class VideoTool:
    """
    Video processing and download tool
    """

    def __init__(
        self,
        ffmpeg_path: str = "/usr/bin/ffmpeg",
        max_duration_seconds: int = 300,
        extract_frames: bool = True,
        frames_per_second: int = 1
    ):
        """
        Initialize video tool

        Args:
            ffmpeg_path: Path to ffmpeg binary
            max_duration_seconds: Maximum video duration to process
            extract_frames: Whether to extract frames
            frames_per_second: Frames to extract per second
        """
        self.ffmpeg_path = ffmpeg_path
        self.max_duration_seconds = max_duration_seconds
        self.extract_frames = extract_frames
        self.frames_per_second = frames_per_second

        # Verify ffmpeg is available
        if not self._check_ffmpeg():
            logger.warning("ffmpeg not found, some features may not work")

        logger.info("Video tool initialized")

    def _check_ffmpeg(self) -> bool:
        """Check if ffmpeg is available"""
        try:
            subprocess.run(
                [self.ffmpeg_path, "-version"],
                capture_output=True,
                check=True
            )
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def download_video(
        self,
        url: str,
        save_path: Optional[str] = None,
        quality: str = "best"
    ) -> Optional[Dict[str, Any]]:
        """
        Download video from URL using yt-dlp

        Args:
            url: Video URL (YouTube, Vimeo, etc.)
            save_path: Path to save video
            quality: Video quality (best, worst, or specific format)

        Returns:
            Dict with video metadata
        """
        try:
            ydl_opts = {
                "format": quality,
                "quiet": True,
                "no_warnings": True,
            }

            if save_path:
                ydl_opts["outtmpl"] = save_path

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)

                metadata = {
                    "url": url,
                    "title": info.get("title", ""),
                    "description": info.get("description", ""),
                    "duration_seconds": info.get("duration", 0),
                    "uploader": info.get("uploader", ""),
                    "upload_date": info.get("upload_date", ""),
                    "view_count": info.get("view_count", 0),
                    "like_count": info.get("like_count", 0),
                    "thumbnail": info.get("thumbnail", ""),
                    "width": info.get("width", 0),
                    "height": info.get("height", 0),
                    "fps": info.get("fps", 0),
                    "format": info.get("format", ""),
                    "filesize": info.get("filesize", 0),
                    "success": True
                }

                if save_path:
                    metadata["saved_path"] = ydl.prepare_filename(info)

                logger.info(f"Downloaded video: {metadata['title']} ({metadata['duration_seconds']}s)")
                return metadata

        except Exception as e:
            logger.error(f"Error downloading video from {url}: {e}")
            return {
                "url": url,
                "success": False,
                "error": str(e)
            }

    def get_video_info(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Get video information without downloading

        Args:
            url: Video URL

        Returns:
            Dict with video metadata
        """
        try:
            ydl_opts = {
                "quiet": True,
                "no_warnings": True,
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)

                metadata = {
                    "url": url,
                    "title": info.get("title", ""),
                    "description": info.get("description", ""),
                    "duration_seconds": info.get("duration", 0),
                    "uploader": info.get("uploader", ""),
                    "uploader_id": info.get("uploader_id", ""),
                    "channel_id": info.get("channel_id", ""),
                    "upload_date": info.get("upload_date", ""),
                    "view_count": info.get("view_count", 0),
                    "like_count": info.get("like_count", 0),
                    "comment_count": info.get("comment_count", 0),
                    "thumbnail": info.get("thumbnail", ""),
                    "width": info.get("width", 0),
                    "height": info.get("height", 0),
                    "fps": info.get("fps", 0),
                    "categories": info.get("categories", []),
                    "tags": info.get("tags", []),
                    "success": True
                }

                logger.debug(f"Retrieved video info: {metadata['title']}")
                return metadata

        except Exception as e:
            logger.error(f"Error getting video info from {url}: {e}")
            return {
                "url": url,
                "success": False,
                "error": str(e)
            }

    def extract_frames_from_video(
        self,
        video_path: str,
        output_dir: str,
        fps: Optional[int] = None
    ) -> List[str]:
        """
        Extract frames from video using ffmpeg

        Args:
            video_path: Path to video file
            output_dir: Directory to save frames
            fps: Frames per second to extract (None = extract all)

        Returns:
            List of frame file paths
        """
        try:
            if not self._check_ffmpeg():
                logger.error("ffmpeg not available")
                return []

            # Create output directory
            os.makedirs(output_dir, exist_ok=True)

            # Build ffmpeg command
            output_pattern = os.path.join(output_dir, "frame_%04d.jpg")

            cmd = [self.ffmpeg_path, "-i", video_path]

            if fps:
                cmd.extend(["-vf", f"fps={fps}"])

            cmd.extend(["-q:v", "2", output_pattern])

            # Run ffmpeg
            subprocess.run(cmd, capture_output=True, check=True)

            # Get list of extracted frames
            frames = sorted([
                os.path.join(output_dir, f)
                for f in os.listdir(output_dir)
                if f.startswith("frame_") and f.endswith(".jpg")
            ])

            logger.info(f"Extracted {len(frames)} frames from {video_path}")
            return frames

        except Exception as e:
            logger.error(f"Error extracting frames: {e}")
            return []

    def get_video_metadata_ffprobe(self, video_path: str) -> Optional[Dict[str, Any]]:
        """
        Get video metadata using ffprobe

        Args:
            video_path: Path to video file

        Returns:
            Dict with video metadata
        """
        try:
            cmd = [
                "ffprobe",
                "-v", "quiet",
                "-print_format", "json",
                "-show_format",
                "-show_streams",
                video_path
            ]

            result = subprocess.run(cmd, capture_output=True, check=True, text=True)
            data = json.loads(result.stdout)

            # Extract video stream info
            video_stream = None
            audio_stream = None

            for stream in data.get("streams", []):
                if stream.get("codec_type") == "video" and not video_stream:
                    video_stream = stream
                elif stream.get("codec_type") == "audio" and not audio_stream:
                    audio_stream = stream

            format_info = data.get("format", {})

            metadata = {
                "duration_seconds": float(format_info.get("duration", 0)),
                "size_bytes": int(format_info.get("size", 0)),
                "bit_rate": int(format_info.get("bit_rate", 0)),
                "format_name": format_info.get("format_name", ""),
            }

            if video_stream:
                metadata.update({
                    "width": int(video_stream.get("width", 0)),
                    "height": int(video_stream.get("height", 0)),
                    "codec": video_stream.get("codec_name", ""),
                    "fps": eval(video_stream.get("r_frame_rate", "0/1")),
                })

            if audio_stream:
                metadata["has_audio"] = True
                metadata["audio_codec"] = audio_stream.get("codec_name", "")
            else:
                metadata["has_audio"] = False

            return metadata

        except Exception as e:
            logger.error(f"Error getting video metadata with ffprobe: {e}")
            return None

    def extract_audio(self, video_path: str, output_path: str, format: str = "mp3") -> bool:
        """
        Extract audio from video

        Args:
            video_path: Path to video file
            output_path: Path to save audio file
            format: Audio format (mp3, wav, etc.)

        Returns:
            True if successful
        """
        try:
            if not self._check_ffmpeg():
                logger.error("ffmpeg not available")
                return False

            cmd = [
                self.ffmpeg_path,
                "-i", video_path,
                "-vn",  # No video
                "-acodec", "libmp3lame" if format == "mp3" else "copy",
                output_path
            ]

            subprocess.run(cmd, capture_output=True, check=True)

            logger.info(f"Extracted audio to {output_path}")
            return True

        except Exception as e:
            logger.error(f"Error extracting audio: {e}")
            return False

    def create_thumbnail(self, video_path: str, thumbnail_path: str, timestamp: str = "00:00:01") -> bool:
        """
        Create thumbnail from video at specific timestamp

        Args:
            video_path: Path to video file
            thumbnail_path: Path to save thumbnail
            timestamp: Timestamp (HH:MM:SS)

        Returns:
            True if successful
        """
        try:
            if not self._check_ffmpeg():
                logger.error("ffmpeg not available")
                return False

            cmd = [
                self.ffmpeg_path,
                "-i", video_path,
                "-ss", timestamp,
                "-vframes", "1",
                "-q:v", "2",
                thumbnail_path
            ]

            subprocess.run(cmd, capture_output=True, check=True)

            logger.info(f"Created thumbnail at {thumbnail_path}")
            return True

        except Exception as e:
            logger.error(f"Error creating thumbnail: {e}")
            return False

    def parse_youtube_id(self, url: str) -> Optional[str]:
        """
        Extract YouTube video ID from URL

        Args:
            url: YouTube URL

        Returns:
            Video ID or None
        """
        try:
            parsed = urlparse(url)

            if parsed.hostname in ["www.youtube.com", "youtube.com"]:
                if parsed.path == "/watch":
                    query = parse_qs(parsed.query)
                    return query.get("v", [None])[0]
                elif parsed.path.startswith("/embed/"):
                    return parsed.path.split("/")[2]
                elif parsed.path.startswith("/v/"):
                    return parsed.path.split("/")[2]

            elif parsed.hostname in ["youtu.be"]:
                return parsed.path[1:]

            return None

        except:
            return None


# Convenience functions
def download_youtube_video(url: str, save_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Convenience function to download YouTube video

    Args:
        url: YouTube URL
        save_path: Path to save video

    Returns:
        Video metadata
    """
    tool = VideoTool()
    return tool.download_video(url, save_path)


def get_youtube_info(url: str) -> Optional[Dict[str, Any]]:
    """
    Convenience function to get YouTube video info

    Args:
        url: YouTube URL

    Returns:
        Video metadata
    """
    tool = VideoTool()
    return tool.get_video_info(url)
