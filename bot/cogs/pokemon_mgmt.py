import math

from discord import Embed, Color, File
from discord.ext import commands
import random
import json
from cache import get_active_spawn, set_active_spawn, delete_active_spawn, set_pokemon_page, get_pokemon_page

class PokemonManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot # store bot ref for access to conn pool
        
        # load the pokemon data when this cog is created so I can access it wherever in this cog
        with open('ultimate_pokemon_data.json', 'r', encoding='utf-8') as file:
            self.POKEMON_DATA = json.load(file)

        self.POKEMON_IDS = list(self.POKEMON_DATA.keys())
        self.SPAWN_WEIGHTS = [pokemon["spawn_weight"] for pokemon in self.POKEMON_DATA.values()]
        self.SPAWN_RATE = 0.05 # 5% spawn rate per msg
        self.SHINY_CHANCE = 1/4096 # original pokemon game shiny rate


    # -------------------------------------------------HELPER FUNCTIONS------------------------------------------------- #
    async def _send_pokemon_page(self, ctx, owner_id: int, page: int):
        query = '''
            SELECT *, COUNT(*) OVER() AS total_count
            FROM caught_pokemon
            WHERE owner_id = $1
            ORDER BY id
            LIMIT $2 OFFSET $3
        '''

        try:
            async with self.bot.pool.acquire() as conn:
                caught_pokemon = await conn.fetch(query, owner_id, 20, page * 20)
        except Exception as e:
            print(f"Failed to fetch caught pokemon with exception {e}")
            return await ctx.send("Something went wrong fetching your pokemon - Try again.")
        
        total_count = caught_pokemon[0]["total_count"] if caught_pokemon else 0
        total_pages = max(1, math.ceil(total_count / 20))
        page = max(0, min(page, total_pages - 1)) # clamp first and last page

        if not caught_pokemon:
            return await ctx.send("You haven't caught any Pokemon yet!")

        embed = Embed(
            title=f"{ctx.author.display_name}'s Pokemon", 
            color=Color.red()
        )

        for row in caught_pokemon:
            name = self.POKEMON_DATA[str(row["species_id"])]["name"].title()
            embed.add_field(
                name=f"**{name}** {"⭐" if row["is_shiny"] else ""} {"**| LEGENDARY |**" if row["is_legendary"] else ""} {"**| MYTHICAL |**" if row["is_mythical"] else ""} {"**| ULTRA BEAST |**" if row["is_ultra_beast"] else ""}",
                value=f"Lvl: {row["level"]} | Number: {row["id"]} | IV: {row["total_iv_percent"]}%",
                inline=False,
            )
        embed.set_footer(text=f"Page {page + 1}/{total_pages} Type p!pokemon next or p!pokemon prev to navigate!")

        await set_pokemon_page(self.bot.redis, owner_id, page)
        await ctx.send(embed=embed)

    # -------------------------------------------------LISTENERS----------------------------------------------------------- #
    @commands.Cog.listener("on_message")
    async def handle_msg_spawn(self, message):
        if message.author == self.bot.user or message.content.startswith("p!"):
            return

        if random.random() < self.SPAWN_RATE:
            spawn_id = random.choices(self.POKEMON_IDS, weights=self.SPAWN_WEIGHTS, k=1)[0]
            pokemon_info = self.POKEMON_DATA[spawn_id]
            name = pokemon_info["name"]

            spawn_weight = pokemon_info["spawn_weight"] # for testing spawn weighting accuracy

            # RARITY FLAGS
            is_legendary = pokemon_info["is_legendary"] # can use this flag to make legendary/mythic embeds yellow instead of green
            is_mythical = pokemon_info["is_mythical"] # embed color: magenta
            is_ultra_beast = pokemon_info["is_ultra_beast"] # embed color: red
            is_shiny = random.random() < self.SHINY_CHANCE # flag for shiny, embed color: orange

            # IV ROLLS
            iv_hp = random.randint(0, 31)
            iv_atk = random.randint(0, 31)
            iv_def = random.randint(0, 31)
            iv_spatk = random.randint(0, 31)
            iv_spdef = random.randint(0, 31)
            iv_speed = random.randint(0, 31)

            # SETUP SPAWNED POKEMON CACHING
            cached_data = pokemon_info.copy()
            cached_data["species_id"] = spawn_id
            cached_data["is_shiny"] = is_shiny
            cached_data["iv_hp"] = iv_hp
            cached_data["iv_atk"] = iv_atk
            cached_data["iv_def"] = iv_def
            cached_data["iv_spatk"] = iv_spatk
            cached_data["iv_spdef"] = iv_spdef
            cached_data["iv_speed"] = iv_speed

            # print(cached_data) # NOTE: UNCOMMENT FOR DEBUGGING

            channel = message.channel.id

            # set ttl_seconds to 30s and TODO: add some sort of ui that disallows catching if player fails to catch within 30s
            await set_active_spawn(self.bot.redis, channel, cached_data, ttl_seconds=30)

            # NOTE: no need to get from redis here - pokemon_info has everything we need for rendering already

            print(f"Spawned a: {name.title()} (Spawn Weight: {spawn_weight}), (Shiny?: {is_shiny}), (Legendary?: {is_legendary}), (Mythical?: {is_mythical}), (Ultra Beast?: {is_ultra_beast})") # NOTE: UNCOMMENT FOR DEBUGGING

            directory = "shiny" if is_shiny else "regular" # shiny embed description and asset directory logic

            spawn_title = "A wild Pokémon appeared!"

            if is_shiny:
                spawn_title = "⭐ A wild SHINY Pokémon appeared! ⭐"
                embed_color = Color.orange()
            elif is_legendary:
                embed_color = Color.yellow()
            elif is_mythical:
                embed_color = Color.magenta()
            else:
                embed_color = Color.green()

            file = File(f"assets/official-artwork/{directory}/{spawn_id}.png", filename=f"{spawn_id}.png")

            embed = Embed(
                title=spawn_title,
                description="You have 30 seconds to guess the pokemon and type p!catch <pokemon> to catch it!",
                color=embed_color,
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
        species_id = int(spawned_pokemon_data["species_id"])
        pokemon_name = spawned_pokemon_data['name']
        is_shiny = spawned_pokemon_data['is_shiny']
        is_legendary = spawned_pokemon_data['is_legendary']
        is_mythical = spawned_pokemon_data['is_mythical']
        is_ultra_beast = spawned_pokemon_data['is_ultra_beast']
        iv_hp = spawned_pokemon_data["iv_hp"]
        iv_atk = spawned_pokemon_data["iv_atk"]
        iv_def = spawned_pokemon_data["iv_def"]
        iv_spatk = spawned_pokemon_data["iv_spatk"]
        iv_spdef = spawned_pokemon_data["iv_spdef"]
        iv_speed = spawned_pokemon_data["iv_speed"]

        query = '''
            INSERT INTO caught_pokemon (
                owner_id, 
                species_id,
                is_shiny, 
                is_legendary, 
                is_mythical, 
                is_ultra_beast, 
                iv_hp,
                iv_atk,
                iv_def,
                iv_spatk,
                iv_spdef,
                iv_speed,
                caught_at
            )
            VALUES (
                $1, 
                $2, 
                $3, 
                $4, 
                $5,
                $6,
                $7,
                $8,
                $9,
                $10,
                $11,
                $12,
                NOW()
            )
        '''

        # print(f"entered pokemon: {entered_pokemon}, pokemon name: {pokemon_name}")

        if entered_pokemon.lower() == pokemon_name.lower():
            try:
                async with self.bot.pool.acquire() as conn:
                    await conn.execute(
                        query, owner_id, species_id, is_shiny, is_legendary, is_mythical, is_ultra_beast, 
                        iv_hp, iv_atk, iv_def, iv_spatk, iv_spdef, iv_speed
                    )
            except Exception as e:
                print(f"Failed to update pokemon to database with exception {e}")
                return await ctx.send("Something went wrong catching that Pokemon - try again.")

            await delete_active_spawn(self.bot.redis, channel_id)
            bot_msg = f"Congratulations {username}, you caught a **{pokemon_name.title()}**"
            
        else:
            bot_msg = f"{username} That's not the correct pokemon. Try again."
        
        await ctx.send(bot_msg)

    @commands.group(name="pokemon", invoke_without_command=True)
    async def display_player_pokemon(self, ctx):
        await self._send_pokemon_page(ctx, ctx.author.id, page=0)

    @display_player_pokemon.command(name="next")
    async def next_page(self, ctx):
        current = await get_pokemon_page(self.bot.redis, ctx.author.id)
        await self._send_pokemon_page(ctx, ctx.author.id, page=current + 1)

    @display_player_pokemon.command(name="prev")
    async def prev_page(self, ctx):
        current = await get_pokemon_page(self.bot.redis, ctx.author.id)
        await self._send_pokemon_page(ctx, ctx.author.id, page=current - 1)
        
async def setup(bot):
    await bot.add_cog(PokemonManager(bot=bot))