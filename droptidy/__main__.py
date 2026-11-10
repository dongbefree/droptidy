"""DropTidy CLI — `python -m droptidy <command>`."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from . import config, organizer, watcher
from .templates import TEMPLATES


def main() -> None:
    args = sys.argv[1:]
    if not args:
        print("📥 DropTidy — 把文件丢进去，自动归好类")
        print()
        print("Usage:")
        print("  python -m droptidy setup         首次配置（选模板 + 自定义）")
        print("  python -m droptidy start         启动后台监控（一直运行）")
        print("  python -m droptidy run           手动跑一次整理（处理完就退出）")
        print("  python -m droptidy dry-run       预览会怎么整理，不真正移动")
        print("  python -m droptidy undo          撤销上一次整理")
        print("  python -m droptidy init          在桌面创建投递区文件夹")
        print("  python -m droptidy load-config <文件>   从配置文件加载规则")
        print("  python -m droptidy config        查看当前设置")
        print("  python -m droptidy config <key> <value>   改设置")
        print("  python -m droptidy rules         查看当前分类规则")
        return

    cmd, rest = args[0], args[1:]

    if cmd == "setup":
        _setup()

    elif cmd == "start":
        watcher.run()

    elif cmd == "run":
        results = organizer.scan_drop_zone()
        if not results:
            print("投递区是空的，没什么要整理的。")
        for r in results:
            _print_result(r)

    elif cmd == "dry-run":
        results = organizer.scan_drop_zone(dry_run=True)
        if not results:
            print("投递区是空的，没什么要整理的。")
        for r in results:
            _print_result(r)
        print("\n（以上只是预览，没有移动任何文件。确认无误后跑 `run`。）")

    elif cmd == "undo":
        undone = organizer.undo_last()
        if not undone:
            print("没有可撤销的操作。")
        for u in undone:
            if u.get("error"):
                print(f"  ✗ {u['file']} — {u['error']}")
            elif u.get("skipped"):
                print(f"  ⊙ 跳过：{u['file']}（目标位置已有文件，未覆盖）")
            else:
                print(f"  ↩ {u['file']}  →  {u['restored_to']}")

    elif cmd == "init":
        path = watcher.ensure_drop_zone()
        print(f"✓ 投递区已创建：{path}")
        print("  以后把文件丢进这个文件夹，就会自动归类。")

    elif cmd == "load-config":
        if not rest:
            print("Usage: droptidy load-config <配置文件路径>")
            sys.exit(1)
        _load_config(rest[0])

    elif cmd == "config":
        if len(rest) == 0:
            cfg = config.load()
            print("当前设置：")
            for k, v in cfg.items():
                print(f"  {k} = {v}")
        elif len(rest) == 2:
            key, value = rest
            config.set_key(key, value)
            print(f"✓ {key} = {value}")
        else:
            print("Usage: droptidy config [key] [value]")

    elif cmd == "rules":
        rules = config.get_effective_rules()
        print("当前分类规则：")
        for ext, rule in sorted(rules.items()):
            print(f"  .{ext:6s}  →  {rule['folder']}  ({rule['label']})")
        print(f"\n  其他    →  {config.get('fallback_folder')}  (其他)")

    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)


def _print_result(r: dict) -> None:
    if r["status"] == "moved":
        print(f"  ✓ [{r['label']}] {r['file']}  →  {r['dest']}")
    elif r["status"] == "planned":
        print(f"  ⊡ [{r['label']}] {r['file']}  →  {r['dest']}")
    elif r["status"] == "skipped":
        print(f"  ⊙ 跳过：{r['file']}（{r.get('reason', '同名文件已存在')}）")
    elif r["status"] == "error":
        print(f"  ✗ 失败：{r['file']} — {r.get('error', '未知错误')}")


def _load_config(path_str: str) -> None:
    """从 JSON 配置文件加载自定义规则（`custom_rules` 或 `rules` 字段）。"""
    p = Path(path_str).expanduser()
    if not p.exists():
        print(f"✗ 找不到配置文件：{p}")
        sys.exit(1)
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"✗ 配置文件不是合法 JSON：{e}")
        sys.exit(1)

    # 兼容两种字段名：custom_rules 或 rules
    rules = data.get("custom_rules") or data.get("rules")
    if not isinstance(rules, dict) or not rules:
        print("✗ 配置文件里没有找到 rules / custom_rules 字段。")
        print("  格式示例：")
        print('  { "custom_rules": { "pdf": "~/Downloads/论文", "png": "~/Pictures/截图" } }')
        sys.exit(1)

    # 规范化：值可以是字符串（只给路径）或 {folder, label} 对象
    normalized = {}
    for ext, rule in rules.items():
        ext = str(ext).strip().lstrip(".").lower()
        if isinstance(rule, str):
            normalized[ext] = {"folder": rule, "label": ext.upper()}
        elif isinstance(rule, dict) and "folder" in rule:
            normalized[ext] = {
                "folder": rule["folder"],
                "label": rule.get("label", ext.upper()),
            }
        else:
            print(f"✗ 规则格式不对（.{ext}）：应为路径字符串或 {{folder, label}}")
            sys.exit(1)

    cfg = config.load()
    existing = cfg.get("custom_rules", {})
    existing.update(normalized)
    cfg["custom_rules"] = existing
    config.save(cfg)

    # 顺手创建目标文件夹
    for rule in normalized.values():
        Path(rule["folder"]).expanduser().mkdir(parents=True, exist_ok=True)

    print(f"✓ 已加载 {len(normalized)} 条规则：")
    for ext, rule in sorted(normalized.items()):
        print(f"  .{ext:6s}  →  {rule['folder']}")


def _setup() -> None:
    """首次设置流程：三种模式可选（模板 / 逐个问 / 配置文件）。"""
    print()
    print("📥 欢迎使用 DropTidy，先花 30 秒设置一下：")
    print()
    print("你想用哪种方式配置？")
    print("  1) 选一个预设模板（学术 / 工作 / 简洁）")
    print("  2) 便利版 — 我一个个问你，你填路径就行")
    print("  3) 高级版 — 给你一个配置文件模板，自己填")
    print()

    choice = input("> ").strip()

    if choice == "1":
        _setup_template()
    elif choice == "3":
        _setup_advanced()
    else:
        _setup_easy()


def _setup_template() -> None:
    """选一个预设模板。"""
    print()
    print("选一个模板：")
    for key, t in TEMPLATES.items():
        print(f"  {key:10s} — {t['name']}：{t['description']}")
    print()
    key = input("> ").strip()
    if key not in TEMPLATES:
        print(f"✗ 没有这个模板：{key}")
        return
    t = TEMPLATES[key]
    cfg = config.load()
    cfg["custom_rules"] = dict(t["rules"])
    config.save(cfg)
    watcher.ensure_drop_zone()
    for rule in t["rules"].values():
        Path(rule["folder"]).expanduser().mkdir(parents=True, exist_ok=True)
    print(f"✓ 已应用模板「{t['name']}」，共 {len(t['rules'])} 条规则。")


def _setup_easy() -> None:
    """便利版：逐个问用户每个类型的文件放到哪。"""
    print()
    print("好，我们一个一个来。直接输入路径就行，回车用默认值。")
    print()

    groups = [
        ("📄 PDF 文档", ["pdf"], "~/Documents/文档"),
        ("📝 Word 文档", ["docx", "doc"], "~/Documents/文档"),
        ("📊 Excel 表格", ["xlsx", "xls", "csv"], "~/Documents/表格"),
        ("📚 电子书", ["epub", "mobi", "azw3"], "~/Documents/电子书"),
        ("🖼️ 图片 / 截图", ["png", "jpg", "jpeg", "gif"], "~/Pictures/图片"),
        ("🗜️ 压缩包", ["zip", "rar", "7z"], "~/Downloads/压缩包"),
        ("📽️ PPT", ["pptx", "ppt"], "~/Documents/演示"),
        ("💻 代码文件", ["py", "js", "html", "css"], "~/Documents/代码"),
        ("📦 安装包", ["dmg", "pkg", "exe"], "~/Downloads/安装包"),
    ]

    rules = {}
    for group_name, exts, default_path in groups:
        user_input = input(f"{group_name} → {default_path}\n  回车保持，或输入新路径：").strip()
        target = user_input if user_input else default_path
        for ext in exts:
            rules[ext] = {"folder": target, "label": group_name.split(" ", 1)[-1]}

    print()
    print("还有其他文件类型要配吗？（直接回车跳过）")
    print("  格式：扩展名:路径，比如 txt:~/Documents/笔记")
    while True:
        extra = input("> ").strip()
        if not extra:
            break
        if ":" in extra:
            ext, path = extra.split(":", 1)
            ext = ext.strip().lstrip(".")
            path = path.strip()
            rules[ext] = {"folder": path, "label": ext.upper()}
            print(f"  ✓ .{ext} → {path}")

    cfg = config.load()
    cfg["custom_rules"] = rules
    config.save(cfg)

    watcher.ensure_drop_zone()
    for rule in rules.values():
        Path(rule["folder"]).expanduser().mkdir(parents=True, exist_ok=True)

    print()
    print("✓ 设置完成！")
    print(f"  投递区：{cfg['drop_zone']}")
    print()
    print("以后把文件丢进投递区，就会自动归到你指定的文件夹。")


def _setup_advanced() -> None:
    """高级版：生成一个配置文件模板，让用户自己填，再用 load-config 加载。"""
    config_path = Path.cwd() / "droptidy_config.json"

    template = {
        "_说明": {
            "格式": "扩展名 → 目标文件夹路径",
            "例子": "pdf: ~/Downloads/论文与作业",
            "怎么填": "左边是文件后缀（不带点），右边是你想放到哪个文件夹",
            "注意": "~ 表示你的用户目录，比如 ~/Downloads 就是你的下载文件夹",
        },
        "custom_rules": {
            "pdf": "~/Downloads/论文与作业",
            "docx": "~/Downloads/论文与作业",
            "xlsx": "~/Downloads/课程参考资料",
            "epub": "~/Downloads/在读文学作品",
            "png": "~/Downloads/备忘事项",
            "zip": "~/Downloads/压缩包",
        },
        "fallback_folder": "~/Documents/其他",
    }

    config_path.write_text(
        json.dumps(template, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print()
    print(f"✓ 配置文件已生成：{config_path}")
    print()
    print("打开它，按说明改路径就行。")
    print()
    print("填完之后跑：")
    print(f"  python -m droptidy load-config {config_path}")


if __name__ == "__main__":
    main()
