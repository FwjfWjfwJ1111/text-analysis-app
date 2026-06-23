import pytest
import json
from pathlib import Path
from modules.history import (
    load_history, save_record, delete_record, clear_all, get_record_by_id,
    MAX_HISTORY
)


@pytest.fixture
def temp_history_path(tmp_path, monkeypatch):
    history_file = tmp_path / "history.json"
    
    def mock_get_history_path():
        return history_file
    
    monkeypatch.setattr("modules.history._get_history_path", mock_get_history_path)
    return history_file


def test_load_history_empty(temp_history_path):
    records = load_history()
    assert records == []


def test_save_record(temp_history_path):
    record = {
        "source_type": "paste",
        "source_label": "test",
        "text_preview": "测试文本",
        "total_words": 10,
        "vocabulary_size": 5,
        "top20": [("测试", 5)],
        "chart_type": "词云图",
        "min_freq": 1
    }
    
    save_record(record)
    records = load_history()
    
    assert len(records) == 1
    assert records[0]["source_type"] == "paste"
    assert records[0]["source_label"] == "test"
    assert "id" in records[0]
    assert "timestamp" in records[0]


def test_delete_record(temp_history_path):
    record = {
        "source_type": "paste",
        "source_label": "test",
        "text_preview": "测试文本",
        "total_words": 10,
        "vocabulary_size": 5,
        "top20": [("测试", 5)],
        "chart_type": "词云图",
        "min_freq": 1
    }
    
    save_record(record)
    records = load_history()
    record_id = records[0]["id"]
    
    result = delete_record(record_id)
    assert result is True
    
    records = load_history()
    assert len(records) == 0


def test_delete_record_not_found(temp_history_path):
    result = delete_record("nonexistent-id")
    assert result is False


def test_clear_all(temp_history_path):
    record = {
        "source_type": "paste",
        "source_label": "test",
        "text_preview": "测试文本",
        "total_words": 10,
        "vocabulary_size": 5,
        "top20": [("测试", 5)],
        "chart_type": "词云图",
        "min_freq": 1
    }
    
    save_record(record)
    save_record(record)
    
    clear_all()
    records = load_history()
    assert records == []


def test_get_record_by_id(temp_history_path):
    record = {
        "source_type": "paste",
        "source_label": "test",
        "text_preview": "测试文本",
        "total_words": 10,
        "vocabulary_size": 5,
        "top20": [("测试", 5)],
        "chart_type": "词云图",
        "min_freq": 1
    }
    
    save_record(record)
    records = load_history()
    record_id = records[0]["id"]
    
    found = get_record_by_id(record_id)
    assert found is not None
    assert found["id"] == record_id


def test_get_record_by_id_not_found(temp_history_path):
    found = get_record_by_id("nonexistent-id")
    assert found is None


def test_max_history_capacity(temp_history_path):
    record = {
        "source_type": "paste",
        "source_label": "test",
        "text_preview": "测试文本",
        "total_words": 10,
        "vocabulary_size": 5,
        "top20": [("测试", 5)],
        "chart_type": "词云图",
        "min_freq": 1
    }
    
    for i in range(55):
        save_record(record)
    
    records = load_history()
    assert len(records) == 50