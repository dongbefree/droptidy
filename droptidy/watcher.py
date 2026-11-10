"""Background watcher: polls the drop zone folder every few seconds."""

from __future__ import annotations

import time
from pathlib import Path

from . import config, organizer


def ensure_drop_zone() -> Path:
    """确保投递区文件夹存在，返回路径。"""
    cfg = config.load()
    drop_zone = Path(cfg["drop_zone"]).expanduser()
    drop_zone.mkdir(parents=True, exist_ok=True)
    return drop_zone


def run(interval: int = 3) -> None:
    """持续监控投递区，有新文件就自动归类。

    interval: 每隔几秒检查一次，默认 3 秒。
    """
    drop_zone = ensure_drop_zone()
    print(f"📥 DropTidy 已启动")
    print(f"   投递区：{drop_zone}")
    print(f"   每隔 {interval} 秒检查一次")
    print(f"   按 Ctrl+C 退出")
    print()

    # 启动时先处理一次已有文件
    results = organizer.scan_drop_zone()
    for r in results:
        _print_result(r)

    # 持续监控
    seen = set()
    while True:
        try:
            cfg = config.load()
            drop_zone = Path(cfg["drop_zone"]).expanduser()

            if not drop_zone.exists():
                time.sleep(interval)
                continue

            current = set()
            for item in drop_zone.iterdir():
                if item.name.startswith("."):
                    continue
                if item.is_dir():
                    continue
                current.add(item.name)

            # 找出新出现的文件
            new_files = current - seen
            if new_files:
                # 等一下，确保文件复制完了（大文件需要时间）
                time.sleep(0.5)
                results = organizer.scan_drop_zone()
                for r in results:
                    _print_result(r)
                seen = set()
            else:
                seen = current

        except KeyboardInterrupt:
            print("\n👋 已停止")
            break
        except Exception as e:
            print(f"⚠️ 出错了：{e}")

        time.sleep(interval)


def _print_result(r: dict) -> None:
    """打印一条处理结果。"""
    if r["status"] in ("moved", "planned"):
        marker = "→" if r["status"] == "moved" else "☞"
        print(f"  {'✓' if r['status'] == 'moved' else '⊡'} [{r['label']}] {r['file']}  {marker}  {r['dest']}")
    elif r["status"] == "skipped":
        print(f"  ⊙ 跳过：{r['file']}（{r.get('reason', '同名文件已存在')}）")
    elif r["status"] == "error":
        print(f"  ✗ 失败：{r['file']} — {r.get('error', '未知错误')}")
