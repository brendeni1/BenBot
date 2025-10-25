import discord
import random
import re
import asyncio

import sys
from discord.ext import commands

from src.utils import regexs
from src.utils import dates

from src.classes import *

INQUIRY_REGEXS = [
    r"^who\?*$",
    r"^what\?*$",
    r"^when\?*$",
    r"^where\?*$",
    r"^why\?*$",
    r"^how\?*$",
    r"^ok$",
    r"^yea?$",
    r"^and$",
]


class Jokes(commands.Cog):
    ISCOG = True

    def __init__(self, bot):
        self.bot: discord.Bot = bot
        self.description = "Funny jokes."
        self.timeout = 15

    @discord.slash_command(
        description="Says a random funny joke, optionally at someone's expense. Bwahahahaha!!!!",
        guild_ids=[799341195109203998],
    )
    async def joke(
        self,
        ctx: discord.ApplicationContext,
        expense: discord.Option(
            discord.Member,
            description="Pick a user to target the joke towards.",
            required=False,
        ),  # type: ignore
        id: discord.Option(
            int,
            description="Pick a joke by ID. To see IDs: /view table:jokes. Overrides expense parameter.",
            required=False,
        ),  # type: ignore
    ):
        joke = None

        debugReply = EmbedReply("Jokes - Error", "jokes", True)

        try:
            database: LocalDatabase = LocalDatabase()

            tables = database.listTables()

            if "jokes" not in tables:
                raise Exception("No jokes table...")

            jokes: list[tuple] = database.get("SELECT * FROM jokes")

        except Exception as e:
            debugReply.description = (
                f"There was an error loading the jokes database.\n\n{e}"
            )

            await debugReply.send(ctx)
            return
        if id and jokes:
            filteredJokes: list[tuple] = database.get(
                "SELECT * FROM jokes WHERE id = ?", (id,)
            )

            if not filteredJokes:
                debugReply.description = (
                    "<:bensad:801246370106179624> That ID doesn't exist..."
                )

                await debugReply.send(ctx)
                return
            else:
                joke = random.choice(filteredJokes)
        elif expense and jokes:
            filteredJokes: list[tuple] = database.get(
                "SELECT * FROM jokes WHERE expense = ?", (expense.id,)
            )

            if not filteredJokes:
                debugReply.description = "<:bensad:801246370106179624> That user doesn't have any jokes associated with them..."

                await debugReply.send(ctx)
                return
            else:
                joke = random.choice(filteredJokes)
        elif jokes:
            joke = random.choice(jokes)
        else:
            debugReply.description = (
                "<:bensad:801246370106179624> There aren't any jokes in the file!"
            )
            await debugReply.send(ctx)

        initialReply = EmbedReply("Jokes - Setup", "jokes")

        (
            jokeID,
            jokeCreatedBy,
            jokeCreatedAt,
            jokeCreatedGuild,
            jokeCreatedChannel,
            jokeSetup,
            jokePunchline,
            jokeExpense,
        ) = joke

        jokeCreatedAt = dates.formatSimpleDate(timestamp=jokeCreatedAt, discordDateFormat="f")
        jokeCreatedBy = await self.bot.get_or_fetch_user(jokeCreatedBy)

        initialReply.description = f"<:sus:816524395605786624> {jokeSetup}"
        initialReply.set_footer(
            text=f"Joke ID: {jokeID} · Hint: Say 'who/what/when/where/why/how', 'yea', 'ok', or 'and' within {self.timeout} seconds for the punchline."
        )

        await initialReply.send(ctx)

        def check(message: discord.Message):
            if (
                (message.author != ctx.author)
                and (message.channel == ctx.channel)
                and (message.author != self.bot.user)
            ):
                badAuthorReply = EmbedReply(
                    "Jokes - Wrong person!!",
                    "jokes",
                    True,
                    description="Find your own joke pal...",
                )
                asyncio.get_event_loop().create_task(
                    badAuthorReply.send(ctx, quote=False)
                )

            return all(
                [
                    regexs.multiRegexMatch(INQUIRY_REGEXS, message.content, re.I),
                    (message.author == ctx.author),
                    (message.author != self.bot.user),
                    (message.channel == ctx.channel),
                ]
            )

        punchlineReply = EmbedReply(
            "Jokes - Punchline",
            "jokes",
            description=f"<:joshrad:801246993682137108> {jokePunchline}",
        )
        
        punchlineReply.add_field(name="Joke Author", value=jokeCreatedBy.mention)
        punchlineReply.add_field(name="Joke Created", value=jokeCreatedAt)
        
        punchlineReply.set_footer(
            text=f"Joke ID: {jokeID}"
        )

        try:
            await self.bot.wait_for("message", check=check, timeout=self.timeout)

            await punchlineReply.send(ctx)
        except TimeoutError:
            timeoutReply = EmbedReply(
                "Jokes - Timeout Error",
                "jokes",
                error=True,
                description="<:bensad:801246370106179624> You left me hanging...",
            )

            await timeoutReply.send(ctx)


def setup(bot):
    currentFile = sys.modules[__name__]

    for name in dir(currentFile):
        obj = getattr(currentFile, name)

        if isinstance(obj, type) and obj.__module__ == currentFile.__name__:
            if obj.ISCOG:
                bot.add_cog(obj(bot))
