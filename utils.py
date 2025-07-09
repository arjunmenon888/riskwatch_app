# utils.py

import io
from PIL import Image

def compress_image(image_bytes, max_dimension=1024, quality=85):
    """
    Compresses, resizes, and corrects orientation of an image from bytes.
    - image_bytes: The raw byte content of the image.
    - max_dimension: The maximum width or height of the output image.
    - quality: The JPEG quality for the output image (1-95).
    """
    try:
        img = Image.open(io.BytesIO(image_bytes))
        
        # Correct for EXIF orientation
        if hasattr(img, '_getexif'):
            exif = img._getexif()
            if exif:
                orientation_key = 274 # cf ExifTags
                if orientation_key in exif:
                    orientation = exif[orientation_key]
                    rotations = {3: 180, 6: 270, 8: 90}
                    if orientation in rotations:
                        img = img.rotate(rotations[orientation], expand=True)
                        
        # Ensure image is in RGB format for saving as JPEG
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
            
        # Resize the image while maintaining aspect ratio
        img.thumbnail((max_dimension, max_dimension))
        
        # Save the compressed image to a byte buffer
        buffer = io.BytesIO()
        img.save(buffer, format='JPEG', quality=quality)
        return buffer.getvalue()
    except Exception as e:
        print(f"Error compressing image: {e}")
        # Return original bytes if compression fails
        return image_bytes