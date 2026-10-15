from drain3 import TemplateMiner
from drain3.template_miner_config import TemplateMinerConfig
from pathlib import Path
import os

config = TemplateMinerConfig()
config_path = Path(__file__).resolve().parent / "drain3.ini"
config.load(str(config_path))
miner = TemplateMiner(persistence_handler=None, config=config)

def normalize_uri(uri):
    from urllib.parse import urlsplit
    if uri is None:
        return ""
    uri = str(uri).strip()
    if not uri:
        return ""
    parsed = urlsplit(uri)
    path = parsed.path
    query = parsed.query
    if query:
        return f"{path}?{query}"
    return path

def process_list(uris):
    results = []
    for u in uris:
        n = normalize_uri(u)
        if not n:
            continue
        r = miner.add_log_message(n)
        results.append((u, n, r["template_mined"]))
    return results

if __name__ == "__main__":
    # Example: read lines from a file named large_uris.txt in the same folder
    sample_file = Path(__file__).resolve().parent / "large_uris.txt"
    if not sample_file.exists():
        print("No large_uris.txt found; create one with URIs (one per line) to run large test.")
        raise SystemExit(1)
    with sample_file.open("r", encoding="utf-8") as f:
        uris = [l.strip() for l in f if l.strip()]
    out = process_list(uris)
    for o in out[:200]:
        print(o)