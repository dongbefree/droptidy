"""Core: take a file from the drop zone, figure out where it belongs, move it.

安全设计：
- `--dry-run` 预览模式：只计算去向，不真正移动文件。
- 每次真正移动都会写入操作日志（data/undo.log），支持 `undo` 一键撤销。
- 移动用 shutil.move（同盘 rename，跨盘 copy+unlink），不做删除。
"""

from __future__ import annotations

import json
import shutil
import time
from pathlib import Path

from . import config
from .rules import get_folder_for


# ---- 操作日志（用于 undo）----


def _undo_log_path() -> Path:
    return Path(__file__).resolve().parent.parent / "data" / "undo.log"


def _append_undo(entry: dict) -> None:
    p = _undo_log_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")


def _read_undo_log() -> list:
    p = _undo_log_path()
    if not p.exists():
        return []
    entries = []
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            entries.append(json.loads(line))
        except Exception:
            continue
    return entries


# ---- 冲突处理 ----


def _resolve_conflict(dest: Path, strategy: str) -> Path | None:
    """如果目标路径已有同名文件，根据策略决定最终路径。"""
    if not dest.exists():
        return dest

    if strategy == "overwrite":
        return dest

    if strategy == "skip":
        return None

    # rename: 加 (1) (2) (3) ...
    stem = dest.stem
    suffix = dest.suffix
    parent = dest.parent
    counter = 1
    while True:
        candidate = parent / f"{stem} ({counter}){suffix}"
        if not candidate.exists():
            return candidate
        counter += 1


# ---- 单个文件处理 ----


def plan_file(file_path: Path, dry_run: bool = True) -> dict:
    """计算一个文件的去向（不移动）。

    返回 dict：
      status: "planned" / "skipped"
      file: 原文件名
      src: 源绝对路径
      dest: 目标绝对路径（如果可移动）
      label: 分类标签
      reason: 跳过原因（如果 skipped）
    """
    cfg = config.load()
    rules = config.get_effective_rules()

    ext = file_path.suffix.lstrip(".")
    dest_folder, label = get_folder_for(ext, rules)

    # 如果是 fallback（没匹配到规则），用配置里的 fallback_folder
    if ext.lower() not in rules:
        dest_folder = Path(cfg.get("fallback_folder", "~/Documents/其他")).expanduser()

    dest = dest_folder / file_path.name
    strategy = cfg.get("on_duplicate", "rename")
    final_dest = _resolve_conflict(dest, strategy)

    if final_dest is None:
        return {
            "status": "skipped",
            "file": file_path.name,
            "src": str(file_path),
            "dest": None,
            "label": label,
            "reason": "目标已有同名文件，策略为 skip",
        }

    return {
        "status": "planned",
        "file": file_path.name,
        "src": str(file_path),
        "dest": str(final_dest),
        "label": label,
    }


def execute_plan(plan: dict) -> dict:
    """执行一个 plan_file 的结果（真正移动）。"""
    if plan["status"] != "planned":
        return {
            "status": "skipped",
            "file": plan["file"],
            "dest": None,
            "label": plan["label"],
        }

    src = Path(plan["src"])
    dest = Path(plan["dest"])

    if not src.exists():
        return {
            "status": "error",
            "file": plan["file"],
            "dest": None,
            "label": plan["label"],
            "error": "源文件不存在",
        }

    dest.parent.mkdir(parents=True, exist_ok=True)

    try:
        shutil.move(str(src), str(dest))
        _append_undo({
            "ts": time.time(),
            "src": str(dest),   # 移动后，文件现在在 dest
            "original": str(src),
        })
        return {
            "status": "moved",
            "file": plan["file"],
            "dest": str(dest),
            "label": plan["label"],
        }
    except Exception as e:
        return {
            "status": "error",
            "file": plan["file"],
            "dest": None,
            "label": plan["label"],
            "error": str(e),
        }


def organize_file(file_path: Path) -> dict:
    """处理一个文件：plan + execute（等价于原来的 organize_file）。

    返回 dict：
      status: "moved" / "skipped" / "error"
      file / dest / label / error
    """
    plan = plan_file(file_path)
    return execute_plan(plan)


def scan_drop_zone(dry_run: bool = False) -> list:
    """扫描投递区文件夹。

    dry_run=True 时只返回计划（不移动）；否则执行移动。
    """
    cfg = config.load()
    drop_zone = Path(cfg["drop_zone"]).expanduser()

    if not drop_zone.exists():
        return []

    results = []
    for item in sorted(drop_zone.iterdir()):
        # 跳过隐藏文件和文件夹
        if item.name.startswith("."):
            continue
        if item.is_dir():
            # 文件夹暂时不处理，跳过
            continue
        if dry_run:
            results.append(plan_file(item))
        else:
            results.append(organize_file(item))

    return results


# ---- undo ----


def undo_last() -> list:
    """撤销日志里的全部移动操作（后进先出），返回撤销结果列表。"""
    entries = _read_undo_log()
    undone = []
    for entry in reversed(entries):
        src = Path(entry.get("src", ""))
        original = Path(entry.get("original", ""))
        try:
            if src.exists() and not original.exists():
                original.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(src), str(original))
                undone.append({"file": src.name, "restored_to": str(original)})
            else:
                undone.append({
                    "file": src.name,
                    "restored_to": str(original),
                    "skipped": True,
                })
        except Exception as e:
            undone.append({"file": src.name, "error": str(e)})

    # 清空日志（已处理）
    p = _undo_log_path()
    if p.exists():
        p.write_text("", encoding="utf-8")
    return undone
