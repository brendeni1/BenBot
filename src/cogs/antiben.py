import discord
import random
import sys
from discord.ext import commands

from src.classes import *

ANTI_BEN_PLEDGE_EMOJI_CHOICES = [
    801246993682137108,
    801246369796587569,
    1089027418959904809,
    801248240698916895,
]

ANTI_BEN_WEBSITE_BUTTON = OpenLink(
    "Anti-Ben Movement Website", "https://anti-ben.brendenian.net/"
)


class AllegianceReply(EmbedReply):
    ISCOG = False

    def __init__(self, user: discord.User):
        super().__init__(
            "Anti-Ben - Pledge of Allegiance",
            "antiben",
            description=f"""
            I, {user.mention}, solemnly swear to uphold the principles of the Anti-Ben Movement. <:benNerd:1337974775561191495> I pledge to relentlessly protest the actions of Benjamin Robert Garrick <:niggawhat:858531525016682546>, to spread awareness of [his misdeeds](https://anti-ben.brendenian.net/), and to stand in solidarity with all fellow members of this noble cause <:Hotboys:801485557356167168>. I will fight for justice, for camaraderie, and for a Ben-free future! 🚫 <:bussy:801246370396110848>
            
            #AntiBenForever

            And, of course... Fuck Oreo too! <:retardedfatstupidobesedumbfuck:855178257631674398> 🔫🔫
            """,
        )


class AntiBenMovementView(discord.ui.View):
    ISCOG = False

    def __init__(self, emoji: discord.Emoji = None):
        super().__init__(timeout=None)

        self.emoji = emoji

    @discord.ui.button(
        style=discord.ButtonStyle.primary,
        label="Pledge Your Allegiance",
        custom_id="anti-ben-pledge",
    )
    async def callback(self, button: discord.Button, interaction: discord.Interaction):
        reply = AllegianceReply(interaction.user)

        await interaction.response.send_message(
            embed=reply, view=discord.ui.View(ANTI_BEN_WEBSITE_BUTTON, timeout=None)
        )


class AntiBen(commands.Cog):
    ISCOG = True

    def __init__(self, bot):
        self.bot: discord.Bot = bot

        self.description = "Commands for the Anti-Ben movement. ⛔"

    antiben = discord.SlashCommandGroup(
        name="antiben",
        description="Commands for the Anti-Ben Movement! ⛔",
        guild_ids=[799341195109203998],
    )

    @antiben.command(
        description="State the movement, live the movement.",
        guild_ids=[799341195109203998],
    )
    async def movement(self, ctx: discord.ApplicationContext):
        reply = EmbedReply(
            title="Anti-Ben - Movement",
            commandName="antiben",
            description=f"""
            {" ⛔ <:benNerd:1337974775561191495> ANTI-BEN MOVEMENT <:benNerd:1337974775561191495> ⛔ ".center(125, "-")}

            The Anti-Ben Movement is a grassroots initiative <:colehappy:801246369796587569> dedicated to raising awareness about, and protesting against, the individual known as BENJAMIN Robert GARRICK --> <:benchad:801248240698916895>. Fueled by a potent mix of camaraderie <:Hotboys:801485557356167168>, inside jokes <:zamn:1089027418959904809>, and the compelling evidence <:brenda:815455359849988106> found on [our movement's website](https://anti-ben.brendenian.net/), we strive to hold Ben accountable for his... actions. Join us in our noble quest! #AntiBenForever.

            We encourage all members of the {ctx.guild.name} to pledge their stand <:joshrad:801246993682137108> <:joshrad:801246993682137108> against Benjamin Robert Garrick. WE NEED YOU 🫵😘 {ctx.user.mention} for Anti BEN army!!!
            
            Use `/antiben pledge` or click the pledge button below to show your solditude <:benpants:1234985201160163450> for the Anti Ben movement and continue the fight.

            Fuck Oreo too! <:retardedfatstupidobesedumbfuck:855178257631674398> 🔫 <:retardedfatstupidobesedumbfuck:855178257631674398> 🔫
            """,
        )

        pledgeButtonEmoji: discord.Emoji = await ctx.guild.fetch_emoji(
            random.choice(ANTI_BEN_PLEDGE_EMOJI_CHOICES)
        )

        pledgeView = AntiBenMovementView(pledgeButtonEmoji)
        pledgeView.get_item("anti-ben-pledge").emoji = pledgeButtonEmoji
        pledgeView.add_item(ANTI_BEN_WEBSITE_BUTTON)

        await ctx.send_response(embed=reply, view=pledgeView)

    @antiben.command(
        description="Pledge the movement, be the movement.",
        guild_ids=[799341195109203998],
    )
    async def pledge(self, ctx: discord.ApplicationContext):
        reply = AllegianceReply(ctx.user)

        await ctx.send_response(
            embed=reply, view=discord.ui.View(ANTI_BEN_WEBSITE_BUTTON, timeout=None)
        )


def setup(bot):
    currentFile = sys.modules[__name__]

    for name in dir(currentFile):
        obj = getattr(currentFile, name)

        if isinstance(obj, type) and obj.__module__ == currentFile.__name__:
            if obj.ISCOG:
                bot.add_cog(obj(bot))
