from discord import Intents
from discord.ext import commands

import os
from dotenv import load_dotenv

from database import create_db_pool, setup_tables
from cache import get_redis_client

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
        super().__init__(command_prefix='p!', intents=intents, help_command=None)
        self.pool = None
        self.redis = None
    
    async def setup_hook(self):
        self.pool = await create_db_pool()
        await setup_tables(self.pool)
        self.redis = await get_redis_client()

        # load cogs
        await self.load_extension("cogs.economy")
        await self.load_extension("cogs.pokemon_mgmt")
        await self.load_extension("cogs.util")
    
    async def close(self):
        if self.redis:
            await self.redis.aclose() # this closes the redis conn in async manner
        await super().close() # this closes the bot since we're overriding the commands.Bot close function

bot = PokecordBot()

# -------------------------------------------------EVENTS----------------------------------------------------------- #

# This event runs once when the bot successfully connects to Discord
@bot.event
async def on_ready():
    print(f'Successfully logged in as {bot.user} (ID: {bot.user.id})') # type: ignore
    print('------')

# Run the bot
if __name__ == '__main__':
    bot.run(token)