from __future__ import annotations

import math

# Approximate growth exponent for each named complexity class, used to judge
# empirically-measured time/space growth against a problem's authored optimal
# complexity. These are deliberately generous relative to the textbook
# exponent -- real measurements include constant-factor noise, GC pauses, and
# interpreter overhead that a growth-rate slope doesn't fully filter out. The
# goal is to catch a clearly worse complexity class (e.g. O(n^2) submitted
# where O(n) was asked for), not to certify a mathematically exact exponent.
CLASS_EXPONENT: dict[str, float] = {
    "constant": 0.0,
    "logarithmic": 0.3,
    "linear": 1.0,
    "linearithmic": 1.25,
    "quadratic": 2.0,
    "cubic": 3.0,
}

CLASS_LABEL: dict[str, str] = {
    "constant": "O(1)",
    "logarithmic": "O(log n)",
    "linear": "O(n)",
    "linearithmic": "O(n log n)",
    "quadratic": "O(n^2)",
    "cubic": "O(n^3)",
}

# How much slope above a class's nominal exponent still counts as "meets that
# class" -- generous enough to absorb real-world measurement noise without
# letting a genuinely worse complexity class sneak through.
_TOLERANCE = 0.4


def fit_growth_exponent(points: list[tuple[int, float]]) -> float | None:
    """Least-squares slope of log(metric) vs log(n) across (n, metric) pairs,
    i.e. the empirical exponent k in metric ~= n^k. Returns None if there
    isn't enough usable (n>1, metric>0) data to fit a line -- e.g. every
    measurement was too fast/small to produce a positive value, which we
    treat as "not measurable" rather than a failure.
    """
    xs: list[float] = []
    ys: list[float] = []
    for n, metric in points:
        if n <= 1 or metric <= 0:
            continue
        xs.append(math.log(n))
        ys.append(math.log(metric))
    if len(xs) < 2:
        return None
    mean_x = sum(xs) / len(xs)
    mean_y = sum(ys) / len(ys)
    num = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    den = sum((x - mean_x) ** 2 for x in xs)
    if den == 0:
        return None
    return num / den


def meets_class(observed_exponent: float | None, target_class: str) -> bool:
    """Whether an empirically observed growth exponent is consistent with the
    target complexity class, generous tolerance included. A failed fit
    (observed_exponent is None -- e.g. every run was too fast to measure)
    passes by default: a submission is never failed on measurement noise,
    only on a clearly-worse-than-target observed growth rate.
    """
    if observed_exponent is None:
        return True
    return observed_exponent <= CLASS_EXPONENT[target_class] + _TOLERANCE


def describe_class(target_class: str) -> str:
    return CLASS_LABEL[target_class]
