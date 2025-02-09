import discord
from discord.ext import commands
import sys

from src.utils import dates
from src.utils import db

from src.classes import *

DATABASES: list[str] = db.listDBs(filterByExtension=".db")

class Sql(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @discord.slash_command(description = "Run a SQL command on a database.", guild_ids=[799341195109203998])
    @commands.is_owner()
    async def sql(
        self,
        ctx: discord.ApplicationContext,
        database: discord.Option(
            str,
            description="Pick a database to execute on.",
            choices=DATABASES
        ), # type: ignore
        action: discord.Option(
            str,
            description="What action are you taking?",
            choices=["get", "setOne", "query"]
        ), # type: ignore
        query: discord.Option(
            str,
            description="Provide a query to execute."
        ), # type: ignore
        limit: discord.Option(
            int,
            description="Provide a limit of results (GET ONLY).",
            required=False
        ) # type: ignore
    ):
        reply = EmbedReply("test", "sql", description="test")
        await reply.send(ctx)
        # TODO: MAKE IT SO THIS COMMAND ACTUALLY DOES SHIT AND YEA>:)
    
    @sql.error
    async def onError(self, ctx: discord.ApplicationContext, error: discord.DiscordException):
        if isinstance(error, commands.NotOwner):
            notOwnerReply = EmbedReply("SQL - Not Owner Error", "sql", "True", description="Sorry, only the bot owner can use this command!")
            await notOwnerReply.send(ctx)
        else:
            raise error

def setup(bot):
    currentFile = sys.modules[__name__]
    
    for name in dir(currentFile):
        obj = getattr(currentFile, name)
        if isinstance(obj, type) and obj.__module__ == currentFile.__name__:
            bot.add_cog(obj(bot))