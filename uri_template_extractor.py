"""Reusable module for extracting URI templates from URIs using drain3.

Example:
    template = extract_uri_template("https://example.com/users/123/orders/456")
"""

from __future__ import annotations

import threading
from typing import Optional
from urllib.parse import urlsplit

import re
from drain3 import TemplateMiner
from drain3.template_miner_config import TemplateMinerConfig

__all__ = ["UriTemplateExtractor", "normalize_uri", "extract_uri_template"]


def _mask_high_cardinality(text: str) -> str:
    """Replace common high-cardinality values (UUID, long hex, IPv4, numeric segments) with "<*>"."""
    try:
        text = re.sub(r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}", "<*>", text, flags=re.IGNORECASE)
        text = re.sub(r"(?<![0-9a-fA-F])[0-9a-fA-F]{32}(?![0-9a-fA-F])", "<*>", text, flags=re.IGNORECASE)
        text = re.sub(r"(?<![0-9a-fA-F])[0-9a-fA-F]{16,}(?![0-9a-fA-F])", "<*>", text, flags=re.IGNORECASE)
        text = re.sub(r"(?:[0-9]{1,3}\.){3}[0-9]{1,3}", "<*>", text)
        text = re.sub(r"/(?P<num>[0-9]+)(?=/|$)", r"/<*>", text)
        # Heuristic: mask probable username-like segments: alpha-numeric, length >=6,
        # not common path words (api, users, login, profile, files, products, etc.)
        common_tokens = [
            "api",
            "users",
            "login",
            "profile",
            "files",
            "products",
            "download",
            "search",
            "blog",
            "orders",
            "items",
        ]
        def _mask_user_segment(m: re.Match) -> str:
            seg = m.group(1)
            if seg.lower() in common_tokens:
                return "/" + seg
            # mask if length >=6 and alphanumeric (allow hyphen/underscore)
            if re.fullmatch(r"[A-Za-z0-9_-]{6,}", seg):
                return "/<*>"
            return "/" + seg

        text = re.sub(r"/([A-Za-z0-9_-]{3,})(?=/|$)", _mask_user_segment, text)
    except Exception:
        return text
    return text


def normalize_uri(uri: str, include_query: bool = False) -> str:
    """Trim, lowercase scheme/host, drop fragment and trailing slash.

    Query is dropped unless include_query is True (then only names are kept).
    """
    if not isinstance(uri, str) or not uri.strip():
        raise ValueError("uri must be a non-empty string")

    parts = urlsplit(uri.strip())
    scheme = parts.scheme.lower()
    host = parts.netloc.lower()
    path = parts.path.rstrip("/")

    # Mask high-cardinality path segments (numbers, UUIDs, IPs, long hex)
    def mask_segment(seg: str) -> str:
        if not seg:
            return seg
        # UUID
        if re.fullmatch(r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}", seg):
            return "<*>"
        # compact 32 hex
        if re.fullmatch(r"[0-9a-fA-F]{32}", seg):
            return "<*>"
        # long hex
        if re.fullmatch(r"[0-9a-fA-F]{16,}", seg):
            return "<*>"
        # IPv4
        if re.fullmatch(r"(?:[0-9]{1,3}\\.){3}[0-9]{1,3}", seg):
            return "<*>"
        # numeric
        if re.fullmatch(r"[0-9]+", seg):
            return "<*>"
        return seg

    masked_parts = [mask_segment(s) for s in path.split("/") if s != ""]
    masked_path = ("/" + "/".join(masked_parts)) if masked_parts else ""

    # Convert query params into masked path-style segments when requested
    if include_query and parts.query:
        names = []
        for p in parts.query.split("&"):
            if not p:
                continue
            k = p.split("=", 1)[0]
            names.append(k)
        if names:
            suffix = "".join(f"/{n}/<*>" for n in names)
            masked_path = masked_path + suffix

    normalized = f"{scheme}://{host}" if scheme and host else host
    normalized += masked_path
    return normalized


class UriTemplateExtractor:
    """Thread-safe URI template extractor backed by a drain3 TemplateMiner."""

    def __init__(
        self,
        config: Optional[TemplateMinerConfig] = None,
        include_query: bool = False,
        wildcard: str = "<*>",
    ) -> None:
        if config is None:
            config = TemplateMinerConfig()
            # Attempt to auto-load a local drain3.ini next to this module
            try:
                from pathlib import Path

                cfg_path = Path(__file__).resolve().parent / "drain3.ini"
                if cfg_path.exists():
                    try:
                        config.load(str(cfg_path))
                    except Exception:
                        # If loading fails, fall back to sensible defaults
                        config.drain_sim_th = 0.5
                        config.drain_depth = 4
                        config.profiling_enabled = False
                else:
                    config.drain_sim_th = 0.5
                    config.drain_depth = 4
                    config.profiling_enabled = False
            except Exception:
                config.drain_sim_th = 0.5
                config.drain_depth = 4
                config.profiling_enabled = False
        self._miner = TemplateMiner(config=config)
        self._include_query = include_query
        self._wildcard = wildcard
        self._lock = threading.Lock()

    def extract(self, uri: str) -> str:
        """Normalize the URI, mine it with drain3, and return the template."""
        normalized = normalize_uri(uri, self._include_query)
        # Extra safety: ensure common high-cardinality patterns are masked in the
        # normalized string (catch any missed by normalize_uri).
        # Mask UUIDs, long hex, IPv4, and pure numeric path segments.
        try:
            # UUID
            normalized = re.sub(r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}", "<*>", normalized, flags=re.IGNORECASE)
            # 32-char hex
            normalized = re.sub(r"(?<![0-9a-fA-F])[0-9a-fA-F]{32}(?![0-9a-fA-F])", "<*>", normalized, flags=re.IGNORECASE)
            # long hex (16+)
            normalized = re.sub(r"(?<![0-9a-fA-F])[0-9a-fA-F]{16,}(?![0-9a-fA-F])", "<*>", normalized, flags=re.IGNORECASE)
            # IPv4
            normalized = re.sub(r"(?:[0-9]{1,3}\.){3}[0-9]{1,3}", "<*>", normalized)
            # numeric path segments (slash-delimited)
            normalized = re.sub(r"/(?P<num>[0-9]+)(?=/|$)", r"/<*>", normalized)
        except Exception:
            # If regex fails for any reason, continue with original normalized
            pass
        # Tokenize on "/" by converting to a space-delimited line.
        line = normalized.replace("://", " ", 1).replace("/", " ").strip()
        with self._lock:
            result = self._miner.add_log_message(line)
        tokens = result["template_mined"].split()

        # normalize known drain3 mask tokens to the configured wildcard
        mask_tokens = {
            "<*>", "<NUM>", "<UUID>", "<IP>", "<HEX>",
            "<<NUM>>", "<<UUID>>", "<<IP>>", "<<HEX>>", "<NUMS>"
        }
        tokens = [self._wildcard if t in mask_tokens or re.fullmatch(r"<+\w+>+", t) else t for t in tokens]
        if "://" in normalized and len(tokens) >= 2:
            scheme, host, rest = tokens[0], tokens[1], tokens[2:]
            out = f"{scheme}://{host}" + "".join("/" + t for t in rest)
            # ensure any missed high-cardinality tokens are masked in the final output
            return _mask_high_cardinality(out)
        return _mask_high_cardinality("/".join(tokens))


_default_extractor: Optional[UriTemplateExtractor] = None
_default_lock = threading.Lock()


def extract_uri_template(uri: str) -> str:
    """Extract a URI template using a shared default extractor."""
    global _default_extractor
    with _default_lock:
        # Ensure the shared extractor matches the desired default wildcard.
        if (
            _default_extractor is None
            or getattr(_default_extractor, "_wildcard", None) != "<*>"
        ):
            # Recreate the default extractor to ensure masking and wildcard
            _default_extractor = UriTemplateExtractor(wildcard="<*>")
    return _default_extractor.extract(uri)
