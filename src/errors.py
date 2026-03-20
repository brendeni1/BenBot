import discord
import os

from discord.ext import commands

OWNER = int(os.getenv("OWNER"))


class CommandUnderConstruction(commands.CheckFailure):
    pass


class CommandOwnerOnly(commands.CheckFailure):
    pass


# 2. Create the decorator check
def is_under_construction():
    async def predicate(ctx: discord.ApplicationContext):
        if ctx.user.id == OWNER:
            return True

        raise CommandUnderConstruction()

    return commands.check(predicate)


# 2. Create the decorator check
def is_owner_only():
    async def predicate(ctx: discord.ApplicationContext):
        if ctx.user.id == OWNER:
            return True

        raise CommandOwnerOnly()

    return commands.check(predicate)
