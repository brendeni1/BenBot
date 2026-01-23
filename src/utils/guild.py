import discord


def getAllHumanMembers(ctx: discord.ApplicationContext) -> list[discord.Member]:
    humans = list(filter(lambda member: not member.bot, ctx.guild.members))

    return humans
