import os
import discord
import dotenv

from src import Bot

from src.utils.files import clear_temp_folder
from src.utils.terminal import cls

# Load the .env secret file.
dotenv.load_dotenv()

# Constants.
OWNER = int(os.getenv("OWNER"))  # type: ignore
COGS_PATH = "src.cogs"
BOT_TOKEN = os.getenv("DISCORD_TOKEN")

# Clear terminal.
cls()
clear_temp_folder()

# Enable all intents for the bot.
intents = discord.Intents.all()

# Generate the bot.
bot = Bot(intents=intents, owner_id=OWNER)


# Log messages in console.
@bot.event
async def on_message(m: discord.Message):
    if m.author == bot.user:
        return

    print(f"{m.guild} -> {m.channel} - {m.author} said: {m.content}")


bot.load_extension(COGS_PATH, recursive=True)

# Run the bot.
bot.run(BOT_TOKEN)
