#Импорт библиотек
import discord
from discord.ext import commands
from discord import ui as dis_ui 
from configs import settings
from discord import guild
from requests import get
import sqlite3
from discord.ui import Button, View
from QiwiBillPaymentsAPI import QiwiBillPaymentsAPI
from random import randint

intents = discord.Intents.all() # НАМЕРЕНИЕ ПРИСУТСТВИЯ. Требуется, чтобы ваш бот получал события
intents.members = True 
intents.message_content = True

connection = sqlite3.connect('server.db')
cursor = connection.cursor()

bot = commands.Bot(command_prefix="/", intents=intents) # Префикс,с чего начинается команда
guild_group = int(settings['guild_group'])

PUBLIC_KEY = '48e7qUxn9T7RyYE1MVZswX1FRSbE6iyCj2gCRwwF3Dnh5XrasNTx3BGPiMsyXQFNKQhvukniQG8RTVhYm3iPufHmkigGKF445cTTXMoM5p3YJjJmtk9D9rmjYb5y4uB77RnRSBxtpUAvYcLbG2UGoWZkT7g1RvrM4co65kFp3qw9JyJpKSNnc8f75Yr1Z'
SECRET_KEY = 'eyJ2ZXJzaW9uIjoiUDJQIiwiZGF0YSI6eyJwYXlpbl9tZXJjaGFudF9zaXRlX3VpZCI6Imc2ejRtZi0wMCIsInVzZXJfaWQiOiI3OTUwNTU0NzcyOSIsInNlY3JldCI6IjU3YTJmNzg1OGQwMDViODhjMTBlZTY0NzNhYjY2NmYwZDc4MGM3ODM1N2ZjNDMyYWY0YzllZmQ4OTdjYjQwOGUifX0'

qiwiApi = QiwiBillPaymentsAPI(PUBLIC_KEY, SECRET_KEY)

@bot.event
async def on_ready():
    guild_count = 0
    for guild in bot.guilds:
        print(f"- {guild.id} (name: {guild.name})")

        guild_count = guild_count + 1
    print('Loaded AutoDonate Bot... | version 0.1 | created Gecoste Studio | guilds' + ' ' + str(guild_count))
    await bot.change_presence(status = discord.Status.online)
    
    cursor.execute("""CREATE TABLE IF NOT EXISTS users (
    name TEXT,
    id INT,
    money BIGINT,
    adm INT
    )""")
    connection.commit()
    
    guc = bot.get_guild(guild_group)
    members = await guc.fetch_members(limit = 3000, after =None).flatten()
    
    for guild in bot.guilds:
        for member in members:
            if cursor.execute(f"SELECT id FROM users WHERE id = {member.id}").fetchone() is None:
                cursor.execute(f"INSERT INTO users VALUES ('{member}', {member.id}, 0, 0)")
            else:
                pass
    
    connection.commit()
    print('client (users) connected for BaseData')
    
@bot.event
async def on_member_join(member):
    if cursor.execute(f"SELECT id FROM users WHERE id = {member.id}").fetchone() is None:
        cursor.execute(f"INSERT INTO users VALUES ('{member}', {member.id}, 0, 0)")
        connection.commit()
    else:
        pass
    await bot.process_commands(member)
#Подключение к правам администратора

@bot.event
async def on_message(message):
    if message.content.startswith('adminpanel'):
        user_id = str(message.author.id)
        if user_id in settings['admin_user']:
            author = int(user_id)
            await message.channel.send(f'{message.author.mention} - зашел(ла) в админ панель!')
            cursor.execute('UPDATE users SET adm = {} WHERE id = {}'.format(int(1), author))
        else:
            author = int(user_id)
            await message.author.send(f'{message.author.mention}. У вас недостаточно прав,для совершения действия!')
    await bot.process_commands(message)
#Основной код с методами и командами

class startbutton(dis_ui.View):  # класс описывает набор кнопок
    def __init__(self, *, timeout=180):  # конструктор класса
        super().__init__(timeout=timeout)
    @dis_ui.button(label="📖Помощь",style=discord.ButtonStyle.gray)
    async def help_button(self,button:discord.ui.Button,interaction:discord.Interaction):
        await interaction.response.edit_message(content=f"This is an edited button response!")
    @dis_ui.button(label="☎️Тех.Поддержка",style=discord.ButtonStyle.gray)
    async def poc_button(self,button:discord.ui.Button,interaction:discord.Interaction):
        await interaction.response.edit_message(content=f"This is an edited button response!")

@bot.slash_command(id_server=settings['chanel_id'], description='Магазин,профиль и Техническая Поддержка')
async def start(ctx):  # по команде /start отсылается сообщение с кнопками
    try:
        await ctx.delete()
    except discord.errors.NotFound:
        pass
    embed=discord.Embed(title="Основное меню", description="Выберите опцию,которую хотите выполнить: ", color=0x00FFFF)
    embed.set_thumbnail(url = ctx.author.avatar)
    message = await ctx.send(embed=embed)
    back_menu = Button(label="🔙Профиль",style=discord.ButtonStyle.gray)
    
    async def back_callback(interaction):
        await profile(ctx=ctx)
        
    back_menu.callback=back_callback
    viewbutton=View()
    viewbutton.add_item(back_menu)
    await ctx.send(
        view=viewbutton)

@bot.slash_command(id_server=settings['chanel_id'], description='Пополнить баланс')
async def пополнить(ctx, amount: int = None):
    try:
        await ctx.delete()
    except discord.errors.NotFound:
        pass
    bill_id = randint(13232434, 46577847)
    params = {
    'publicKey': qiwiApi.public_key,
    'amount': amount,
    'billId': bill_id,
    'successUrl': f'https://merchant.com/payment/success?billId={bill_id}'
    }
    link = qiwiApi.createPaymentForm(params)
    await ctx.send(f'Ссылка: {link}')

@bot.slash_command(id_server=settings['chanel_id'], description='Изменение баланса пользователя')
async def put(ctx, member : discord.Member = None, amount : int = None):
    try:
        await ctx.delete()
    except discord.errors.NotFound:
        pass
    user = cursor.execute(f'SELECT adm FROM users WHERE id = {ctx.author.id}').fetchone()[0]
    if user != 0:
        if member is None:
            await ctx.send(f"**{ctx.author.mention}**, укажите пользователя, которому хотите начислить рубли!")
        else:
            if amount is None:
                await ctx.send(f"**{ctx.author.mention}**, укажите сумму, которую желаете отнять у счета пользователя")
            elif int(amount) < 1:
                await ctx.send(f"**{ctx.author.mention}**, укажите сумму больше 1 :leaves:")
            else:
                cursor.execute("UPDATE users SET money = money + {} WHERE id = {}".format(int(amount), member.id))
                await ctx.send(f'{ctx.author.mention}, вы успешно передали {member.id} : {amount} рубль(ей)')
                connection.commit()
    else:
        await ctx.send(f'{ctx.author.mention}, вы не имеете прав администратора или разработчика!')

@bot.slash_command(id_server=settings['chanel_id'], description='Ваш Профиль')
async def profile(ctx):
    try:
        await ctx.delete()
    except discord.errors.NotFound:
        pass
    embed = discord.Embed(colour = discord.Colour(0x00FFFF), description = f'Профиль - {ctx.author.mention}: ')
    embed.set_thumbnail(url = ctx.author.avatar)
    embed.add_field(name='', value=f'''Ваш баланс составляет **{cursor.execute(f'SELECT money FROM users WHERE id = {ctx.author.id}').fetchone()[0]}** рублей''')
    message = await ctx.send(embed=embed)
    back_menu = Button(label="🔙Вернуться в главное меню",style=discord.ButtonStyle.gray)
    
    async def back_callback(interaction):
        await start(ctx=ctx)
        
    back_menu.callback=back_callback
    viewbutton=View()
    viewbutton.add_item(back_menu)
    await ctx.send(
        view=viewbutton)
        
bot.run(token= settings['token']) #Обязательное заполнение
