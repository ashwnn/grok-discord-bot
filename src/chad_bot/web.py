import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Any, Dict, Optional

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

from .config import Settings
from .database import GuildConfig, Database
from .discord_api import DiscordApiClient
from .grok_client import GrokClient
from .service import RequestProcessor
from .yaml_config import YAMLConfig

logger = logging.getLogger(__name__)


class ConfigUpdate(BaseModel):
    auto_approve_enabled: Optional[bool] = None
    admin_bypass_auto_approve: Optional[bool] = None
    ask_window_seconds: Optional[int] = Field(None, ge=1)
    ask_max_per_window: Optional[int] = Field(None, ge=1)
    image_window_seconds: Optional[int] = Field(None, ge=1)
    image_max_per_window: Optional[int] = Field(None, ge=1)
    duplicate_window_seconds: Optional[int] = Field(None, ge=1)
    user_daily_chat_token_limit: Optional[int] = Field(None, ge=0)
    global_daily_chat_token_limit: Optional[int] = Field(None, ge=0)
    user_daily_image_limit: Optional[int] = Field(None, ge=0)
    global_daily_image_limit: Optional[int] = Field(None, ge=0)
    system_prompt: Optional[str] = None
    temperature: Optional[float] = None
    max_completion_tokens: Optional[int] = None
    max_prompt_chars: Optional[int] = None


class ApprovalDecision(BaseModel):
    decision: str
    manual_reply_content: Optional[str] = None
    reason: Optional[str] = None


def create_app(settings: Settings) -> FastAPI:
    db = Database(settings.database_path)
    grok = GrokClient(
        api_key=settings.grok_api_key,
        api_base=settings.grok_api_base,
        chat_model=settings.grok_chat_model,
        image_model=settings.grok_image_model,
    )
    discord_api = DiscordApiClient(settings.discord_token)
    yaml_config = YAMLConfig()
    processor = RequestProcessor(db=db, grok=grok, settings=settings, yaml_config=yaml_config)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # Startup
        await db.connect()
        await db.create_schema()
        logger.info("Web backend connected to %s", settings.database_path)
        yield
        # Shutdown
        await db.close()

    app = FastAPI(title="Chad Bot Admin", lifespan=lifespan)

    templates = Jinja2Templates(directory="templates")
    app.mount("/static", StaticFiles(directory="static"), name="static")

    async def require_admin(request: Request) -> str:
        """
        Extract and validate admin credentials from request.
        Returns the admin user ID if valid, raises HTTPException otherwise.
        """
        user_id = request.headers.get("X-Discord-User-ID")
        if not user_id:
            raise HTTPException(status_code=401, detail="Missing X-Discord-User-ID header")
        
        # Try to get guild_id from various sources
        guild_id = None
        
        # 1. Try path params (for routes like /guilds/{guild_id}/...)
        if hasattr(request, "path_params") and "guild_id" in request.path_params:
            guild_id = request.path_params["guild_id"]
        
        # 2. Try query params
        if not guild_id and request.query_params.get("guild_id"):
            guild_id = request.query_params.get("guild_id")
        
        # 3. For approval endpoints, look up message and get guild_id from it
        if not guild_id and "message_id" in request.path_params:
            try:
                message = await db.get_message(int(request.path_params["message_id"]))
                guild_id = message["guild_id"] if message else None
            except (ValueError, TypeError):
                pass
        
        if not guild_id:
            raise HTTPException(status_code=400, detail="Could not determine guild_id from request")
        
        # Verify admin status
        if not await db.is_admin(user_id, guild_id):
            raise HTTPException(status_code=403, detail="Not an admin for this guild")
        
        return user_id

    @app.get("/", response_class=HTMLResponse)
    async def index(request: Request):
        guilds = await db.list_guilds()
        return templates.TemplateResponse(
            "index.html",
            {"request": request, "guilds": guilds},
        )

    @app.get("/guilds/{guild_id}", response_class=HTMLResponse)
    async def overview(request: Request, guild_id: str):
        config = await db.get_guild_config(guild_id)
        pending = await db.pending_messages(guild_id)
        recent = await db.recent_messages(guild_id)
        usage = await db.get_usage(guild_id)
        analytics = await db.analytics(guild_id)
        return templates.TemplateResponse(
            "overview.html",
            {
                "request": request,
                "page": "dashboard",
                "guild_id": guild_id,
                "config": config,
                "pending": pending,
                "recent": recent,
                "usage": usage,
                "analytics": analytics,
                "model_pricing": {"prompt": processor.prompt_price_per_m_token, "completion": processor.completion_price_per_m_token, "model": settings.grok_chat_model},
            },
        )

    @app.get("/guilds/{guild_id}/config", response_class=HTMLResponse)
    async def config_page(request: Request, guild_id: str):
        config = await db.get_guild_config(guild_id)
        return templates.TemplateResponse(
            "config.html",
            {
                "request": request,
                "page": "config",
                "guild_id": guild_id,
                "config": config,
            },
        )

    @app.get("/guilds/{guild_id}/queue", response_class=HTMLResponse)
    async def queue_page(request: Request, guild_id: str):
        pending = await db.pending_messages(guild_id)
        return templates.TemplateResponse(
            "queue.html",
            {
                "request": request,
                "page": "queue",
                "guild_id": guild_id,
                "pending": pending,
            },
        )

    @app.get("/guilds/{guild_id}/history", response_class=HTMLResponse)
    async def history_page(
        request: Request,
        guild_id: str,
        limit: int = 100,
        status: Optional[str] = None,
        command_type: Optional[str] = None,
    ):
        history = await db.history(guild_id, limit=limit, status=status, command_type=command_type)
        return templates.TemplateResponse(
            "history.html",
            {
                "request": request,
                "page": "history",
                "guild_id": guild_id,
                "history": history,
                "status_filter": status,
                "command_type_filter": command_type,
                "model_pricing": {"prompt": processor.prompt_price_per_m_token, "completion": processor.completion_price_per_m_token, "model": settings.grok_chat_model},
            },
        )

    @app.get("/guilds/{guild_id}/analytics", response_class=HTMLResponse)
    async def analytics_page(request: Request, guild_id: str):
        analytics = await db.analytics(guild_id)
        recent_messages = await db.recent_messages(guild_id, limit=100)
        return templates.TemplateResponse(
            "analytics.html",
            {
                "request": request,
                "page": "analytics",
                "guild_id": guild_id,
                "analytics": analytics,
                "recent": recent_messages,
                "model_pricing": {"prompt": processor.prompt_price_per_m_token, "completion": processor.completion_price_per_m_token, "model": settings.grok_chat_model},
            },
        )

    @app.get("/guilds/{guild_id}/admins", response_class=HTMLResponse)
    async def admins_page(request: Request, guild_id: str):
        return templates.TemplateResponse(
            "admins.html",
            {
                "request": request,
                "page": "admins",
                "guild_id": guild_id,
            },
        )

    @app.get("/messages", response_class=HTMLResponse)
    async def messages_page(request: Request):
        return templates.TemplateResponse(
            "messages.html",
            {
                "request": request,
                "page": "messages",
            },
        )

    @app.get("/api/guilds/{guild_id}/config")
    async def get_config(guild_id: str, user: str = Depends(require_admin)):
        config = await db.get_guild_config(guild_id)
        return config.__dict__

    @app.post("/api/guilds/{guild_id}/config")
    async def update_config(guild_id: str, payload: ConfigUpdate, user: str = Depends(require_admin)):
        current = await db.get_guild_config(guild_id)
        update_data = current.__dict__
        for key, value in payload.model_dump(exclude_none=True).items():
            update_data[key] = value
        updated = await db.upsert_guild_config(GuildConfig(**update_data))
        return updated.__dict__

    @app.get("/api/guilds/{guild_id}/pending")
    async def list_pending(guild_id: str, user: str = Depends(require_admin)):
        return await db.pending_messages(guild_id)

    @app.get("/api/guilds/{guild_id}/history")
    async def list_history(
        guild_id: str,
        limit: int = 50,
        status: Optional[str] = None,
        command_type: Optional[str] = None,
        user: str = Depends(require_admin),
    ):
        return await db.history(guild_id, limit=limit, status=status, command_type=command_type)

    @app.get("/api/guilds/{guild_id}/analytics")
    async def get_analytics(guild_id: str, user: str = Depends(require_admin)):
        return await db.analytics(guild_id)

    @app.get("/api/guilds/{guild_id}/admins")
    async def list_admins(guild_id: str, user: str = Depends(require_admin)):
        # For now return empty list - could expand to show actual admin users from db
        async with db.conn.execute(
            "SELECT discord_user_id, role, created_at FROM admin_users WHERE guild_id = ? ORDER BY created_at",
            (guild_id,),
        ) as cur:
            rows = await cur.fetchall()
            return [dict(r) for r in rows]

    class AdminUserCreate(BaseModel):
        discord_user_id: str

    @app.post("/api/guilds/{guild_id}/admins")
    async def add_admin_user(guild_id: str, payload: AdminUserCreate, user: str = Depends(require_admin)):
        await db.add_admin(payload.discord_user_id, guild_id, role="admin")
        return {"status": "added", "discord_user_id": payload.discord_user_id}

    @app.delete("/api/guilds/{guild_id}/admins/{admin_user_id}")
    async def remove_admin_user(guild_id: str, admin_user_id: str, user: str = Depends(require_admin)):
        async with db._lock:
            await db.conn.execute(
                "DELETE FROM admin_users WHERE discord_user_id = ? AND guild_id = ?",
                (admin_user_id, guild_id),
            )
            await db.conn.commit()
        return {"status": "removed"}

    # YAML Configuration endpoints
    @app.get("/api/yaml-config")
    async def get_yaml_config():
        """Get all YAML configuration values."""
        return yaml_config.get_all()

    class YAMLConfigUpdate(BaseModel):
        updates: Dict[str, Any]

    @app.post("/api/yaml-config")
    async def update_yaml_config(payload: YAMLConfigUpdate):
        """Update YAML configuration values."""
        yaml_config.update(payload.updates)
        return {"status": "updated", "config": yaml_config.get_all()}

    @app.get("/api/yaml-config/messages")
    async def get_yaml_messages():
        """Get all bot messages from YAML config."""
        return yaml_config.get("messages", {})

    @app.get("/api/yaml-config/system-prompt")
    async def get_yaml_system_prompt():
        """Get system prompt from YAML config."""
        return {"system_prompt": yaml_config.get_system_prompt()}

    @app.get("/api/yaml-config/bot-settings")
    async def get_yaml_bot_settings():
        """Get bot settings (prefix/suffix) from YAML config."""
        return yaml_config.get("bot_settings", {})

    async def _send_discord_message(channel_id: str, content: str, mention_id: Optional[str] = None, image_url: Optional[str] = None):
        try:
            await discord_api.send_message(channel_id=channel_id, content=content, mention_user_id=mention_id, embed_url=image_url)
        except Exception as exc:  # noqa: BLE001
            logger.exception("Could not send Discord message: %s", exc)

    async def _process_grok(message: Dict[str, Any], admin_id: str) -> Dict[str, Any]:
        cfg = await db.get_guild_config(message["guild_id"])
        if message["command_type"] == "ask":
            try:
                result = await grok.chat(
                    system_prompt=yaml_config.get_system_prompt() or cfg.system_prompt,
                    user_content=message["user_content"],
                    temperature=cfg.temperature,
                    max_tokens=cfg.max_completion_tokens,
                )
            except Exception as exc:  # noqa: BLE001
                await db.update_message_status(
                    message["id"],
                    status="error",
                    decision="grok",
                    error_code="grok_error",
                    error_detail=str(exc),
                )
                raise HTTPException(status_code=502, detail="Grok call failed")
            usage = result.usage or {}
            total_tokens = usage.get("total_tokens", 0) or 0
            prompt_tokens = usage.get("prompt_tokens", 0) or 0
            completion_tokens = usage.get("completion_tokens", 0) or 0
            if total_tokens:
                await db.increment_daily_chat_usage(message["guild_id"], message["user_id"], total_tokens)
            
            # Format reply with prefix/suffix
            formatted_content = yaml_config.format_reply(result.content)
            
            await db.update_message_status(
                message["id"],
                status="approved_grok",
                decision="grok",
                grok_response_content=result.content,
                prompt_tokens=usage.get("prompt_tokens"),
                completion_tokens=usage.get("completion_tokens"),
                total_tokens=usage.get("total_tokens"),
                estimated_cost_usd=(prompt_tokens / 1_000_000.0 * processor.prompt_price_per_m_token + completion_tokens / 1_000_000.0 * processor.completion_price_per_m_token) if (prompt_tokens or completion_tokens) else None,
                approved_by_admin_id=admin_id,
            )
            await _send_discord_message(
                channel_id=message["channel_id"],
                content=formatted_content,
                mention_id=message["user_id"],
            )
            return {"status": "approved_grok", "reply": formatted_content}
        
        # Image generation has been removed
        raise HTTPException(status_code=400, detail="Unknown or unsupported command type")

    @app.post("/api/approvals/{message_id}")
    async def approve(message_id: int, payload: ApprovalDecision, admin_id: str = Depends(require_admin)):
        message = await db.get_message(message_id)
        if not message:
            raise HTTPException(status_code=404, detail="Message not found")
        if message["status"] != "pending_approval":
            raise HTTPException(status_code=400, detail="Message not pending")
        if payload.decision == "grok":
            return await _process_grok(message, admin_id)
        if payload.decision == "manual":
            manual_text = payload.manual_reply_content or yaml_config.get_message("manual_reply_default")
            formatted_manual = yaml_config.format_reply(manual_text)
            await db.update_message_status(
                message_id,
                status="approved_manual",
                decision="manual",
                manual_reply_content=manual_text,
                approved_by_admin_id=admin_id,
            )
            await _send_discord_message(
                channel_id=message["channel_id"],
                content=formatted_manual,
                mention_id=message["user_id"],
            )
            return {"status": "approved_manual", "reply": formatted_manual}
        if payload.decision == "reject":
            reply_text = payload.reason or yaml_config.get_message("rejection_default")
            formatted_rejection = yaml_config.format_reply(reply_text)
            await db.update_message_status(
                message_id,
                status="rejected",
                decision="reject",
                approved_by_admin_id=admin_id,
                error_detail=payload.reason,
            )
            await _send_discord_message(
                channel_id=message["channel_id"],
                content=formatted_rejection,
                mention_id=message["user_id"],
            )
            return {"status": "rejected", "reply": formatted_rejection}
        raise HTTPException(status_code=400, detail="Invalid decision")

    @app.get("/health")
    async def health():
        return {"ok": True}

    return app


app = create_app(Settings())


def run() -> None:
    import uvicorn

    logging.basicConfig(level=logging.INFO)
    settings = Settings()
    uvicorn.run("chad_bot.web:app", host=settings.web_host, port=settings.web_port, reload=False)


if __name__ == "__main__":
    run()
