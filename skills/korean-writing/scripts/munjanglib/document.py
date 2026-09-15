"""Lossless review units, conservative protection and descriptive diagnostics.

Sentence boundaries and lints are heuristics, NOT linguistic or factual proofs.
"""
from __future__ import annotations
from collections import Counter
from dataclasses import asdict, dataclass
import difflib
import re
from typing import Any

@dataclass(frozen=True)
class Unit:
    id: str
    text: str
    start: int
    end: int
    kind: str
    editable: bool


URL = re.compile(r"https?://[^\s<>\"'`]+", re.I)
NUMBER = re.compile(r"(?<![A-Za-z_\d])[+-]?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?(?:[eE][+-]?\d+)?(?:\s?(?:%|‰|kg|mg|km|cm|mm|mL|ml|kWh|Wh|kW|MW|GB|MB|GiB|MiB|Hz|MHz|GHz|°C|원|만원|억원|개|명|년|월|일|시|분|초))?", re.I)
QUOTE_PATTERNS = (
    re.compile(r'"[^"\r\n]+"'), re.compile(r'“[^”\r\n]+”'), re.compile(r'「[^」]+」'),
    re.compile(r'『[^』]+』'), re.compile(r"(?<![\w])'[^'\r\n]+'(?![\w])"),
    re.compile(r'‘[^’\r\n]+’'),
)
CITATION = re.compile(r"\[(?:\d+(?:\s*[-,]\s*\d+)*|\^[^\]\s]+)\]|(?:cite|filecite)[^]+")
MATH = re.compile(r"(?<!\\)\$\$[\s\S]*?(?<!\\)\$\$|\\\[[\s\S]*?\\\]|\\\([^\n]*?\\\)")
INLINE_MATH = re.compile(r"(?<![\\\w])\$(?!\s|\d+\b)[^\n$]+(?<!\s)\$")
ABBREVIATION = re.compile(r"(?:\b(?:Mr|Mrs|Ms|Dr|Prof|Sr|Jr|St|vs|etc|Fig|No)|\b(?:[A-Za-z]\.)+[A-Za-z]|\b[A-Z])\.$")
PREFIX = re.compile(r"^(?:\ufeff)?(?:[ \t]*(?:#{1,6}[ \t]+|(?:[-+*]|\d+[.)])[ \t]+|>[ \t]?|\[[ xX]\][ \t]+)|[ \t]+)")


def fence_spans(text: str) -> list[tuple[int, int]]:
    spans = []
    active = None
    pos = 0
    for line in text.splitlines(keepends=True):
        if active is None:
            bom = 1 if pos == 0 and line.startswith('\ufeff') else 0
            match = re.match(r"^ {0,3}(`{3,}|~{3,})([^\r\n]*)", line[bom:])
            if match:
                marker = match[1]
                if marker[0] != '`' or '`' not in match[2]:
                    active = (pos + bom, marker[0], len(marker))
        elif re.match(r"^ {0,3}" + re.escape(active[1]) + "{" + str(active[2]) + r",}[ \t]*(?:\r?\n)?$", line):
            spans.append((active[0], pos + len(line)))
            active = None
        pos += len(line)
    if active:
        spans.append((active[0], len(text)))  # Unclosed code remains protected.
    return spans


def inline_code_spans(text: str) -> list[tuple[int, int]]:
    spans = []
    i = 0
    while i < len(text):
        if text[i] != '`' or i and text[i - 1] == '\\':
            i += 1
            continue
        end = i + 1
        while end < len(text) and text[end] == '`':
            end += 1
        marker = text[i:end]
        close = re.search(r"(?<!`)" + re.escape(marker) + r"(?!`)", text[end:])
        if close:
            stop = end + close.end()
            spans.append((i, stop))
            i = stop
        else:
            i = end
    return spans


def protected_spans(text: str, quote_policy: str = "protect") -> list[dict]:
    spans: list[dict] = []
    def add(kind: str, start: int, end: int) -> None:
        if start < end:
            spans.append({"kind": kind, "text": text[start:end], "start": start, "end": end})
    fences = fence_spans(text)
    for start, end in fences:
        add("code_block", start, end)
    for start, end in inline_code_spans(text):
        if not any(a <= start and end <= b for a, b in fences):
            add("inline_code", start, end)
    for match in URL.finditer(text):
        value = match[0].rstrip('.,;:!?。！？')
        while value.endswith(')') and value.count(')') > value.count('('):
            value = value[:-1]
        while value.endswith(']') and value.count(']') > value.count('['):
            value = value[:-1]
        add("url", match.start(), match.start() + len(value))
    patterns = [("citation", CITATION), ("math", MATH), ("math", INLINE_MATH)]
    if quote_policy == "protect":
        patterns.extend(("quote", p) for p in QUOTE_PATTERNS)
    for kind, pattern in patterns:
        for m in pattern.finditer(text):
            if not any(a <= m.start() and m.end() <= b for a, b in fences):
                add(kind, m.start(), m.end())
    return sorted(spans, key=lambda s: (s["start"], s["end"], s["kind"]))


def sentence_pieces(text: str) -> list[str]:
    """Split only confidently spaced terminal punctuation, preserving every byte."""
    protected = protected_spans(text)
    pieces = []
    start, i = 0, 0
    while i < len(text):
        char = text[i]
        if char not in '.?!。！？' or any(s['start'] <= i < s['end'] for s in protected):
            i += 1
            continue
        if char == '.' and i and i + 1 < len(text) and text[i - 1].isdigit() and text[i + 1].isdigit():
            i += 1
            continue
        if char == '.' and ABBREVIATION.search(text[max(start, i - 20):i + 1]):
            i += 1
            continue
        stop = i + 1
        while stop < len(text) and text[stop] in '.?!。！？':
            stop += 1
        while stop < len(text) and text[stop] in '\"\'”’)]}':
            stop += 1
        if stop == len(text) or text[stop].isspace():
            pieces.append(text[start:stop])
            start = stop
        i = stop
    if start < len(text):
        pieces.append(text[start:])
    return pieces or ([text] if text else [])


def units(text: str) -> list[Unit]:
    result: list[Unit] = []
    position = 0
    def add(value: str, kind: str, editable: bool) -> None:
        nonlocal position
        if value:
            result.append(Unit(f"u{len(result) + 1:06d}", value, position, position + len(value), kind, editable))
            position += len(value)
    fences = dict(fence_spans(text))
    while position < len(text):
        if position == 0 and text.startswith('\ufeff'):
            add('\ufeff', 'layout', False)
            continue
        if position in fences:
            add(text[position:fences[position]], "code", False)
            continue
        end = text.find('\n', position)
        line = text[position:] if end < 0 else text[position:end + 1]
        body = line.rstrip('\r\n')
        newline = line[len(body):]
        if not body.strip():
            add(body, "layout", False)
            add(newline, "layout", False)
            continue
        prefix = PREFIX.match(body)
        if prefix:
            add(prefix[0], "layout", False)
            body = body[len(prefix[0]):]
        for piece in sentence_pieces(body):
            left = len(piece) - len(piece.lstrip())
            right = len(piece.rstrip())
            add(piece[:left], "layout", False)
            add(piece[left:right], "prose", True)
            if right >= left:
                add(piece[right:], "layout", False)
        add(newline, "layout", False)
    assert ''.join(u.text for u in result) == text
    return result


def editable_ids(text: str) -> list[str]:
    return [u.id for u in units(text) if u.editable]


def unit_records(text: str) -> list[dict]:
    return [asdict(u) for u in units(text)]


def diff_metrics(before: str, after: str) -> dict[str, Any]:
    # autojunk bounds common repetitive inputs; this is not minimum edit distance.
    matcher = difflib.SequenceMatcher(None, before, after, autojunk=True)
    counts = {"inserted": 0, "deleted": 0, "replaced_before": 0, "replaced_after": 0}
    for tag, a, b, c, d in matcher.get_opcodes():
        if tag == 'insert': counts['inserted'] += d - c
        elif tag == 'delete': counts['deleted'] += b - a
        elif tag == 'replace':
            counts['replaced_before'] += b - a
            counts['replaced_after'] += d - c
    return {
        "method": "difflib.SequenceMatcher, Unicode code points, autojunk=True, whitespace included; NOT Levenshtein",
        "change_ratio": 1.0 - matcher.ratio(),
        "before_chars": len(before), "after_chars": len(after),
        "after_chars_without_whitespace": sum(not c.isspace() for c in after),
        "after_utf8_bytes": len(after.encode('utf-8')), **counts,
    }


def lint(text: str) -> list[dict]:
    """Review candidates only: never auto-replace or assign a quality score."""
    rules = {
        "generic_opening": r"현대 사회에서|급변하는 시대에|오늘날.{0,12}중요",
        "empty_evaluation": r"시사하는 바가 크|주목할 만|혁신적",
        "vague_source": r"전문가들은|연구에 따르면",
        "nominalized_verb": r"분석을 진행|검토를 진행|설명을 제공",
        "formulaic_contrast": r"단순[한히].{0,35}넘어",
    }
    spans = protected_spans(text)
    out = []
    for u in units(text):
        if not u.editable:
            continue
        for name, pattern in rules.items():
            for m in re.finditer(pattern, u.text):
                a, b = u.start + m.start(), u.start + m.end()
                if any(s['start'] <= a and b <= s['end'] for s in spans):
                    continue
                out.append({"rule": name, "unit_id": u.id, "excerpt": m[0],
                            "status": "review_candidate_only", "start": a, "end": b})
    return out
