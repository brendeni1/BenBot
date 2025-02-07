import discord

from discord.ext import commands

class AppReply:
    def __init__(self, success: bool, reply: str, reason: str="", error: bool=False):
        self.success = success
        self.reason = reason
        self.reply = reply
    
    async def sendReply(self, context: commands.Context):
        await context.respond(self.reply)

class StandardReply:
    def __init__(self, success: bool, reply: str, reason: str="", error: bool=False):
        self.success = success
        self.reason = reason
        self.reply = reply
    
    async def sendReply(self, context: commands.Context):
        await context.send(self.reply)

class DataModal(discord.ui.Modal):
    def __init__(self, title: str, custom_id: int = None, timeout: int = None):
        super().__init__(title=title, custom_id=custom_id, timeout=timeout)

class SelectGuildMember(discord.ui.Select):
    def __init__(self, members: list[discord.Member]):
        # Create a list of options; note that Discord limits the number of options.
        options = [discord.SelectOption(label="This joke is not directed towards a member.", value="0")]
        
        for member in members[:24]:
            options.append(discord.SelectOption(label=member.display_name, value=str(member.id)))

        super().__init__(placeholder="Select the member which the joke is directed towards...", options=fla(options))

class SelectGuildMemberView(discord.ui.View):
    def __init__(self, members: list[discord.Member]):
        super().__init__()
        self.add_item(SelectGuildMember(members))