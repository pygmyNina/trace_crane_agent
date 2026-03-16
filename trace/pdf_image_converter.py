"""
PDF to Image Converter for TRACE
Converts PDF pages to images for Vision API analysis
"""

import os
from typing import List, Optional, Tuple
from PIL import Image
import base64
from io import BytesIO

try:
    from pdf2image import convert_from_path
    PDF2IMAGE_AVAILABLE = True
except ImportError:
    PDF2IMAGE_AVAILABLE = False


class PDFImageConverter:
    """Handles conversion of PDF pages to images"""

    def __init__(self, cache_dir: str = ".trace_cache"):
        self.cache_dir = cache_dir
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)

    def _get_cache_path(self, pdf_path: str, page_num: int) -> str:
        """Generate cache path for a PDF page image"""
        pdf_basename = os.path.basename(pdf_path).replace('.pdf', '')
        safe_name = "".join(c if c.isalnum() else "_" for c in pdf_basename)
        return os.path.join(self.cache_dir, f"{safe_name}_page_{page_num}.png")

    def convert_page(self, pdf_path: str, page_num: int, dpi: int = 200) -> Optional[str]:
        """
        Convert a single PDF page to image

        Args:
            pdf_path: Path to PDF file
            page_num: Page number (1-indexed)
            dpi: Resolution for conversion (higher = better quality but larger file)

        Returns:
            Path to generated image file, or None on error
        """
        if not PDF2IMAGE_AVAILABLE:
            print("⚠ pdf2image not installed. Run: pip install pdf2image")
            print("⚠ Also requires poppler: apt-get install poppler-utils (Linux)")
            return None

        if not os.path.exists(pdf_path):
            print(f"✗ PDF not found: {pdf_path}")
            return None

        # Check cache first
        cache_path = self._get_cache_path(pdf_path, page_num)
        if os.path.exists(cache_path):
            return cache_path

        try:
            # Convert single page
            images = convert_from_path(
                pdf_path,
                dpi=dpi,
                first_page=page_num,
                last_page=page_num
            )

            if not images:
                print(f"✗ Failed to convert page {page_num}")
                return None

            # Save to cache
            images[0].save(cache_path, 'PNG')
            return cache_path

        except Exception as e:
            print(f"✗ Error converting PDF page: {e}")
            return None

    def convert_pages(self, pdf_path: str, page_nums: List[int] = None,
                     dpi: int = 200) -> List[str]:
        """
        Convert multiple PDF pages to images

        Args:
            pdf_path: Path to PDF file
            page_nums: List of page numbers (1-indexed), or None for all pages
            dpi: Resolution for conversion

        Returns:
            List of paths to generated image files
        """
        if not PDF2IMAGE_AVAILABLE:
            print("⚠ pdf2image not installed")
            return []

        if not os.path.exists(pdf_path):
            print(f"✗ PDF not found: {pdf_path}")
            return []

        image_paths = []

        try:
            if page_nums:
                # Convert specific pages
                for page_num in page_nums:
                    img_path = self.convert_page(pdf_path, page_num, dpi)
                    if img_path:
                        image_paths.append(img_path)
            else:
                # Convert all pages
                images = convert_from_path(pdf_path, dpi=dpi)
                for i, image in enumerate(images, start=1):
                    cache_path = self._get_cache_path(pdf_path, i)
                    image.save(cache_path, 'PNG')
                    image_paths.append(cache_path)

        except Exception as e:
            print(f"✗ Error converting PDF pages: {e}")

        return image_paths

    def encode_image_base64(self, image_path: str) -> Optional[str]:
        """
        Encode image to base64 for API transmission

        Args:
            image_path: Path to image file

        Returns:
            Base64-encoded string, or None on error
        """
        try:
            with open(image_path, 'rb') as img_file:
                return base64.b64encode(img_file.read()).decode('utf-8')
        except Exception as e:
            print(f"✗ Error encoding image: {e}")
            return None

    def optimize_for_api(self, image_path: str, max_size: Tuple[int, int] = (2048, 2048)) -> str:
        """
        Optimize image for Vision API (reduce size if needed)

        Args:
            image_path: Path to image file
            max_size: Maximum dimensions (width, height)

        Returns:
            Path to optimized image
        """
        try:
            img = Image.open(image_path)

            # Check if resize needed
            if img.size[0] > max_size[0] or img.size[1] > max_size[1]:
                img.thumbnail(max_size, Image.Resampling.LANCZOS)

                # Save optimized version
                optimized_path = image_path.replace('.png', '_optimized.png')
                img.save(optimized_path, 'PNG', optimize=True)
                return optimized_path

            return image_path

        except Exception as e:
            print(f"⚠ Error optimizing image: {e}")
            return image_path

    def clear_cache(self, pdf_path: str = None):
        """
        Clear cached images

        Args:
            pdf_path: Specific PDF to clear, or None to clear all
        """
        if pdf_path:
            # Clear specific PDF cache
            pdf_basename = os.path.basename(pdf_path).replace('.pdf', '')
            safe_name = "".join(c if c.isalnum() else "_" for c in pdf_basename)
            pattern = f"{safe_name}_page_"

            for filename in os.listdir(self.cache_dir):
                if filename.startswith(pattern):
                    os.remove(os.path.join(self.cache_dir, filename))
        else:
            # Clear all cache
            for filename in os.listdir(self.cache_dir):
                if filename.endswith('.png'):
                    os.remove(os.path.join(self.cache_dir, filename))

    def get_cache_size(self) -> Tuple[int, int]:
        """
        Get cache statistics

        Returns:
            (number of files, total size in MB)
        """
        if not os.path.exists(self.cache_dir):
            return 0, 0

        total_size = 0
        file_count = 0

        for filename in os.listdir(self.cache_dir):
            filepath = os.path.join(self.cache_dir, filename)
            if os.path.isfile(filepath):
                total_size += os.path.getsize(filepath)
                file_count += 1

        return file_count, total_size / (1024 * 1024)  # Convert to MB
