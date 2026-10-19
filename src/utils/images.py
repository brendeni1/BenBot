import discord
import aiohttp
import os
import numpy as np
from io import BytesIO
from PIL import Image
from sklearn.cluster import KMeans
from html.parser import HTMLParser
from urllib.parse import urlparse, urljoin

FILE_HOST_PAGES = {"files.brendenian.net"}
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; DiscordBot)"}


async def uploadToFlare(image: discord.Attachment | bytes):
    token = os.getenv("FLARE_BENBOT_TOKEN")
    if not token:
        raise RuntimeError("Missing FLARE_BENBOT_TOKEN")

    flareEndpoint = "https://files.brendenian.net/api/files"

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

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(flareEndpoint, data=data, headers=headers) as response:
            if response.status != 200:
                error_text = await response.text()
                raise Exception(
                    f"Flare upload failed ({response.status}): {error_text}"
                )

            response_data = await response.json()
            raw_url = response_data.get("data", {}).get("rawUrl")
            if not raw_url:
                raise RuntimeError("Flare upload response did not include data.rawUrl")
            return raw_url


async def extractColours(url: str, num_colors: int = 1) -> list:
    """Downloads image and runs KMeans clustering to find dominant colors."""
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; DiscordBot)",
        "Accept": "image/*,*/*;q=0.8",
    }
    content = b""
    contentType = None

    try:
        timeout = aiohttp.ClientTimeout(total=10)
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(url, timeout=timeout) as response:
                contentType = response.headers.get("Content-Type")
                if response.status != 200:
                    return [[0, 0, 0]]  # Fallback to black on error
                content = await response.read()

        img = Image.open(BytesIO(content)).convert("RGB")
    except Exception as e:
        print(
            f"extractColours failed for {url}: {e!r} "
            f"(content-type={contentType}, first bytes={content[:32]!r})"
        )
        return [[0, 0, 0]]

    img = img.resize((150, 150))

    img_data = np.array(img).reshape((-1, 3))

    kmeans = KMeans(n_clusters=num_colors, random_state=42, n_init="auto")
    kmeans.fit(img_data)

    return kmeans.cluster_centers_.astype(int).tolist()


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


class _ImageTagParser(HTMLParser):
    """Collects og:image-style meta tags and <img> sources from an HTML page."""

    def __init__(self):
        super().__init__()
        self.meta_images = []
        self.img_srcs = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "meta":
            key = a.get("property") or a.get("name")
            if key in ("og:image", "og:image:url", "twitter:image") and a.get("content"):
                self.meta_images.append(a["content"])
        elif tag == "img" and a.get("src"):
            self.img_srcs.append(a["src"])


async def _isDirectImage(session: aiohttp.ClientSession, url: str) -> bool:
    """HEAD check, falling back to a streamed GET if HEAD isn't supported."""
    timeout = aiohttp.ClientTimeout(total=5)
    try:
        async with session.head(url, allow_redirects=True, timeout=timeout) as resp:
            if resp.status == 200:
                return resp.headers.get("Content-Type", "").startswith("image/")
            if resp.status not in (403, 405, 501):
                return False
    except Exception:
        pass
    try:
        async with session.get(url, allow_redirects=True, timeout=timeout) as resp:
            return resp.status == 200 and resp.headers.get("Content-Type", "").startswith("image/")
    except Exception:
        return False


async def resolveImageUrl(url: str) -> str | None:
    """Returns a direct image URL for `url`, or None if it isn't/doesn't reference an image."""
    try:
        async with aiohttp.ClientSession(headers=HEADERS) as session:
            if await _isDirectImage(session, url):
                return url

            parsed = urlparse(url)
            host = (parsed.hostname or "").lower()
            if host not in FILE_HOST_PAGES:
                return None

            # files.brendenian.net page links map directly to <page>/raw
            path = parsed.path.rstrip("/")
            if not path.endswith("/raw"):
                rawUrl = parsed._replace(path=path + "/raw", query="", fragment="").geturl()
                if await _isDirectImage(session, rawUrl):
                    return rawUrl

            # Fallback: scrape the page for og:image / <img>
            timeout = aiohttp.ClientTimeout(total=5)
            async with session.get(url, allow_redirects=True, timeout=timeout) as resp:
                if resp.status != 200 or "text/html" not in resp.headers.get("Content-Type", ""):
                    return None
                html = await resp.text()
                base = str(resp.url)

            parser = _ImageTagParser()
            parser.feed(html)

            for candidate in parser.meta_images + parser.img_srcs:
                full = urljoin(base, candidate)
                if await _isDirectImage(session, full):
                    return full
    except Exception:
        pass
    return None


async def urlIsImage(url: str) -> bool:
    """True if the URL is an image, or (for files.brendenian.net) a page referencing one."""
    return await resolveImageUrl(url) is not None