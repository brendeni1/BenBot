import discord
import random
import asyncio
import re

import sys
from discord.ext import commands

from src.utils import db
from src.utils import regexs

from src.classes import AppReply, StandardReply

INQUIRY_REGEXS = [r"^what\?*$", r"^ok$", r"^yea?$", r"^and$"]

class Jokes(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.description = "Funny jokes."
        self.timeout = 15
    
    @discord.slash_command(description = "Says a random funny joke, optionally at someone's expense. Bwahahahaha!!!!", guild_ids=[799341195109203998])
    async def joke(
        self,
        ctx: discord.ApplicationContext,
        expense: discord.Option(
            discord.Member,
            description="Pick a user to target the joke towards.",
            required=False
        ) # type: ignore
    ):
        reply = None
        joke = None

        jokes: list[dict] = db.jsonDB("jokes")

        if isinstance(jokes, AppReply):
            # Error occured!
            await jokes.sendReply(ctx)
            return
        
        if expense and jokes:
            if expense.id not in [joke["expense"] for joke in jokes]:
                reply = AppReply(
                    False,
                    "<:bensad:801246370106179624> That user doesn't have any jokes associated with them..."
                )
            else:
                jokesFiltered = list(filter(lambda joke: joke["expense"] == expense.id, jokes))

                joke = random.choice(jokesFiltered)
        elif jokes:
            joke = random.choice(jokes)
        else:
            reply = AppReply(
                False,
                f"<:bensad:801246370106179624> There aren't any jokes in the file!"
            )

        if not reply:
            reply = AppReply(
                True,
                f"<:sus:816524395605786624> {joke['joke']}\n\n-# Hint: Say 'what', 'yea', 'ok', or 'and' within {self.timeout} seconds for the next part of the joke."
            )
            await reply.sendReply(ctx)

            def check(message: discord.Message):
                if (message.author != ctx.author) and (message.channel == ctx.channel) and (message.author != self.bot.user):
                    badAuthorReply = StandardReply(False, "Find your own joke pal...")
                    
                    asyncio.get_event_loop().create_task(badAuthorReply.sendReply(ctx))

                return all(
                    [
                        regexs.multiRegexMatch(INQUIRY_REGEXS, message.content, re.I),
                        (message.author == ctx.author),
                        (message.author != self.bot.user),
                        (message.channel == ctx.channel)
                    ]
                )
            
            try:
                prompt = await self.bot.wait_for("message", check=check, timeout=self.timeout)
                
                reply = AppReply(
                    True,
                    f"<:joshrad:801246993682137108> {joke["answer"]}"
                )
            except TimeoutError:
                reply = AppReply(
                False,
                f"<:bensad:801246370106179624> You left me hanging...",
                "TimeoutError",
                True
            )
        
        await reply.sendReply(ctx)
        

def setup(bot):
    currentFile = sys.modules[__name__]
    
    for name in dir(currentFile):
        obj = getattr(currentFile, name)
        if isinstance(obj, type) and obj.__module__ == currentFile.__name__:
            bot.add_cog(obj(bot))