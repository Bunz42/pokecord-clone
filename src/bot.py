import discord
from discord.ext import commands
import os
from dotenv import load_dotenv

# Load the secret token from the .env file
load_dotenv()
token = os.getenv('DISCORD_TOKEN')
if token is None:
    raise ValueError("token not found.")

# Set up the bot's intents (what events it is allowed to listen to)
intents = discord.Intents.default()
intents.message_content = True

# Initialize the bot with a command prefix
bot = commands.Bot(command_prefix='!', intents=intents)

# This event runs once when the bot successfully connects to Discord
@bot.event
async def on_ready():
    print(f'Successfully logged in as {bot.user} (ID: {bot.user.id})') # type: ignore
    print('------')

# A basic command: type !ping in Discord, and the bot replies "Pong!"
@bot.command()
async def ping(ctx):
    await ctx.send('Pong!')

# Run the bot
if __name__ == '__main__':
    bot.run(token)