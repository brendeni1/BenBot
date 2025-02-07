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

    async def callback(self, interaction):
        await interaction.respond(f'Your joke is almost ready...', ephemeral=True)

class SelectGuildMember(discord.ui.Select):
    def __init__(self, members: list[discord.Member], placeholderTitle: str, noMemberOption: bool):
        options = []

        if noMemberOption:
            options = [discord.SelectOption(label="DO NOT associate with a member.", value="0")]
        
        for member in members[:24]:
            options.append(discord.SelectOption(label=member.display_name, value=str(member.id)))

        super().__init__(placeholder=placeholderTitle, options=options)

    async def callback(self, interaction: discord.Interaction): # the function called when the user is done selecting options
        # await interaction.response.send_message()
        await interaction.respond(f"Associated with <@{self.values[0]}>", ephemeral=True)
        
        self.view.stop()
        self.disabled = True     
        await interaction.message.delete()

class SelectGuildMemberView(discord.ui.View):
    def __init__(self, members: list[discord.Member], placeholderTitle: str, noMemberOption: bool = False):
        super().__init__(timeout=30, disable_on_timeout=True)
        self.add_item(SelectGuildMember(members, placeholderTitle, noMemberOption))