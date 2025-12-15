import discord
from discord.ext import commands
import sys

import asyncio

from src.utils import dates
from src.utils import guild

from src.classes import *

MAX_FIELDS_EMBED: int = 25

EDITABLE_TABLES: list[str] = [
    "jokes",
    "taylortracker"
]

class JokeModal(discord.ui.Modal):
    ISCOG = False

    def __init__(self, title: str, custom_id: int = None, timeout: int = None):
        super().__init__(title=title, custom_id=custom_id, timeout=timeout)

    async def callback(self, interaction):
        jokeReceivedEmbed = EmbedReply("Add Data - Recieved", "data", description="Your joke has been recieved. Please associate it with a member below. If your joke isn't targeted towards someone, choose 'No Member' in the dropdown.")
        
        jokeReceivedEmbed.add_field(name="Joke", value=self.children[0].value, inline=False)
        jokeReceivedEmbed.add_field(name="Punchline", value=self.children[1].value, inline=False)
        jokeReceivedEmbed.add_field(name="At The Expense Of", value="Not Set - See Below.", inline=False)

        await interaction.response.send_message(embed=jokeReceivedEmbed, ephemeral=True)

class DataCommands(commands.Cog):
    ISCOG = True
    tables = LocalDatabase().listTables()

    def __init__(self, bot):
        self.bot = bot

    data = discord.SlashCommandGroup("data", "A collection of commands for manipulating data within the bot's DB.", guild_ids=[799341195109203998])
    
    @data.command(description = "Add data to a table in the bot's db. Select table > click Enter > further instructions presented.", guild_ids=[799341195109203998])
    async def add(
        self,
        ctx: discord.ApplicationContext,
        table: discord.Option(
            str,
            description="Provide a database table to add data to.",
            choices=tables,
            required=True
        ) # type: ignore
    ):
        database = LocalDatabase()

        if table == "jokes":
            modal = JokeModal("Enter the details of the joke.")

            modal.add_item(discord.ui.InputText(label="Enter the joke's setup line:", style=discord.InputTextStyle.long))
            modal.add_item(discord.ui.InputText(label="Enter the joke's punchline:", style=discord.InputTextStyle.long))

            await ctx.send_modal(modal)
            await modal.wait()

            setup, punchline = [child.value for child in modal.children]
            createdBy, createdGuild, createdChannel = ctx.author.id, ctx.guild.id, ctx.channel.id

            humanMembers = guild.getAllHumanMembers(ctx)

            humanMembers.sort(key = lambda member: member.nick if member.nick else member.name)

            memberView = SelectGuildMemberView(humanMembers, "Select a server member...", noMemberOption=True)

            memberSelectionReply = EmbedReply("Add Data - Add Member", "data", description="Please select the member that the joke is making fun of:")
            
            selectionMsg = await ctx.respond(embed=memberSelectionReply, view=memberView)
            
            timedOut = await memberView.wait()
            
            if timedOut:
                timeoutReply = EmbedReply("Add Data - Timeout", "data", True, description=f"Joke not added.\n\nYou took too long to select a member, please re-add the joke and use the dropdown.")

                await timeoutReply.send(ctx, True, ephemeral=True)

                await asyncio.sleep(15)
                
                try:
                    await selectionMsg.delete()
                except discord.NotFound:
                    pass
                
                return

            selection = memberView.children[0]
            expense = selection.values[0]

            try:
                database.setOne(f"INSERT INTO jokes (createdBy, createdGuild, createdChannel, setup, punchline, expense) VALUES (?,?,?,?,?,?)", (createdBy, createdGuild, createdChannel, setup, punchline, expense))

                reply = EmbedReply("Add Data - Success", "data", description="Successfully inserted joke into database.")

                results = database.get(f"SELECT * FROM jokes WHERE setup=?", (setup,), limit=1)

                if not results:
                    raise Exception(f"Couldn't find joke in database after adding. setup = {setup}")
                else:
                    result = results[0]

                jokeID, jokeCreatedBy, jokeCreatedAt, jokeCreatedGuild, jokeCreatedChannel, jokeSetup, jokePunchline, jokeExpense = result
                jokeCreatedAt = dates.formatSimpleDate(timestamp=jokeCreatedAt)

                jokeAuthorObj: discord.User = self.bot.get_user(jokeCreatedBy)
                jokeExpenseParsed: discord.User = (self.bot.get_user(jokeExpense)).name if jokeExpense else "Not associated with a user."
                jokeGuildObj: discord.Guild = self.bot.get_guild(jokeCreatedGuild)
                jokeChannelObj: discord.abc.GuildChannel = self.bot.get_channel(jokeCreatedChannel)

                reply.add_field(name="ID", value=jokeID, inline=False)
                reply.add_field(name="By", value=jokeAuthorObj.name if jokeAuthorObj else "None", inline=False)
                reply.add_field(name="At", value=jokeCreatedAt, inline=False)
                reply.add_field(name="In Guild", value=jokeGuildObj.name if jokeGuildObj else "None", inline=True)
                reply.add_field(name="In Channel", value=jokeChannelObj.name if jokeChannelObj else "None", inline=True)
                reply.add_field(name="Joke Setup", value=jokeSetup, inline=False)
                reply.add_field(name="Joke Punchline", value=jokePunchline, inline=False)
                reply.add_field(name="Joke Expense", value=jokeExpenseParsed, inline=False)
                
                await reply.send(ctx)
            except Exception as e:
                reply = EmbedReply("Add Data - Error", "data", True, description=f"Your joke could not be added: {e}")

                await reply.send(ctx)
        elif table == "taylortracker":
            try:
                currentChannel = ctx.channel_id

                channels = database.get(f"SELECT * FROM {table} WHERE receivingChannel = {currentChannel}")

                if channels:
                    reply = EmbedReply("Add Data - Taylor Tracker - Error", "data", True, description="This channel is already enrolled in flight updates for Taylor Swift's jets.\n\nUse /data delete to disable (put a random number in the ID field when using the command).")

                    await reply.send(ctx)
                    return
                
                database.setOne(f"INSERT INTO {table} (receivingChannel) VALUES (?)", (currentChannel,))

                reply = EmbedReply("Add Data - Taylor Tracker", "data", description="Successfully enrolled this chat in flight updates for Taylor Swift's jets.\n\nUse /data delete to undo (put a random number in the ID field when using the command).")

                await reply.send(ctx)
            except Exception as e:
                reply = EmbedReply("Add Data - Taylor Tracker - Error", "data", True, description=f"Error: {e}")

                await reply.send(ctx)
        else:
            reply = EmbedReply("Add Data - Error", "data", True, description=f"You chose a table that doesn't exist or doesn't support the ability to be edited. Choice: {table}")

            await reply.send(ctx)

    @data.command(description = "View data in a table in the bot's db. Select table > click Enter", guild_ids=[799341195109203998])
    async def view(
        self,
        ctx: discord.ApplicationContext,
        table: discord.Option(
            str,
            description="Provide a database table to view data in.",
            choices=tables,
            required=True
        ), # type: ignore
        startingid: discord.Option(
            int,
            description="ID to begin looking at. Useful for when the list of results maxes out and you want to see beyond.",
            default=0
        ) # type: ignore
    ):
        database = LocalDatabase()

        if table == "jokes":
            try:
                results = database.get("SELECT id, setup, createdAt FROM jokes WHERE id >= ?", (startingid,))

                if not results:
                    raise Exception("No jokes available for that ID. Use /view table:jokes to see available IDs.")
                
                if len(results) >= MAX_FIELDS_EMBED:
                    resultsLeft = len(results[MAX_FIELDS_EMBED:])
                    results = results[:MAX_FIELDS_EMBED - 1]

                    results.append(("MAX LENGTH REACHED", f"Use the startingid parameter on this command and enter {results[-1][0]} to get the next {MAX_FIELDS_EMBED if MAX_FIELDS_EMBED <= resultsLeft else resultsLeft} results. You have reached the max length of data that Discord allows in an Embed.", "MAX LENGTH"))

                reply = EmbedReply("View Data - Jokes", "data", description="A list of jokes and their IDs:")

                for result in results:
                    jokeID, jokeSetup, jokeCreatedAt = result

                    if jokeCreatedAt != "MAX LENGTH":
                        jokeCreatedAt = dates.formatSimpleDate(timestamp=jokeCreatedAt)

                    reply.add_field(name=f"ID: {jokeID}", value=f"{jokeSetup} · {jokeCreatedAt}")

                await reply.send(ctx)

            except Exception as e:
                reply = EmbedReply("View Data - Error", "data", True, description=f"Error: {e}")

                await reply.send(ctx)
        elif table == "taylortracker":
            try:
                currentChannel = ctx.channel_id

                channels = database.get(f"SELECT * FROM {table} WHERE receivingChannel = {currentChannel}")

                if channels:
                    reply = EmbedReply("View Data - Taylor Tracker", "data", description="This channel is enrolled in flight updates for Taylor Swift's jets.\n\nUse /data delete to disable (put a random number in the ID field when using the command).")

                    await reply.send(ctx)
                else:
                    reply = EmbedReply("View Data - Taylor Tracker", "data", True, description="This channel is not enrolled in flight updates for Taylor Swift's jets.\n\nUse /data add to enable.")

                    await reply.send(ctx)
            except Exception as e:
                reply = EmbedReply("View Data - Taylor Tracker - Error", "data", True, description=f"Error: {e}")

                await reply.send(ctx)
        else:
            reply = EmbedReply("View Data - Error", "data", True, description=f"You chose a table that doesn't exist or doesn't support the ability to be viewed. Choice: {table}")

            await reply.send(ctx)

    @data.command(description = "Delete data in a table in the bot's db. Select table > Select ID > Click Enter", guild_ids=[799341195109203998])
    async def delete(
        self,
        ctx: discord.ApplicationContext,
        table: discord.Option(
            str,
            description="Provide a database table to delete data in.",
            choices=tables,
            required=True
        ), # type: ignore
        id: discord.Option(
            int,
            description="ANY NUMBER IF U ARE DOING TAYLORTRACKER!! ID to delete. Use /view to see IDs for data within tables.",
            required=True
        ) # type: ignore
    ):
        database = LocalDatabase()

        if table == "taylortracker":
            try:
                currentChannel = ctx.channel_id

                channels = database.get(f"SELECT * FROM {table} WHERE receivingChannel = {currentChannel}")

                if not channels:
                    reply = EmbedReply("Delete Data - Taylor Tracker - Error", "data", True, description="This channel is not enrolled in flight updates for Taylor Swift's jets.\n\nUse /data add to enable.")

                    await reply.send(ctx)
                    return
                
                database.query(f"DELETE FROM {table} WHERE receivingChannel = ?", (currentChannel,))

                reply = EmbedReply("Delete Data - Taylor Tracker", "data", description="Successfully un-enrolled this chat in flight updates for Taylor Swift's jets.\n\nUse /data add to undo.")

                await reply.send(ctx)
            except Exception as e:
                reply = EmbedReply("Delete Data - Taylor Tracker - Error", "data", True, description=f"Error: {e}")

                await reply.send(ctx)
        elif table in EDITABLE_TABLES:
            try:
                results = database.get(f"SELECT id FROM {table} WHERE id >= ?", (id,))

                if not results:
                    raise Exception(f"No data in table {table} available for that ID.")

                database.query(f"DELETE FROM {table} WHERE id = ?", (id,))

                reply = EmbedReply("Delete Data - Success", "data", description=f"Deleted {len(results)} record in {table} where ID: {id}")

                await reply.send(ctx)

            except Exception as e:
                reply = EmbedReply("Delete Data - Error", "data", True, description=f"Error: {e}")

                await reply.send(ctx)
        else:
            reply = EmbedReply("Delete Data - Error", "data", True, description=f"You chose a table that doesn't exist or doesn't support the ability to be edited. Choice: {table}")

            await reply.send(ctx)


def setup(bot):
    currentFile = sys.modules[__name__]
    
    for name in dir(currentFile):
        obj = getattr(currentFile, name)

        if isinstance(obj, type) and obj.__module__ == currentFile.__name__:
            if obj.ISCOG:
                bot.add_cog(obj(bot))