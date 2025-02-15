import discord
from discord.ext import commands
from discord.ui import View, Modal, TextInput
from datetime import datetime, timedelta
import sqlite3

# Подключение к базе данных SQLite
conn = sqlite3.connect('bot_database.db')
cursor = conn.cursor()

# Создание таблиц
# Создание таблиц
# Создание таблиц
cursor.execute('''
CREATE TABLE IF NOT EXISTS voice_sessions (
    session_id INTEGER PRIMARY KEY,
    user_id INTEGER,
    guild_id INTEGER,
    channel_id INTEGER,
    start_time DATETIME,
    end_time DATETIME,
    duration INTEGER
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS user_messages (
    user_id INTEGER,
    guild_id INTEGER,
    message_count INTEGER,
    PRIMARY KEY (user_id, guild_id)
)
''')
conn.commit()

# Токен вашего бота
BOT_TOKEN = '---'

# ID отслеживаемого голосового канала
WATCHED_CHANNEL_ID = 1241459903730548826

intents = discord.Intents.default()
intents.messages = True
intents.voice_states = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Словарь для отслеживания созданных каналов
created_channels = {}

# Словарь для отслеживания голосовых сессий
voice_sessions = {}


class EditChannelModal(Modal, title="Изменение канала"):
    def __init__(self, channel):
        super().__init__()
        self.channel = channel
        self.add_item(TextInput(label="Название канала", default=channel.name, max_length=100))
        self.add_item(TextInput(label="Лимит пользователей", default="0", max_length=3, required=False))

    async def on_submit(self, interaction: discord.Interaction):
        new_name = self.children[0].value
        new_limit = int(self.children[1].value) if self.children[1].value.isdigit() else 0

        # Изменение канала
        await self.channel.edit(name=new_name, user_limit=new_limit)

        # Уведомление об успешных изменениях
        await interaction.response.send_message(
            embed=discord.Embed(
                title="Канал изменён!",
                description=f"Название: `{new_name}`\nЛимит пользователей: `{new_limit}`",
                color=discord.Color.green()
            ),
            ephemeral=True
        )


class ChannelControlView(View):
    def __init__(self, channel, owner):
        super().__init__()
        self.channel = channel
        self.owner = owner  # Владелец канала

    @discord.ui.button(label="Изменить канал", style=discord.ButtonStyle.primary)
    async def edit_channel(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Проверка, что взаимодействие инициировал создатель канала
        if interaction.user != self.owner:
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="Доступ запрещён",
                    description="Только создатель канала может изменять его настройки.",
                    color=discord.Color.red()
                ),
                ephemeral=True
            )
            return

        # Открытие модального окна для редактирования
        await interaction.response.send_modal(EditChannelModal(self.channel))


@bot.event
async def on_ready():
    print(f"Бот запущен как {bot.user}")
    await bot.tree.sync()  # Синхронизация команд
    print("Команды синхронизированы!")


@bot.event
async def on_voice_state_update(member, before, after):
    guild = member.guild

    # Проверка: пользователь зашел в отслеживаемый канал
    if after.channel and after.channel.id == WATCHED_CHANNEL_ID:
        category = after.channel.category

        # Создание нового голосового канала
        new_channel = await guild.create_voice_channel(
            name=f"Канал {member.name}",
            category=category,
            overwrites={
                guild.default_role: discord.PermissionOverwrite(view_channel=True),  # Открываем для всех
                member: discord.PermissionOverwrite(
                    view_channel=True,
                    manage_channels=True
                ),
            }
        )

        # Сохранение ID созданного канала
        created_channels[new_channel.id] = {"channel_id": new_channel.id, "owner": member}

        # Перемещение пользователя в созданный канал
        await member.move_to(new_channel)

        # Получение текстового чата, связанного с голосовым каналом
        text_channel = new_channel.guild.get_channel(new_channel.id)
        if text_channel is None:
            text_channel = await new_channel.create_text_channel(name=f"chat-{new_channel.name}")

        # Отправка embed-сообщения с кнопками в текстовый чат голосового канала
        embed = discord.Embed(
            title="Управление каналом",
            description="Вы можете изменить название канала или установить лимит участников.",
            color=discord.Color.blurple()
        )
        embed.add_field(name="Название канала", value=new_channel.name, inline=False)
        embed.add_field(name="Лимит пользователей", value="0", inline=False)

        view = ChannelControlView(new_channel, member)  # Передача владельца
        await text_channel.send(embed=embed, view=view)

    # Проверка: пользователь покинул голосовой канал
    if before.channel and before.channel.id in created_channels:
        # Получение канала
        channel = guild.get_channel(before.channel.id)

        # Если канал пуст, удалить его
        if channel and len(channel.members) == 0:
            await channel.delete()
            del created_channels[before.channel.id]

    # Логирование времени в голосовых каналах
    if member.bot:
        return

    guild_id = member.guild.id
    user_id = member.id

    # Пользователь зашел в канал
    if before.channel is None and after.channel is not None:
        voice_sessions[user_id] = {
            'channel_id': after.channel.id,
            'start_time': datetime.now()
        }

    # Пользователь вышел или сменил канал
    elif before.channel is not None and (after.channel is None or after.channel != before.channel):
        if user_id in voice_sessions:
            session = voice_sessions[user_id]
            end_time = datetime.now()
            duration = int((end_time - session['start_time']).total_seconds())

            cursor.execute('''
                INSERT INTO voice_sessions (user_id, guild_id, channel_id, start_time, end_time, duration)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, guild_id, session['channel_id'], session['start_time'], end_time, duration))
            conn.commit()

            # Если пользователь перешел в другой канал, начинаем новую сессию
            if after.channel is not None:
                voice_sessions[user_id] = {
                    'channel_id': after.channel.id,
                    'start_time': datetime.now()
                }
            else:
                del voice_sessions[user_id]


@bot.event
async def on_message(message):
    if message.author.bot or not message.guild:
        return

    cursor.execute('''
        INSERT INTO user_messages (user_id, guild_id, message_count)
        VALUES (?, ?, 1)
        ON CONFLICT(user_id, guild_id) DO UPDATE SET
        message_count = message_count + 1
    ''', (message.author.id, message.guild.id))
    conn.commit()

    await bot.process_commands(message)


@bot.tree.command(name="stats", description="Посмотреть статистику активности")
async def stats(interaction: discord.Interaction, пользователь: discord.Member = None):
    # Если пользователь не указан, используем автора команды
    target_user = пользователь if пользователь else interaction.user
    guild = interaction.guild
    member = await guild.fetch_member(target_user.id)
    
    # Основная информация
    embed = discord.Embed(
        title=f"Статистика {target_user.display_name}",
        color=discord.Color.blurple()
    )
    embed.set_thumbnail(url=target_user.display_avatar.url)
    embed.add_field(name="Никнейм", value=target_user.display_name, inline=False)
    embed.add_field(name="На сервере с", value=member.joined_at.strftime("%d.%m.%Y %H:%M:%S"), inline=False)

    # Количество сообщений
    cursor.execute('''
        SELECT message_count FROM user_messages
        WHERE user_id = ? AND guild_id = ?
    ''', (target_user.id, guild.id))
    msg_count = cursor.fetchone()
    embed.add_field(name="Сообщений", value=msg_count[0] if msg_count else 0, inline=True)

    # Время в голосовых
    cursor.execute('''
        SELECT SUM(duration) FROM voice_sessions
        WHERE user_id = ? AND guild_id = ?
    ''', (target_user.id, guild.id))
    total_time = cursor.fetchone()[0] or 0
    embed.add_field(name="В голосовых", value=str(timedelta(seconds=total_time)), inline=True)

    # Топ каналов (ограничение до 5)
    cursor.execute('''
        SELECT channel_id, SUM(duration) as total
        FROM voice_sessions
        WHERE user_id = ? AND guild_id = ?
        GROUP BY channel_id
        ORDER BY total DESC
        LIMIT 5
    ''', (target_user.id, guild.id))
    top_channels = cursor.fetchall()
    
    top_str = ""
    for idx, (channel_id, duration) in enumerate(top_channels, 1):
        channel = guild.get_channel(channel_id)
        name = channel.name if channel else "Удаленный канал"
        top_str += f"{idx}. {name} - {timedelta(seconds=duration)}\n"
    
    embed.add_field(name="Топ каналов", value=top_str if top_str else "Нет данных", inline=False)

    await interaction.response.send_message(embed=embed)            
            
            
bot.run(BOT_TOKEN)
