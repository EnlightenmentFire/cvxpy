"""Event times shared by picture and sound (pure Python)."""


def sonar_hits(cues, D):
    s7 = cues.get("d07", (0.5, 0.5))[0]
    s8 = cues.get("d08", (D * 0.6, D * 0.6))[0]
    beale = tuple(s7 + 1.2 + i * 0.55 for i in range(5))
    cony = tuple(s7 + 4.4 + i * 0.5 for i in range(5))
    heavy = tuple(s8 + 2.6 + i * 0.7 for i in range(4))
    return beale, cony, heavy


def plane_passes(cues, D, shot):
    """Times (shot-local) when an aircraft passes closest, for fly-by sounds."""
    if shot == "topdown":
        s4 = cues.get("f04", (2.0, 2.0))[0]
        out = []
        # strafe: plane_t = t - s4 + 1.7, closest when (plane_t % 6)/6 ~ 0.5
        t = s4 - 1.7 + 3.0
        while t < s4 + 4.5:
            out.append(t)
            t += 6.0
        t = s4 + 4.5 - 1.0 + 0.476 * 6.0
        while t < D:
            out.append(t)
            t += 6.0
        return out
    if shot == "tower":
        s6 = cues.get("f06", (0.3, 0.3))[0]
        return [s6 + 2.5 + 5.0 * k for k in range(20) if s6 + 2.5 + 5.0 * k < D]
    return []
