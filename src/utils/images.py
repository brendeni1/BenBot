from PIL import Image
import numpy as np
import requests
import discord
from io import BytesIO
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt


def extractColours(url, num_colors=1) -> list[list[int, int, int]]:
    # Download image
    response = requests.get(url)
    img = Image.open(BytesIO(response.content)).convert("RGB")
    img = img.resize((150, 150))  # Resize for faster clustering

    # Convert image to numpy array
    img_data = np.array(img)
    img_data = img_data.reshape((-1, 3))  # Flatten to list of RGB pixels

    # Run KMeans clustering
    kmeans = KMeans(n_clusters=num_colors, random_state=42)
    kmeans.fit(img_data)

    colours = kmeans.cluster_centers_.astype(int)

    return colours


async def fetchToFile(url: str, filename: str) -> discord.File:
    """
    Fetch an image from a URL, load it with Pillow,
    and return a Discord File object ready for attachment embedding.

    Use in embeds like:
    embed.set_thumbnail(url=f"attachment://{filename}")
    """

    # Fetch the image with browser-like headers to avoid blocks
    r = requests.get(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "en-CA,en;q=0.7",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Referer": "https://www.landmarkcinemas.com/showtimes/windsor",
            "Cookie": "LMC_TheatreId=7802; LMC_TheatreURL=%2Fshowtimes%2Fwindsor; LMC_TheatreName=%2Fnow-playing%2Fwindsor",
        },
    )
    r.raise_for_status()

    # Load image with Pillow
    img = Image.open(BytesIO(r.content))

    # Convert/save into memory buffer
    buffer = BytesIO()
    img.save(buffer, format=img.format if img.format else "PNG")
    buffer.seek(0)

    # Return Discord File object
    return discord.File(fp=buffer, filename=filename)


def urlIsImage(url: str) -> bool:
    try:
        r = requests.head(url, allow_redirects=True, timeout=5)
        if r.status_code != 200:
            return False

        content_type = r.headers.get("Content-Type", "")
        return content_type.startswith("image/")
    except requests.RequestException:
        return False
