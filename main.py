import discord
from discord.ext import commands
from discord.ui import View, Modal, TextInput

# Токен вашего бота
BOT_TOKEN = 'ТОКЕН'

# ID отслеживаемого голосового канала
WATCHED_CHANNEL_ID = Какнал в который нужно зайти для создания

intents = discord.Intents.default()
intents.guilds = True
intents.voice_states = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Словарь для отслеживания созданных каналов
created_channels = {}


class EditChannelModal(Modal):
    def __init__(self, channel):
        self.channel = channel
        super().__init__(title="Изменение канала")

        # Поля модального окна
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


bot.run(BOT_TOKEN)
