"""One-time data-prep script: parses newfacade/LeetCodeDataset entries (cached
in the scratchpad as <slug>.json) into our TestCase args/expected shape and
writes filtered, deduplicated bulk case files to server/problems/data/.

Not part of the running app -- run once to regenerate the bulk case files.
"""

import ast
import json
from pathlib import Path

SCRATCHPAD = Path(
    r"C:\Users\3shub\AppData\Local\Temp\claude\C--Users-3shub-Documents-Volna-Code"
    r"\258045fe-df0d-4e89-85f0-7b36612c46bf\scratchpad"
)
OUT_DIR = Path(__file__).resolve().parent.parent / "problems" / "data"
OUT_DIR.mkdir(parents=True, exist_ok=True)

SLUGS = [
    "two-sum",
    "add-two-numbers",
    "longest-substring-without-repeating-characters",
    "median-of-two-sorted-arrays",
    "longest-palindromic-substring",
]

# Expected-output types are not reliably inferable from the raw string alone
# (e.g. a palindrome answer like "12321" is syntactically a valid Python int
# literal but must stay a string). Declare the real type per problem instead
# of guessing.
ALWAYS_STRING_SLUGS = {"longest-palindromic-substring"}


def _split_top_level_assignments(input_str: str) -> str:
    """'nums = [3,3], target = 6' -> 'nums = [3,3]\ntarget = 6'

    Splits on commas that are at bracket-depth 0 and outside quotes, which are
    the ones separating separate `key = value` assignments (as opposed to
    commas inside a list/tuple literal).
    """
    depth = 0
    in_quote: str | None = None
    out = []
    i = 0
    while i < len(input_str):
        ch = input_str[i]
        if in_quote:
            out.append(ch)
            if ch == in_quote:
                in_quote = None
        elif ch in "'\"":
            in_quote = ch
            out.append(ch)
        elif ch in "([{":
            depth += 1
            out.append(ch)
        elif ch in ")]}":
            depth -= 1
            out.append(ch)
        elif ch == "," and depth == 0:
            out.append("\n")
        else:
            out.append(ch)
        i += 1
    return "".join(out)


def parse_args(input_str: str) -> dict:
    ns: dict = {}
    split = _split_top_level_assignments(input_str)
    normalized = "\n".join(line.strip() for line in split.split("\n"))
    exec(normalized, {"__builtins__": {}}, ns)
    return ns


def parse_expected(output_str: str, force_string: bool = False):
    if force_string:
        return output_str
    try:
        return ast.literal_eval(output_str)
    except (ValueError, SyntaxError):
        return output_str


def main() -> None:
    for slug in SLUGS:
        obj = json.load(open(SCRATCHPAD / f"{slug}.json", encoding="utf-8"))
        seen: set[str] = set()
        cases = []
        dropped_none = 0
        dropped_dupe = 0

        for entry in obj["input_output"]:
            output_raw = str(entry["output"]).strip()
            if output_raw == "None":
                dropped_none += 1
                continue

            args = parse_args(entry["input"])
            expected = parse_expected(entry["output"], force_string=slug in ALWAYS_STRING_SLUGS)

            key = json.dumps(args, sort_keys=True)
            if key in seen:
                dropped_dupe += 1
                continue
            seen.add(key)

            cases.append({"args": args, "expected": expected})

        out_path = OUT_DIR / f"{slug.replace('-', '_')}.json"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(cases, f, indent=2)

        print(
            f"{slug}: wrote {len(cases)} cases "
            f"(dropped {dropped_none} constraint-violating None cases, "
            f"{dropped_dupe} duplicates) -> {out_path}"
        )


if __name__ == "__main__":
    main()
