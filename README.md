# rag-cite-check

Independent demo, not affiliated with CI&T.

A small offline tool that checks a RAG answer against the sources the retriever gave the model. When an assistant answers with `[source-id]` markers, this tells you which sentences you can't trust.

It uses no model and no network. It reads one JSON file and prints a report.

## What it checks

| Issue | Meaning |
|---|---|
| `uncited` | A sentence has no `[id]` marker. |
| `unknown-id` | The marker names a source that was never retrieved. |
| `quote-missing` | A quoted span is not in the cited source. |
| `number-missing` | A number in the sentence is not in the cited source. |

Quotes are matched after lowercasing, straightening curly quotes and dashes, and collapsing whitespace. Numbers like `1,200`, `1.200` and `1200` count as the same figure.

## Run it

```bash
uv sync
uv run rag-cite-check examples/example.json          # markdown report
uv run rag-cite-check examples/example.json --json   # JSON
uv run pytest -q
```

Input format:

```json
{"sources": {"kb-1": "text of source 1"}, "answer": "Claim [kb-1]."}
```

The exit code is 1 when there are issues and 0 when there are none, so you can use it in CI.

`examples/example.json` is invented data. It has one planted problem of each kind, and the tool finds all four.

## What was tested

- 12 pytest tests, all offline, run in GitHub Actions on every push.
- Each issue kind, with a clean answer and a failing one.
- A quote that is in source B but cited to source A is flagged.
- Curly quotes, uppercase and line-wrapped quotes still match.
- Number formats (`1,200` vs `1.200`).
- Exit codes and JSON output of the CLI.

While writing the tests, a line break inside a quoted span split the sentence in two and caused a false `quote-missing`. Sentences now split only on blank lines. A test covers it.

## What was not tested

- Real model output. All answers in the tests are written by hand.
- Large inputs or speed.
- Languages other than English and Portuguese-style accents (one example uses "São Paulo").
- Sentence splitting on abbreviations such as "e.g. Foo". It may split there.
- Paraphrase. A claim that restates a source in different words is not checked beyond its numbers and quotes. A passing result does not mean the answer is correct.
