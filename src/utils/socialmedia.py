import aiohttp
import os

import discord
from discord.ext import pages

from dataclasses import dataclass, asdict

from enum import Enum

from src.utils import dates, text
from src.classes import *

STEADY_API_TOKEN = os.getenv("STEADY_API_TOKEN")

STEADY_API_BASE_INSTA = "https://api.steadyapi.com/v1/instagram"

INSTAGRAM_POST_BROWSE_TIMEOUT = 890


class InstagramPaginator(pages.Paginator):
    def __init__(self, posts: list["InstagramPost"]):
        self.posts = posts
        postPages = []

        for post in self.posts:
            embedData = post.toEmbed()
            pageEmbeds = (
                [embedData] if isinstance(embedData, discord.Embed) else embedData
            )
            postPages.append(pages.Page(embeds=pageEmbeds))

        super().__init__(
            pages=postPages,
            author_check=False,
            disable_on_timeout=True,
            timeout=INSTAGRAM_POST_BROWSE_TIMEOUT,
        )


async def fetchInstagramPosts(username: str) -> list["InstagramPost"]:
    headers = {"Authorization": f"Bearer {STEADY_API_TOKEN}"}

    params = {"username": username}

    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"{STEADY_API_BASE_INSTA}/posts", headers=headers, params=params
        ) as results:
            results.raise_for_status()

            resultBody = await results.json()

            resultBodyData = resultBody.get("body")

            if resultBodyData == None:
                raise Exception(
                    "There was an error finding the result data in the API response!"
                )

            if resultBodyData == []:
                raise Exception("That user is private and/or does not have any posts!")

            resultBodyData.sort(key=lambda post: post.get("taken_at", 0), reverse=True)

            parsedResults = []

            for rawResult in resultBodyData:
                userData = rawResult.get("user", {})

                user = InstagramUser(
                    id=int(userData.get("id", 0)),
                    username=userData.get("username", ""),
                    isVerified=userData.get("is_verified", False),
                    avatar=userData.get("profile_pic", ""),
                )

                views = (
                    rawResult.get("ig_play_count")
                    or rawResult.get("play_count")
                    or None
                )

                post = InstagramPost(
                    id=int(rawResult.get("id", 0)),
                    user=user,
                    slug=rawResult.get("shortcode", ""),
                    productType=ProductType(rawResult.get("product_type", "unknown")),
                    timestamp=dates.datetime.datetime.fromtimestamp(
                        timestamp=rawResult.get("taken_at", 0)
                    ),
                    caption=rawResult.get("caption", ""),
                    likes=rawResult.get("like_count", None),
                    comments=rawResult.get("comment_count", None),
                    views=views,
                    reposts=rawResult.get("reshare_count", None),
                    postLink=rawResult.get("permalink", ""),
                    mediaLink=rawResult.get("media_url", ""),
                    thumbnailLink=rawResult.get("thumbnail_url", ""),
                    width=rawResult.get("width", 0),
                    height=rawResult.get("height", 0),
                    hasAudio=rawResult.get("has_audio", False),
                    isAd=rawResult.get("is_paid_partnership", False),
                )

                parsedResults.append(post)

            return parsedResults


class ProductType(Enum):
    PICTURE = "feed"
    PICTURES = "carousel_container"
    REEL = "clips"
    STORY = "story"
    MEDIA = "unknown"


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

    def toEmbed(self) -> EmbedReply:
        reply = EmbedReply(
            title=f"{self.productType.name.title()} by {self.user.username}{"<:verified:1467677332201410785>" if self.user.isVerified else ""} on Instagram 🔗↗️",
            commandName="socialmedia",
            url=self.postLink,
            description=text.truncateString(self.caption, maxLength=4000)[0]
            or "***(No Caption)***",
        )

        reply.set_image(url=self.thumbnailLink)
        reply.set_thumbnail(url=self.user.avatar)

        reply.add_field(
            name="Date Posted",
            value=dates.formatSimpleDate(
                timestamp=self.timestamp, discordDateFormat="R"
            ),
        )

        reply.add_field(
            name="Engagement",
            value=f"👁️ {self.likes} ❤️ {self.likes}\n💬 {self.comments} 🔁 {self.comments}",
        )

        reply.add_field(
            name="Link",
            value=self.postLink or "***(No Link Available)***",
            inline=False,
        )

        reply.set_footer(
            text=f"Data by SteadyAPI · Post ID: {self.id} · Instagram User ID: {self.user.id}",
            icon_url="https://i.brendenian.net/ns6VvKUd.jpg",
        )

        return reply
