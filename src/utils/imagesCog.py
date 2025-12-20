import discord
import datetime
from dataclasses import dataclass

from src.classes import *
from src.utils import dates, text


def dbToObj(result) -> "ImageEntry":
    id, timestamp, album, link, description, keywords, createdBy = result

    timestamp = dates.simpleDateObj(timestamp)

    keywords = keywords.split(",") if keywords else []

    obj = ImageEntry(id, timestamp, album, link, description, keywords, createdBy)

    return obj


@dataclass
class ImageEntry:
    id: str
    timestamp: datetime.datetime
    album: str
    link: str
    description: str
    keywords: list[str]
    createdBy: int

    def writeToDB(self):
        db = LocalDatabase()

        db.setOne(
            query="INSERT INTO `images` (`id`,`timestamp`,`album`,`link`,`description`,`keywords`,`createdBy`) VALUES (?,?,?,?,?,?,?)",
            params=(
                self.id,
                dates.formatSimpleDate(self.timestamp, databaseDate=True),
                self.album.lower() if self.album else None,
                self.link,
                self.description if self.description else None,
                ",".join(self.keywords) if self.keywords else None,
                self.createdBy,
            ),
        )

    def toEmbed(self, title: str = "Images - View Image 🔗↗️"):
        embed = EmbedReply(
            title=title,
            commandName="images",
            url=self.link,
            description=(
                f"**Description from <@{self.createdBy}>:**\n> {text.truncateString(self.description, 3500)[0]}"
                if self.description
                else "*(No Description)*"
            ),
        )

        embed.set_image(url=self.link)

        embed.add_field(
            name="Direct Link",
            value=(self.link if self.link else "*(No Link)*"),
            inline=False,
        )

        embed.add_field(
            name="Created At",
            value=(
                dates.formatSimpleDate(self.timestamp, discordDateFormat="f")
                if self.timestamp
                else "*(Unknown)*"
            ),
        )

        embed.add_field(
            name="Created By",
            value=f"<@{self.createdBy}>" if self.createdBy else "*(Unknown)*",
        )

        embed.add_field(
            name="In Album",
            value=f"`{self.album}`" if self.album else "*(No Album)*",
        )

        embed.add_field(
            name="Keywords",
            value=(
                "\n".join(text.truncateList([f"· {k}" for k in self.keywords], 1024))
                if self.keywords
                else "*(No Keywords)*"
            ),
        )

        embed.set_footer(text=f"Image ID: {self.id}")

        return embed


def listAlbums(ctx: discord.AutocompleteContext) -> list[str]:
    db = LocalDatabase()

    sql = "SELECT album FROM images"
    params = ()

    if ctx.value:
        sql += f" WHERE album LIKE ?"
        params = (f"%{ctx.value}%",)

    sql += " ORDER BY album"

    results = db.get(sql, params=params)

    unique = set([result[0] for result in results])

    return sorted(list(unique))
