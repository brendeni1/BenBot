import discord
from discord.ext import commands
import sys

from src.utils import dates
from src.utils import db

from src.classes import AppReply, StandardReply

class MyCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @discord.slash_command(description = "Example command.", guild_ids=[799341195109203998])
    async def joke(
        self,
        ctx: discord.ApplicationContext
    ):
        pass 

def setup(bot):
    pass
    # currentFile = sys.modules[__name__]
    
    # for name in dir(currentFile):
    #     obj = getattr(currentFile, name)
    #     if isinstance(obj, type) and obj.__module__ == currentFile.__name__:
    #         bot.add_cog(obj(bot))