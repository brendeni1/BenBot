import discord
import sqlite3

from src.utils.db import *
from src.utils import text


class OpenLink(discord.ui.Button):
    def __init__(self, label: str, link: str, **kwargs):
        super().__init__(
            label=label, url=link, style=discord.ButtonStyle.link, **kwargs
        )


class SelectGuildMember(discord.ui.Select):
    def __init__(
        self, members: list[discord.Member], placeholderTitle: str, noMemberOption: bool
    ):
        options = []

        if noMemberOption:
            options = [discord.SelectOption(label="No Member", value="0")]

            members = members[:24]
        else:
            members = members[:25]

        for member in members:
            options.append(
                discord.SelectOption(label=member.display_name, value=str(member.id))
            )

        super().__init__(placeholder=placeholderTitle, options=options)

    async def callback(self, interaction: discord.Interaction):
        if not int(self.values[0]):
            await interaction.respond(f"Not associated with a member.", ephemeral=True)
        else:
            await interaction.respond(
                f"Associated with <@{self.values[0]}>", ephemeral=True
            )

        self.view.stop()
        self.disabled = True

        await interaction.message.delete()


class SelectGuildMemberView(discord.ui.View):
    def __init__(
        self,
        members: list[discord.Member],
        placeholderTitle: str,
        noMemberOption: bool = False,
    ):
        super().__init__(timeout=60, disable_on_timeout=True)
        self.add_item(SelectGuildMember(members, placeholderTitle, noMemberOption))


class EmbedReply(discord.Embed):
    def __init__(
        self,
        title: str,
        commandName: str,
        error: bool = False,
        *,
        url: str = None,
        description: str = None,
    ):
        colour = 0xFF0000 if error else 0xDFB690
        super().__init__(
            colour=colour,
            title=(
                text.truncateString(title, 255)[0]
                if not error
                else "Error" if not title else title
            ),
            url=(
                url
                if url
                else f"https://github.com/brendeni1/BenBot/blob/main/src/cogs/commands/{commandName.lower()}.py"
            ),
            description=(
                text.truncateString(description, 4096)[0]
                if description != None
                else None
            ),
        )
        super().set_author(
            name="BenBot",
            url="https://github.com/brendeni1/BenBot",
            icon_url="https://cdn.discordapp.com/emojis/1337974783396286575.webp?size=96",
        )
        self.error = error

    async def send(self, ctx: discord.ApplicationContext, quote: bool = True, **kwargs):
        if quote:
            if "embeds" in kwargs:
                return await ctx.respond(**kwargs)
            else:
                return await ctx.respond(embed=self, **kwargs)
        else:
            if "embeds" in kwargs:
                return await ctx.send(**kwargs)
            else:
                return await ctx.send(embed=self, **kwargs)


class LocalDatabase:
    def __init__(self, database: str = "db"):
        database = f"{database}.db"

        availableDatabases = listDBs(withFileExtensions=True)

        if database not in availableDatabases:
            raise ValueError(
                f"src>classes>LocalDatabase: Database not in list of available databases. Tried to access '{database}'."
            )

        self.database = database

    def get(self, query: str, params: tuple = (), limit: int = 0) -> list:
        try:
            connection = sqlite3.connect(f"src/data/{self.database}")
            cursor = connection.cursor()

            cursor.execute(query, params)

            if limit:
                results = cursor.fetchmany(limit)
            else:
                results = cursor.fetchall()

            return results
        finally:
            cursor.close()
            connection.close()

    def getRaw(self, query: str, limit: int = 0) -> list:
        try:
            connection = sqlite3.connect(f"src/data/{self.database}")
            cursor = connection.cursor()

            cursor.execute(query)

            if limit:
                results = cursor.fetchmany(limit)
            else:
                results = cursor.fetchall()

            return results
        finally:
            cursor.close()
            connection.close()

    def listTables(self) -> list:
        try:
            connection = sqlite3.connect(f"src/data/{self.database}")
            cursor = connection.cursor()

            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")

            results = cursor.fetchall()

            resultsFiltered = []

            for result in results:
                if result[0] != "sqlite_sequence":
                    resultsFiltered.append(result[0])

            return resultsFiltered
        finally:
            cursor.close()
            connection.close()

    def setOne(self, query: str, params: tuple = ()):
        try:
            connection = sqlite3.connect(f"src/data/{self.database}")
            cursor = connection.cursor()

            cursor.execute(query, params)

            connection.commit()

            return True
        finally:
            cursor.close()
            connection.close()

    def setOneRaw(self, query: str):
        try:
            connection = sqlite3.connect(f"src/data/{self.database}")
            cursor = connection.cursor()

            cursor.execute(query)

            connection.commit()

            return True
        finally:
            cursor.close()
            connection.close()

    def setMany(self, query: str, data: tuple):
        try:
            connection = sqlite3.connect(f"src/data/{self.database}")
            cursor = connection.cursor()

            cursor.executemany(query, data)

            connection.commit()

            return True
        finally:
            cursor.close()
            connection.close()

    def query(self, query: str, data: tuple):
        try:
            connection = sqlite3.connect(f"src/data/{self.database}")
            cursor = connection.cursor()

            cursor.execute(query, data)

            connection.commit()

            return True
        finally:
            cursor.close()
            connection.close()

    def queryRaw(self, query: str):
        try:
            connection = sqlite3.connect(f"src/data/{self.database}")
            cursor = connection.cursor()

            cursor.execute(query)

            connection.commit()

            return True
        finally:
            cursor.close()
            connection.close()
