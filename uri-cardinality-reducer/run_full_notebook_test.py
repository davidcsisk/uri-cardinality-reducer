from drain3 import TemplateMiner
from drain3.template_miner_config import TemplateMinerConfig
from pathlib import Path
from urllib.parse import urlsplit
import os

def normalize_uri(uri):
    from urllib.parse import urlsplit, parse_qsl
    if uri is None:
        return ""
    uri = str(uri).strip()
    if not uri:
        return ""
    parsed = urlsplit(uri)
    path = parsed.path
    query = parsed.query
    if query:
        params = parse_qsl(query, keep_blank_values=True)
        # convert query params to path-style masked segments: /key/<*>
        suffix = "".join(f"/{k}/<*>" for k, _ in params)
        return f"{path}{suffix}"
    return path

def normalize_uri_unmasked(uri):
    from urllib.parse import urlsplit, parse_qsl
    if uri is None:
        return ""
    uri = str(uri).strip()
    if not uri:
        return ""
    parsed = urlsplit(uri)
    path = parsed.path
    query = parsed.query
    if query:
        params = parse_qsl(query, keep_blank_values=True)
        # convert query params to path-style unmasked segments: /key/value
        suffix = "".join(f"/{k}/{v}" for k, v in params)
        return f"{path}{suffix}"
    return path

def load_miners():
    config = TemplateMinerConfig()
    config_path = Path(__file__).resolve().parent / "drain3.ini"
    config.load(str(config_path))
    miner = TemplateMiner(persistence_handler=None, config=config)

    config_no_mask = TemplateMinerConfig()
    config_no_mask.load(str(config_path))
    config_no_mask.masking = []
    miner_no_mask = TemplateMiner(persistence_handler=None, config=config_no_mask)
    return miner, miner_no_mask

uris = [
    "/api/users/12345/orders/98765",
    "/api/users/67890/orders/12345",
    "/api/users/55555/orders/77777",

    "/api/products/12345",
    "/api/products/67890",
    "/api/products/98765",

    "/api/login",
    "/api/login?user=dave",
    "/api/login?user=john",
    "/api/login?user=mary",

    "/api/files/550e8400-e29b-41d4-a716-446655440000",
    "/api/files/6ba7b810-9dad-11d1-80b4-00c04fd430c8",

    "https://example.com/api/users/12345/orders/99999",
    "https://example.com/api/users/77777/orders/88888",

    "/download/192.168.1.25/file",
    "/download/10.20.30.40/file",

    "/objects/0123456789abcdef0123456789abcdef",
]

def run():
    miner, miner_no_mask = load_miners()
    records = []
    for uri in uris:
        normalized_masked = normalize_uri(uri)
        normalized_unmasked = normalize_uri_unmasked(uri)
        if not normalized_masked:
            continue
        res_mask = miner.add_log_message(normalized_masked)
        res_no_mask = miner_no_mask.add_log_message(normalized_unmasked)
        records.append({
            "original_uri": uri,
            "normalized_masked": normalized_masked,
            "normalized_unmasked": normalized_unmasked,
            "template_masked": res_mask["template_mined"],
            "template_unmasked": res_no_mask["template_mined"],
            "cluster_id": res_mask["cluster_id"],
            "cluster_size": res_mask["cluster_size"],
        })

    # Print results
    print("Processed", len(records), "URIs")
    print(f"{'original_uri':60} | {'normalized_unmasked':40} | {'unmasked':40} | {'masked':30} | cluster:size")
    print('-'*170)
    for r in records:
        # convert space-separated tokens back to path style (replace spaces with '/')
        masked = r['template_masked'].replace(' ', '/')
        unmasked = r['template_unmasked'].replace(' ', '/')
        print(f"{r['original_uri'][:60]:60} | {r.get('normalized_unmasked','')[:40]:40} | {unmasked[:40]:40} | {masked[:30]:30} | {r['cluster_id']}:{r['cluster_size']}")

if __name__ == '__main__':
    run()
