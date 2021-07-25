import discord
import random

from discord.ext import commands
from discord.utils import get
from cogs.game import Game
from math import ceil


class Player(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command()
    async def select(self, ctx, *, message):
        '''New Users can select a Class to use most of bot's functionality'''

        #Check if they chose a valid Class
        if message.lower() not in Game.classes_stats.keys():
            await ctx.send(f"{ctx.author.mention} That was an invalid Class. Use $classes for more information.", delete_after=10)
            await ctx.message.delete(delay=10)
            return
        
        #Check if they have chosen a Class already 
        if get(ctx.author.roles, id=868589512354332793) is not None:
            await ctx.send(f"{ctx.author.mention} You have already chosen a Class.", delete_after=10)
            await ctx.message.delete(delay=10)
            return

        #Add user to database and give Class Selected role
        query = "INSERT INTO user_info (id, class, atk, hp, armor, gold) VALUES ($1, $2, $3, $4, $5, $6);"
        user_id = ctx.author.id
        selected_class = message.lower()
        atk, hp, armor = Game.classes_stats[selected_class]["atk"], Game.classes_stats[selected_class]["hp"], Game.classes_stats[selected_class]["armor"]
        gold = 0
        await self.bot.db.add_user(query, user_id, selected_class, atk, hp, armor, gold)
        print("USER ADDED")
        await ctx.author.add_roles(get(ctx.author.guild.roles, id=868589512354332793))
        await ctx.author.add_roles(get(ctx.author.guild.roles, name=selected_class.capitalize()))
        
        await ctx.send(f"{ctx.author.mention} You haven chosen the {selected_class.capitalize()} Class. Use $hunt to begin earining gold!")

    @commands.command()
    @commands.cooldown(rate=1, per=10, type=commands.BucketType.user)
    @commands.has_role(868589512354332793)
    async def hunt(self, ctx):
        '''Hunt for gold'''
        
        #Get user data
        fetch_query = "SELECT class, gold FROM user_info WHERE id = $1"
        user_id = ctx.author.id
        data = await self.bot.db.fetchrow(fetch_query, user_id)
        
        user_class, user_gold = data["class"], data["gold"]
        
        #Hunt for gold based on user Class
        gold_low, gold_high = Game.classes_stats[user_class]["gold_per_hunt"]["low"], Game.classes_stats[user_class]["gold_per_hunt"]["high"]
        
        #Check for multiplier
        if Game.time_ == "day" and user_class in ["warrior", "mage", "ninja"]:
            multiplier = 2
        elif Game.time_ == "night" and user_class in ["werewolf", "vampire", "zombie"]:
            multiplier = 2
        else:
            multiplier = 1

        gold_amount = random.randint(gold_low, gold_high) * multiplier

        #Update user gold
        update_query = "UPDATE user_info SET gold = $1 WHERE id = $2"
        await self.bot.db.execute(update_query, user_gold + gold_amount, user_id)
        
        await ctx.send(f"{ctx.author.mention} You earned {gold_amount} :coin: from that hunt! You now have {user_gold + gold_amount} :coin:")

    @commands.command()
    @commands.cooldown(rate=1, per=120, type=commands.BucketType.user)
    @commands.has_role(868589512354332793)
    async def rob(self, ctx, *, opponent: discord.Member):
        '''Rob a user for gold'''

        #User cannot rob themselves
        if ctx.author.id == opponent.id:
            await ctx.send(f"{ctx.author.mention} You cannot rob yourself...")
            return
            
        #Check if opponent has picked a Class
        if get(opponent.roles, id=868589512354332793) is None:
            await ctx.send(f"{ctx.author.mention} {opponent.name} has not selected a Class yet.", delete_after=10)
            await ctx.message.delete(delay=10)
            return

        #Get user gold
        user_id = ctx.author.id
        user_query = "SELECT gold FROM user_info WHERE id = $1"
        user_gold = (await self.bot.db.fetchrow(user_query, user_id))["gold"]

        #Get opponent gold
        opponent_id = opponent.id
        opponent_query = "SELECT gold FROM user_info WHERE id = $1"        
        opponent_gold = (await self.bot.db.fetchrow(opponent_query, opponent_id))["gold"]

        #Check if opponent has any gold
        if opponent_gold == 0:
            await ctx.send(f"{ctx.author.mention} {opponent.name} has no gold.")
            return

        amount_stolen = random.randint(ceil(opponent_gold * .05), ceil(opponent_gold * .15))
        user_gold += amount_stolen
        opponent_gold -= amount_stolen

        #Update both user and opponent gold in Database
        user_query = "UPDATE user_info SET gold = $1 WHERE id = $2"
        opponent_query = "UPDATE user_info SET gold = $1 WHERE id = $2"
        await self.bot.db.execute(user_query, user_gold, user_id)
        await self.bot.db.execute(opponent_query, opponent_gold, opponent_id)

        await ctx.send(f"{ctx.author.mention} You stole {amount_stolen} :coin: from {opponent.name}! You now have {user_gold} :coin:.")


def setup(bot):
    bot.add_cog(Player(bot))