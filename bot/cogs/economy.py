from discord.ext import commands
from discord import Color, Embed
import random

class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot # storing the bot reference so cmds can reach bot.pool
    
    @commands.command(name="daily")
    async def give_daily_balance(self, ctx):
        player_id = ctx.author.id
        rand_bal_addition = random.randint(300, 1000) # TODO: use this for random balance additions
        player_mention = ctx.author.mention

        # TODO: implement time tracking to make it so you can only bal once per day
        
        try:
            async with self.bot.pool.acquire() as conn:

                # player registration now happens in p!pick, so daily only ever
                # updates an existing player who has already chosen a starter.
                row = await conn.fetchrow('''
                    UPDATE players
                    SET balance = balance + $2,
                        last_daily = now()
                    WHERE discord_id = $1
                        AND (last_daily IS NULL OR last_daily < now() - interval '1 day')
                    RETURNING balance
                ''', player_id, rand_bal_addition)

                if row is not None:
                    await ctx.send(f"{player_mention} you claimed **{rand_bal_addition}** coins! Your new balance is **${row['balance']}.**")
                    return

                # no row updated: either the player doesn't exist yet, or they're on cooldown
                remaining_time = await conn.fetchval('''
                    SELECT (last_daily + interval '1 day') - now()
                    FROM players
                    WHERE discord_id = $1
                ''', player_id)

                if remaining_time is None:
                    # no player row -> they haven't picked a starter yet
                    await ctx.send(f"{player_mention} you haven't picked your starter pokemon yet! Run `p!start` to begin.")
                    return

                remaining_seconds = int(remaining_time.total_seconds())
                hours, rem = divmod(remaining_seconds, 3600)
                minutes, seconds = divmod(rem, 60)

                await ctx.send(f"{player_mention} you've already claimed your daily! Come back in **{hours}h and {minutes}m**. ⏳")
        except Exception as e:
            print(f"Failed to update player balance with exception {e}")

    @commands.command(name="balance", aliases=['bal'])
    async def show_balance(self, ctx):
        player_id = ctx.author.id
        mention = ctx.author.mention
        username = ctx.author.display_name
        
        query = '''
            SELECT balance FROM players
            WHERE discord_id = $1
        '''

        async with self.bot.pool.acquire() as conn:
            balance = await conn.fetchval(query, player_id)

            if balance is None:
                await ctx.send(f"{mention} you haven't picked your starter pokemon yet!")
            else:
                embed=Embed(
                    title=f"{username.title()}'s balance 💰",
                    description=f"You currently have **{balance}** credits.",
                    color=Color.yellow()
                )
                await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Economy(bot=bot))