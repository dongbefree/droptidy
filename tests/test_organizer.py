"""Tests for DropTidy's safe-file-handling core: dry-run + undo."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from droptidy import config, organizer


@pytest.fixture
def tmp_cfg(monkeypatch):
    """Point drop zone / targets at temp dirs and stub the config file."""
    tmp_path = Path(tempfile.mkdtemp())
    drop = tmp_path / "drop"
    drop.mkdir()
    data_dir = tmp_path / "data"
    data_dir.mkdir()

    # Stub config functions to write into the temp data dir
    import droptidy.config as cfgmod

    monkeypatch.setattr(cfgmod, "_config_dir", lambda: data_dir)
    monkeypatch.setattr(organizer, "_undo_log_path", lambda: data_dir / "undo.log")

    cfg = cfgmod.load()
    cfg["drop_zone"] = str(drop)
    cfg["fallback_folder"] = str(tmp_path / "其他")
    cfg["custom_rules"] = {
        "txt": {"folder": str(tmp_path / "笔记"), "label": "笔记"},
        "pdf": {"folder": str(tmp_path / "论文"), "label": "论文"},
    }
    cfgmod.save(cfg)
    return {"drop": drop, "tmp": tmp_path, "cfg": cfg}


def _mk(drop, name, content="hello"):
    f = drop / name
    f.write_text(content, encoding="utf-8")
    return f


def test_dry_run_does_not_move(tmp_cfg):
    drop = tmp_cfg["drop"]
    f = _mk(drop, "a.txt")
    results = organizer.scan_drop_zone(dry_run=True)
    assert len(results) == 1
    assert results[0]["status"] == "planned"
    assert results[0]["label"] == "笔记"
    # 文件还在原地
    assert f.exists()


def test_run_moves_and_logs(tmp_cfg):
    drop = tmp_cfg["drop"]
    f = _mk(drop, "a.txt")
    results = organizer.scan_drop_zone()
    assert results[0]["status"] == "moved"
    assert not f.exists()
    # 目标文件存在
    dest = tmp_cfg["tmp"] / "笔记" / "a.txt"
    assert dest.exists()
    # 日志有一条
    log = organizer._read_undo_log()
    assert len(log) == 1


def test_undo_restores(tmp_cfg):
    drop = tmp_cfg["drop"]
    _mk(drop, "a.txt")
    organizer.scan_drop_zone()
    dest = tmp_cfg["tmp"] / "笔记" / "a.txt"
    assert dest.exists()

    undone = organizer.undo_last()
    assert len(undone) == 1
    assert (drop / "a.txt").exists()
    assert not dest.exists()


def test_duplicate_rename(tmp_cfg):
    drop = tmp_cfg["drop"]
    (tmp_cfg["tmp"] / "笔记").mkdir(parents=True, exist_ok=True)
    (tmp_cfg["tmp"] / "笔记" / "a.txt").write_text("existing", encoding="utf-8")
    _mk(drop, "a.txt", "new")

    results = organizer.scan_drop_zone()
    assert results[0]["status"] == "moved"
    # rename 策略 → 变成 a (1).txt
    assert (tmp_cfg["tmp"] / "笔记" / "a (1).txt").exists()


def test_duplicate_skip(tmp_cfg):
    drop = tmp_cfg["drop"]
    (tmp_cfg["tmp"] / "笔记").mkdir(parents=True, exist_ok=True)
    (tmp_cfg["tmp"] / "笔记" / "a.txt").write_text("existing", encoding="utf-8")

    cfg = config.load()
    cfg["on_duplicate"] = "skip"
    config.save(cfg)

    _mk(drop, "a.txt", "new")
    results = organizer.scan_drop_zone()
    assert results[0]["status"] == "skipped"
    # 原文件还在（skip 不移动）
    assert (drop / "a.txt").exists()


def test_fallback_folder(tmp_cfg):
    drop = tmp_cfg["drop"]
    _mk(drop, "mystery.xyz")
    results = organizer.scan_drop_zone()
    assert results[0]["label"] == "其他"
    assert str(results[0]["dest"]).endswith("其他/mystery.xyz")
