from discord import Embed, Color, Intents, File
from discord.ext import commands

import os
from dotenv import load_dotenv

# -------------------------------------------------ENV VAR + BOT SETUP----------------------------------------------------------- #

load_dotenv()
token = os.getenv('DISCORD_TOKEN')
if token is None:
    raise ValueError("token not found.")

intents = Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

# ------------------------------------------------------------------------------------------------------------------------------- #

# -------------------------------------------------EVENTS----------------------------------------------------------- #

# This event runs once when the bot successfully connects to Discord
@bot.event
async def on_ready():
    print(f'Successfully logged in as {bot.user} (ID: {bot.user.id})') # type: ignore
    print('------')

# ------------------------------------------------------------------------------------------------------------------ #


# -------------------------------------------------COMMANDS----------------------------------------------------------- #
@bot.command(name="spawn", aliases=["s"])
async def handle_spawn(ctx):
    file = File("assets/scaled_sprites/shiny/pikachu.gif", filename="pikachu.gif")

    embed = Embed(
        title="A wild pokemon appeared!", 
        description="Guess the pokemon and type .catch <pokemon> to catch it!",
        color=Color.green()
    )

    embed.set_image(url="attachment://pikachu.gif")

    await ctx.send(file=file, embed=embed)

# -------------------------------------------------------------------------------------------------------------------- #

# Run the bot
if __name__ == '__main__':
    bot.run(token)