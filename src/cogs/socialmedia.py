import discord
import sys
from discord.ext import commands

import instaloader
import os
from itertools import islice

from src.classes import *
from src.utils import dates

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
TEMP_DIR = os.path.join(CURRENT_DIR, '..', 'temp')

INSTA_USERNAME = os.getenv("INSTA_USERNAME")
INSTA_PASSWORD = os.getenv("INSTA_PASSWORD")

CC_USERNAME = "caffeinatedcollectivee"
SP_USERNAME = "sophiapapiaa"

MAX_PINNED_INSTA = 3
class Instagram(commands.Cog):
    ISCOG = True

    def __init__(self, bot):
        self.bot: discord.Bot = bot
        
        self.description = "A collection of Instagram API-using commands that gets the latest post/story from an account."

        # self.useragent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 OPR/107.0.0.0'

        self.instaAPI = instaloader.Instaloader(max_connection_attempts=3)
        
        # self.instaAPI.load_session_from_file(INSTA_USERNAME)
    
    instaGroup = discord.SlashCommandGroup("instagram", "A collection of commands for fetching social media posts/stories.", guild_ids=[799341195109203998])

    def fetchLatestMedia(self, username: str) -> instaloader.Post | instaloader.StoryItem:
        profile = instaloader.Profile.from_username(self.instaAPI.context, username)

        if profile.is_private:
            raise Exception(f"The user {username} has their profile set to private.")
            
        posts: list[instaloader.Post] = list(islice(profile.get_posts(), MAX_PINNED_INSTA + 1))
        
        stories: list[instaloader.Story] = list(islice(self.instaAPI.get_stories([profile.userid]), 1))

        if not posts and not stories:
            return None

        posts.sort(key=lambda post: post.date_utc, reverse=True)

        if stories:
            storyItem: instaloader.StoryItem = list(islice(stories[0].get_items(), 1))[0]

        if stories and posts:
            if storyItem.date_utc > posts[0].date_utc:
                return storyItem
            else:
                return posts[0]
        elif stories and not posts:
            return storyItem
        elif posts and not stories:
            return posts[0]
        else:
            raise ValueError(f"Error when trying to determine what post/story is most recent for {username}")

    @instaGroup.command(description = "Fetches the latest post/story from any valid Instagram user.", guild_ids=[799341195109203998])
    async def latest(
        self,
        ctx: discord.ApplicationContext,
        username = discord.Option(
            str,
            description="Provide the username of the person to fetch the latest media."
        )
    ):
        # await ctx.defer()

        # try:
        #     media = self.fetchLatestMedia(username)

        #     if not media:
        #         reply = EmbedReply("Media - Instagram - Error", "socialmedia", True, description=f"The user {username} doesn't have any posts/stories.")

        #         await ctx.followup.send(embed=reply)
        #         return
            
        #     reply = EmbedReply("Media - Instagram", "socialmedia")

        #     if isinstance(media, instaloader.Post):
        #         profilePic, caption, image, date, commentCount = media.owner_profile.profile_pic_url, media.caption if media.caption else "<No Caption Provided>", media.url, media.date_utc, media.comments
                
        #         reply.set_thumbnail(url=profilePic)
        #         reply.description = f"[{username}](https://www.instagram.com/{username}/) posted a new photo:\n\n{caption}"
        #         reply.set_image(url=image)
        #         reply.set_footer(text=f"{commentCount} Comment(s) · Posted on {dates.formatSimpleDate(timestamp=date)} UTC")
        #     elif isinstance(media, instaloader.StoryItem):
        #         profilePic, caption, image, date, expiry = media.owner_profile.profile_pic_url, media.caption if media.caption else "<No Caption Provided>", media.url, media.date_utc, media.expiring_utc

        #         expiryDelta = dates.deltaInSeconds(expiry, againstTimeNow=True, utc=True)

        #         formattedExpiry = dates.formatSeconds(expiryDelta)
                
        #         reply.set_thumbnail(url=profilePic)
        #         reply.description = f"[{username}](https://www.instagram.com/{username}/) posted a new story:\n\n{caption}"
        #         reply.set_image(url=image)
        #         reply.set_footer(text=f"Story Expires In {formattedExpiry} · Posted on {dates.formatSimpleDate(timestamp=date)} UTC")

        #     await ctx.followup.send(embed=reply)
        # except instaloader.ProfileNotExistsException:
        #     reply = EmbedReply("Media - Instagram - Error", "socialmedia", True, description=f"The user {username} doesn't exist.")

        #     await ctx.followup.send(embed=reply)
        # except Exception as e:
        #     reply = EmbedReply("Media - Instagram - Error", "socialmedia", True, description=f"Error: {e}.")

        #     await ctx.followup.send(embed=reply)
        
        reply = EmbedReply("Media - Instagram - Error", "socialmedia", True, description=f"Error: Instagram is allergic to fun and banned the BenBot account for botting--ironically, they discontinued the only official way to get a users latest Instagram post. Shame on Meta.\n\nThis command is (temporarily??) unavailable.")

        await reply.send(ctx)

    @instaGroup.command(description = "Fetches the latest media from Windsor's most lucrative business, Caffinated Collective. ☕🍵", guild_ids=[799341195109203998])
    async def cc(self, ctx):
        # await ctx.defer()

        # try:
        #     media = self.fetchLatestMedia(CC_USERNAME)

        #     if not media:
        #         reply = EmbedReply("Media - Instagram - Error", "socialmedia", True, description=f"The user {CC_USERNAME} doesn't have any posts/stories.")

        #         await ctx.followup.send(embed=reply)
        #         return
            
        #     reply = EmbedReply("Media - Instagram", "socialmedia")

        #     if isinstance(media, instaloader.Post):
        #         profilePic, caption, image, date, commentCount = media.owner_profile.profile_pic_url, media.caption if media.caption else "<No Caption Provided>", media.url, media.date_utc, media.comments
                
        #         reply.set_thumbnail(url=profilePic)
        #         reply.description = f"[{CC_USERNAME}](https://www.instagram.com/{CC_USERNAME}/) posted a new photo:\n\n{caption}"
        #         reply.set_image(url=image)
        #         reply.set_footer(text=f"{commentCount} Comment(s) · Posted on {dates.formatSimpleDate(timestamp=date)} UTC")
        #     elif isinstance(media, instaloader.StoryItem):
        #         profilePic, caption, image, date, expiry = media.owner_profile.profile_pic_url, media.caption if media.caption else "<No Caption Provided>", media.url, media.date_utc, media.expiring_utc

        #         expiryDelta = dates.deltaInSeconds(expiry, againstTimeNow=True, utc=True)

        #         formattedExpiry = dates.formatSeconds(expiryDelta)
                
        #         reply.set_thumbnail(url=profilePic)
        #         reply.description = f"[{CC_USERNAME}](https://www.instagram.com/{CC_USERNAME}/) posted a new story:\n\n{caption}"
        #         reply.set_image(url=image)
        #         reply.set_footer(text=f"Story Expires In {formattedExpiry} · Posted on {dates.formatSimpleDate(timestamp=date)} UTC")

        #     await ctx.followup.send(embed=reply)
        # except instaloader.ProfileNotExistsException:
        #     reply = EmbedReply("Media - Instagram - Error", "socialmedia", True, description=f"The user {CC_USERNAME} doesn't exist.")

        #     await ctx.followup.send(embed=reply)
        # except Exception as e:
        #     reply = EmbedReply("Media - Instagram - Error", "socialmedia", True, description=f"Error: {e}.")

        #     await ctx.followup.send(embed=reply)
        
        reply = EmbedReply("Media - Instagram - Error", "socialmedia", True, description=f"Error: Instagram is allergic to fun and banned the BenBot account for botting--ironically, they discontinued the only official way to get a users latest Instagram post. Shame on Meta.\n\nThis command is (temporarily??) unavailable.")

        await reply.send(ctx)

    @instaGroup.command(description = "Fetches the latest media from the businesswoman herself, Sophia Papia. 😍💼", guild_ids=[799341195109203998])
    async def sp(self, ctx):
        # await ctx.defer()

        # try:
        #     media = self.fetchLatestMedia(SP_USERNAME)

        #     if not media:
        #         reply = EmbedReply("Media - Instagram - Error", "socialmedia", True, description=f"The user {SP_USERNAME} doesn't have any posts/stories.")

        #         await ctx.followup.send(embed=reply)
        #         return
            
        #     reply = EmbedReply("Media - Instagram", "socialmedia")

        #     if isinstance(media, instaloader.Post):
        #         profilePic, caption, image, date, commentCount = media.owner_profile.profile_pic_url, media.caption if media.caption else "<No Caption Provided>", media.url, media.date_utc, media.comments
                
        #         reply.set_thumbnail(url=profilePic)
        #         reply.description = f"[{SP_USERNAME}](https://www.instagram.com/{SP_USERNAME}/) posted a new photo:\n\n{caption}"
        #         reply.set_image(url=image)
        #         reply.set_footer(text=f"{commentCount} Comment(s) · Posted on {dates.formatSimpleDate(timestamp=date)} UTC")
        #     elif isinstance(media, instaloader.StoryItem):
        #         profilePic, caption, image, date, expiry = media.owner_profile.profile_pic_url, media.caption if media.caption else "<No Caption Provided>", media.url, media.date_utc, media.expiring_utc

        #         expiryDelta = dates.deltaInSeconds(expiry, againstTimeNow=True, utc=True)

        #         formattedExpiry = dates.formatSeconds(expiryDelta)
                
        #         reply.set_thumbnail(url=profilePic)
        #         reply.description = f"[{SP_USERNAME}](https://www.instagram.com/{SP_USERNAME}/) posted a new story:\n\n{caption}"
        #         reply.set_image(url=image)
        #         reply.set_footer(text=f"Story Expires In {formattedExpiry} · Posted on {dates.formatSimpleDate(timestamp=date)} UTC")

        #     await ctx.followup.send(embed=reply)
        # except instaloader.ProfileNotExistsException:
        #     reply = EmbedReply("Media - Instagram - Error", "socialmedia", True, description=f"The user {SP_USERNAME} doesn't exist.")

        #     await ctx.followup.send(embed=reply)
        # except Exception as e:
        #     reply = EmbedReply("Media - Instagram - Error", "socialmedia", True, description=f"Error: {e}.")

        #     await ctx.followup.send(embed=reply)
        
        reply = EmbedReply("Media - Instagram - Error", "socialmedia", True, description=f"Error: Instagram is allergic to fun and banned the BenBot account for botting--ironically, they discontinued the only official way to get a users latest Instagram post. Shame on Meta.\n\nThis command is (temporarily??) unavailable.")

        await reply.send(ctx)

def setup(bot):
    currentFile = sys.modules[__name__]
    
    for name in dir(currentFile):
        obj = getattr(currentFile, name)

        if isinstance(obj, type) and obj.__module__ == currentFile.__name__:
            if obj.ISCOG:
                bot.add_cog(obj(bot))