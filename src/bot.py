from discord import Embed, Color, Intents, File
from discord.ext import commands
import random

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

# -------------------------------------------------FUNCTIONS----------------------------------------------------------- #
async def function(param):
    pass
    
# --------------------------------------------------------------------------------------------------------------------- #

# -------------------------------------------------EVENTS----------------------------------------------------------- #

# This event runs once when the bot successfully connects to Discord
@bot.event
async def on_ready():
    print(f'Successfully logged in as {bot.user} (ID: {bot.user.id})') # type: ignore
    print('------')

@bot.listen("on_message")
async def handle_msg_spawn(message):
    if message.author == bot.user:
        return
    

    if random.random() < 0.5: # tune value for spawn rate (currently 50% every msg)

        # print("50% chance event happened!")

        directory = "shiny" if random.random() < 0.5 else "regular"
        file = File(f"assets/scaled_sprites/{directory}/pikachu.gif", filename="pikachu.gif")

        embed = Embed(
            title="A wild pokemon appeared!", 
            description="Guess the pokemon and type .catch <pokemon> to catch it!",
            color=Color.green(),
        )

        embed.set_image(url="attachment://pikachu.gif")

        await message.channel.send(file=file, embed=embed)

# ------------------------------------------------------------------------------------------------------------------ #


# -------------------------------------------------COMMANDS----------------------------------------------------------- #
# @bot.command(name="spawn", aliases=["s"])


# -------------------------------------------------------------------------------------------------------------------- #

# Run the bot
if __name__ == '__main__':
    bot.run(token)