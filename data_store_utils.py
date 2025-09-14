# data_store_utils.py
# Simple JSON-backed data store helper (atomic writes)

import json
import os
from typing import Any, Dict

DATA_FILE = os.path.join(os.path.dirname(__file__), "data_store.json")

DEFAULT_STORE = {
    "availability": {},   # keys are "d_s" (e.g. "0_3") -> bool
    "bookings": [],       # list of {"day":int,"slot":int,"token":str,"time":str}
    "counsellors": [],    # list of {"id":int,"name":str,"specialty":str}
    "chat_logs": [],
}

def load_data() -> Dict[str, Any]:
    # Ensure default file exists
    if not os.path.exists(DATA_FILE):
        save_data(DEFAULT_STORE)
        return DEFAULT_STORE.copy()
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        # ensure keys exist
        for k in DEFAULT_STORE:
            if k not in data:
                data[k] = DEFAULT_STORE[k]
        return data
    except Exception:
        # on parse error, re-create default
        save_data(DEFAULT_STORE)
        return DEFAULT_STORE.copy()

def save_data(data: Dict[str, Any]) -> None:
    # atomic write
    tmp = DATA_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    os.replace(tmp, DATA_FILE)
