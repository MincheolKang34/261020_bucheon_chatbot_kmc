"""대화 저장소. data/conversations.json 한 파일에 모든 대화를 보관한다."""
import json
import os
import threading
import time
import uuid

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
PATH = os.path.join(DATA_DIR, "conversations.json")
_lock = threading.Lock()


def _load():
    try:
        with open(PATH, encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, ValueError):
        return {}


def _save(data):
    os.makedirs(DATA_DIR, exist_ok=True)
    tmp = PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    os.replace(tmp, PATH)


def list_conversations():
    with _lock:
        data = _load()
    items = [{"id": k, "title": v["title"], "updated": v["updated"]} for k, v in data.items()]
    return sorted(items, key=lambda x: x["updated"], reverse=True)


def get(cid):
    with _lock:
        return _load().get(cid)


def create():
    cid = uuid.uuid4().hex[:12]
    now = time.time()
    with _lock:
        data = _load()
        data[cid] = {"title": "새 대화", "created": now, "updated": now, "messages": []}
        _save(data)
    return cid


def append(cid, *new_messages):
    """메시지를 추가한다. 첫 사용자 메시지로 제목을 정한다. 대화가 없으면 None."""
    with _lock:
        data = _load()
        conv = data.get(cid)
        if conv is None:
            return None
        if not conv["messages"] and new_messages:
            first = new_messages[0]["content"].strip().replace("\n", " ")
            conv["title"] = first[:30] + ("…" if len(first) > 30 else "")
        conv["messages"].extend(new_messages)
        conv["updated"] = time.time()
        _save(data)
        return conv


def delete(cid):
    with _lock:
        data = _load()
        if cid not in data:
            return False
        del data[cid]
        _save(data)
        return True


def set_summary(cid, summary, summarized):
    """요약문과, 그 요약에 반영된 메시지 수를 저장한다."""
    with _lock:
        data = _load()
        conv = data.get(cid)
        if conv is None:
            return False
        conv["summary"] = summary
        conv["summarized"] = summarized
        _save(data)
        return True
