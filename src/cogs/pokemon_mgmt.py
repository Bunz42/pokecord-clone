from discord import Embed, Color, File
from discord.ext import commands
import random
import json
from cache import get_active_spawn, set_active_spawn, delete_active_spawn

class PokemonManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot # store bot ref for access to conn pool
        
        # load the pokemon data when this cog is created so I can access it wherever in this cog
        with open('advanced_pokemon_data.json', 'r') as file:
            self.POKEMON_DATA = json.load(file)

        self.POKEMON_IDS = list(self.POKEMON_DATA.keys())
        self.SPAWN_WEIGHTS = [pokemon["weight"] for pokemon in self.POKEMON_DATA.values()]
        self.SPAWN_RATE = 0.5 # 50% spawn rate per msg
        self.SHINY_CHANCE = 0.5 #50% chance of shiny spawn


    # -------------------------------------------------LISTENERS----------------------------------------------------------- #
    @commands.Cog.listener("on_message")
    async def handle_msg_spawn(self, message):
        if message.author == self.bot.user or message.content.startswith("p!"):
            return

        if random.random() < self.SPAWN_RATE:
            spawn_id = random.choices(self.POKEMON_IDS, weights=self.SPAWN_WEIGHTS, k=1)[0]
            pokemon_info = self.POKEMON_DATA[spawn_id]
            name = pokemon_info["name"]
            is_rare = pokemon_info["is_rare"] # can use this flag to make legendary/mythic embeds yellow instead of green
            is_shiny = random.random() < self.SHINY_CHANCE # flag for shiny

            cached_data = pokemon_info.copy()
            cached_data["is_shiny"] = is_shiny
            channel = message.channel.id

            # set ttl_seconds to 30s and TODO: add some sort of ui that disallows catching if player fails to catch within 30s
            await set_active_spawn(self.bot.redis, channel, cached_data, ttl_seconds=30)
            # no need to get from redis here - pokemon_info has everything we need for rendering already

            print(f"Spawned a: {name.title()} (Rare: {is_rare})") # print name and rarity for testing purposes

            directory = "shiny" if is_shiny else "regular" # shiny spawning logic
            if is_shiny:
                spawn_title = "⭐ A wild SHINY Pokémon appeared! ⭐"
            else:
                spawn_title = "A wild Pokémon appeared!"

            file = File(f"assets/official-artwork/{directory}/{spawn_id}.png", filename=f"{spawn_id}.png")

            embed = Embed(
                title=spawn_title,
                description="You have 30 seconds to guess the pokemon and type p!catch <pokemon> to catch it!",
                color=Color.green() if not is_rare else Color.yellow(),
            )

            embed.set_image(url=f"attachment://{spawn_id}.png")

            await message.channel.send(file=file, embed=embed)

    # -------------------------------------------------COMMANDS----------------------------------------------------------- #
    @commands.command(name="catch")
    async def catch(self, ctx, entered_pokemon: str):
        channel_id = ctx.channel.id
        spawned_pokemon_data = await get_active_spawn(self.bot.redis, channel_id)

        if not spawned_pokemon_data:
            return await ctx.send("There's no wild Pokemon to catch right now!")

        username = ctx.author.mention
        owner_id = ctx.author.id
        pokemon_name = spawned_pokemon_data['name']
        is_shiny = spawned_pokemon_data['is_shiny']
        is_rare = spawned_pokemon_data['is_rare']

        query = '''
            INSERT INTO caught_pokemon (owner_id, is_shiny, caught_at, is_rare, name)
            VALUES ($1, $2, NOW(), $3, $4)
        '''

        # print(f"entered pokemon: {entered_pokemon}, pokemon name: {pokemon_name}")

        if entered_pokemon.lower() == pokemon_name.lower():
            try:
                async with self.bot.pool.acquire() as conn:
                    await conn.execute(query, owner_id, is_shiny, is_rare, pokemon_name)
            except Exception as e:
                print(f"Failed to update pokemon to database with exception {e}")
                return await ctx.send("Something went wrong catching that Pokemon - try again.")

            await delete_active_spawn(self.bot.redis, channel_id)
            bot_msg = f"Congratulations {username}, you caught a **{pokemon_name.title()}**"
            
        else:
            bot_msg = f"{username} That's not the correct pokemon. Try again."
        
        await ctx.send(bot_msg)

async def setup(bot):
    await bot.add_cog(PokemonManager(bot=bot))