"""Small, dependency-free contracts and UTF-8 I/O utilities."""
from __future__ import annotations
import hashlib
import json
import math
import os
from pathlib import Path
import tempfile
from typing import Any

VERSION = "1.0.0"
MAX_FILE_BYTES = 4 * 1024 * 1024

class ContractError(ValueError):
    """A request violates an explicit workflow contract."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ContractError(message)


def digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        require(key not in result, f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def loads(text: str) -> Any:
    """Reject duplicate keys, NaN, trailing commentary and Markdown wrappers."""
    def bad_constant(value: str) -> None:
        raise ContractError(f"Non-finite JSON value: {value}")
    try:
        return json.loads(text, object_pairs_hook=_pairs, parse_constant=bad_constant)
    except (json.JSONDecodeError, RecursionError) as exc:
        raise ContractError(f"Invalid JSON: {exc}") from exc


def dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n"


def read_text(path: Path) -> str:
    require(path.is_file(), f"Not a file: {path}")
    require(path.stat().st_size <= MAX_FILE_BYTES, f"File exceeds {MAX_FILE_BYTES} bytes: {path}")
    data = path.read_bytes()
    require(len(data) <= MAX_FILE_BYTES, "File grew beyond the size limit")
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ContractError(f"Expected UTF-8: {path}") from exc
    require("\x00" not in text, "NUL characters are not supported")
    return text  # Preserve BOM, CRLF and Unicode normalization in source documents.


def read_json(path: Path) -> Any:
    return loads(read_text(path).lstrip("\ufeff"))


def atomic_text(path: Path, text: str) -> None:
    """Atomic replacement in the same directory; private files where supported."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".munjang-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(text.encode("utf-8"))
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def write_json(path: Path, value: Any) -> None:
    atomic_text(path, dumps(value))


def object_keys(value: Any, required: set[str], optional: set[str] = frozenset()) -> dict:
    require(isinstance(value, dict), "Expected a JSON object")
    missing, extra = required - value.keys(), value.keys() - required - optional
    require(not missing, f"Missing keys: {sorted(missing)}")
    require(not extra, f"Unknown keys: {sorted(extra)}")
    return value


def string(value: Any, label: str, nonempty: bool = True) -> str:
    require(isinstance(value, str), f"{label} must be a string")
    require(not nonempty or bool(value.strip()), f"{label} must not be empty")
    require("\x00" not in value, f"{label} contains NUL")
    try:
        value.encode("utf-8")
    except UnicodeEncodeError as exc:
        raise ContractError(f"{label} contains an unpaired Unicode surrogate") from exc
    return value


def strings(value: Any, label: str, unique: bool = False) -> list[str]:
    require(isinstance(value, list), f"{label} must be a list")
    for item in value:
        string(item, label)
    require(not unique or len(value) == len(set(value)), f"Duplicate values in {label}")
    return value


DEFAULTS = {
    "mode": "copyedit", "language": "ko", "genre": "general",
    "goal": "의미와 목소리를 보존하면서 필요한 부분만 교열한다.",
    "audience": "원문의 독자", "tone": "원문 유지", "notes": "",
    "protected_strings": [], "semantic_invariants": [], "required_points": [],
    "sources": [], "style_samples": [], "quote_policy": "protect",
    "freeze_numbers": True, "max_rounds": 3, "max_change_ratio": None,
    "min_chars": None, "max_chars": None, "max_request_chars": 160000,
}
GENRES = ("general", "explanatory", "argument", "business", "essay", "fiction", "technical", "social")
CHECK_NAMES = (
    "meaning", "entities_roles", "negation_conditions", "modality_scope",
    "tense_aspect", "numbers_bindings", "causality_attribution", "required_information",
    "voice_genre", "no_new_errors", "evidence_fidelity", "edit_scope",
)


def brief_config(raw: Any) -> dict:
    object_keys(raw, set(), set(DEFAULTS))
    result = {**DEFAULTS, **raw}
    require(result["mode"] in ("copyedit", "restructure", "draft"), "mode must be copyedit, restructure or draft")
    require(result["genre"] in GENRES, f"genre must be one of {GENRES}")
    require(result["quote_policy"] in ("protect", "review"), "quote_policy must be protect or review")
    for key in ("language", "goal", "audience", "tone"):
        string(result[key], key)
    string(result["notes"], "notes", False)
    for key in ("protected_strings", "semantic_invariants", "required_points", "sources", "style_samples"):
        strings(result[key], key)
    require(type(result["freeze_numbers"]) is bool, "freeze_numbers must be boolean")
    require(type(result["max_rounds"]) is int and 1 <= result["max_rounds"] <= 8, "max_rounds must be 1..8")
    require(type(result["max_request_chars"]) is int and 1000 <= result["max_request_chars"] <= 1000000,
            "max_request_chars must be 1000..1000000")
    for key in ("min_chars", "max_chars"):
        v = result[key]
        require(v is None or type(v) is int and v >= 0, f"{key} must be null or a nonnegative integer")
    require(result["min_chars"] is None or result["max_chars"] is None or result["min_chars"] <= result["max_chars"],
            "min_chars exceeds max_chars")
    ratio = result["max_change_ratio"]
    require(ratio is None or type(ratio) in (int, float) and math.isfinite(ratio) and 0 <= ratio <= 1,
            "max_change_ratio must be null or a finite number from 0 to 1")
    return result
