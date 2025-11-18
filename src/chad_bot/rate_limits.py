from dataclasses import dataclass
from typing import Optional

from .database import Database
from .yaml_config import YAMLConfig


@dataclass
class RateLimitRule:
    window_seconds: int
    max_calls: int


@dataclass
class RateLimitResult:
    allowed: bool
    reply: Optional[str] = None


async def check_rate_limit(
    db: Database,
    *,
    guild_id: str,
    user_id: str,
    command_type: str,
    rule: RateLimitRule,
    yaml_config: Optional[YAMLConfig] = None,
) -> RateLimitResult:
    if yaml_config is None:
        yaml_config = YAMLConfig()
    
    recent = await db.count_recent(
        guild_id=guild_id, user_id=user_id, command_type=command_type, window_seconds=rule.window_seconds
    )
    if recent >= rule.max_calls:
        return RateLimitResult(
            allowed=False,
            reply=yaml_config.get_message("rate_limit_chat"),
        )
    return RateLimitResult(allowed=True)
