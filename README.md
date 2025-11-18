# Chad - Discord AI Bot

A feature-rich Discord bot powered by Grok AI with a comprehensive web-based admin dashboard. Designed to be offensive.

## Features

### Bot Capabilities
- **Slash Commands**: Uses Discord's native `/ask` command for seamless integration
- **Smart Validation**: Filters spam, gibberish, duplicates, and trivial inputs
- **Rate Limiting**: Configurable per-user and per-guild rate limits
- **Daily Budgets**: Token-based budget management to control API costs
- **Auto-Approve Workflow**: Optional admin approval queue for all requests
- **Customizable Personality**: Fully editable system prompt and bot responses

### Admin Dashboard
- **Configuration Management**: Edit all bot settings through an intuitive web UI
- **Message Customization**: Configure all bot messages, errors, and responses via YAML
- **Approval Queue**: Review and approve/reject pending requests
- **History & Analytics**: Track usage, costs, and message history
- **Admin Management**: Manage admin users per guild
- **No Authentication Required**: Internal tool for trusted environments

## Quick Start

### Prerequisites
- Python 3.10 or higher
- Discord Bot Token
- Grok API Key (optional, will use stubbed responses if not provided)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/chad.git
   cd chad
   ```

2. **Configure Discord Bot Intents**
   - Go to https://discord.com/developers/applications/
   - Select your application
   - Go to "Bot" section
   - Under "Privileged Gateway Intents", enable:
     - ✅ **Message Content Intent** (required for message validation)
   - Save changes

3. **Install dependencies**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   Create a `.env` file in the project root:
   ```env
   DISCORD_BOT_TOKEN=your_discord_bot_token_here
   GROK_API_KEY=your_grok_api_key_here
   GROK_API_BASE=https://api.x.ai/v1
   GROK_CHAT_MODEL=grok-beta
   DATABASE_PATH=data/chad.sqlite3
   WEB_HOST=0.0.0.0
   WEB_PORT=8000
   ```

5. **Run the bot**
   ```bash
   python -m chad_bot.bot
   ```

6. **Run the web dashboard** (in another terminal)
   ```bash
   python -m chad_bot.web
   ```

7. **Access the dashboard**
   Open `http://localhost:8000` in your browser

## Docker Deployment

### Using Docker Compose

1. **Build and start services**
   ```bash
   docker-compose up --build
   ```

2. **Access the dashboard**
   - Web UI: `http://localhost:8000`
   - The bot will automatically connect to Discord

### Environment Variables

All configuration is done through environment variables (in `.env` file):

| Variable | Description | Default |
|----------|-------------|---------|
| `DISCORD_BOT_TOKEN` | Discord bot token (required) | - |
| `GROK_API_KEY` | Grok API key (optional) | - |
| `GROK_API_BASE` | Grok API base URL | `https://api.x.ai/v1` |
| `GROK_CHAT_MODEL` | Chat model name | `grok-beta` |
| `DATABASE_PATH` | SQLite database path | `data/chad.sqlite3` |
| `WEB_HOST` | Web server host | `0.0.0.0` |
| `WEB_PORT` | Web server port | `8000` |
| `MAX_PROMPT_CHARS` | Maximum prompt length | `4000` |

## Configuration

### Bot Messages & Personality

All bot messages, error responses, and the system prompt can be configured through:
1. The `config/config.yaml` file
2. The Web UI at `http://localhost:8000/messages`

This includes:
- System prompt (AI personality)
- Reply prefix and suffix
- Error messages
- Rate limit messages
- Budget exhaustion messages
- Validation messages

### Guild Settings

Per-guild configuration is available through the web dashboard:
- Rate limits (requests per time window)
- Daily token budgets
- Auto-approve mode
- Admin bypass settings
- Temperature and max tokens

## Project Structure

```
chad/
├── src/
│   └── chad_bot/          # Main package
│       ├── bot.py         # Discord bot with slash commands
│       ├── web.py         # FastAPI web dashboard
│       ├── service.py     # Request processing logic
│       ├── database.py    # SQLite data layer
│       ├── grok_client.py # Grok API client
│       ├── yaml_config.py # YAML configuration manager
│       ├── spam.py        # Input validation
│       ├── rate_limits.py # Rate limiting
│       ├── config.py      # Settings management
│       └── discord_api.py # Discord messaging
├── config/
│   └── config.yaml        # Bot messages and settings
├── templates/             # Web UI templates
├── static/                # CSS and assets
├── Dockerfile             # Docker configuration
├── docker-compose.yml     # Docker Compose setup
├── docs/                  # Documentation
├── data/                  # SQLite database (created at runtime)
├── requirements.txt       # Python dependencies
└── README.md
```

## Database

The bot uses SQLite with the following main tables:
- `guild_config` - Per-guild settings
- `admin_users` - Admin permissions
- `message_log` - Complete message history
- `user_daily_usage` - Per-user daily token tracking
- `guild_daily_usage` - Per-guild daily token tracking

## License
Licensed under [CC BY-NC-SA 4.0](http://creativecommons.org/licenses/by-nc-sa/4.0/), Attribution-NonCommercial-ShareAlike 4.0 International.

You are free to:

* Share: copy and redistribute the material
* Adapt: remix, transform, and build upon the material

Under the following terms:

* Attribution: you must give appropriate credit.
* NonCommercial: you may not use the material for commercial purposes.
* ShareAlike: if you remix or adapt, you must distribute your contributions under the same license.
