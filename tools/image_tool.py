"""
Image Processing Tool
Download, process, and extract metadata from images
"""

import os
import logging
from typing import Dict, List, Optional, Any, Tuple
from io import BytesIO
from urllib.parse import urlparse
import hashlib

import requests
from PIL import Image
import numpy as np

logger = logging.getLogger(__name__)


class ImageTool:
    """
    Image processing and manipulation tool
    """

    def __init__(
        self,
        max_size_mb: int = 10,
        allowed_formats: Optional[List[str]] = None,
        timeout: int = 30
    ):
        """
        Initialize image tool

        Args:
            max_size_mb: Maximum image size in MB
            allowed_formats: List of allowed image formats
            timeout: Download timeout in seconds
        """
        self.max_size_mb = max_size_mb
        self.max_size_bytes = max_size_mb * 1024 * 1024

        self.allowed_formats = allowed_formats or ["PNG", "JPEG", "JPG", "WEBP", "GIF"]
        self.timeout = timeout

        logger.info(f"Image tool initialized (max size: {max_size_mb}MB)")

    def download_image(self, url: str, save_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Download image from URL

        Args:
            url: Image URL
            save_path: Optional path to save image

        Returns:
            Dict with image data and metadata
        """
        try:
            # Download image
            response = requests.get(url, timeout=self.timeout, stream=True)
            response.raise_for_status()

            # Check content type
            content_type = response.headers.get("Content-Type", "")
            if not content_type.startswith("image/"):
                logger.warning(f"URL is not an image: {content_type}")
                return None

            # Check size
            content_length = response.headers.get("Content-Length")
            if content_length and int(content_length) > self.max_size_bytes:
                logger.warning(f"Image too large: {content_length} bytes")
                return None

            # Load image
            image_bytes = BytesIO(response.content)
            image = Image.open(image_bytes)

            # Validate format
            if image.format not in self.allowed_formats:
                logger.warning(f"Image format not allowed: {image.format}")
                return None

            # Extract metadata
            metadata = self.extract_metadata(image, url)

            # Save if path provided
            if save_path:
                image.save(save_path)
                metadata["saved_path"] = save_path

            # Generate hash
            image_hash = hashlib.md5(response.content).hexdigest()
            metadata["hash"] = image_hash

            # Convert to bytes for storage
            metadata["bytes"] = response.content
            metadata["size_bytes"] = len(response.content)

            logger.debug(f"Downloaded image: {url} ({metadata['width']}x{metadata['height']})")
            return metadata

        except Exception as e:
            logger.error(f"Error downloading image from {url}: {e}")
            return None

    def extract_metadata(self, image: Image.Image, url: str = "") -> Dict[str, Any]:
        """
        Extract metadata from image

        Args:
            image: PIL Image object
            url: Original URL

        Returns:
            Dict with metadata
        """
        metadata = {
            "url": url,
            "format": image.format,
            "mode": image.mode,
            "width": image.width,
            "height": image.height,
            "aspect_ratio": round(image.width / image.height, 2) if image.height > 0 else 0,
            "size_pixels": image.width * image.height
        }

        # Extract EXIF data if available
        exif_data = {}
        try:
            exif = image.getexif()
            if exif:
                for tag_id, value in exif.items():
                    exif_data[str(tag_id)] = str(value)
                metadata["exif"] = exif_data
        except:
            pass

        # Color analysis
        try:
            if image.mode == "RGB" or image.mode == "RGBA":
                # Get dominant colors
                image_array = np.array(image.convert("RGB"))
                pixels = image_array.reshape(-1, 3)

                # Sample pixels for performance
                sample_size = min(1000, len(pixels))
                sampled_pixels = pixels[np.random.choice(len(pixels), sample_size, replace=False)]

                # Calculate average color
                avg_color = np.mean(sampled_pixels, axis=0).astype(int)
                metadata["avg_color_rgb"] = avg_color.tolist()

        except Exception as e:
            logger.debug(f"Error analyzing colors: {e}")

        return metadata

    def resize_image(
        self,
        image: Image.Image,
        max_width: int = 1920,
        max_height: int = 1080,
        maintain_aspect_ratio: bool = True
    ) -> Image.Image:
        """
        Resize image

        Args:
            image: PIL Image object
            max_width: Maximum width
            max_height: Maximum height
            maintain_aspect_ratio: Maintain aspect ratio

        Returns:
            Resized image
        """
        try:
            if maintain_aspect_ratio:
                image.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
                return image
            else:
                return image.resize((max_width, max_height), Image.Resampling.LANCZOS)

        except Exception as e:
            logger.error(f"Error resizing image: {e}")
            return image

    def create_thumbnail(self, image: Image.Image, size: Tuple[int, int] = (200, 200)) -> Image.Image:
        """
        Create thumbnail

        Args:
            image: PIL Image object
            size: Thumbnail size (width, height)

        Returns:
            Thumbnail image
        """
        try:
            image_copy = image.copy()
            image_copy.thumbnail(size, Image.Resampling.LANCZOS)
            return image_copy

        except Exception as e:
            logger.error(f"Error creating thumbnail: {e}")
            return image

    def convert_format(self, image: Image.Image, target_format: str = "PNG") -> Image.Image:
        """
        Convert image format

        Args:
            image: PIL Image object
            target_format: Target format (PNG, JPEG, WEBP)

        Returns:
            Converted image
        """
        try:
            # Handle transparency for JPEG
            if target_format == "JPEG" and image.mode in ("RGBA", "LA", "P"):
                # Convert to RGB
                rgb_image = Image.new("RGB", image.size, (255, 255, 255))
                rgb_image.paste(image, mask=image.split()[-1] if image.mode == "RGBA" else None)
                return rgb_image

            return image

        except Exception as e:
            logger.error(f"Error converting image format: {e}")
            return image

    def download_multiple(self, urls: List[str], save_dir: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Download multiple images

        Args:
            urls: List of image URLs
            save_dir: Directory to save images

        Returns:
            List of image metadata
        """
        results = []

        for i, url in enumerate(urls):
            save_path = None
            if save_dir:
                # Generate filename from URL
                filename = self._generate_filename(url, i)
                save_path = os.path.join(save_dir, filename)

            result = self.download_image(url, save_path)
            if result:
                results.append(result)

        logger.info(f"Downloaded {len(results)} out of {len(urls)} images")
        return results

    def _generate_filename(self, url: str, index: int) -> str:
        """Generate filename from URL"""
        parsed = urlparse(url)
        path = parsed.path

        # Try to extract filename from URL
        if path:
            filename = os.path.basename(path)
            if filename and "." in filename:
                return filename

        # Generate filename from URL hash
        url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
        return f"image_{index}_{url_hash}.jpg"

    def validate_image_url(self, url: str) -> bool:
        """
        Validate if URL points to an image

        Args:
            url: URL to validate

        Returns:
            True if valid image URL
        """
        try:
            # Check URL extension
            parsed = urlparse(url)
            path = parsed.path.lower()

            image_extensions = [".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"]
            if any(path.endswith(ext) for ext in image_extensions):
                return True

            # Check content type with HEAD request
            response = requests.head(url, timeout=5)
            content_type = response.headers.get("Content-Type", "")
            return content_type.startswith("image/")

        except:
            return False


# Convenience functions
def download_image(url: str, save_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Convenience function to download an image

    Args:
        url: Image URL
        save_path: Optional path to save image

    Returns:
        Image metadata
    """
    tool = ImageTool()
    return tool.download_image(url, save_path)


def create_thumbnail(image_path: str, thumbnail_path: str, size: Tuple[int, int] = (200, 200)) -> bool:
    """
    Convenience function to create thumbnail

    Args:
        image_path: Path to source image
        thumbnail_path: Path to save thumbnail
        size: Thumbnail size

    Returns:
        True if successful
    """
    try:
        tool = ImageTool()
        image = Image.open(image_path)
        thumbnail = tool.create_thumbnail(image, size)
        thumbnail.save(thumbnail_path)
        return True

    except Exception as e:
        logger.error(f"Error creating thumbnail: {e}")
        return False
