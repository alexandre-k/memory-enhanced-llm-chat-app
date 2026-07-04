import json
import os
import uuid
import socket
from pathlib import Path
import ipaddress


STORE_FILE = Path.cwd() / "ip_users.json"



def load_store() -> dict:
    if STORE_FILE.exists():
        return json.loads(STORE_FILE.read_text(encoding="utf-8"))
    return {}


def save_store(store: dict) -> None:
    tmp = STORE_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(store, indent=2), encoding="utf-8")
    os.replace(tmp, STORE_FILE)


def get_or_create_user_id() -> str:
    store = load_store()
    if not store:
        save_store(str(uuid.uuid4()))
        return load_store()
    return store