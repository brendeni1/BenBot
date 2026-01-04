import discord
import sys
from discord.ext import commands

from src.classes import *
from src.utils import tools


class ShortenURLCommands(commands.Cog):
    ISCOG = True

    def __init__(self, bot):
        self.bot: discord.Bot = bot

        self.description = (
            f"Commands for shortening URLs using {tools.URL_SHORTENER_NAME}."
        )

    shortenURLCommands = discord.SlashCommandGroup(
        name="shorturl",
        description=f"Commands for shortening URLs using {tools.URL_SHORTENER_NAME}.",
        guild_ids=[799341195109203998],
    )

    @shortenURLCommands.command(
        name="add",
        description="Create a shortened URL with full configuration.",
        guild_ids=[799341195109203998],
    )
    async def add(
        self,
        ctx: discord.ApplicationContext,
        url: discord.Option(str, "The long URL to shorten"),  # type: ignore
        slug: discord.Option(str, "Custom alias (slug)", default=None),  # type: ignore
        title: discord.Option(str, "Title for the short link", default=None),  # type: ignore
        max_visits: discord.Option(int, "Limit total clicks", default=None),  # type: ignore
        tags: discord.Option(
            str, "Comma-separated tags (e.g. social,promo)", default=None
        ),  # type: ignore
        valid_until: discord.Option(
            str, "Expiration date (ISO 8601 format)", default=None
        ),  # type: ignore
        crawlable: discord.Option(bool, "Allow search engines to index", default=True),  # type: ignore
        forward_query: discord.Option(
            bool, "Forward query params to long URL", default=True
        ),  # type: ignore
    ):
        await ctx.defer()

        # Process tags if provided
        processed_tags = [t.strip() for t in tags.split(",")] if tags else None

        try:
            result = await tools.shortenURL(
                url=url,
                custom_slug=slug,
                title=title,
                max_visits=max_visits,
                tags=processed_tags,
                valid_until=valid_until,
                crawlable=crawlable,
                forward_query=forward_query,
            )

            short_url = result.get("shortUrl")

            reply = EmbedReply(
                "Shorten URL - Add", "tools", description="URL successfully shortened."
            )

            replyView = discord.ui.View(
                OpenLink(
                    "View Short Links (Tailscale Only)", "https://links.brendenian.net"
                ),
                timeout=None,
            )

            reply.add_field(name="Short URL", value=short_url, inline=False)
            reply.add_field(name="Destination URL", value=url, inline=False)

            await reply.send(ctx, view=replyView)
        except Exception as e:
            reply = EmbedReply(
                "Shorten URL - Error",
                "tools",
                error=True,
                description=f"**Error Details:**\n{e}",
            )
            await reply.send(ctx)

    @shortenURLCommands.command(
        name="delete",
        description="Delete a shortened URL by its short code.",
        guild_ids=[799341195109203998],
    )
    async def delete(
        self,
        ctx: discord.ApplicationContext,
        short_code: discord.Option(str, "The short code of the URL to delete"),  # type: ignore
        domain: discord.Option(str, "The domain (if using multi-domain setup)", default=None),  # type: ignore
    ):
        await ctx.defer()

        try:
            # We call the helper tool to perform the DELETE request
            result = await tools.deleteShortURL(short_code=short_code, domain=domain)

            # 204 No Content usually means success in Shlink
            reply = EmbedReply(
                "Shorten URL - Delete",
                "tools",
                description=f"Successfully deleted short URL with code: `{short_code}`",
            )

            replyView = discord.ui.View(
                OpenLink(
                    "View Short Links (Tailscale Only)", "https://links.brendenian.net"
                ),
                timeout=None,
            )

            await reply.send(ctx, view=replyView)
        except Exception as e:
            # Handle specific error messages based on the documentation image
            error_msg = str(e)

            # If your tool returns the JSON error body, we can parse it for better feedback
            if "short-url-not-found" in error_msg:
                error_detail = f"No URL was found for the short code: `{short_code}`"
            elif "invalid-short-url-deletion" in error_msg:
                error_detail = "This URL cannot be deleted because it has exceeded the visits threshold."
            else:
                error_detail = f"**Error Details:**\n{e}"

            reply = EmbedReply(
                "Shorten URL - Error",
                "tools",
                error=True,
                description=error_detail,
            )
            await reply.send(ctx)


def setup(bot):
    currentFile = sys.modules[__name__]

    for name in dir(currentFile):
        obj = getattr(currentFile, name)

        if isinstance(obj, type) and obj.__module__ == currentFile.__name__:
            if obj.ISCOG:
                bot.add_cog(obj(bot))
