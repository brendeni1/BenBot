import discord
from discord.ext import commands
import sys

from src.utils import dates
from src.utils import db
from src.utils import guild

from src.classes import *

DATABASES: list[str] = db.listDBs()

class Data(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @discord.slash_command(description = "Add data to a selection of databases within the bot.", guild_ids=[799341195109203998])
    async def adddata(
        self,
        ctx: discord.ApplicationContext,
        database: discord.Option(
            str,
            description="Provide a database to add data to.",
            choices=DATABASES,
            required=True
        ) # type: ignore
    ):
        if database == "jokes":
            modal = DataModal("Enter the details of the joke.")

            modal.add_item(discord.ui.InputText(label="First part of the joke", style=discord.InputTextStyle.long))
            modal.add_item(discord.ui.InputText(label="Second part of the joke", style=discord.InputTextStyle.long))

            await ctx.send_modal(modal)
            await modal.wait()

            joke, answer = [child.value for child in modal.children]

            humanMembers = guild.getAllHumanMembers(ctx)

            memberView = SelectGuildMemberView(humanMembers, "Select a server member...", True)

            await ctx.respond("Please select the member that the joke is making fun of:\n", view=memberView)
            await memberView.wait()

            selection = memberView.children[0]
            expense = selection.values[0]

            reply = AppReply(
                True,
                f"{joke=}{answer=}<@{expense}>"
            )

            await reply.sendReply(ctx)

            # TODO: ADD CATCH FOR THE "DO NOT ASSOCIATE MEMBER (id:0) AND MAKE IT INTEGRATE WITH THE JSON FILE SO THAT THE JOKES ACTUALLY GET RECORDED."


def setup(bot):
    currentFile = sys.modules[__name__]
    
    for name in dir(currentFile):
        obj = getattr(currentFile, name)
        if isinstance(obj, type) and obj.__module__ == currentFile.__name__:
            bot.add_cog(obj(bot))