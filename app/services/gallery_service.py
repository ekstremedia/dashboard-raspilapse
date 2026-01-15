import os
from datetime import datetime, timedelta
from pathlib import Path


def get_available_dates(images_dir):
    """Get list of dates that have images"""
    dates = []

    try:
        # Walk through year/month/day structure
        for year_dir in sorted(os.listdir(images_dir), reverse=True):
            year_path = os.path.join(images_dir, year_dir)
            if not os.path.isdir(year_path) or not year_dir.isdigit():
                continue

            for month_dir in sorted(os.listdir(year_path), reverse=True):
                month_path = os.path.join(year_path, month_dir)
                if not os.path.isdir(month_path) or not month_dir.isdigit():
                    continue

                for day_dir in sorted(os.listdir(month_path), reverse=True):
                    day_path = os.path.join(month_path, day_dir)
                    if not os.path.isdir(day_path) or not day_dir.isdigit():
                        continue

                    # Count images in this directory
                    try:
                        image_count = len(
                            [f for f in os.listdir(day_path) if f.endswith(".jpg")]
                        )
                        if image_count > 0:
                            dates.append(
                                {
                                    "year": int(year_dir),
                                    "month": int(month_dir),
                                    "day": int(day_dir),
                                    "date": f"{year_dir}-{month_dir}-{day_dir}",
                                    "count": image_count,
                                }
                            )
                    except OSError:
                        pass

    except OSError:
        pass

    return dates[:100]  # Limit to last 100 days


def get_images_for_date(images_dir, year, month, day):
    """Get list of images for a specific date"""
    day_path = os.path.join(images_dir, str(year), f"{month:02d}", f"{day:02d}")

    images = []

    try:
        for filename in sorted(os.listdir(day_path)):
            if not filename.endswith(".jpg"):
                continue

            filepath = os.path.join(day_path, filename)
            rel_path = f"{year}/{month:02d}/{day:02d}/{filename}"

            try:
                stat = os.stat(filepath)

                # Extract time from filename if possible
                # Format: kringelen_nord_YYYY_MM_DD_HH_MM_SS.jpg
                time_str = None
                parts = filename.replace(".jpg", "").split("_")
                if len(parts) >= 6:
                    try:
                        time_str = f"{parts[-3]}:{parts[-2]}:{parts[-1]}"
                    except (IndexError, ValueError):
                        pass

                images.append(
                    {
                        "filename": filename,
                        "path": rel_path,
                        "size": stat.st_size,
                        "time": time_str,
                        "url": f"/gallery/image/{rel_path}",
                    }
                )
            except OSError:
                pass

    except OSError:
        pass

    return images


def get_images_for_date_paginated(images_dir, year, month, day, page=1, per_page=50):
    """Get paginated images for a date"""
    all_images = get_images_for_date(images_dir, year, month, day)

    start = (page - 1) * per_page
    end = start + per_page

    return {
        "images": all_images[start:end],
        "total": len(all_images),
        "page": page,
        "per_page": per_page,
        "pages": (len(all_images) + per_page - 1) // per_page,
    }
