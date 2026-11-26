"""Check a RAG answer against the sources that were retrieved for it.

No model calls, no network. It looks at four things:

* uncited      - a sentence with no [source-id] marker
* unknown-id   - a marker that names a source that was not retrieved
* quote-missing - a "quoted span" that is not in the cited source
* number-missing - a number in the sentence that is not in the cited source
"""
from __future__ import annotations

import re
from dataclasses import dataclass, asdict

CITE = re.compile(r"\[([A-Za-z0-9_.\-]+)\]")
QUOTE = re.compile(r"[\"“]([^\"”]{4,})[\"”]")
NUMBER = re.compile(r"\d+(?:[.,]\d+)*")
SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z\"“\[])|\n\s*\n")

_QUOTES = str.maketrans({"‘": "'", "’": "'", "“": '"', "”": '"',
                         "–": "-", "—": "-", " ": " "})


def norm(text: str) -> str:
    """Lowercase, straighten quotes and dashes, collapse whitespace."""
    return re.sub(r"\s+", " ", text.translate(_QUOTES)).strip().lower()


def norm_number(n: str) -> str:
    """'1,200' and '1.200' and '1200' are the same figure; '3.5' stays '3.5'."""
    if re.fullmatch(r"\d{1,3}([.,]\d{3})+", n):
        return re.sub(r"[.,]", "", n)
    return n.replace(",", ".")


@dataclass
class Issue:
    kind: str
    sentence: str
    detail: str


def sentences(answer: str) -> list[str]:
    return [s.strip() for s in SPLIT.split(answer) if s.strip()]


def check_answer(answer: str, sources: dict[str, str]) -> list[Issue]:
    issues: list[Issue] = []
    normed = {k: norm(v) for k, v in sources.items()}
    nums = {k: {norm_number(n) for n in NUMBER.findall(v)} for k, v in sources.items()}
    for sent in sentences(answer):
        ids = CITE.findall(sent)
        if not ids:
            issues.append(Issue("uncited", sent, "no [source-id] marker"))
            continue
        known = [i for i in ids if i in sources]
        for i in ids:
            if i not in sources:
                issues.append(Issue("unknown-id", sent, f"[{i}] was not retrieved"))
        if not known:
            continue
        body = CITE.sub("", sent)
        for q in QUOTE.findall(body):
            if not any(norm(q) in normed[i] for i in known):
                issues.append(Issue("quote-missing", sent,
                                    f'"{q}" not found in {", ".join(known)}'))
        body_no_quotes = QUOTE.sub("", body)
        for n in NUMBER.findall(body_no_quotes):
            if not any(norm_number(n) in nums[i] for i in known):
                issues.append(Issue("number-missing", sent,
                                    f"{n} not found in {', '.join(known)}"))
    return issues


def report(issues: list[Issue], total: int) -> str:
    lines = [f"# Citation check", "", f"Sentences checked: {total}. Issues: {len(issues)}.", ""]
    for it in issues:
        lines.append(f"- **{it.kind}**: {it.detail}\n  > {it.sentence}")
    if not issues:
        lines.append("No issues found.")
    return "\n".join(lines) + "\n"


def to_dicts(issues: list[Issue]) -> list[dict]:
    return [asdict(i) for i in issues]
