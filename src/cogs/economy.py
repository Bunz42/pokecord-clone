from discord.ext import commands
import random

class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot # storing the bot reference so cmds can reach bot.pool
    
    @commands.command(name="daily")
    async def give_daily_balance(self, ctx):
        player_id = ctx.author.id
        player_name = ctx.author.display_name
        rand_bal_addition = random.randint(300, 1000) # TODO: use this for random balance additions
        player_mention = ctx.author.mention

        # TODO: implement time tracking to make it so you can only bal once per day
        
        try:
            async with self.bot.pool.acquire() as conn:

                """
                query to update a player's balance (temporary implementation for insertion of player if they don't exist 
                in db yet: 
                TODO -> migrate this to the starter command and add gates to all other cmds
                """

                row = await conn.fetchrow('''
                    INSERT INTO players (discord_id, name, balance, last_daily)
                    VALUES ($1, $2, $3, now())
                    ON CONFLICT (discord_id)
                    DO UPDATE SET 
                        balance = players.balance + $3,
                        last_daily = now()
                    WHERE players.last_daily IS NULL
                        OR players.last_daily < now() - interval '10 minutes'
                    RETURNING balance
                ''', player_id, player_name, rand_bal_addition)

                if row is None:

                    # Interval for daily claims set to 10 minutes right now for testing purposes. Change to '1 day' in the UPDATE and the SELECT query for actual.

                    remaining_time = await conn.fetchval('''
                        SELECT (last_daily + interval '10 minutes') - now() 
                        FROM players
                        WHERE discord_id = $1
                    ''', player_id)

                    remaining_seconds = int(remaining_time.total_seconds())
                    hours, rem = divmod(remaining_seconds, 3600)
                    minutes, seconds = divmod(rem, 60)

                    await ctx.send(f"{player_mention} you've already claimed your daily! Come back in **{hours}h and {minutes}m**. ⏳")
                else:
                    await ctx.send(f"{player_mention} you claimed **{rand_bal_addition}** coins! Your new balance is **${row['balance']}.**")
        except Exception as e:
            print(f"Failed to update player balance with exception {e}")

async def setup(bot):
    await bot.add_cog(Economy(bot=bot))