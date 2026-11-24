"""Facts for ep03: pure arithmetic, checked by program."""
from math import lcm

GAN = "甲乙丙丁戊己庚辛壬癸"
ZHI = "子丑寅卯辰巳午未申酉戌亥"


def pair(n):
    """n-th pair, 1-based (1 -> 甲子)."""
    return GAN[(n - 1) % 10] + ZHI[(n - 1) % 12]


def year_pair(y):
    """Ganzhi of Gregorian year y, anchored at 1984 = 甲子 (label for the lunar year mostly overlapping y)."""
    return pair((y - 1984) % 60 + 1)


if __name__ == "__main__":
    seq = [pair(n) for n in range(1, 62)]
    print("1..12:", " ".join(seq[:12]))
    for n in (11, 21, 31, 41, 51, 61):
        print(f"pair {n}: {pair(n)}")
    # first return to 甲子
    first = next(n for n in range(2, 200) if pair(n) == "甲子")
    print("first repeat of 甲子 at pair", first, "-> steps:", first - 1, " lcm(10,12)=", lcm(10, 12))
    all60 = set(seq[:60])
    print("distinct pairs in one cycle:", len(all60), "of", 10 * 12, "possible")
    jia = [z for z in ZHI if "甲" + z in all60]
    print("甲 pairs with:", "".join(jia), "; 甲丑 occurs:", "甲丑" in all60)
    parity_ok = all((GAN.index(p[0]) % 2) == (ZHI.index(p[1]) % 2) for p in all60)
    print("parity rule (odd stem<->odd branch) holds:", parity_ok)
    for y in (1984, 2044, 2024, 2026, 1924):
        print(y, year_pair(y))
    print("pair 60:", pair(60), " pair 10:", pair(10))
