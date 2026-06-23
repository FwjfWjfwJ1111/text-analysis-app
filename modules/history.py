import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional


MAX_HISTORY = 50


def _get_history_path() -> Path:
    """
    获取历史记录文件路径。
    
    Returns:
        history.json 文件的绝对路径
    """
    module_dir = Path(__file__).parent
    project_dir = module_dir.parent
    data_dir = project_dir / "data"
    data_dir.mkdir(exist_ok=True)
    return data_dir / "history.json"


def _ensure_file_exists(path: Path) -> None:
    """
    确保历史记录文件存在，不存在则创建空数组。
    
    Args:
        path: history.json 文件路径
    """
    if not path.exists():
        with open(path, "w", encoding="utf-8") as f:
            json.dump([], f)


def load_history() -> List[Dict]:
    """
    加载历史记录。文件不存在时自动创建空数组。
    
    Returns:
        历史记录列表（按时间倒序）
    """
    path = _get_history_path()
    _ensure_file_exists(path)
    
    try:
        with open(path, "r", encoding="utf-8") as f:
            records = json.load(f)
    except (json.JSONDecodeError, IOError):
        records = []
        with open(path, "w", encoding="utf-8") as f:
            json.dump(records, f)
    
    return sorted(records, key=lambda x: x.get("timestamp", ""), reverse=True)


def save_record(record: Dict) -> None:
    """
    保存单条记录，自动管理容量（最多50条，超过则删除最旧）。
    
    Args:
        record: 记录字典，必须包含以下字段：
            - source_type: "url" | "upload" | "paste"
            - source_label: 来源标签
            - text_preview: 文本预览（前100字符）
            - total_words: 分词总数
            - vocabulary_size: 词汇量（去重）
            - top20: Top20词频列表
            - chart_type: 图表类型
            - min_freq: 词频阈值
    """
    path = _get_history_path()
    _ensure_file_exists(path)
    
    record_with_id = {
        "id": str(uuid.uuid4()),
        "timestamp": datetime.now().isoformat(),
        **record
    }
    
    records = load_history()
    records.insert(0, record_with_id)
    
    if len(records) > MAX_HISTORY:
        records = records[:MAX_HISTORY]
    
    with open(path, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)


def delete_record(record_id: str) -> bool:
    """
    按 ID 删除单条记录。
    
    Args:
        record_id: 记录 ID
    
    Returns:
        是否成功删除
    """
    path = _get_history_path()
    _ensure_file_exists(path)
    
    records = load_history()
    original_count = len(records)
    records = [r for r in records if r.get("id") != record_id]
    
    if len(records) < original_count:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(records, f, ensure_ascii=False, indent=2)
        return True
    return False


def clear_all() -> None:
    """
    清空所有历史记录。
    """
    path = _get_history_path()
    with open(path, "w", encoding="utf-8") as f:
        json.dump([], f)


def get_record_by_id(record_id: str) -> Optional[Dict]:
    """
    按 ID 查询单条记录。
    
    Args:
        record_id: 记录 ID
    
    Returns:
        记录字典，如果不存在返回 None
    """
    records = load_history()
    for record in records:
        if record.get("id") == record_id:
            return record
    return None