"""Default file type → folder mapping.

用户可以在 config.json 里覆盖这些规则。
"""

from __future__ import annotations

from pathlib import Path

# 用 ~ 表示用户主目录，后面会展开
DEFAULT_RULES = {
    # 论文 / PDF
    "pdf": {"folder": "~/Documents/论文", "label": "论文"},
    # 表格
    "xlsx": {"folder": "~/Documents/表格", "label": "表格"},
    "xls": {"folder": "~/Documents/表格", "label": "表格"},
    "csv": {"folder": "~/Documents/表格", "label": "表格"},
    # 文档
    "docx": {"folder": "~/Documents/文档", "label": "文档"},
    "doc": {"folder": "~/Documents/文档", "label": "文档"},
    "md": {"folder": "~/Documents/笔记", "label": "笔记"},
    "txt": {"folder": "~/Documents/笔记", "label": "笔记"},
    # 图片 / 截图
    "png": {"folder": "~/Pictures/截图归档", "label": "截图"},
    "jpg": {"folder": "~/Pictures/截图归档", "label": "图片"},
    "jpeg": {"folder": "~/Pictures/截图归档", "label": "图片"},
    "gif": {"folder": "~/Pictures/截图归档", "label": "图片"},
    # 压缩包
    "zip": {"folder": "~/Downloads/压缩包", "label": "压缩包"},
    "rar": {"folder": "~/Downloads/压缩包", "label": "压缩包"},
    "7z": {"folder": "~/Downloads/压缩包", "label": "压缩包"},
    # 代码
    "py": {"folder": "~/Documents/代码", "label": "代码"},
    "js": {"folder": "~/Documents/代码", "label": "代码"},
    # 安装包
    "dmg": {"folder": "~/Downloads/安装包", "label": "安装包"},
    "pkg": {"folder": "~/Downloads/安装包", "label": "安装包"},
}

# 找不到规则的文件放这里
FALLBACK_FOLDER = "~/Documents/其他"


def get_folder_for(ext: str, rules: dict | None = None) -> tuple[Path, str]:
    """根据扩展名，返回 (目标文件夹路径, 分类标签)。

    找不到匹配的规则就返回 FALLBACK_FOLDER。
    """
    rules = rules or DEFAULT_RULES
    ext = ext.lower().lstrip(".")

    if ext in rules:
        folder = Path(rules[ext]["folder"]).expanduser()
        label = rules[ext]["label"]
    else:
        folder = Path(FALLBACK_FOLDER).expanduser()
        label = "其他"

    return folder, label
