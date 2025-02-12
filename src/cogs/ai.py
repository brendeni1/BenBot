import discord
import sys
from discord.ext import commands

import os
import asyncio
from google import genai

from src.classes import *

GEMINI_TOKEN = os.getenv("GEMINI_TOKEN")
MINIMUM_PROMPT_LENGTH = 5
CONVERSATION_INACTIVITY_TIMEOUT = 0.25 # Minutes for a conversation to be considered inactive.

activeThreads = {}

class Ai(commands.Cog):
    ISCOG = True

    def __init__(self, bot):
        self.bot: discord.Bot = bot
        
        self.description = "Contains modules for commands that use AI."
    
    @commands.Cog.listener()
    async def on_thread_delete(self, thread):
        if thread.id in activeThreads:
            del activeThreads[thread.id]

    ai = discord.SlashCommandGroup("ai", "A collection of commands for prompting AI models.", guild_ids=[799341195109203998])
    
    @ai.command(description = "Prompt a LLM with text. Attachments not supported yet...", guild_ids=[799341195109203998])
    async def prompt(
        self,
        ctx: discord.ApplicationContext,
        prompt: discord.Option(
            str,
            description="Prompt to ask AI.",
            required = True
        ), # type: ignore
        model: discord.Option(
            str,
            description="AI model to use. Default: Google Gemini.",
            choices = ["Gemini"],
            default = "Gemini"
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

        threadTitle = f"{ctx.author.name}'s conversation with {model}"
        
        reply = EmbedReply("AI - Prompt", "ai", description=f"Created new thread for this conversation.")
    
        await reply.send(ctx)

        origMessage = await ctx.interaction.original_response()
        
        thread = await origMessage.create_thread(name=threadTitle, auto_archive_duration=60)

        threadInstructions = EmbedReply(f"{model} - Conversation", "ai", description=f"You have started a new conversation with {model}.\n\nReply within this thread to continue the conversation.\n\nTo end this conversation, delete this thread or use /ai end. This thread will also close after {CONVERSATION_INACTIVITY_TIMEOUT} mins of inactivity.")

        await thread.send(embed=threadInstructions)

        def conversationCheck(message: discord.Message) -> bool:
            return message.author != self.bot.user and message.channel == thread

        activeThreads[thread.id] = True

        closeConversationReply = EmbedReply("AI - Conversation Closed", "ai", description=f"Conversation with AI started by {ctx.author.mention} has timed out and the thread was deleted.")

        while activeThreads.get(thread.id, False):
            try:
                nextMessage = await self.bot.wait_for("message", check = conversationCheck, timeout = CONVERSATION_INACTIVITY_TIMEOUT * (60))

                reply = EmbedReply("AI - Response", "ai", description=f"You said: {nextMessage.content}")

                await thread.send(embed=reply)
            except asyncio.TimeoutError:
                if thread.id not in activeThreads:
                    return
                
                activeThreads[thread.id] = False

                try:
                    await thread.delete()
                except discord.NotFound:
                    # Thread is already deleted
                    pass

                await closeConversationReply.send(ctx)

                return
            except asyncio.CancelledError:
                # If the thread was manually deleted while waiting, safely exit.
                return
            except Exception as e:
                reply = EmbedReply("AI - Error", "ai", True, description=f"Error in thread: {e}")

                await reply.send(ctx)
    
    @ai.command(description = "End a conversation with an LLM. Only usable inside of threads which were invoked by /ai prompt.", guild_ids=[799341195109203998])
    async def end(
        self,
        ctx: discord.ApplicationContext
    ):
        try:
            if isinstance(ctx.channel, discord.Thread):
                if ctx.channel.id in activeThreads:
                    thread = self.bot.get_channel(ctx.channel.id)

                    del activeThreads[thread.id]
                    await thread.delete()
                else:
                    reply = EmbedReply("AI - Error", "ai", True, description="This thread cannot be closed because is not registered as an active AI conversation by the bot. You will need to delete this yourself.")

                    await reply.send(ctx)
            else:
                reply = EmbedReply("AI - Error", "ai", True, description="This command can only be used in a thread which was created by the /ai prompt command and is registered as an active AI conversation by the bot.")

                await reply.send(ctx)
        except Exception as e:
            reply = EmbedReply("AI - Error", "ai", True, description=f"Error occured when ending thread: {e}")

            await reply.send(ctx)
        
def setup(bot):
    currentFile = sys.modules[__name__]
    
    for name in dir(currentFile):
        obj = getattr(currentFile, name)

        if isinstance(obj, type) and obj.__module__ == currentFile.__name__:
            if obj.ISCOG:
                bot.add_cog(obj(bot))