import discord
import sys
from discord.ext import commands

import os
from google import genai

from src.classes import *

GEMINI_TOKEN = os.getenv("GEMINI_TOKEN")
MINIMUM_PROMPT_LENGTH = 5

class Ai(commands.Cog):
    ISCOG = True

    def __init__(self, bot):
        self.bot = bot

        # self.geminiClient = genai.Client(
        #     api_key=GEMINI_TOKEN
        # )
        
        self.description = "Contains modules for commands that use AI."
    
    @discord.slash_command(description = "Prompt Google Gemini with text. Attachments not supported.", guild_ids=[799341195109203998])
    async def gemini(
        self,
        ctx: discord.ApplicationContext,
        prompt: discord.Option(
            str,
            description="Prompt to use.",
            required = True
        ) # type: ignore
    ):
        if len(prompt) < MINIMUM_PROMPT_LENGTH:
            reply = EmbedReply("Gemini - Error", "ai", True, description=f"Please provide a prompt at least {MINIMUM_PROMPT_LENGTH} characters long.")

            await reply.send(ctx)
            return

        # try:
        #     chat = self.geminiClient.chats.create(model="gemini-2.0-flash")

        #     response = chat.send_message(f"Give me a few word title for this prompt. No quotes just the title: {prompt}")
        # except Exception as e:
        #     reply = EmbedReply("Gemini - Error", "ai", True, description=f"Error: {e}")

        #     await reply.send(ctx)

        #     return

        threadTitle = prompt#response.text
        
        reply = EmbedReply("Gemini", "ai", description=f"Created new thread for this conversation.")
    
        threadInitial: discord.Message = await reply.send(ctx)

        origMessage = await ctx.interaction.original_response()
        
        thread = await origMessage.create_thread(name=threadTitle, auto_archive_duration=60)

        # thread.send()

        # async def on_message(self, newPrompt):
        #     if newPrompt.author == self.bot.user or newPrompt.channel.id != thread.id:
        #         return
            
        #     reply = EmbedReply("Gemeni - Prompt", "ai", description="Gemeni says:")
            
        #     reply.add_field(name="You Said", value=newPrompt.content)
                

        
        
def setup(bot):
    currentFile = sys.modules[__name__]
    
    for name in dir(currentFile):
        obj = getattr(currentFile, name)

        if isinstance(obj, type) and obj.__module__ == currentFile.__name__:
            if obj.ISCOG:
                bot.add_cog(obj(bot))