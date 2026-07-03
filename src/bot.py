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

@bot.listen("on_message")
async def handle_msg_spawn(message):
    if message.author == bot.user:
        return

    if random.random() < 0.5: # tune value for spawn rate (currently 50% every msg)
        spawn_id = random.choices(POKEMON_IDS, weights=SPAWN_WEIGHTS, k=1)[0]
        pokemon_info = POKEMON_DATA[spawn_id]
        name = pokemon_info["name"]
        is_rare = pokemon_info["is_rare"] # can use this flag to make legendary/mythic embeds yellow instead of green
            
        print(f"Spawned a: {name.title()} (Rare: {is_rare})") # print name and rarity for testing purposes

        directory = "shiny" if random.random() < 0.5 else "regular" # shiny spawning logic
        if directory == "shiny":
            spawn_title = "⭐ A wild SHINY Pokémon appeared! ⭐"
        else:
            spawn_title = "A wild Pokémon appeared!"


        file = File(f"assets/official-artwork/{directory}/{spawn_id}.png", filename=f"{spawn_id}.png")

        embed = Embed(
            title=spawn_title,
            description="Guess the pokemon and type .catch <pokemon> to catch it!",
            color=Color.green() if not is_rare else Color.yellow(),
        )

        embed.set_image(url=f"attachment://{spawn_id}.png")

        await message.channel.send(file=file, embed=embed)


# -------------------------------------------------COMMANDS----------------------------------------------------------- #
@bot.command(name="catch")
async def catch(ctx, pokemon: str, entered_pokemon: str):
    username = ctx.author.mention
    if entered_pokemon.lower() == pokemon.lower():
        bot_msg = f"Congratulations {username}, you caught a **{pokemon.title()}**"
    else:
        bot_msg = f"{username} That's not the correct pokemon. Try again."
    
    await ctx.send(bot_msg)


# Run the bot
if __name__ == '__main__':
    bot.run(token)