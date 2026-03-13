"""
User-Agent 配置工具
提供全局默认 User-Agent 的读取和获取逻辑。
"""

from __future__ import annotations

import os
from typing import Optional

try:
    import tomllib  # type: ignore
except ImportError:  # pragma: no cover - 兼容 Python <3.11 环境
    try:  # pragma: no cover
        import tomli as tomllib  # type: ignore
    except ImportError:  # pragma: no cover
        tomllib = None

CONFIG_PATHS = [
    "config.toml",
    "../config.toml",
    "../../config.toml",
]


def _load_config_silent() -> Optional[dict]:
    """静默加载配置文件（如果存在）。"""
    if tomllib is None:
        return None

    for path in CONFIG_PATHS:
        if os.path.exists(path):
            try:
                with open(path, "rb") as f:
                    return tomllib.load(f)
            except Exception:
                return None
    return None


def get_configured_user_agent(config: Optional[dict] = None) -> Optional[str]:
    """获取配置或环境变量指定的全局 User-Agent。

    优先级：环境变量 USER_AGENT / ZSXQ_USER_AGENT > 配置文件 network.user_agent >
    顶层 user_agent。
    """

    env_ua = os.environ.get("USER_AGENT") or os.environ.get("ZSXQ_USER_AGENT")
    if env_ua and env_ua.strip():
        return env_ua.strip()

    cfg = config if config is not None else _load_config_silent()
    if not isinstance(cfg, dict):
        return None

    network_cfg = cfg.get("network") if isinstance(cfg.get("network"), dict) else None
    if network_cfg:
        ua = network_cfg.get("user_agent")
        if isinstance(ua, str) and ua.strip():
            return ua.strip()

    ua = cfg.get("user_agent")
    if isinstance(ua, str) and ua.strip():
        return ua.strip()

    return None
