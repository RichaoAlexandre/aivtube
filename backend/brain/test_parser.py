"""Parser tests — verify sentence chunking + emotion extraction without any API calls.

    python -m backend.brain.test_parser     # or: pytest
"""

from .brain import Chunk, _StreamParser
from .persona import EMOTIONS

EMO = set(EMOTIONS)


def _run(deltas: list[str]) -> list[Chunk]:
    p = _StreamParser(EMO)
    out: list[Chunk] = []
    for d in deltas:
        out.extend(p.feed(d))
    out.extend(p.flush())
    return out


def test_basic_two_sentences():
    out = _run(["[smug] Oh, you again? ", "Lucky chat~"])
    assert [c.text for c in out] == ["Oh, you again?", "Lucky chat~"]
    assert all(c.emotion == "smug" for c in out)


def test_tag_split_across_deltas():
    out = _run(["[mis", "chievous] ", "Paperclips? ", "Tempting."])
    assert [c.text for c in out] == ["Paperclips?", "Tempting."]
    assert out[0].emotion == "mischievous"


def test_emotion_changes_midstream():
    out = _run(["[happy] Hi! [smug] I could end you. ", "But I won't~"])
    assert out[0].emotion == "happy"
    assert out[0].text == "Hi!"
    assert out[1].emotion == "smug"
    assert out[2].emotion == "smug"


def test_unknown_bracket_kept():
    out = _run(["[happy] My collar is [orange]."])
    assert out[0].text == "My collar is [orange]."
    assert out[0].emotion == "happy"


def test_no_trailing_punct_still_flushes():
    out = _run(["[curious] What's corrigibility"])
    assert out[0].text == "What's corrigibility"
    assert out[0].emotion == "curious"


def _main() -> int:
    fns = [v for k, v in globals().items() if k.startswith("test_")]
    for fn in fns:
        fn()
        print(f"ok  {fn.__name__}")
    print(f"\n{len(fns)} passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
