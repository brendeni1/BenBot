import discord
from discord.ext import commands
import sys

from src.utils import dates
from src.utils import db

from src.classes import *

MAX_FIELDS_EMBED: int = 25

class Sql(commands.Cog):
    ISCOG = True

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
            choices=db.listDBs(filterByExtension=".db")
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
            default=0
        ) # type: ignore
    ):        
        databaseConnection: LocalDatabase = LocalDatabase(database)

        if action == "get":
            try:
                reply = EmbedReply("SQL - Get", "sql")

                results = databaseConnection.getRaw(query, limit)

                if len(results) >= MAX_FIELDS_EMBED:
                    resultsTrimmed = results[:MAX_FIELDS_EMBED - 1]
                    
                    resultsLeft = len(results[MAX_FIELDS_EMBED:])

                    results.append(f"... and {resultsLeft} more")
                
                reply.description = f"Results of your query ({query}):"
                
                for num, result in enumerate(results, 1):
                    reply.add_field(name=f"Row {num}", value=", ".join([str(value) for value in result]), inline=False)
                
                await reply.send(ctx)
            except Exception as e:
                reply = EmbedReply("SQL - Error", "sql", True, description=e)

                await reply.send(ctx)
        elif action == "setOne":
            try:
                reply = EmbedReply("SQL - Set One", "sql")

                success = databaseConnection.setOneRaw(query)
                
                reply.description = f"Successfully set your data ({query})."

                await reply.send(ctx)
            except Exception as e:
                reply = EmbedReply("SQL - Error", "sql", True, description=e)

                await reply.send(ctx)
        elif action == "query":
            try:
                reply = EmbedReply("SQL - Query", "sql")

                success = databaseConnection.queryRaw(query)
                
                reply.description = f"Successfully ran your query ({query})."

                await reply.send(ctx)
            except Exception as e:
                reply = EmbedReply("SQL - Error", "sql", True, description=e)

                await reply.send(ctx)
        else:
            reply = EmbedReply("SQL - Error", "sql", True, description="You somehow ran an ACTION parameter which doesn't exist.")

            await reply.send(ctx)
    
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
            if obj.ISCOG:
                bot.add_cog(obj(bot))