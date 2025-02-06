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