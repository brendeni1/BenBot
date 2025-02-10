import discord
from discord.ext import commands
import sys

from src.utils import dates
from src.utils import db
from src.utils import guild

from src.classes import *

class JokeModal(discord.ui.Modal):
    def __init__(self, title: str, custom_id: int = None, timeout: int = None):
        super().__init__(title=title, custom_id=custom_id, timeout=timeout)

    async def callback(self, interaction):
        jokeReceivedEmbed=discord.Embed(title="Joke Recieved", description="Your joke has been recieved. Please associate it with a member below. If your joke isn't targeted towards someone, choose 'No Member' in the dropdown.", color=0xff2600)
        jokeReceivedEmbed.set_author(name="BenBot - AddData")
        jokeReceivedEmbed.set_thumbnail(url="https://cdn.discordapp.com/emojis/1337974783396286575.webp?size=96")
        jokeReceivedEmbed.add_field(name="Joke", value=self.children[0], inline=False)
        jokeReceivedEmbed.add_field(name="Punchline", value=self.children[1], inline=False)
        jokeReceivedEmbed.add_field(name="At The Expense Of", value="Not Set - See Below.", inline=False)

        await interaction.response.send_message(embed=jokeReceivedEmbed)

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
            choices=db.listDBs(),
            required=True
        ) # type: ignore
    ):
        if database == "jokes":
            modal = JokeModal("Enter the details of the joke.")

            modal.add_item(discord.ui.InputText(label="First part of the joke", style=discord.InputTextStyle.long))
            modal.add_item(discord.ui.InputText(label="Second part of the joke", style=discord.InputTextStyle.long))

            await ctx.send_modal(modal)
            await modal.wait()

            joke, answer = [child.value for child in modal.children]

            humanMembers = guild.getAllHumanMembers(ctx)

            memberView = SelectGuildMemberView(humanMembers, "Select a server member...", noMemberOption=True)

            await ctx.respond("Please select the member that the joke is making fun of:\n", view=memberView)
            await memberView.wait()

            selection = memberView.children[0]
            expense = selection.values[0]

            # TODO: MAKE THIS SHIT WORK!!!!!! SQL IS UP AND RUNNIGN!!!


def setup(bot):
    pass
    # currentFile = sys.modules[__name__]
    
    # for name in dir(currentFile):
    #     obj = getattr(currentFile, name)
    #     if isinstance(obj, type) and obj.__module__ == currentFile.__name__:
    #         bot.add_cog(obj(bot))