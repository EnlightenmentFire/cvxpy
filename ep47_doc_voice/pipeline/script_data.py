"""Episode 47 narration: 113 lines, one sentence per line, read verbatim from ep47_lines.txt.
The three Han Feizi classical lines are kind="quote"; everything else is "narr"."""
import os

_HERE = os.path.dirname(os.path.abspath(__file__))
QUOTES = {
    "韩非子有度写道：法不阿贵，绳不挠曲。",
    "法之所加，智者弗能辞，勇者弗敢争。",
    "刑过不避大臣，赏善不遗匹夫。",
}


def all_lines():
    with open(os.path.join(_HERE, "ep47_lines.txt"), encoding="utf-8") as fh:
        texts = [t.rstrip("\n") for t in fh if t.strip()]
    assert len(texts) == 113, len(texts)
    return [dict(id=f"line_{i:04d}", say=t, kind="quote" if t in QUOTES else "narr")
            for i, t in enumerate(texts, 1)]
