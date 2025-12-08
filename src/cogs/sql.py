import discord
from discord.ext import commands
from discord.ext.pages import Paginator
import sys

from src.utils import dates
from src.utils import db

from src.classes import *

RESULTS_PER_PAGE: int = 5


def paginateDBResults(
    results: list[tuple], query: str, idIndexInResult: int
) -> list[discord.Embed]:
    pageList = []
    rowCounter = 1

    for chunk in range(0, len(results), RESULTS_PER_PAGE):
        page = EmbedReply(
            "SQL - Get - Results",
            "sql",
            description=f"Results of your query ({query}):",
        )

        for result in results[chunk : chunk + RESULTS_PER_PAGE]:
            title = f"Row {rowCounter} (ID: {result[idIndexInResult]})"
            value = "\n".join(
                [
                    f"Col {colIdx}: {text.truncateString(str(value), maxLength=100)[0]}"
                    for colIdx, value in enumerate(result, start=1)
                ]
            )

            page.add_field(name=title, value=value, inline=False)

            rowCounter += 1

        pageList.append(page)

    return pageList


class Sql(commands.Cog):
    ISCOG = True

    def __init__(self, bot):
        self.bot: discord.Bot = bot

    @discord.slash_command(
        description="Run a SQL command on a database.", guild_ids=[799341195109203998]
    )
    async def sql(
        self,
        ctx: discord.ApplicationContext,
        database: discord.Option(
            str,
            description="Pick a database to execute on.",
            choices=db.listDBs(filterByExtension=".db"),
        ),  # type: ignore
        action: discord.Option(
            str,
            description="What action are you taking?",
            choices=["get", "set", "query"],
        ),  # type: ignore
        query: discord.Option(
            str, description="Provide a query to execute."
        ),  # type: ignore
        limit: discord.Option(
            int, description="Provide a limit of results (GET ONLY).", default=0
        ),  # type: ignore
    ):
        try:
            if not await self.bot.is_owner(ctx.user):
                raise Exception("This command is for the bot owner only.")

            databaseConnection: LocalDatabase = LocalDatabase(database)

            if action == "get":
                results = databaseConnection.getRaw(query, limit)

                if not results:
                    raise Exception("No results found for that query!")

                paginatedResults = paginateDBResults(results, query, idIndexInResult=0)

                paginator = Paginator(pages=paginatedResults)

                await paginator.respond(ctx.interaction)
            elif action == "set":
                reply = EmbedReply("SQL - Set", "sql")

                success = databaseConnection.setOneRaw(query)

                reply.description = f"Successfully set your data ({query})."

                await reply.send(ctx)
            elif action == "query":
                reply = EmbedReply("SQL - Query", "sql")

                databaseConnection.queryRaw(query)

                reply.description = f"Ran your query ({query})."

                await reply.send(ctx)
            else:
                raise Exception("Invalid action!")
        except Exception as e:
            reply = EmbedReply(
                "SQL - Error", "sql", error=True, description=f"Error: {e}"
            )

            await reply.send(ctx)


def setup(bot):
    currentFile = sys.modules[__name__]

    for name in dir(currentFile):
        obj = getattr(currentFile, name)

        if isinstance(obj, type) and obj.__module__ == currentFile.__name__:
            if obj.ISCOG:
                bot.add_cog(obj(bot))
