from __future__ import annotations

import argparse
import json
import sys

from .check import check_answer, report, sentences, to_dicts


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="rag-cite-check",
                                description="Check a RAG answer's citations against its sources.")
    p.add_argument("input", help="JSON file: {\"sources\": {id: text}, \"answer\": text}")
    p.add_argument("--json", action="store_true", help="print JSON instead of markdown")
    a = p.parse_args(argv)
    with open(a.input, encoding="utf-8") as f:
        data = json.load(f)
    issues = check_answer(data["answer"], data["sources"])
    if a.json:
        print(json.dumps(to_dicts(issues), indent=2, ensure_ascii=False))
    else:
        print(report(issues, len(sentences(data["answer"]))), end="")
    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
