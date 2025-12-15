import discord
import sys
from discord.ext import commands

from src.classes import *
from src import constants
from src.utils import stats

LEADERBOARD_AMOUNT = 10


class StatsCommand(commands.Cog):
    ISCOG = True

    def __init__(self, bot):
        self.bot: discord.Bot = bot

        self.description = "Commands for viewing the usage stats of the bot's commands."

    statsGroup = discord.SlashCommandGroup(
        "stats",
        "Use these commands to view stats on the bot.",
        guild_ids=[799341195109203998],
    )

    statsCommandUsage = statsGroup.create_subgroup(
        "commandusage",
        "Use these commands to view stats for command usage.",
        guild_ids=[799341195109203998],
    )

    @statsCommandUsage.command(
        description="View the top commands and most active users.",
        guild_ids=[799341195109203998],
    )
    async def top(self, ctx: discord.ApplicationContext):
        await ctx.defer()

        try:
            logEntries = stats.fetchCommandLogs()

            if not logEntries:
                raise Exception("No one has used a command matching those filters!")

            topCommands = stats.tallyByEntryAttribute(
                entries=logEntries, key="qualifiedCommandName", reverseSort=True
            )
            topUsers = stats.tallyByEntryAttribute(
                entries=logEntries, key="invocationUserID", reverseSort=True
            )

            reply = EmbedReply(
                "Stats - Commands - Top",
                "stats",
                description="Here is the leaderboard for the top commands and users.",
            )

            formattedTopCommands = ""

            for idx, command in enumerate(topCommands, start=1):
                formattedTopCommands += f"{constants.RANKING_MEDALS.get(str(idx), "")} {idx}. `/{command[0]}` ({command[1]} Uses)\n"

                if idx == LEADERBOARD_AMOUNT:
                    break

            reply.add_field(
                name="🤖 Top Commands", value=formattedTopCommands, inline=False
            )

            formattedTopUsers = ""

            for idx, user in enumerate(topUsers, start=1):
                formattedTopUsers += f"{constants.RANKING_MEDALS.get(str(idx), "")} {idx}. <@{user[0]}> ({user[1]} Commands Sent)\n"

                if idx == LEADERBOARD_AMOUNT:
                    break

            reply.add_field(name="👤 Top Users", value=formattedTopUsers, inline=False)

            await reply.send(ctx)

        except Exception as e:
            reply = EmbedReply(
                "Stats - Command Usage - Error",
                "",
                error=True,
                description=f"Error: {e}",
            )

            await reply.send(ctx)


def setup(bot):
    currentFile = sys.modules[__name__]

    for name in dir(currentFile):
        obj = getattr(currentFile, name)

        if isinstance(obj, type) and obj.__module__ == currentFile.__name__:
            if obj.ISCOG:
                bot.add_cog(obj(bot))
