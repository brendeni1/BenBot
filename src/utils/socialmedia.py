import aiohttp
from dataclasses import dataclass, asdict
from enum import Enum
from typing import Any, Dict
from src.utils import text, images, dates
from src.classes import *
from src import constants


class MediaType(Enum):
    IMAGE = 1
    VIDEO = 2
    CAROUSEL = 3


class ProductType(Enum):
    FEED = "feed"
    REEL = "reel"
    STORY = "story"


@dataclass(slots=True)
class InstagramUser:
    id: int
    username: str
    isVerified: bool
    avatar: str


@dataclass(slots=True)
class InstagramPost:
    id: int
    user: InstagramUser
    slug: str
    mediaType: MediaType
    productType: ProductType
    timestamp: dates.datetime.datetime
    caption: str
    likes: int
    comments: int
    views: int
    reposts: int
    postLink: str
    mediaLink: str
    thumbnailLink: str
    width: int
    height: int
    hasAudio: bool
    isAd: bool
