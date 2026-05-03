import discord
from discord.ext import commands

TOKEN = 'MTUwMDI0OTk1NTg4NDA3MzI2Mg.GNNOLV.BWz2GaP2Z63JFpgArPqdQbnet_CbZAYywOWbbI'

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'Bot {bot.user} je pripravljen in povezan!')

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    if message.content.lower() == 'zdravo':
        await message.channel.send('Pozdravljen nazaj!')

    await bot.process_commands(message)

bot.run(TOKEN)