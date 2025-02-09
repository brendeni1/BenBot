import discord
import random
import re
import asyncio

import sys
from discord.ext import commands

from src.utils import db
from src.utils import regexs

from src.classes import *

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
        joke = None

        debugReply = EmbedReply("Jokes - Error", "jokes", True)

        try:
            jokes: list[dict] = db.jsonDB("jokes")
        except FileNotFoundError:
            debugReply.description = "There was an error finding the jokes database."
            await debugReply.send(ctx)
            return
        
        if expense and jokes:
            if expense.id not in [joke["expense"] for joke in jokes]:
                debugReply.description = "<:bensad:801246370106179624> That user doesn't have any jokes associated with them..."
                
                await debugReply.send(ctx)
                return
            else:
                jokesFiltered = list(filter(lambda joke: joke["expense"] == expense.id, jokes))

                joke = random.choice(jokesFiltered)
        elif jokes:
            joke = random.choice(jokes)
        else:
            debugReply.description = "<:bensad:801246370106179624> There aren't any jokes in the file!"
            await debugReply.send(ctx)
        
        initialReply = EmbedReply("Jokes", "jokes")

        initialReply.description = f"<:sus:816524395605786624> {joke['joke']}"
        initialReply.set_footer(text=f"Hint: Say 'what', 'yea', 'ok', or 'and' within {self.timeout} seconds for the next part of the joke.")

        await initialReply.send(ctx)

        def check(message: discord.Message):
            if (message.author != ctx.author) and (message.channel == ctx.channel) and (message.author != self.bot.user):
                badAuthorReply = EmbedReply("Jokes - Wrong person!!", "jokes", True, description="Find your own joke pal...")
                asyncio.get_event_loop().create_task(badAuthorReply.send(ctx, quote=False))

            return all(
                [
                    regexs.multiRegexMatch(INQUIRY_REGEXS, message.content, re.I),
                    (message.author == ctx.author),
                    (message.author != self.bot.user),
                    (message.channel == ctx.channel)
                ]
            )
        
        punchlineReply = EmbedReply("Jokes", "jokes", description=f"<:joshrad:801246993682137108> {joke["answer"]}")

        try:
            await self.bot.wait_for("message", check=check, timeout=self.timeout)
            
            await punchlineReply.send(ctx)
        except TimeoutError:
            timeoutReply = EmbedReply("Jokes - Timeout Error", "jokes", error=True, description="<:bensad:801246370106179624> You left me hanging...")
            
            await timeoutReply.send(ctx)

def setup(bot):
    currentFile = sys.modules[__name__]
    
    for name in dir(currentFile):
        obj = getattr(currentFile, name)
        if isinstance(obj, type) and obj.__module__ == currentFile.__name__:
            bot.add_cog(obj(bot))