import math

from discord import Embed, Color, File
from discord.ext import commands
import random
import json
from cache import get_active_spawn, set_active_spawn, delete_active_spawn, set_pokemon_page, get_pokemon_page

NATURE_MODIFIERS = {
    "hardy": {}, "lonely": {"increased": "attack", "decreased": "defense"},
    "brave": {"increased": "attack", "decreased": "speed"},
    "adamant": {"increased": "attack", "decreased": "special-attack"},
    "naughty": {"increased": "attack", "decreased": "special-defense"},
    "bold": {"increased": "defense", "decreased": "attack"},
    "docile": {},
    "relaxed": {"increased": "defense", "decreased": "speed"},
    "impish": {"increased": "defense", "decreased": "special-attack"},
    "lax": {"increased": "defense", "decreased": "special-defense"},
    "timid": {"increased": "speed", "decreased": "attack"},
    "hasty": {"increased": "speed", "decreased": "defense"},
    "serious": {},
    "jolly": {"increased": "speed", "decreased": "special-attack"},
    "naive": {"increased": "speed", "decreased": "special-defense"},
    "modest": {"increased": "special-attack", "decreased": "attack"},
    "mild": {"increased": "special-attack", "decreased": "defense"},
    "quiet": {"increased": "special-attack", "decreased": "speed"},
    "bashful": {},
    "rash": {"increased": "special-attack", "decreased": "special-defense"},
    "calm": {"increased": "special-defense", "decreased": "attack"},
    "gentle": {"increased": "special-defense", "decreased": "defense"},
    "sassy": {"increased": "special-defense", "decreased": "speed"},
    "careful": {"increased": "special-defense", "decreased": "special-attack"},
    "quirky": {},
}

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
    def _get_rarity_color(self, pokemon):
        if pokemon["is_shiny"]:
            return Color.gold()
        elif pokemon["is_legendary"]:
            return Color.yellow()
        elif pokemon["is_mythical"]:
            return Color.magenta()
        elif pokemon["is_ultra_beast"]:
            return Color.red()
        return Color.green()

    def _calculate_stats(self, base_stats, ivs, level, nature):
        nature_mods = NATURE_MODIFIERS.get(nature.lower(), {})

        stats = {"hp": (2 * base_stats["hp"] + ivs["hp"]) * level // 100 + level + 10}

        for stat in ("attack", "defense", "special-attack", "special-defense", "speed"):
            value = (2 * base_stats[stat] + ivs[stat]) * level // 100 + 5
            if nature_mods.get("increased") == stat:
                value = math.floor(value * 1.1)
            elif nature_mods.get("decreased") == stat:
                value = math.floor(value * 0.9)
            stats[stat] = value

        return stats

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
                value=f"Level: {row["level"]} | Number: {row["id"]} | IV: {row["total_iv_percent"]}%",
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

            embed_color = self._get_rarity_color(cached_data)

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

    @commands.command(name="select")
    async def select_pokemon(self, ctx, pokemon_id: int):
        player_id = ctx.author.id
        player_mention = ctx.author.mention

        query = '''
            UPDATE players
            SET active_pokemon_id = $1
            FROM caught_pokemon
            WHERE players.discord_id = $2
                AND caught_pokemon.id = $1
                AND caught_pokemon.owner_id = $2
            RETURNING caught_pokemon.species_id
        '''
        try:
            async with self.bot.pool.acquire() as conn:
                species_id = await conn.fetchval(query, pokemon_id, player_id)

            if species_id is None:
                await ctx.send(f"{player_mention} you don't own a Pokemon with that ID.")
            else:
                pokemon_name = self.POKEMON_DATA[str(species_id)]["name"].title()
                await ctx.send(f"{player_mention} your active Pokemon has been set to **{pokemon_name}** (#{pokemon_id}).")
        except Exception as e:
            print(f"Failed to select pokemon with exception {e}")
            await ctx.send("Something went wrong selecting this pokemon.")

    @commands.command(name="info")
    async def display_selected_pokemon(self, ctx):
        player_id = ctx.author.id
        player_mention = ctx.author.mention
        
        query = '''
            SELECT caught_pokemon.*
            FROM players
            JOIN caught_pokemon ON caught_pokemon.id = players.active_pokemon_id
            WHERE players.discord_id = $1
        '''

        try:
            async with self.bot.pool.acquire() as conn:
                row = await conn.fetchrow(query, player_id)

                if row is None:
                    await ctx.send(f"{player_mention} you don't have a pokemon selected! Use `p!select <number>` to select one!")
                else:
                    embed_color = self._get_rarity_color(row)

                    species_data = self.POKEMON_DATA[str(row['species_id'])]
                    form_data = species_data['forms'][row['form']]

                    ivs = {
                        "hp": row['iv_hp'],
                        "attack": row['iv_atk'],
                        "defense": row['iv_def'],
                        "special-attack": row['iv_spatk'],
                        "special-defense": row['iv_spdef'],
                        "speed": row['iv_speed'],
                    }
                    stats = self._calculate_stats(form_data['base_stats'], ivs, row['level'], row['nature'])

                    # TODO: no per-species growth rate data yet - assumes medium-fast (level^3) curve for every species
                    xp_to_next_level = (row['level'] + 1) ** 3 - row['level'] ** 3

                    types_line = " | ".join(t.title() for t in form_data['types'])

                    description = "\n".join([
                        f"{row['xp']}/{xp_to_next_level}XP",
                        f"**Types:** {types_line}",
                        f"**Nature:** {row['nature'].title()}",
                        f"**HP:** {stats['hp']} - IV: {row['iv_hp']}/31",
                        f"**Attack:** {stats['attack']} - IV: {row['iv_atk']}/31",
                        f"**Defense:** {stats['defense']} - IV: {row['iv_def']}/31",
                        f"**Sp. Atk:** {stats['special-attack']} - IV: {row['iv_spatk']}/31",
                        f"**Sp. Def:** {stats['special-defense']} - IV: {row['iv_spdef']}/31",
                        f"**Speed:** {stats['speed']} - IV: {row['iv_speed']}/31",
                        f"**Total IV %:** {row['total_iv_percent']}%",
                    ])

                    oak_file = File("assets/professor_oak.jpg", filename="professor_oak.jpg")

                    directory = "shiny" if row['is_shiny'] else "regular"
                    artwork_file = File(f"assets/official-artwork/{directory}/{row['species_id']}.png", filename=f"{row['species_id']}.png")

                    embed = Embed(
                        title=f"Level {row['level']} {species_data['name'].title()} {" ⭐" if row['is_shiny'] else ""}",
                        description=description,
                        color=embed_color
                    )
                    embed.set_author(name="Professor Oak", icon_url="attachment://professor_oak.jpg")
                    embed.set_image(url=f"attachment://{row['species_id']}.png")

                    await ctx.send(files=[oak_file, artwork_file], embed=embed)

        except Exception as e:
            print(f"Failed to display pokemon info with exception {e}")

async def setup(bot):
    await bot.add_cog(PokemonManager(bot=bot))