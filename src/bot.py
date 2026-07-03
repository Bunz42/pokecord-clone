from discord import Embed, Color, Intents, File
from discord.ext import commands

import random
import json
import os
from dotenv import load_dotenv

from database import create_db_pool, setup_tables

# -------------------------------------------------ENV VAR + BOT SETUP----------------------------------------------------------- #

load_dotenv()
token = os.getenv('DISCORD_TOKEN')
if token is None:
    raise ValueError("token not found.")

intents = Intents.default()
intents.message_content = True

# bot child class that contains database pool
class PokecordBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix='p!', intents=intents)
        self.pool = None
    
    async def setup_hook(self):
        self.pool = await create_db_pool()
        await setup_tables(self.pool)

        # load cogs
        await self.load_extension("cogs.economy")
        await self.load_extension("cogs.pokemon_mgmt")

bot = PokecordBot()

with open('advanced_pokemon_data.json', 'r') as file:
    POKEMON_DATA = json.load(file)

POKEMON_IDS = list(POKEMON_DATA.keys())
SPAWN_WEIGHTS = [data["weight"] for data in POKEMON_DATA.values()]

# -------------------------------------------------EVENTS----------------------------------------------------------- #

# This event runs once when the bot successfully connects to Discord
@bot.event
async def on_ready():
    print(f'Successfully logged in as {bot.user} (ID: {bot.user.id})') # type: ignore
    print('------')

# -------------------------------------------------COMMANDS----------------------------------------------------------- #


# Run the bot
if __name__ == '__main__':
    bot.run(token)