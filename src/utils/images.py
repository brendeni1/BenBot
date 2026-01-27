import discord
import aiohttp
import os
import numpy as np
from io import BytesIO
from PIL import Image
from sklearn.cluster import KMeans


async def uploadToChibisafe(image: discord.Attachment | bytes):
    token = os.getenv("CHIBISAFE_BENBOT_TOKEN")
    cdnEndpoint = "https://cdn.brendenian.net/api/upload"

    # Download the file from Discord into memory asynchronously
    if isinstance(image, discord.Attachment):
        fileBytes = await image.read()
    else:
        fileBytes = image

    # Prepare the multipart form data
    data = aiohttp.FormData()

    data.add_field(
        "file",
        fileBytes,
        filename=image.filename,
        content_type=image.content_type,
    )

    headers = {"x-api-key": f"{token}", "Accept": "application/json"}

    async with aiohttp.ClientSession() as session:
        async with session.post(cdnEndpoint, data=data, headers=headers) as response:
            if response.status == 200:
                res_data = await response.json()
                return res_data.get("url")
            else:
                error_text = await response.text()
                raise Exception(
                    f"Chibisafe Upload Failed ({response.status}): {error_text}"
                )


async def extractColours(url: str, num_colors: int = 1) -> list:
    """Downloads image and runs KMeans clustering to find dominant colors."""
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status != 200:
                return [[0, 0, 0]]  # Fallback to black on error

            content = await response.read()

    # Processing with Pillow/Numpy (CPU intensive, but manageable)
    img = Image.open(BytesIO(content)).convert("RGB")
    img = img.resize((150, 150))

    img_data = np.array(img)
    img_data = img_data.reshape((-1, 3))

    kmeans = KMeans(n_clusters=num_colors, random_state=42, n_init="auto")
    kmeans.fit(img_data)

    colours = kmeans.cluster_centers_.astype(int).tolist()
    return colours


async def fetchToFile(url: str, filename: str) -> discord.File | None:
    # Use headers that mimic your successful browser request
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "image/avif,image/webp,image/apng,image/svg+xml,*/*;q=0.8",
        "Accept-Language": "en-CA,en-US;q=0.9,en;q=0.8",
        "Referer": "https://www.landmarkcinemas.com/",
        "Sec-Fetch-Dest": "image",
        "Sec-Fetch-Mode": "no-cors",
        "Sec-Fetch-Site": "same-site",
        "Sec-Ch-Ua": '"Not(A:Brand";v="8", "Chromium";v="144", "Brave";v="144"',
    }

    try:
        # Increased timeout and added the headers to the session
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(url, timeout=10) as response:
                # Check status manually instead of raise_for_status()
                if response.status != 200:
                    print(f"Failed to fetch image: {response.status} for {url}")
                    return None

                content = await response.read()

        # Process the image with Pillow
        img = Image.open(BytesIO(content))
        buffer = BytesIO()
        img.save(buffer, format=img.format if img.format else "PNG")
        buffer.seek(0)

        return discord.File(fp=buffer, filename=filename)

    except Exception as e:
        print(f"Error processing image {url}: {e}")
        return None


async def urlIsImage(url: str) -> bool:
    """Performs a HEAD request to check if a URL points to an image."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.head(url, allow_redirects=True, timeout=5) as response:
                if response.status != 200:
                    return False

                content_type = response.headers.get("Content-Type", "")
                return content_type.startswith("image/")
    except Exception:
        return False
