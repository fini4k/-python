
# Discord Voice Channel Manager Bot

Бот для автоматического создания голосовых каналов и отслеживания активности пользователей на сервере Discord.

## 📋 Особенности
- **Динамическое создание голосовых каналов**  
  При входе пользователя в указанный канал автоматически создаётся персональный голосовой канал.
- **Управление каналами**  
  Создатель канала может изменить его название и лимит участников через интерактивное меню.
- **Статистика активности**  
  Отслеживание:
  - Времени, проведённого в голосовых каналах.
  - Количества отправленных сообщений.
- **Команда `/stats`**  
  Показывает детальную статистику для любого пользователя.

## 🛠 Установка и настройка

### 1. Клонирование репозитория
git clone https://github.com/fini4k/-python


### 2. Установка зависимостей
```bash
pip install -r requirements.txt
```

### 3. Настройка конфигурации
1. Создайте файл `.env` и укажите:
```ini
BOT_TOKEN=ваш_токен_бота
WATCHED_CHANNEL_ID=ID_отслеживаемого_канала
```

2. Получите токен бота на [Discord Developer Portal](https://discord.com/developers/applications).

3. Укажите ID канала, при входе в который будут создаваться новые каналы.

## 🚀 Использование

### Добавление бота на сервер
1. Сгенерируйте OAuth2-ссылку с правами:
   - `applications.commands`
   - `Send Messages`
   - `Manage Channels`
   - `Connect to Voice`

2. Перейдите по ссылке, чтобы добавить бота на сервер.

### Основные функции
1. **Создание каналов**  
   При входе в отслеживаемый канал:
   - Создаётся новый голосовой канал.
   - Пользователь перемещается в него автоматически.
   - Появляется текстовый канал с кнопкой управления.

2. **Команда `/stats`**  
   Примеры:
   - `/stats` — ваша статистика.
   - `/stats пользователь: @username` — статистика другого участника.

## ⚙ Настройка прав
Убедитесь, что у бота включены следующие **интенты**:
- `SERVER MEMBERS INTENT`
- `MESSAGE CONTENT INTENT`
- `PRESENCE INTENT` (опционально)

![Intents Settings](https://i.imgur.com/abc123.png)

## 🗃 База данных
Данные хранятся в SQLite-файле `bot_database.db`:
- `voice_sessions` — сессии в голосовых каналах.
- `user_messages` — статистика сообщений.

## 🔧 Возможные проблемы
- **Ошибки прав**: Убедитесь, что бот имеет права `Manage Channels` и `Move Members`.
- **Не работают слеш-команды**: Выполните синхронизацию:
  ```python
  @bot.event
  async def on_ready():
      await bot.tree.sync()
  ```

---

🤖 **Автор**: FINIK
Telegram: @ws_fi
Discord: fini4k
Support server: https://discord.gg/BugVHqjmAd
