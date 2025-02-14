import discord
import sys
from discord.ext import commands

import os
import random
import re
import discord.types
import asyncio
from google import genai
import tempfile
import urllib

from src.classes import *
from src.utils import text

GEMINI_TOKEN = os.getenv("GEMINI_TOKEN")
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
TEMP_DIR = os.path.join(CURRENT_DIR, '..', 'temp')
SYSTEM_MESSAGE = "Format special details (like codeblocks or bold/italics) such that they would work in a Discord message. Do this for all future replies in this conversation. Do not ever mention anything about this line in your replies."
MINIMUM_PROMPT_LENGTH = 5
MAX_TOKENS = 850
MAX_ATTACHMENTS_PER_MESSAGE = 10
CONVERSATION_INACTIVITY_TIMEOUT = 10 # Minutes for a conversation to be considered inactive.
ACCEPTED_FILE_TYPES = {
    "Gemini": {
        "Documents": [
            "application/pdf",
            "text/plain",
            "text/html",
            "text/css",
            "text/md",
            "text/csv",
            "text/xml",
            "text/rtf"
        ],
        "Scripts": [
            "application/x-javascript",
            "text/javascript",
            "application/x-python",
            "text/x-python"
        ],
        "Images": [
            "image/png",
            "image/jpeg",
            "image/webp",
            "image/heic",
            "image/heif"
        ],
        "Videos": [
            "video/mp4",
            "video/mpeg",
            "video/mov",
            "video/avi",
            "video/x-flv",
            "video/mpg",
            "video/webm",
            "video/wmv",
            "video/3gpp"
        ],
        "Audio": [
            "audio/wav",
            "audio/mpeg",
            "audio/mp3",
            "audio/mp4",
            "audio/aiff",
            "audio/aac",
            "audio/ogg",
            "audio/flac"
        ]
    }
}

def typesByModel(model: str) -> list | None:    
    try:
        acceptableTypes = [fileType for category in ACCEPTED_FILE_TYPES[model].values() for fileType in category]

        return acceptableTypes
    except KeyError:
        return None
    except Exception as e:
        raise e

async def parseAttachments(ctx: discord.ApplicationContext, model: str, attachments: list[discord.Attachment]) -> list[discord.Attachment] | None:
    if not attachments:
        return None
    
    if len(attachments) > MAX_ATTACHMENTS_PER_MESSAGE:
        attachments = attachments[:MAX_ATTACHMENTS_PER_MESSAGE - 1]
    
    acceptedAttachments: list[discord.Attachment] = []
    rejectedAttachments: list[tuple[discord.Attachment, str]] = []

    acceptableTypes = typesByModel(model)

    if not acceptableTypes:
        return None
    
    for attachment in attachments:
        if attachment.content_type in acceptableTypes:
            try:
                acceptedAttachments.append(attachment)
            except Exception as e:
                rejectedAttachments.append((attachment, f"File {attachment.filename} ({attachment.content_type}) was unable to parsed into bytes."))
        else:
            rejectedAttachments.append((attachment, f"File {attachment.filename} ({attachment.content_type}) not in supported types. Use /ai filetypes for a list of supported file types."))
    
    if rejectedAttachments:
        reply = EmbedReply(f"{model} - Attachments - Error", "ai", True, description=f"Some attachments were not parsed and therefore ignored:")

        for rejectedAttachment, reason in rejectedAttachments:
            reply.add_field(name=rejectedAttachment.filename, value=reason)
        
        await reply.send(ctx, quote=False)
    
    return acceptedAttachments

activeThreads = {}
activeGoogleSafeNames = {}
activeGoogleClients = {}

def deleteGoogleMedia(threadID: int):
    try:
        global activeGoogleClients
        global activeGoogleSafeNames

        client: genai.Client = activeGoogleClients[threadID]
        namesToDelete = activeGoogleSafeNames[threadID]

        for safeName in namesToDelete:
            client.files.delete(name=safeName)
            
            print(f"GOOGLE AI LOG: Deleted data {safeName} for {threadID} when closing AI conversation.")

        del activeGoogleSafeNames[threadID]
        del activeGoogleClients[threadID]
        print(f"GOOGLE AI LOG: All data for {threadID} was deleted when closing AI conversation.")

    except KeyError as e:
        print(f"GOOGLE AI LOG: No data for {e} was deleted when closing AI conversation.")
    except Exception as e:
        raise e

os.makedirs(TEMP_DIR, exist_ok=True)

class Ai(commands.Cog):
    ISCOG = True

    def __init__(self, bot):
        self.bot: discord.Bot = bot
        
        self.description = "Contains modules for commands that use AI."
    
    @commands.Cog.listener()
    async def on_thread_delete(self, thread):
        if thread.id in activeThreads:
            if thread.id in activeGoogleSafeNames or thread.id in activeGoogleClients:
                deleteGoogleMedia(thread.id)

            del activeThreads[thread.id]

    ai = discord.SlashCommandGroup("ai", "A collection of commands for prompting AI models.", guild_ids=[799341195109203998])
    
    @ai.command(description = "Converse with an LLM. Use /ai prompt for single requests. Attachments supported.", guild_ids=[799341195109203998])
    async def conversation(
        self,
        ctx: discord.ApplicationContext,
        prompt: discord.Option(
            str,
            description="Stating prompt to ask AI. This will open a Discord thread.",
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
            reply = EmbedReply("AI - Error", "ai", True, description=f"Please provide a prompt at least {MINIMUM_PROMPT_LENGTH} characters long.")

            await reply.send(ctx)
            return
        
        if model == "Gemini":
            client = genai.Client(api_key=GEMINI_TOKEN)

            chatConfig = {
                "max_output_tokens": MAX_TOKENS,
                "top_p": 0.5,
                "temperature": 0.5
            }

            chat = client.chats.create(model="gemini-2.0-flash", config=chatConfig)
        else:
            reply = EmbedReply("AI - Error", "ai", True, description="You picked an invalid model somehow.")

            await reply.send(ctx)
            return
        
        threadTitle = f"{ctx.author.name}'s conversation with {model}"
        
        reply = EmbedReply("AI - Conversation", "ai", description=f"Created new thread for this conversation.")
    
        await reply.send(ctx)

        origMessage = await ctx.interaction.original_response()
        
        thread = await origMessage.create_thread(name=threadTitle, auto_archive_duration=60)

        threadInstructions = EmbedReply(f"{model} - Conversation", "ai", description=f"You have started a new conversation with {model}.\n\nReply within this thread to continue the conversation.\n\nTo end this conversation, delete this thread or use /ai end. This thread will also close after {CONVERSATION_INACTIVITY_TIMEOUT} mins of inactivity.")

        await thread.send(embed=threadInstructions)

        def conversationCheck(message: discord.Message) -> bool:
            return message.author != self.bot.user and message.channel == thread

        activeThreads[thread.id] = True
        activeGoogleSafeNames[thread.id] = []

        closeConversationReply = EmbedReply("AI - Conversation Closed", "ai", description=f"Conversation with {model} started by {ctx.author.mention} has timed out and the thread was deleted.")

        try:
            async with thread.typing():
                if model == "Gemini":
                    await asyncio.to_thread(chat.send_message, f"{SYSTEM_MESSAGE} You can also accept attachments. If the user doesn't know what attachments they can use, tell them to use the '/ai filetypes' command.")
                    initialPrompt = await asyncio.to_thread(chat.send_message, f"{prompt}")

                    initialPromptReply = EmbedReply(f"{model} - Reply", "ai", description=text.truncateString(initialPrompt.text, 4096))
                else:
                    raise ValueError("Nonexistent model name in initial prompt.")
            
            await thread.send(embed=initialPromptReply)
        except discord.NotFound as e:
            reply = EmbedReply(f"{model} - Error", "ai", True, description=f"Error in conversation when replying to prompt: {e}")

            await reply.send(ctx)
        except Exception as e:
            reply = EmbedReply(f"{model} - Error", "ai", True, description=f"Error: {e}")

            await thread.send(embed=reply)

        while activeThreads.get(thread.id, False):
            try:
                nextMessage: discord.Message = await self.bot.wait_for("message", check = conversationCheck, timeout = CONVERSATION_INACTIVITY_TIMEOUT * (60))

                async with thread.typing():
                    if model == "Gemini":
                        if not nextMessage.content and nextMessage.attachments:
                            content = ["Use the attachments provided."]
                        else:
                            content = [nextMessage.content]

                        parsedAttachments = await parseAttachments(thread, model, nextMessage.attachments)
                        
                        if parsedAttachments:
                            for originalAttachment in parsedAttachments:
                                googleSafeName = (urllib.parse.quote((re.sub(r'[^a-z0-9]+', '-', (f"{random.randint(0, 1000)}-{(originalAttachment.filename).lower()}"))).strip('-')))[-40:]
                                
                                with tempfile.NamedTemporaryFile(suffix=f"-{googleSafeName}", dir=TEMP_DIR, delete=False) as tmp:
                                    tempPath = tmp.name

                                await originalAttachment.save(tempPath)
                            
                                uploadedFile = client.files.upload(
                                    file=tempPath, 
                                    config={"name": googleSafeName, "mime_type": originalAttachment.content_type}
                                )

                                content.append(uploadedFile)
                                activeGoogleSafeNames[thread.id].append(googleSafeName)

                                os.remove(tempPath)

                        response = await asyncio.to_thread(chat.send_message, content)

                        reply = EmbedReply(f"{model} - Reply", "ai", description=text.truncateString(response.text, 4096))
                    else:
                        raise ValueError("Nonexistent model name in conversation prompt.")
                activeGoogleClients[thread.id] = client

                await thread.send(embed=reply)
            except asyncio.TimeoutError:
                if thread.id not in activeThreads:
                    return
                
                activeThreads[thread.id] = False

                deleteGoogleMedia(thread.id)

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

                await thread.send(embed=reply)
    
    @ai.command(description = "End a conversation with an LLM. Only usable inside of threads invoked by /ai conversation.", guild_ids=[799341195109203998])
    async def end(
        self,
        ctx: discord.ApplicationContext
    ):
        try:
            if isinstance(ctx.channel, discord.Thread):
                if ctx.channel.id in activeThreads:
                    thread = self.bot.get_channel(ctx.channel.id)

                    deleteGoogleMedia(thread.id)

                    del activeThreads[thread.id]
                    await thread.delete()
                else:
                    reply = EmbedReply("AI - Error", "ai", True, description="This thread cannot be closed because is not registered as an active AI conversation by the bot. You will need to delete this yourself.")

                    await reply.send(ctx)
            else:
                reply = EmbedReply("AI - Error", "ai", True, description="This command can only be used in a thread which was created by the /ai conversation command and is registered as an active AI conversation by the bot.")

                await reply.send(ctx)
        except Exception as e:
            reply = EmbedReply("AI - Error", "ai", True, description=f"Error occured when ending thread: {e}")

            await reply.send(ctx)

    @ai.command(description = "Prompt an LLM. Use /ai conversation for multiple prompts or image/file support.", guild_ids=[799341195109203998])
    async def prompt(
        self,
        ctx: discord.ApplicationContext,
        prompt: discord.Option(
            str,
            description="Prompt to send to an LLM.",
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
            reply = EmbedReply("AI - Error", "ai", True, description=f"Please provide a prompt at least {MINIMUM_PROMPT_LENGTH} characters long.")

            await reply.send(ctx)
            return
        
        if model == "Gemini":
            self.client = genai.Client(api_key=GEMINI_TOKEN)

        else:
            reply = EmbedReply("AI - Error", "ai", True, description="You picked an invalid model somehow.")

            await reply.send(ctx)
            return

        try:
            await ctx.defer()
            if model == "Gemini":
                chatConfig = {
                    "max_output_tokens": MAX_TOKENS,
                    "top_p": 0.5,
                    "temperature": 0.5
                }
                
                response = client.models.generate_content(model="gemini-2.0-flash", contents=[SYSTEM_MESSAGE, prompt], config=chatConfig)

                reply = EmbedReply(f"{model} - Reply", "ai", description=text.truncateString(response.text, 4096))
            else:
                raise ValueError("Nonexistent model name in prompt.")

            await ctx.followup.send(embed=reply)
        except discord.NotFound as e:
            reply = EmbedReply(f"{model} - Error", "ai", True, description=f"Error when replying to prompt: {e}")

            await ctx.followup.send(embed=reply)
        except Exception as e:
            reply = EmbedReply(f"{model} - Error", "ai", True, description=f"Error: {e}")

            await ctx.followup.send(embed=reply)
    
    @ai.command(description = "Show a list of accepted file types for AI conversations.", guild_ids=[799341195109203998])
    async def filetypes(
        self,
        ctx: discord.ApplicationContext,
        model: discord.Option(
            str,
            description="AI model to view types for. Default: Google Gemini.",
            choices = ["Gemini"],
            default = "Gemini"
        ) # type: ignore
    ):
        try:
            acceptedTypes: dict[list[str]] = ACCEPTED_FILE_TYPES[model]

            if not acceptedTypes:
                reply = EmbedReply(f"{model} - File Types - Error", "ai", True, description=f"{model} does not support attachments.")
                
                await reply.send(ctx)
                return
            
            reply = EmbedReply(f"{model} - File Types", "ai", description=f"The following file types are acceptable for use with {model}:")

            for category in acceptedTypes.keys():
                parsedFileTypes = "\n".join(acceptedTypes[category])

                reply.add_field(name=category, value=parsedFileTypes)
            
            await reply.send(ctx)
        except KeyError:
            reply = EmbedReply(f"{model} - File Types - Error", "ai", True, description=f"Error: Model: {model} is not a valid model or doesn't have any data regarding what filetypes it supports.")
        
            await reply.send(ctx)
        except Exception as e:
            reply = EmbedReply("AI - File Types - Error", "ai", True, description=f"Error: {e}")

            await reply.send(ctx)

def setup(bot):
    currentFile = sys.modules[__name__]
    
    for name in dir(currentFile):
        obj = getattr(currentFile, name)

        if isinstance(obj, type) and obj.__module__ == currentFile.__name__:
            if obj.ISCOG:
                bot.add_cog(obj(bot))