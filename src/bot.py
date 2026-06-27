from discord import Embed, Color, Intents, File
from discord.ext import commands
import random
import json

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

# -------------------------------------------------FUNCTIONS----------------------------------------------------------- #
async def function(param):
    pass 

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
        with open('pokemon_data.json' , 'r') as file: # access pokemon data (name and id)
            data = json.load(file)
            id = random.randint(1, 1025)
            name = data[str(id)]
            
            print(f"Spawned a: {name.title()}") # print name for testing purposes

            directory = "shiny" if random.random() < 0.5 else "regular" # shiny spawning logic
            if directory == "shiny":
                spawn_title = "⭐ A wild SHINY Pokémon appeared! ⭐"
            else:
                spawn_title = "A wild Pokémon appeared!"


            file = File(f"assets/official-artwork/{directory}/{id}.png", filename=f"{id}.png")

            embed = Embed(
                title=spawn_title,
                description="Guess the pokemon and type .catch <pokemon> to catch it!",
                color=Color.green(),
            )

            embed.set_image(url=f"attachment://{id}.png")

            await message.channel.send(file=file, embed=embed)


# -------------------------------------------------COMMANDS----------------------------------------------------------- #
# @bot.command(name="spawn", aliases=["s"])


# Run the bot
if __name__ == '__main__':
    bot.run(token)