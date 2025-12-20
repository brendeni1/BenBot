import discord
import datetime
from dataclasses import dataclass

from src.classes import *
from src.utils import dates, text

DELETE_IMAGE_CONFIRMATION_TIMEOUT = 1 * (60)
SELECT_IMAGE_CONFIRMATION_TIMEOUT = 14.9 * (60)


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


class ImageView(discord.ui.View):
    def __init__(self, imageEntry: ImageEntry = None, overrideTimeout=None):
        super().__init__(timeout=overrideTimeout, disable_on_timeout=True)
        self.imageEntry = imageEntry

        if self.imageEntry:
            self.add_item(OpenLink("View Image", link=self.imageEntry.link, row=2))

    @discord.ui.button(
        label="Delete Image",
        custom_id="images-delete",
        style=discord.ButtonStyle.red,
        emoji="🗑️",
        row=1,
    )
    async def deleteCallback(
        self, button: discord.Button, interaction: discord.Interaction
    ):
        try:
            targetMessage: discord.Message = interaction.message
            targetImageID = None
            imageLink = None

            # Parse the embed for BOTH the ID and the Link
            for embed in targetMessage.embeds:
                # 1. Get ID from footer
                footer = embed.footer
                if footer and "Image ID: " in footer.text:
                    targetImageID = footer.text.split("Image ID: ")[-1]

                # 2. Get the link (checking embed URL or the image URL)
                imageLink = embed.url or (embed.image.url if embed.image else None)

            if not targetImageID:
                raise discord.ClientException("Could not find Image ID in footer.")

            # --- THE RESTART FIX ---
            # Check if OpenLink is already in children. If not (bot restarted), add it.
            has_link = any(isinstance(item, OpenLink) for item in self.children)
            if not has_link and imageLink:
                self.add_item(OpenLink("View Image", link=imageLink, row=2))

            confirm_view = DeleteConfirmView(
                image_id=targetImageID,
                original_view=self,
                original_message=targetMessage,
            )

            confirm_embed = EmbedReply(
                "Images - Delete Confirmation",
                "images",
                description=f"Are you sure you want to delete the image with ID `{targetImageID}`\n\nThis cannot be undone.",
                error=True,
            )

            await interaction.response.edit_message(
                embed=confirm_embed, view=confirm_view
            )

        except Exception as e:
            # Error handling remains same...
            reply = EmbedReply(
                "Images - Delete - Error",
                "images",
                error=True,
                description=f"Error: {e}",
            )
            await interaction.response.send_message(embed=reply, ephemeral=True)


class ImageSearchView(ImageView):
    def __init__(self, results: list, current_index: int = 0):
        self.results = results
        self.current_index = current_index

        # Initialize the parent ImageView with the currently selected image.
        # This automatically adds the "Open Link" and "Delete" buttons for this specific image.
        super().__init__(
            results[current_index], overrideTimeout=SELECT_IMAGE_CONFIRMATION_TIMEOUT
        )

        # Only add the Select Menu if there is more than 1 result
        if len(results) > 1:
            options = []
            # Discord limits Select Menus to 25 options
            for i, img in enumerate(results[:25]):
                # Create a label: "Album - ID" or just "Image ID"
                label = f"{img.album} - {img.id}" if img.album else f"Image {img.id}"

                # Get a snippet of the description for the dropdown details
                desc_snippet = (
                    text.truncateString(img.description, 100)[0]
                    if img.description
                    else "(No Description)"
                )

                options.append(
                    discord.SelectOption(
                        label=text.truncateString(label, 100)[0],
                        value=str(i),  # We use the list index as the value
                        default=(i == current_index),
                        description=desc_snippet,
                        emoji="🖼️",
                    )
                )

            self.select_menu = discord.ui.Select(
                placeholder=f"Found {len(results)} images...",
                min_values=1,
                max_values=1,
                options=options,
                row=0,  # Place the dropdown on the top row
            )
            self.select_menu.callback = self.select_menu_callback
            self.add_item(self.select_menu)

    async def select_menu_callback(self, interaction: discord.Interaction):
        # 1. Get the new index from the selected value
        selected_index = int(self.select_menu.values[0])
        selected_image = self.results[selected_index]

        # 2. Create a NEW View instance.
        # We do this because the "Open Link" button in the parent ImageView
        # is created in __init__ with a static URL. To change the link button,
        # we regenerate the view for the new image.
        self.stop()
        new_view = ImageSearchView(self.results, selected_index)

        # 3. Update the message with the new Embed and the new View
        await interaction.response.edit_message(
            embed=selected_image.toEmbed(), view=new_view
        )


class DeleteConfirmView(discord.ui.View):
    def __init__(
        self,
        image_id: str,
        original_view: discord.ui.View,
        original_message: discord.Message,
    ):
        super().__init__(timeout=DELETE_IMAGE_CONFIRMATION_TIMEOUT)
        self.image_id = image_id
        self.original_view = original_view
        self.original_message = original_message

    async def on_timeout(self):
        await self.revert_view()

    async def revert_view(self, interaction: discord.Interaction = None):
        try:
            if interaction:
                await interaction.response.edit_message(
                    embeds=self.original_message.embeds, view=self.original_view
                )
            else:
                await self.original_message.edit(
                    embeds=self.original_message.embeds, view=self.original_view
                )
        except:
            pass

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary)
    async def cancel(self, button: discord.Button, interaction: discord.Interaction):
        self.stop()
        await self.revert_view(interaction)

    @discord.ui.button(label="Confirm Delete", style=discord.ButtonStyle.red, emoji="🗑️")
    async def confirm(self, button: discord.Button, interaction: discord.Interaction):
        self.stop()
        try:
            # Execute your existing delete function
            deletedImageObj = deleteImage(self.image_id)

            newEmbed = EmbedReply(
                "Images - Delete",
                "images",
                description=f"Successfully deleted [image]({deletedImageObj.link}) with ID `{deletedImageObj.id}` from the DB.",
            )

            await interaction.response.edit_message(embed=newEmbed, view=None)

        except Exception as e:
            reply = EmbedReply(
                "Images - Delete - Error",
                "images",
                error=True,
                description=f"Database error: {e}",
            )
            await interaction.response.edit_message(embed=reply, view=None)


def deleteImage(id: str) -> "ImageEntry":
    db = LocalDatabase()

    sql = "SELECT * FROM images WHERE id = ?"
    params = (id,)

    results = db.get(sql, params=params)

    if not results:
        raise ValueError("No images found with that ID!")

    entryObj = dbToObj(results[0])

    sql = "DELETE FROM images WHERE id = ?"

    db.query(sql, params)

    return entryObj


def dbToObj(result) -> "ImageEntry":
    id, timestamp, album, link, description, keywords, createdBy = result

    timestamp = dates.simpleDateObj(timestamp)

    keywords = keywords.split(",") if keywords else []

    obj = ImageEntry(id, timestamp, album, link, description, keywords, createdBy)

    return obj


def listAlbums(ctx: discord.AutocompleteContext) -> list[str]:
    db = LocalDatabase()

    # It's more efficient to filter NULLs in SQL directly
    sql = "SELECT DISTINCT album FROM images WHERE album IS NOT NULL"
    params = ()

    if ctx.value:
        sql += f" AND album LIKE ?"
        params = (f"%{ctx.value}%",)

    sql += " ORDER BY album"

    results = db.get(sql, params=params)

    # results will be a list of tuples, e.g., [("album1",), ("album2",)]
    # Use list comprehension to flatten and ensure no Nones slipped through
    unique = [result[0] for result in results if result[0] is not None]

    # Limit to 25 results (Discord's maximum for autocomplete)
    return unique[:25]
