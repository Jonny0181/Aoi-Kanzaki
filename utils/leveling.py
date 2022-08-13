import discord
import random
import aiosqlite
from colr import color
from discord.ext import commands

class Leveling(commands.Cog):
    def __init__(self, bot):
        self.bot  = bot

    async def cog_load(self):
        async with aiosqlite.connect("./data/level.db") as db:
            await db.execute("CREATE TABLE IF NOT EXISTS levels (level INTEGER, xp INTEGER, xpcap INTEGER, user INTEGER, guild INTEGER)")
            await db.execute("CREATE TABLE IF NOT EXISTS levelSettings (levelsys BOOL, role INTEGER, levelreq INTEGER, guild INTEGER)")
            await db.commit()

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        author = message.author
        guild = message.guild
        if message.guild is None:
            return
        async with aiosqlite.connect("./data/level.db") as db:
            levelsys = await db.execute("SELECT levelsys FROM levelSettings WHERE guild = ?", (guild.id,))
            levelsys = await levelsys.fetchone()
            if levelsys and not levelsys[0]:
                return
            xp = await db.execute("SELECT xp FROM levels WHERE user = ? AND guild = ?", (author.id, guild.id,))
            xp = await xp.fetchone()
            xpcap = await db.execute("SELECT xpcap FROM levels WHERE user = ? AND guild = ?", (author.id, guild.id,))
            xpcap = await xpcap.fetchone()
            level = await db.execute("SELECT level FROM levels WHERE user = ? AND guild = ?", (author.id, guild.id,))
            level = await level.fetchone()
            if not xp or not level:
                await db.execute("INSERT INTO levels (level, xp, xpcap, user, guild) VALUES (?, ?, ?, ?, ?)", (0, 0, 1000, author.id, guild.id,))
                await db.commit()
            try:
                xp = xp[0]
                level = level[0]
            except TypeError:
                xp = 0
                level = 0
            xp += round(random.randint(1, 30) * 1.5)
            await db.execute("UPDATE levels SET xp = ? WHERE user = ? AND guild = ?", (xp, author.id, guild.id,))
            if xp >= xpcap[0]:
                level += 1
                xpcap = round(xpcap[0] * 1.25)
                get_role = await db.execute("SELECT role FROM levelSettings WHERE levelreq = ? AND guild = ?", (level, guild.id,))
                role = await get_role.fetchone()
                await db.execute("UPDATE levels SET level = ? WHERE user = ? AND guild = ?", (level, author.id, guild.id,))
                await db.execute("UPDATE levels SET xp = ? WHERE user = ? AND guild = ?", (0, author.id, guild.id,))
                await db.execute("UPDATE levels SET xpcap = ? WHERE user = ? AND guild = ?", (xpcap, author.id, guild.id,))
                if role:
                    role = role[0]
                    role = guild.get_role(role)
                    try:
                        await author.add_roles(role)
                        await message.channel.send(f"{author.mention} has leveled up to **{level}**! Enjoy your new **{role.name}** role!")
                    except discord.HTTPException:
                        await message.channel.send(f"{author.mention} has leveled up to **{level}**! [WAS NOT ABLE TO GIVE LVL UP ROLE]")
                else:
                    await message.channel.send(f"{author.mention} has leveled up to **{level}**!")
            await db.commit()

async def setup(bot):
    await bot.add_cog(Leveling(bot))