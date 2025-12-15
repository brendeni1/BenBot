import discord
import sys
from discord.ext import commands
from src.utils.logging import messageLogs

from src.classes import *


class LogCommands(commands.Cog):
    ISCOG = True

    def __init__(self, bot):
        self.bot: discord.Bot = bot

        self.description = "Commands for log entries."

    logCommands = discord.SlashCommandGroup(
        name="logs",
        description="Commands for log entries.",
        guild_ids=[799341195109203998],
    )

    messageLogCommands = logCommands.create_subgroup(
        name="messages",
        description="Commands for logged messages.",
        guild_ids=[799341195109203998],
    )

    @messageLogCommands.command(
        description="View a logged message by Discord ID.",
        guild_ids=[799341195109203998],
    )
    async def view(
        self,
        ctx: discord.ApplicationContext,
        id: discord.Option(str, description="Discord ID of message."),  # type: ignore
        is_entry_id: discord.Option(
            bool,
            description="Whether the ID should be looked up by BenBot's entry ID instead of Discord's.",
            default=False,
        ),  # type: ignore
    ):
        await ctx.defer()

        try:
            database = LocalDatabase(database="logs")

            targetColumn = "entryID" if is_entry_id else "discordMessageID"

            sql = f"SELECT * FROM messages WHERE {targetColumn} = ?"

            params = (id,)

            result = database.get(sql, params, limit=1)

            if not result:
                raise Exception(
                    "That `{targetColumn}` ID was not found in the database.\n\n*(Hint: BenBot started logging messages on <t:1765771188:D>)*"
                )

            resultObj = messageLogs.dbResultToLogEntry(result[0])

            reply = resultObj.toEmbed()

            await reply.send(ctx)
        except Exception as e:
            # raise e
            reply = EmbedReply(
                "Logs - Messages - Error", "", error=True, description=f"Error: {e}"
            )

            await reply.send(ctx)


def setup(bot):
    currentFile = sys.modules[__name__]

    for name in dir(currentFile):
        obj = getattr(currentFile, name)

        if isinstance(obj, type) and obj.__module__ == currentFile.__name__:
            if obj.ISCOG:
                bot.add_cog(obj(bot))
