"""Scan every string that reaches the screen or the voice: forbidden name, advice-like phrasing, present-day hooks."""
import ast, glob, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FORBIDDEN = ["刘仲敬"]                       # the name the brief says must never appear
ADVICE = ["现在还能用", "照着做就能赚", "推荐", "建议买", "建议卖", "稳赚", "暴富", "收益率高", "跟单", "课程", "开户"]
PRESENT = ["今天的市场", "当下", "如今的行情", "A股", "港股", "美股", "比特币", "加密货币"]


def strings_in(path):
    tree = ast.parse(open(path).read())
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            yield node.value


def main():
    hits = []
    files = [f for f in glob.glob(os.path.join(ROOT, "src", "*.py")) if not f.endswith("qa_text.py")]
    texts = [(f, s) for f in files for s in strings_in(f)]
    docs = glob.glob(os.path.join(ROOT, "**", "*.md"), recursive=True)
    for f in docs:
        texts.append((f, open(f).read()))
    names = [p for p in glob.glob(os.path.join(ROOT, "**", "*"), recursive=True)]
    for f, s in texts:
        for w in FORBIDDEN:
            if w in s:
                hits.append(("FORBIDDEN", os.path.relpath(f, ROOT), w))
    for p in names:
        for w in FORBIDDEN:
            if w in p:
                hits.append(("FORBIDDEN-FILENAME", p, w))
    on_screen = [(f, s) for f, s in texts if f.endswith((".py",)) and re.search(r"[一-鿿]", s)]
    for f, s in on_screen:
        for w in ADVICE + PRESENT:
            if w in s and "不构成任何投资建议" not in s:
                hits.append(("CHECK", os.path.relpath(f, ROOT), f"{w}: {s[:40]}"))
    for h in hits:
        print(*h)
    print(f"{len(on_screen)} on-screen/spoken strings scanned; {sum(1 for h in hits if h[0].startswith('FORBIDDEN'))} forbidden hits; "
          f"{sum(1 for h in hits if h[0] == 'CHECK')} phrases to review")


if __name__ == "__main__":
    main()
