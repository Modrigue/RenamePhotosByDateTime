import os
import sys
import shutil
from pathlib import Path
from PIL import Image, UnidentifiedImageError
from PIL.ExifTags import TAGS
from datetime import datetime

# Standard EXIF Tag ID for DateTimeOriginal
DATE_TIME_ORIGINAL_TAG = 36867

def get_date_taken(file_path):
    """
    Extracts the DateTimeOriginal from an image's EXIF data.
    Returns a datetime object or None if not found.
    """
    image = None
    try:
        image = Image.open(file_path)
        exif_data = image._getexif()
        
        if not exif_data:
            return None

        # Look for DateTimeOriginal
        date_str = exif_data.get(DATE_TIME_ORIGINAL_TAG)
        
        # If specific tag missing, try looking through named tags
        if not date_str:
            for tag_id, value in exif_data.items():
                tag_name = TAGS.get(tag_id, tag_id)
                if tag_name == 'DateTimeOriginal':
                    date_str = value
                    break

        if date_str:
            # EXIF date format is usually "YYYY:MM:DD HH:MM:SS"
            return datetime.strptime(date_str, '%Y:%m:%d %H:%M:%S')

    except (AttributeError, KeyError, IndexError, ValueError):
        # Errors parsing the specific EXIF tag
        return None
    except UnidentifiedImageError:
        # File is not a valid image
        return None
    except Exception as e:
        print(f"Error reading {file_path.name}: {e}")
        return None
    finally:
        # Explicitly close the image to release the file handle for renaming
        if image:
            image.close()

    return None

def rename_photos(directory):
    target_dir = Path(directory)

    if not target_dir.is_dir():
        print(f"Error: '{directory}' is not a valid directory.")
        return

    print(f"Processing images in: {target_dir.resolve()}")
    
    count = 0
    
    # Iterate over files in the directory
    for file_path in target_dir.iterdir():
        if not file_path.is_file():
            continue

        # Skip hidden files
        if file_path.name.startswith('.'):
            continue

        # Get date taken
        date_taken = get_date_taken(file_path)

        if date_taken:
            # Format date for filename: YYYY-MM-DD_HH-MM-SS
            # We replace colons because they are illegal in Windows filenames
            date_prefix = date_taken.strftime("%Y-%m-%d_%H-%M-%S")
            
            # Check if file is already renamed to avoid double prefixing
            if file_path.name.startswith(date_prefix):
                print(f"Skipping {file_path.name} (already renamed)")
                continue

            new_filename = f"{date_prefix}-{file_path.name}"
            new_file_path = target_dir / new_filename

            try:
                # Rename the file
                file_path.rename(new_file_path)
                print(f"Renamed: {file_path.name} -> {new_filename}")
                count += 1
            except OSError as e:
                print(f"Error renaming {file_path.name}: {e}")
        else:
            print(f"Skipping {file_path.name} (No EXIF date found)")

    print(f"\nCompleted. {count} files renamed.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python rename_photos.py <directory_path>")
    else:
        rename_photos(sys.argv[1])
