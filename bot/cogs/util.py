from discord.ext import commands
from discord import Embed, Color

class Util(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot
    
    @commands.command(name="help")
    async def list_commands(self, ctx):
        embed = Embed(title="Available Commands", color=Color.red())
        for cog_name, cog in self.bot.cogs.items():
            cmds = cog.get_commands()
            if cmds:
                embed.add_field(
                    name=cog_name,
                    value="\n".join(f"`p!{c.name}`" for c in cmds),
                    inline=False
                )
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Util(bot=bot))