import discord
import sys
from discord.ext import commands

import os
import random
import re
import discord.types
import asyncio
from google import genai
from google.genai.errors import ServerError
import tempfile
import urllib

from src.classes import *
from src.utils import text
from src.utils import dates

GEMINI_TOKEN = os.getenv("GEMINI_TOKEN")
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
TEMP_DIR = os.path.join(CURRENT_DIR, '..', 'temp')
SYSTEM_MESSAGE = "Format special details (like codeblocks or bold/italics) such that they would work in a Discord message. Do this for all future replies in this conversation. Do not ever mention anything about this line in your replies."
MINIMUM_PROMPT_LENGTH = 5
MAX_TOKENS = 850
MAX_ATTACHMENTS_PER_MESSAGE = 10
CONVERSATION_INACTIVITY_TIMEOUT = 30 # Minutes for a conversation to be considered inactive.
INACTIVITY_WARNING = (CONVERSATION_INACTIVITY_TIMEOUT / 4) * 60 if CONVERSATION_INACTIVITY_TIMEOUT >= 1 else 0 # Seconds for a conversation warning to be sent in an inactive thread.
TIMEOUT_RESET_SUCCESS = f"The timeout for this thread has been reset to {dates.formatSeconds(int(CONVERSATION_INACTIVITY_TIMEOUT * 60))}."
ARCHIVE_SUCCESS = f"This thread has been archived and spared from deletion.\n\nYou are no longer able to interact with the AI."
ACCEPTED_FILE_TYPES = {
    "Gemini": {
        "Documents": [
            "application/pdf",
            "application/pdf; charset=utf-8",
            "text/plain",
            "text/plain; charset=utf-8",
            "text/html; charset=utf-8",
            "text/html",
            "text/css",
            "text/css; charset=utf-8",
            "text/md",
            "text/md; charset=utf-8",
            "text/csv; charset=utf-8",
            "text/csv",
            "text/xml; charset=utf-8",
            "text/xml",
            "text/rtf; charset=utf-8"
            "text/rtf"
        ],
        "Scripts": [
            "application/x-javascript",
            "text/javascript",
            "application/x-python",
            "text/x-python",
            "text/x-python; charset=utf-8"
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
            acceptedAttachments.append(attachment)
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
googleClient = genai.Client(api_key=GEMINI_TOKEN)

async def sendEndingWarning(thread: discord.Thread, warnAfter: int, bot: discord.Bot):
    try:
        await asyncio.sleep((CONVERSATION_INACTIVITY_TIMEOUT * 60) - warnAfter)

        if thread.id not in activeThreads:
            return

        formattedLeft = dates.formatSeconds(int(warnAfter))

        peopleWhoSpoke = await thread.fetch_members()

        if peopleWhoSpoke:
            peopleWhoSpoke = filter(lambda member: member.id != bot.user.id, peopleWhoSpoke)
        
        warning = EmbedReply("AI Conversation - Timeout Warning", "ai", description=f"⚠️ You have {formattedLeft} left before the conversation times out!\n\nUse /ai timeoutreset or interact with the AI to keep the conversation for another {dates.formatSeconds(int(CONVERSATION_INACTIVITY_TIMEOUT * 60))}.")
        
        formattedSpeakers = " ".join(f"<@{speaker.id}>" for speaker in peopleWhoSpoke)

        await thread.send(formattedSpeakers, embed=warning)
    except asyncio.CancelledError:
        return
    except discord.NotFound:
        return

def deleteGoogleMedia(threadID: int):
    try:
        global googleClient
        global activeGoogleSafeNames

        namesToDelete = activeGoogleSafeNames[threadID]

        if not namesToDelete:
            raise KeyError(threadID)

        for safeName in namesToDelete:
            googleClient.files.delete(name=safeName)
            
            print(f"GOOGLE AI LOG: Deleted data {safeName} for {threadID} when closing AI conversation.")

        del activeGoogleSafeNames[threadID]
        
        print(f"GOOGLE AI LOG: All data for {threadID} was deleted when closing AI conversation.")
    except KeyError as e:
        print(f"GOOGLE AI LOG: No data for {e} was deleted when closing AI conversation.")
    except Exception as e:
        raise e

os.makedirs(TEMP_DIR, exist_ok=True)

class Ai(commands.Cog):
    ISCOG = True
    global googleClient

    def __init__(self, bot):
        self.bot: discord.Bot = bot
        
        self.description = "Contains modules for commands that use AI."
    
    @commands.Cog.listener()
    async def on_raw_thread_delete(self, payload: discord.RawThreadDeleteEvent):
        threadId = payload.thread_id

        if threadId in activeThreads:
            if threadId in activeGoogleSafeNames:
                deleteGoogleMedia(threadId)

            del activeThreads[threadId]

    ai = discord.SlashCommandGroup("ai", "A collection of commands for prompting AI models.", guild_ids=[799341195109203998])
    
    @ai.command(description = "Converse with an LLM. Use /ai prompt for single requests. Attachments supported.", guild_ids=[799341195109203998])
    async def conversation(
        self,
        ctx: discord.ApplicationContext,
        prompt: discord.Option(
            str,
            description="Starting prompt to ask AI. This will open a Discord thread.",
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
            chatConfig = {
                "max_output_tokens": MAX_TOKENS,
                "top_p": 0.5,
                "temperature": 0.5
            }

            chat = googleClient.chats.create(model="gemini-2.0-flash", config=chatConfig)
        else:
            reply = EmbedReply("AI - Error", "ai", True, description="You picked an invalid model somehow.")

            await reply.send(ctx)
            return
        
        if not isinstance(ctx.channel, discord.Thread):
            threadTitle = f"{ctx.author.name}'s conversation with {model}"

            reply = EmbedReply("AI - Conversation", "ai", description=f"Created new thread for this conversation.")
        
            await reply.send(ctx)

            origMessage = await ctx.interaction.original_response()
            
            thread = await origMessage.create_thread(name=threadTitle, auto_archive_duration=60)

        else:
            reply = EmbedReply("AI - Conversation - Error", "ai", True, description=f"You cannot create an AI conversation inside of a thread as the command creates a thread in and of itself.\n\nIf you would like to use this command, please invoke it in a text channel which is not a thread.\n\nFor one-line prompts to {model}, use /ai prompt.")
        
            await reply.send(ctx)
            return

        if model in ACCEPTED_FILE_TYPES and ACCEPTED_FILE_TYPES[model]:
            threadInstructions = EmbedReply(f"{model} - Conversation", "ai", description=f"You have started a new conversation with {model}. Attachments supported with this model, simply send whatever in this thread.\n\nReply within this thread to continue the conversation.\n\nTo end this conversation, delete this thread or use /ai end. This thread will also close after {dates.formatSeconds(int(CONVERSATION_INACTIVITY_TIMEOUT * 60))} of inactivity.")
        else:
            threadInstructions = EmbedReply(f"{model} - Conversation", "ai", description=f"You have started a new conversation with {model}. Attachments not supported with this model.\n\nReply within this thread to continue the conversation.\n\nTo end this conversation, delete this thread or use /ai end. This thread will also close after {dates.formatSeconds(int(CONVERSATION_INACTIVITY_TIMEOUT * 60))} of inactivity.")

        await thread.send(embed=threadInstructions)

        def conversationCheck(message: discord.Message) -> bool:
            try:
                return all([(message.author == self.bot.user and TIMEOUT_RESET_SUCCESS == message.embeds[0].description) or (message.author != self.bot.user), message.channel == thread])
            except IndexError as e:
                return False
            except discord.NotFound as e:
                return e
            except Exception as e:
                raise e

        activeThreads[thread.id] = True
        activeGoogleSafeNames[thread.id] = []

        closeConversationReply = EmbedReply("AI - Conversation Closed", "ai", description=f"Conversation with {model} started by {ctx.author.mention} has timed out and the thread was deleted.")

        try:
            async with thread.typing():
                if model == "Gemini":
                    await asyncio.to_thread(chat.send_message, f"{SYSTEM_MESSAGE} You can also accept attachments. If the user doesn't know what attachments they can use, tell them to use the '/ai filetypes' command.")
                    initialPrompt = await asyncio.to_thread(chat.send_message, f"{prompt}")
                    
                    splitForDiscord = text.truncateString(initialPrompt.text, 4096, splitOnMax=True)

                    for num, chunk in enumerate(splitForDiscord, 1):
                        initialPromptReply = EmbedReply(f"{model} - Reply - ({num}/{len(splitForDiscord)})", "ai", description=chunk)
                        
                        await thread.send(embed=initialPromptReply)
                else:
                    raise ValueError("Nonexistent model name in initial prompt.")
        except discord.NotFound as e:
            reply = EmbedReply(f"{model} - Error", "ai", True, description=f"Error in conversation when replying to prompt: {e}")

            await reply.send(ctx)
        except Exception as e:
            reply = EmbedReply(f"{model} - Error", "ai", True, description=f"Error: {e}")

            await thread.send(embed=reply)

        while thread.id in activeThreads:
            warningTimer = None

            if INACTIVITY_WARNING:
                warningTimer = asyncio.create_task(sendEndingWarning(thread, INACTIVITY_WARNING, self.bot))
            
            try:
                nextMessage: discord.Message = await self.bot.wait_for("message", check = conversationCheck, timeout = CONVERSATION_INACTIVITY_TIMEOUT * (60))

                if warningTimer:
                    warningTimer.cancel()
                    
                    try:
                        await warningTimer
                    except asyncio.CancelledError:
                        pass
                
                if nextMessage.author == self.bot.user and nextMessage.embeds:
                    if TIMEOUT_RESET_SUCCESS in nextMessage.embeds[0].description:
                        continue

                async with thread.typing():
                    if model == "Gemini":
                        parsedAttachments = await parseAttachments(thread, model, nextMessage.attachments)
                        
                        if not nextMessage.content and parsedAttachments:
                            content = ["Use the attachments provided."]
                        elif nextMessage.attachments and not parsedAttachments:
                            content = ["Prompt the user that you could not use the file and tell them to only submit valid filetypes using the /ai filetypes command."]
                        elif nextMessage.content:
                            content = [nextMessage.content]
                        else:
                            reply = EmbedReply(f"{model} - Error", "ai", True, description=f"Error replying to weird message: no content, no attachments, no parsed attachments.\n\nPlease make sure that you are either giving an attachment to {model}, prompting with text, or both.")

                            await thread.send(embed=reply)
                            continue

                        if parsedAttachments:
                            for originalAttachment in parsedAttachments:
                                googleSafeName = (urllib.parse.quote((re.sub(r'[^a-z0-9]+', '-', (f"{random.randint(0, 1000)}-{(originalAttachment.filename).lower()}"))).strip('-')))[-40:]
                                
                                with tempfile.NamedTemporaryFile(suffix=f"-{googleSafeName}", dir=TEMP_DIR, delete=False) as tmp:
                                    tempPath = tmp.name

                                await originalAttachment.save(tempPath)
                            
                                uploadedFile = googleClient.files.upload(
                                    file=tempPath, 
                                    config={"name": googleSafeName, "mime_type": originalAttachment.content_type}
                                )

                                content.append(uploadedFile)
                                activeGoogleSafeNames[thread.id].append(googleSafeName)

                                os.remove(tempPath)

                        response = await asyncio.to_thread(chat.send_message, content)

                        splitForDiscord = text.truncateString(response.text, 4096, splitOnMax=True)

                        for num, chunk in enumerate(splitForDiscord, 1):
                            reply = EmbedReply(f"{model} - Reply - ({num}/{len(splitForDiscord)})", "ai", description=chunk)
                            
                            await thread.send(embed=reply)
                        
                        continue
                    else:
                        raise ValueError("Nonexistent model name in conversation prompt.")
            except asyncio.TimeoutError:
                if thread.id not in activeThreads:
                    break
                
                del activeThreads[thread.id]

                deleteGoogleMedia(thread.id)

                await thread.parent.send(embed=closeConversationReply)

                try:
                    await thread.delete()
                except discord.NotFound:
                    # Thread is already deleted
                    pass

                break
            except discord.NotFound:
                # Thread is already deleted. Only accessed when threads are ended and the wait_for expires.
                break
            except asyncio.CancelledError:
                # If the thread was manually deleted while waiting, safely exit.
                break
            except ServerError as e:
                reply = EmbedReply("AI - Error", "ai", True)

                if e.message == "The model is overloaded. Please try again later.":
                    reply.description = "You've provided too large of files to the model. All context has been removed and you are back to where the chat started."
                else:
                    reply.description = e.message
                
                await thread.send(embed=reply)
                continue
            except Exception as e:
                reply = EmbedReply("AI - Error", "ai", True, description=f"Error in thread: {e}")

                await thread.send(embed=reply)
                
        
        print(f"CONVERSATION LOG: Terminated/Exited conversation while loop with thread ID: {thread.id}")
    
    @ai.command(description = "End a conversation with an LLM. Only usable inside of threads invoked by /ai conversation.", guild_ids=[799341195109203998])
    async def end(
        self,
        ctx: discord.ApplicationContext
    ):
        try:
            if isinstance(ctx.channel, discord.Thread):
                if ctx.channel.id in activeThreads:
                    thread = self.bot.get_channel(ctx.channel.id)
                    
                    await thread.delete()
                else:
                    reply = EmbedReply("AI - End Conversation - Error", "ai", True, description="This thread cannot be closed because is not registered as an active AI conversation by the bot. You will need to delete this yourself.")

                    await reply.send(ctx)
            else:
                reply = EmbedReply("AI - End Conversation - Error", "ai", True, description="This command can only be used in a thread which was created by the /ai conversation command and is registered as an active AI conversation by the bot.")

                await reply.send(ctx)
        except Exception as e:
            reply = EmbedReply("AI - End Conversation - Error", "ai", True, description=f"Error occured when ending thread: {e}")

            await reply.send(ctx)

    @ai.command(description = f"Reset the {CONVERSATION_INACTIVITY_TIMEOUT} min AI conversation inactivity timer.", guild_ids=[799341195109203998])
    async def timeoutreset(
        self,
        ctx: discord.ApplicationContext
    ):
        try:
            if isinstance(ctx.channel, discord.Thread):
                if ctx.channel.id in activeThreads:
                    thread = self.bot.get_channel(ctx.channel.id)

                    reply = EmbedReply("AI - Timeout Reset", "ai", description=TIMEOUT_RESET_SUCCESS)

                    await reply.send(ctx)
                else:
                    reply = EmbedReply("AI - Timeout Reset - Error", "ai", True, description="This thread's timeout cannot be reset because is not registered as an active AI conversation by the bot. You will need to make a new conversation.")

                    await reply.send(ctx)
            else:
                reply = EmbedReply("AI - Timeout Reset - Error", "ai", True, description="This command can only be used in a thread which was created by the /ai conversation command and is registered as an active AI conversation by the bot.")

                await reply.send(ctx)
        except Exception as e:
            reply = EmbedReply("AI - Timeout Reset - Error", "ai", True, description=f"Error occured when resetting thread timeout: {e}")

            await reply.send(ctx)

    @ai.command(description = f"Archive an AI conversation and spare deletion. You won't be able to interact with the model.", guild_ids=[799341195109203998])
    async def archive(
        self,
        ctx: discord.ApplicationContext
    ):
        try:
            if isinstance(ctx.channel, discord.Thread):
                if ctx.channel.id in activeThreads:
                    thread = self.bot.get_channel(ctx.channel.id)

                    reply = EmbedReply("AI - Archive", "ai", description=ARCHIVE_SUCCESS)

                    await reply.send(ctx)

                    del activeThreads[thread.id]

                    await thread.archive(locked=True)
                else:
                    reply = EmbedReply("AI - Archive - Error", "ai", True, description="This thread cannot be archived because is not registered as an active AI conversation by the bot. You will need to make a new conversation.")

                    await reply.send(ctx)
            else:
                reply = EmbedReply("AI - Archive - Error", "ai", True, description="This command can only be used in a thread which was created by the /ai conversation command and is registered as an active AI conversation by the bot.")

                await reply.send(ctx)
        except Exception as e:
            reply = EmbedReply("AI - Archive - Error", "ai", True, description=f"Error occured when resetting thread timeout: {e}")

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

        try:
            await ctx.defer()
            if model == "Gemini":
                chatConfig = {
                    "max_output_tokens": MAX_TOKENS,
                    "top_p": 0.5,
                    "temperature": 0.5
                }
                
                response = googleClient.models.generate_content(model="gemini-2.0-flash", contents=[SYSTEM_MESSAGE, prompt], config=chatConfig)

                splitForDiscord = text.truncateString(response.text, 4096, splitOnMax=True)

                for num, chunk in enumerate(splitForDiscord, 1):
                    reply = EmbedReply(f"{model} - Reply - ({num}/{len(splitForDiscord)})", "ai", description=chunk)
                    
                    if num == 1:
                        await ctx.followup.send(embed=reply)

                        continue
                    
                    await reply.send(ctx)
            else:
                raise ValueError("Nonexistent model name in prompt.")
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
            reply = EmbedReply(f"{model} - File Types - Error", "ai", True, description=f"{model} does not support attachments.")
            
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