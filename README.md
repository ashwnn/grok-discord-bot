# Chad - Discord AI Bot

A feature-rich Discord bot powered by Grok AI with a comprehensive web-based admin dashboard.

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

2. **Install dependencies**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Configure environment variables**
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

4. **Run the bot**
   ```bash
   python -m grok_bot.bot
   ```

5. **Run the web dashboard** (in another terminal)
   ```bash
   uvicorn grok_bot.web:app --host 0.0.0.0 --port 8000
   ```

6. **Access the dashboard**
   Open `http://localhost:8000` in your browser

## Docker Deployment

### Using Docker Compose

1. **Build and start services**
   ```bash
   cd docker
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
- Daily image budgets (legacy, kept for history)
- Auto-approve mode
- Admin bypass settings
- Temperature and max tokens

## Project Structure

```
chad/
├── src/
│   └── grok_bot/          # Main package
│       ├── bot.py         # Discord bot with slash commands
│       ├── web.py         # FastAPI web dashboard
│       ├── service.py     # Request processing logic
│       ├── database.py    # SQLite data layer
│       ├── grok_client.py # Grok API client
│       ├── yaml_config.py # YAML configuration manager
│       ├── spam.py        # Input validation
│       ├── rate_limits.py # Rate limiting
│       └── discord_api.py # Discord messaging
├── config/
│   └── config.yaml        # Bot messages and settings
├── templates/             # Web UI templates
├── static/                # CSS and assets
├── docker/                # Docker configuration
│   ├── Dockerfile
│   └── docker-compose.yml
├── docs/                  # Documentation
├── data/                  # SQLite database (created at runtime)
├── requirements.txt       # Python dependencies
└── README.md
```

## Admin Setup

1. **First-time setup**: On first visit to the web UI, you'll be prompted for your Discord User ID
2. **Add yourself as admin**:
   ```bash
   sqlite3 data/chad.sqlite3 "INSERT INTO admin_users (discord_user_id, guild_id) VALUES ('YOUR_DISCORD_ID', 'GUILD_ID');"
   ```
3. **Or use the Web UI**: Once you're an admin, you can add other admins through the Admin Users page

## Database

The bot uses SQLite with the following main tables:
- `guild_config` - Per-guild settings
- `admin_users` - Admin permissions
- `message_log` - Complete message history
- `user_daily_usage` - Per-user daily token tracking
- `guild_daily_usage` - Per-guild daily token tracking

## Features Removed

- Image generation has been removed from the bot (database columns retained for historical data)
- All commands now use Discord slash commands instead of prefix commands (!ask -> /ask)

## Development

### Running Tests
```bash
pytest tests/ -v
```

### Code Style
The project follows PEP 8 guidelines. Format code with:
```bash
black src/
```

## License
