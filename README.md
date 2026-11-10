# DropTidy 📥

把文件丢进投递区，自动归好类。

零第三方依赖（纯 Python 标准库）。支持预览（dry-run）、撤销（undo）、后台监控、预设模板。

---

## 为什么做

下载目录永远是乱的：论文、截图、安装包、表格混在一起。DropTidy 只做一件事：**你丢进去，它按后缀自动归到对应文件夹**。

它的前提是「安全」——移动文件是不可逆操作，所以它**默认先预览、能撤销**。

---

## 安装

```bash
# 零依赖，直接跑（推荐）
git clone <你的仓库地址> && cd droptidy

# 或安装为命令
pip install -e .
```

Python ≥ 3.8。

---

## 怎么用

```bash
python -m droptidy setup          # 首次配置（模板 / 逐个问 / 配置文件三种方式）
python -m droptidy init           # 在桌面创建投递区文件夹
python -m droptidy dry-run        # 预览会怎么整理（不移动）
python -m droptidy run            # 真正整理一次
python -m droptidy undo           # 撤销上一次整理
python -m droptidy start          # 后台监控，丢进去自动整理
python -m droptidy load-config <文件>   # 从 JSON 文件加载规则
python -m droptidy rules          # 查看当前分类规则
```

典型流程：

```bash
python -m droptidy setup      # 选一个模板或自定义路径
python -m droptidy dry-run    # 先看看它打算把文件挪到哪
python -m droptidy run        # 确认无误后真正执行
```

---

## 安全设计（重点）

移动文件是破坏性操作，所以：

1. **`dry-run` 预览**：只计算去向，不移动任何文件。真正动手前先看一眼。
2. **`undo` 撤销**：每次移动都会写操作日志（`data/undo.log`），`undo` 会按相反顺序把文件放回原位。
3. **重名不覆盖**：默认 `rename`（自动加 `(1)` `(2)`），可选 `skip`（跳过）或 `overwrite`（覆盖）。
4. **只移动、不删除**：内部用 `shutil.move`，没有删除逻辑。

> ⚠️ `undo` 依赖操作日志，日志被清空或文件被手动改动后就无法撤销。重要的整理建议先 `dry-run` 再 `run`。

---

## 分类规则

默认规则见 `droptidy/rules.py`，覆盖 PDF / Word / Excel / 图片 / 压缩包 / 代码 / 安装包等。三种方式自定义：

- **模板**：学术、工作、简洁三套预设（`setup` → 选 1）。
- **逐个问**：`setup` → 选 2，跟着提示填路径。
- **配置文件**：`setup` → 选 3 生成模板，改完 `load-config` 加载。

配置文件格式：

```json
{
  "custom_rules": {
    "pdf": "~/Downloads/论文与作业",
    "png": "~/Pictures/截图"
  }
}
```

---

## 架构

```
投递区（drop zone）
   │  扫描
   ▼
plan_file（算去向）── dry-run 时到此为止
   │  执行
   ▼
execute_plan（shutil.move + 写 undo 日志）
```

- `rules.py`：默认分类规则
- `config.py`：用户配置（投递区位置、自定义规则、重名策略）
- `organizer.py`：核心——plan / execute / undo
- `templates.py`：三套预设模板
- `watcher.py`：后台监控投递区

---

## 我做的取舍

- **默认安全**：dry-run 和 undo 是「移动文件工具」的底线，没有它们我不敢公开这个项目。
- **零依赖**：同 Rhythm，这类小工具的核心价值是「随手可用」。
- **不做文件夹递归**：目前只整理投递区根目录下的文件，不递归子目录——避免误伤嵌套结构。

---

## 已知限制

- 不递归处理子文件夹（投递区里的文件夹会被跳过）。
- 分类只按扩展名，不看文件内容。
- `undo` 依赖日志；日志清空或文件被外部改动后无法撤销。
- 大文件复制完成前，`start` 模式会等待 0.5 秒再处理，极慢的复制仍可能截断。

---

## 测试

```bash
pip install pytest
pytest
```

覆盖 dry-run 不移动、移动+日志、undo 恢复、重名 rename/skip、fallback 兜底。

---

## License

[MIT](./LICENSE)
