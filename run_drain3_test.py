from drain3 import TemplateMiner
from drain3.template_miner_config import TemplateMinerConfig
from urllib.parse import urlsplit

import os

config = TemplateMinerConfig()
# Load drain3.ini from the script directory so relative runs work
config_path = os.path.join(os.path.dirname(__file__), "drain3.ini")
config.load(config_path)
miner = TemplateMiner(persistence_handler=None, config=config)

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

from urllib.parse import urlsplit

def normalize_uri(uri):
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

records = []
for uri in uris:
    normalized = normalize_uri(uri)
    if not normalized:
        continue
    result = miner.add_log_message(normalized)
    template = result['template_mined']
    records.append((uri, normalized, result['cluster_id'], result['cluster_size'], template))

print("Results: URL -> normalized -> template")
for r in records:
    print(r)
