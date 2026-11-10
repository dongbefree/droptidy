"""Preset templates for different user types."""

from __future__ import annotations

from typing import Dict


# 学术/学生模板
TEMPLATE_ACADEMIC: Dict[str, Dict] = {
    "pdf": {"folder": "~/Downloads/论文与作业", "label": "论文文献"},
    "epub": {"folder": "~/Downloads/在读文学作品", "label": "电子书"},
    "mobi": {"folder": "~/Downloads/在读文学作品", "label": "电子书"},
    "docx": {"folder": "~/Downloads/论文与作业", "label": "作业文档"},
    "doc": {"folder": "~/Downloads/论文与作业", "label": "作业文档"},
    "xlsx": {"folder": "~/Downloads/课程参考资料", "label": "课程数据"},
    "xls": {"folder": "~/Downloads/课程参考资料", "label": "课程数据"},
    "csv": {"folder": "~/Downloads/课程参考资料", "label": "课程数据"},
    "png": {"folder": "~/Downloads/备忘事项", "label": "截图"},
    "jpg": {"folder": "~/Downloads/备忘事项", "label": "图片"},
    "jpeg": {"folder": "~/Downloads/备忘事项", "label": "图片"},
    "zip": {"folder": "~/Downloads/压缩包", "label": "压缩包"},
    "rar": {"folder": "~/Downloads/压缩包", "label": "压缩包"},
    "7z": {"folder": "~/Downloads/压缩包", "label": "压缩包"},
    "md": {"folder": "~/Downloads/备忘事项", "label": "笔记"},
    "txt": {"folder": "~/Downloads/备忘事项", "label": "笔记"},
    "pptx": {"folder": "~/Downloads/课程参考资料", "label": "课件"},
    "ppt": {"folder": "~/Downloads/课程参考资料", "label": "课件"},
}

# 工作模板
TEMPLATE_WORK: Dict[str, Dict] = {
    "docx": {"folder": "~/Documents/工作/文档", "label": "文档"},
    "doc": {"folder": "~/Documents/工作/文档", "label": "文档"},
    "xlsx": {"folder": "~/Documents/工作/表格", "label": "表格"},
    "xls": {"folder": "~/Documents/工作/表格", "label": "表格"},
    "csv": {"folder": "~/Documents/工作/表格", "label": "数据"},
    "pptx": {"folder": "~/Documents/工作/演示", "label": "PPT"},
    "ppt": {"folder": "~/Documents/工作/演示", "label": "PPT"},
    "pdf": {"folder": "~/Documents/工作/资料", "label": "PDF资料"},
    "png": {"folder": "~/Documents/工作/截图", "label": "截图"},
    "jpg": {"folder": "~/Documents/工作/截图", "label": "图片"},
    "zip": {"folder": "~/Downloads/压缩包", "label": "压缩包"},
    "dmg": {"folder": "~/Downloads/安装包", "label": "安装包"},
}

# 简洁模板
TEMPLATE_SIMPLE: Dict[str, Dict] = {
    "pdf": {"folder": "~/Documents/文档", "label": "文档"},
    "docx": {"folder": "~/Documents/文档", "label": "文档"},
    "doc": {"folder": "~/Documents/文档", "label": "文档"},
    "xlsx": {"folder": "~/Documents/表格", "label": "表格"},
    "xls": {"folder": "~/Documents/表格", "label": "表格"},
    "png": {"folder": "~/Pictures/图片", "label": "图片"},
    "jpg": {"folder": "~/Pictures/图片", "label": "图片"},
    "zip": {"folder": "~/Downloads/压缩包", "label": "压缩包"},
    "dmg": {"folder": "~/Downloads/安装包", "label": "安装包"},
}


TEMPLATES = {
    "academic": {
        "name": "学术/学生",
        "description": "论文、文献、课程材料、电子书",
        "rules": TEMPLATE_ACADEMIC,
    },
    "work": {
        "name": "工作",
        "description": "文档、表格、PPT、工作资料",
        "rules": TEMPLATE_WORK,
    },
    "simple": {
        "name": "简洁",
        "description": "按类型粗分就行",
        "rules": TEMPLATE_SIMPLE,
    },
}
