import discord
import sys
from discord.ext import commands

from src.classes import *

tarkovCommands = discord.SlashCommandGroup(
    name="tarkov",
    description="Commands for interacting with data from Escape from Tarkov.",
    guild_ids=[799341195109203998],
)


class ItemCommands(commands.Cog):
    ISCOG = True

    def __init__(self, bot):
        self.bot: discord.Bot = bot

        self.description = "Commands for looking up items in Escape from Tarkov."

    itemCommands = discord.SlashCommandGroup(
        name="items",
        description="Commands for looking up items in Escape from Tarkov.",
        guild_ids=[799341195109203998],
        parent=tarkovCommands,
    )

    # @discord.slash_command(description = "Template for commands.", guild_ids=[799341195109203998])
    # async def command(self, ctx: discord.ApplicationContext):
    #     pass


class TaskCommands(commands.Cog):
    ISCOG = True

    def __init__(self, bot):
        self.bot: discord.Bot = bot

        self.description = "Commands for looking up tasks/quests in Escape from Tarkov."

    taskCommands = discord.SlashCommandGroup(
        name="quests",
        description="Commands for looking up tasks/quests in Escape from Tarkov.",
        guild_ids=[799341195109203998],
        parent=tarkovCommands,
    )
    # @discord.slash_command(description = "Template for commands.", guild_ids=[799341195109203998])
    # async def command(self, ctx: discord.ApplicationContext):
    #     pass


def setup(bot):
    currentFile = sys.modules[__name__]

    for name in dir(currentFile):
        obj = getattr(currentFile, name)

        if isinstance(obj, type) and obj.__module__ == currentFile.__name__:
            if obj.ISCOG:
                bot.add_cog(obj(bot))
