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
        
        self.description = "A collection of Instagram API-using commands that get the latest posts from an account."

        self.useragent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 OPR/107.0.0.0'

        self.instaAPI = instaloader.Instaloader(max_connection_attempts=3)
        
        self.instaAPI.load_session_from_file(INSTA_USERNAME)
    
    instaGroup = discord.SlashCommandGroup("instagram", "A collection of commands for fetching social media posts.", guild_ids=[799341195109203998])

    def fetchLatestPost(self, username: str) -> instaloader.Post:
        profile = instaloader.Profile.from_username(self.instaAPI.context, username)

        if profile.is_private:
            raise Exception(f"The user {username} has their profile set to private.")
            
        posts = list(islice(profile.get_posts(), MAX_PINNED_INSTA + 1))

        if not posts:
            return None

        posts.sort(key=lambda post: post.date_utc, reverse=True)

        return posts[0]
    
    def fetchEssentialsFromPost(self, post: instaloader.Post):
        if not post:
            raise ValueError("No post specified!")
        
        details = {
            "username": post.owner_username,
            "profilePicture": post.owner_profile.profile_pic_url,
            "caption": post.caption,
            "date": post.date_utc,
            "commentCount": post.comments,
            "media": post.url
        }

        return details

    @instaGroup.command(description = "Fetches the latest post from any valid Instagram user.", guild_ids=[799341195109203998])
    async def latest(
        self,
        ctx: discord.ApplicationContext,
        username = discord.Option(
            str,
            description="Provide the username of the person to fetch the latest post."
        )
    ):
        await ctx.defer()

        try:
            post = self.fetchLatestPost(username)

            if not post:
                reply = EmbedReply("Posts - Instagram - Error", "posts", True, description=f"The user {username} doesn't have any posts.")

                await ctx.followup.send(embed=reply)
                return
            
            reply = EmbedReply("Posts - Instagram", "posts")

            postDetails = self.fetchEssentialsFromPost(post)

            reply.set_thumbnail(url=postDetails["profilePicture"])
            reply.description = f"[{username}](https://www.instagram.com/{username}/) posted:\n\n{postDetails["caption"]}"
            reply.set_image(url=postDetails["media"])
            reply.set_footer(text=f"{postDetails["commentCount"]} Comment(s) · Posted on {dates.formatSimpleDate(timestamp=postDetails["date"])} UTC")

            await ctx.followup.send(embed=reply)
        except instaloader.ProfileNotExistsException:
            reply = EmbedReply("Posts - Instagram - Error", "posts", True, description=f"The user {username} doesn't exist.")

            await ctx.followup.send(embed=reply)
        except Exception as e:
            reply = EmbedReply("Posts - Instagram - Error", "posts", True, description=f"Error: {e}.")

            await ctx.followup.send(embed=reply)

    @instaGroup.command(description = "Fetches the latest Caffinated Collective post. ☕🍵", guild_ids=[799341195109203998])
    async def cc(self, ctx):
        await ctx.defer()

        try:
            post = self.fetchLatestPost(CC_USERNAME)

            if not post:
                reply = EmbedReply("Posts - Instagram - Error", "posts", True, description=f"The user {CC_USERNAME} doesn't have any posts.")

                await ctx.followup.send(embed=reply)
                return
            
            reply = EmbedReply("Posts - Instagram", "posts")

            postDetails = self.fetchEssentialsFromPost(post)

            reply.set_thumbnail(url=postDetails["profilePicture"])
            reply.description = f"[{CC_USERNAME}](https://www.instagram.com/{CC_USERNAME}/) posted:\n\n{postDetails["caption"]}"
            reply.set_image(url=postDetails["media"])
            reply.set_footer(text=f"{postDetails["commentCount"]} Comment(s) · Posted on {dates.formatSimpleDate(timestamp=postDetails["date"])}")

            await ctx.followup.send(embed=reply)
        except instaloader.ProfileNotExistsException:
            reply = EmbedReply("Posts - Instagram - Error", "posts", True, description=f"The user {CC_USERNAME} doesn't exist.")

            await ctx.followup.send(embed=reply)
        except Exception as e:
            reply = EmbedReply("Posts - Instagram - Error", "posts", True, description=f"Error when retrieving post: {e}.")

            await ctx.followup.send(embed=reply)

    @instaGroup.command(description = "Fetches the latest post from Sophia Papia. 😍💼", guild_ids=[799341195109203998])
    async def sp(self, ctx):
        await ctx.defer()

        try:
            post = self.fetchLatestPost(SP_USERNAME)

            if not post:
                reply = EmbedReply("Posts - Instagram - Error", "posts", True, description=f"The user {SP_USERNAME} doesn't have any posts.")

                await ctx.followup.send(embed=reply)
                return
            
            reply = EmbedReply("Posts - Instagram", "posts")

            postDetails = self.fetchEssentialsFromPost(post)

            reply.set_thumbnail(url=postDetails["profilePicture"])
            reply.description = f"[{SP_USERNAME}](https://www.instagram.com/{SP_USERNAME}/) posted:\n\n{postDetails["caption"]}"
            reply.set_image(url=postDetails["media"])
            reply.set_footer(text=f"{postDetails["commentCount"]} Comment(s) · Posted on {dates.formatSimpleDate(timestamp=postDetails["date"])}")

            await ctx.followup.send(embed=reply)
        except instaloader.ProfileNotExistsException:
            reply = EmbedReply("Posts - Instagram - Error", "posts", True, description=f"The user {SP_USERNAME} doesn't exist.")

            await ctx.followup.send(embed=reply)
        except Exception as e:
            reply = EmbedReply("Posts - Instagram - Error", "posts", True, description=f"Error when retrieving post: {e}.")

            await ctx.followup.send(embed=reply)

def setup(bot):
    currentFile = sys.modules[__name__]
    
    for name in dir(currentFile):
        obj = getattr(currentFile, name)

        if isinstance(obj, type) and obj.__module__ == currentFile.__name__:
            if obj.ISCOG:
                bot.add_cog(obj(bot))