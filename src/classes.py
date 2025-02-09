import discord
import sqlite3

from src.utils.db import *
            
class SelectGuildMember(discord.ui.Select):
    def __init__(self, members: list[discord.Member], placeholderTitle: str, noMemberOption: bool):
        options = []

        if noMemberOption:
            options = [discord.SelectOption(label="No Member", value="0")]
        
        for member in members[:24]:
            options.append(discord.SelectOption(label=member.display_name, value=str(member.id)))

        super().__init__(placeholder=placeholderTitle, options=options)

    async def callback(self, interaction: discord.Interaction):
        await interaction.respond(f"Associated with <@{self.values[0]}>", ephemeral=True)
        
        self.view.stop()
        self.disabled = True     
        await interaction.message.delete()

class SelectGuildMemberView(discord.ui.View):
    def __init__(self, members: list[discord.Member], placeholderTitle: str, noMemberOption: bool = False):
        super().__init__(timeout=30, disable_on_timeout=True)
        self.add_item(SelectGuildMember(members, placeholderTitle, noMemberOption))

class EmbedReply(discord.Embed):
    def __init__(self, title: str, commandName: str, error: bool = False, *, url: str = None, description: str = None):
        colour = 0xff0000 if error else 0xdfb690
        super().__init__(colour=colour, title=title if not error else "Error" if not title else title, url=url if url else f"https://github.com/brendeni1/BenBot/blob/main/src/cogs/{commandName.lower()}.py", description=description)
        super().set_author(name="BenBot", url="https://github.com/brendeni1/BenBot", icon_url="https://cdn.discordapp.com/emojis/1337974783396286575.webp?size=96")
        self.error = error

    async def send(self, ctx: discord.ApplicationContext, quote: bool = True, **kwargs):
        if quote:
            await ctx.respond(embed=self, **kwargs)
        else:
            await ctx.send(embed=self, **kwargs)

class LocalDatabase:
    def __init__(self, database: str):
        database = f"{database}.db"

        availableDatabases = listDBs(withFileExtensions=True)

        if database not in availableDatabases:
            raise ValueError(f"src>classes>LocalDatabase: Database not in list of available databases. Tried to access '{database}'.")
        
        self.database = database

    def get(self, query: str, limit: int = 0) -> list:
        try:
            connection = sqlite3.connect(self.database)
            cursor = connection.cursor()

            cursor.execute(query)

            if limit:
                results = cursor.fetchmany(limit)
            else:
                results = cursor.fetchall()

            connection.commit()

            return results
        finally:
            cursor.close()
            connection.close()

    def setOne(self, query: str):
        try:
            connection = sqlite3.connect(self.database)
            cursor = connection.cursor()

            cursor.execute(query)

            connection.commit()
        finally:
            cursor.close()
            connection.close()
    
    def setMany(self, query: str, data: list[tuple]):
        try:
            connection = sqlite3.connect(self.database)
            cursor = connection.cursor()

            cursor.executemany(query, data)

            connection.commit()
        finally:
            cursor.close()
            connection.close()

    def query(self, query: str):
        try:
            connection = sqlite3.connect(self.database)
            cursor = connection.cursor()

            cursor.execute(query)

            connection.commit()
        finally:
            cursor.close()
            connection.close()