"""User config: drop zone location, custom rules, etc."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from .rules import DEFAULT_RULES, FALLBACK_FOLDER

DEFAULTS: Dict[str, Any] = {
    # 投递区文件夹位置（桌面）
    "drop_zone": "~/Desktop/📥 投递区",
    # 找不到规则时放哪里
    "fallback_folder": FALLBACK_FOLDER,
    # 自定义规则（覆盖默认规则）
    "custom_rules": {},
    # 移动文件时如果目标已有同名文件，怎么处理：
    #   rename → 自动重命名（加 (1) (2)）
    #   overwrite → 覆盖
    #   skip → 跳过
    "on_duplicate": "rename",
}


def _config_dir() -> Path:
    """配置文件放在项目目录下的 data/ 文件夹里。"""
    p = Path(__file__).resolve().parent.parent / "data"
    p.mkdir(parents=True, exist_ok=True)
    return p


def _config_path() -> Path:
    return _config_dir() / "config.json"


def load() -> Dict[str, Any]:
    """Load config, merging with defaults."""
    cfg = dict(DEFAULTS)
    path = _config_path()
    if path.exists():
        try:
            user = json.loads(path.read_text(encoding="utf-8"))
            cfg.update(user)
        except Exception:
            pass
    return cfg


def save(cfg: Dict[str, Any]) -> None:
    path = _config_path()
    path.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")


def get(key: str) -> Any:
    return load().get(key, DEFAULTS.get(key))


def set_key(key: str, value: str) -> None:
    cfg = load()
    # Try to parse as bool/int, else keep as string
    if value.lower() in ("true", "yes", "on"):
        cfg[key] = True
    elif value.lower() in ("false", "no", "off"):
        cfg[key] = False
    else:
        try:
            cfg[key] = int(value)
        except ValueError:
            cfg[key] = value
    save(cfg)


def get_effective_rules() -> dict:
    """合并默认规则 + 用户自定义规则，返回最终规则表。"""
    cfg = load()
    rules = dict(DEFAULT_RULES)
    custom = cfg.get("custom_rules", {})
    for ext, rule in custom.items():
        rules[ext.lower()] = rule
    return rules
