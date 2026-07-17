from discord.ext import commands
from discord import Embed, Color, File
import random

AVAILABLE_STARTERS = {
    1: {
        "region": "Kanto",
        "starters": [
            {"name": "bulbasaur", "species_id": 1},
            {"name": "charmander", "species_id": 4},
            {"name": "squirtle", "species_id": 7},
        ],
    },
    2: {
        "region": "Johto",
        "starters": [
            {"name": "chikorita", "species_id": 152},
            {"name": "cyndaquil", "species_id": 155},
            {"name": "totodile", "species_id": 158},
        ],
    },
    3: {
        "region": "Hoenn",
        "starters": [
            {"name": "treecko", "species_id": 252},
            {"name": "torchic", "species_id": 255},
            {"name": "mudkip", "species_id": 258},
        ],
    },
    4: {
        "region": "Sinnoh",
        "starters": [
            {"name": "turtwig", "species_id": 387},
            {"name": "chimchar", "species_id": 390},
            {"name": "piplup", "species_id": 393},
        ],
    },
    5: {
        "region": "Unova",
        "starters": [
            {"name": "snivy", "species_id": 495},
            {"name": "tepig", "species_id": 498},
            {"name": "oshawott", "species_id": 501},
        ],
    },
    6: {
        "region": "Kalos",
        "starters": [
            {"name": "chespin", "species_id": 650},
            {"name": "fennekin", "species_id": 653},
            {"name": "froakie", "species_id": 656},
        ],
    },
    7: {
        "region": "Alola",
        "starters": [
            {"name": "rowlet", "species_id": 722},
            {"name": "litten", "species_id": 725},
            {"name": "popplio", "species_id": 728},
        ],
    },
    8: {
        "region": "Galar",
        "starters": [
            {"name": "grookey", "species_id": 810},
            {"name": "scorbunny", "species_id": 813},
            {"name": "sobble", "species_id": 816},
        ],
    },
    9: {
        "region": "Paldea",
        "starters": [
            {"name": "sprigatito", "species_id": 906},
            {"name": "fuecoco", "species_id": 909},
            {"name": "quaxly", "species_id": 912},
        ],
    },
}

class Start(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name="start")
    async def show_starters(self, ctx):
        artwork_file = File("assets/pokemon_starters_.webp", filename="pokemon_starters.webp")

        embed = Embed(
            title="**Choose Your Starter!**",
            description="Pick a generation below, then type `p!pick <pokemon>` to begin your journey!",
            color=Color.blue(),
        )

        for gen, data in AVAILABLE_STARTERS.items():
            starter_names = " | ".join(starter["name"].title() for starter in data["starters"])
            embed.add_field(
                name=f"Gen {gen} - {data['region']}",
                value=starter_names,
                inline=False,
            )

        embed.set_image(url="attachment://pokemon_starters.webp")
        await ctx.send(file=artwork_file, embed=embed)

    @commands.command(name="pick")
    async def pick_starter(self, ctx, *, pokemon: str | None = None):
        """Picks the users starter and registers them as a player if not already"""
        player_id = ctx.author.id
        player_mention = ctx.author.mention

        if pokemon is None:
            return await ctx.send(f"{player_mention} you need to name a starter! Run `p!start` to view the list, then `p!pick <pokemon name>`.")

        # validate the choice against the available starters
        chosen = None
        for gen_data in AVAILABLE_STARTERS.values():
            for starter in gen_data["starters"]:
                if starter["name"] == pokemon.lower().strip():
                    chosen = starter
                    break
            if chosen:
                break

        if chosen is None:
            return await ctx.send(f"{player_mention} **{pokemon}** isn't an available starter! Run `p!start` to view the list of valid starters.")

        species_id = chosen["species_id"]

        # IV ROLLS
        iv_hp = random.randint(0, 31)
        iv_atk = random.randint(0, 31)
        iv_def = random.randint(0, 31)
        iv_spatk = random.randint(0, 31)
        iv_spdef = random.randint(0, 31)
        iv_speed = random.randint(0, 31)

        already_started = False
        try:
            async with self.bot.pool.acquire() as conn:
                async with conn.transaction():
                    # anti-farm gate: owning any pokemon means they've already started
                    already_started = await conn.fetchval('''
                        SELECT EXISTS (SELECT 1 FROM caught_pokemon WHERE owner_id = $1)
                    ''', player_id)

                    if not already_started:
                        # register the player if they're brand new (economy's p!daily may already have)
                        await conn.execute('''
                            INSERT INTO players (discord_id)
                            VALUES ($1) ON CONFLICT DO NOTHING
                        ''', player_id)

                        new_pokemon_id = await conn.fetchval('''
                            INSERT INTO caught_pokemon (
                                owner_id, original_owner_id, species_id,
                                level, iv_hp, iv_atk, iv_def, iv_spatk, iv_spdef, iv_speed
                            ) VALUES (
                                $1, $1, $2, 5, $3, $4, $5, $6, $7, $8
                            )
                            RETURNING id
                        ''', player_id, species_id, iv_hp, iv_atk, iv_def, iv_spatk, iv_spdef, iv_speed)

                        # set the freshly picked starter as their active pokemon
                        await conn.execute('''
                            UPDATE players SET active_pokemon_id = $1 WHERE discord_id = $2
                        ''', new_pokemon_id, player_id)
        except Exception as e:
            print(f"Failed to give starter pokemon with exception {e}")
            return await ctx.send("Something went wrong picking your starter - try again.")

        if already_started:
            return await ctx.send(f"{player_mention} you've already chosen a starter! You can't pick another one.")

        await ctx.send(f"Congratulations {player_mention}, you chose **{chosen['name'].title()}** as your starter! Run `p!info` to see it.")

async def setup(bot):
    await bot.add_cog(Start(bot=bot))