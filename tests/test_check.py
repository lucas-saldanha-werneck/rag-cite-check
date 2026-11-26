import json
import pathlib

from ragcite.check import check_answer, norm, norm_number, sentences
from ragcite.cli import main

SRC = {"a": "The plan costs 49 USD and has 3 seats. Replies come within 24 hours.",
       "b": "Exports: CSV and JSON. Revenue was 1,200 last year."}


def kinds(answer):
    return [i.kind for i in check_answer(answer, SRC)]


def test_clean_answer_has_no_issues():
    assert kinds("The plan costs 49 USD [a]. It has 3 seats [a].") == []


def test_uncited_sentence():
    assert kinds("The plan costs 49 USD [a]. It is cheap.") == ["uncited"]


def test_unknown_id():
    assert kinds("See the docs [zzz].") == ["unknown-id"]


def test_quote_must_be_in_cited_source_not_just_any_source():
    assert kinds('It offers "CSV and JSON" [a].') == ["quote-missing"]
    assert kinds('It offers "CSV and JSON" [b].') == []


def test_quote_survives_curly_quotes_case_and_whitespace():
    assert kinds("It says “replies  come\nwithin 24 HOURS” [a].") == []


def test_wrong_number():
    assert kinds("It has 5 seats [a].") == ["number-missing"]


def test_number_formats_match():
    assert norm_number("1.200") == norm_number("1,200") == "1200"
    assert norm_number("3,5") == "3.5"
    assert kinds("Revenue was 1.200 [b].") == []


def test_multiple_ids_any_source_can_support():
    assert kinds("It has 3 seats and CSV [a][b].") == []


def test_unknown_id_does_not_hide_other_checks():
    assert sorted(kinds("It has 9 seats [a][zzz].")) == ["number-missing", "unknown-id"]


def test_norm_and_split():
    assert norm("  A—B  C ") == "a-b c"
    assert len(sentences("One [a]. Two [a].\n\nThree [a].")) == 3
    assert len(sentences("A quote that wraps\nacross lines [a].")) == 1


def test_cli_exit_codes_and_json(tmp_path, capsys):
    good = tmp_path / "g.json"
    good.write_text(json.dumps({"sources": SRC, "answer": "It has 3 seats [a]."}))
    assert main([str(good)]) == 0
    capsys.readouterr()
    bad = tmp_path / "b.json"
    bad.write_text(json.dumps({"sources": SRC, "answer": "It has 7 seats [a]."}))
    assert main([str(bad), "--json"]) == 1
    out = json.loads(capsys.readouterr().out)
    assert out[0]["kind"] == "number-missing"


def test_bundled_example_finds_the_planted_problems(capsys):
    ex = pathlib.Path(__file__).parent.parent / "examples" / "example.json"
    data = json.loads(ex.read_text(encoding="utf-8"))
    found = sorted(i.kind for i in check_answer(data["answer"], data["sources"]))
    assert found == ["number-missing", "quote-missing", "uncited", "unknown-id"]
