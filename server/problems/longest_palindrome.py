from problems._bulk import load_bulk_cases
from problems.schema import (
    BruteForce,
    ComprehensionRubric,
    HintLevel,
    Loophole,
    OptimalApproach,
    Problem,
    TestCase,
)

PROBLEM = Problem(
    id=5,
    slug="longest-palindromic-substring",
    title="Longest Palindromic Substring",
    difficulty="Medium",
    statement="Given a string `s`, return the longest palindromic substring in `s`.",
    constraints=[
        "1 <= s.length <= 1000",
        "s consists of digits and English letters",
    ],
    entry_point="longestPalindrome",
    starter_code="def longestPalindrome(s):\n    pass\n",
    reference_solution=(
        "def longestPalindrome(s):\n"
        "    if not s:\n"
        "        return ''\n"
        "    start, end = 0, 0\n"
        "    def expand(left, right):\n"
        "        while left >= 0 and right < len(s) and s[left] == s[right]:\n"
        "            left -= 1\n"
        "            right += 1\n"
        "        return left + 1, right - 1\n"
        "    for i in range(len(s)):\n"
        "        l1, r1 = expand(i, i)\n"
        "        if r1 - l1 > end - start:\n"
        "            start, end = l1, r1\n"
        "        l2, r2 = expand(i, i + 1)\n"
        "        if r2 - l2 > end - start:\n"
        "            start, end = l2, r2\n"
        "    return s[start:end + 1]\n"
    ),
    compare_fn=(
        "def _compare(result, expected, args):\n"
        "    s = args['s']\n"
        "    if not isinstance(result, str) or result == '' or result not in s:\n"
        "        return False\n"
        "    if result != result[::-1]:\n"
        "        return False\n"
        "    return len(result) == len(expected)\n"
    ),
    test_cases=[
        TestCase(
            id="multiple_valid_answers",
            args={"s": "babad"},
            expected="bab",
            is_edge_case=True,
            edge_case_tag="multiple_correct_answers",
            explanation_if_failed="Both 'bab' and 'aba' are valid longest palindromes here — grading checks palindrome validity and correct length, not one exact string.",
        ),
        TestCase(id="even_length", args={"s": "cbbd"}, expected="bb", is_edge_case=True, edge_case_tag="even_length_palindrome"),
        TestCase(id="single_char", args={"s": "a"}, expected="a", is_edge_case=True, edge_case_tag="minimal_size"),
        TestCase(id="two_distinct_chars", args={"s": "ac"}, expected="a"),
        TestCase(id="whole_string_palindrome", args={"s": "aaaa"}, expected="aaaa", is_edge_case=True, edge_case_tag="entire_string_is_palindrome"),
        TestCase(id="no_repeats", args={"s": "abcde"}, expected="a"),
    ],
    brute_force=BruteForce(
        description="Check every possible substring (O(n^2) of them) and test each for being a palindrome (O(n) per check).",
        complexity="O(n^3) time",
        why_insufficient="At n = 1000, O(n^3) is up to 10^9 operations — borderline too slow, and there's a much cleaner O(n^2) technique available.",
    ),
    optimal_approach=OptimalApproach(
        description=(
            "Expand around center: every palindrome has a center, either a single character "
            "(odd length) or between two characters (even length). Try all 2n-1 centers, "
            "expanding outward while characters match, and track the longest found."
        ),
        complexity="O(n^2) time, O(1) space (Manacher's algorithm gets this to O(n) if needed)",
    ),
    hint_ladder=[
        HintLevel(level=1, text="Instead of checking every substring, what if you grew outward from a center point?"),
        HintLevel(level=2, text="Every palindrome has a center — but note centers can be a single character (odd-length palindromes) or the gap between two characters (even-length palindromes)."),
        HintLevel(level=3, text="For each of the 2n-1 possible centers, expand left and right as long as the characters match; track the longest span found so far."),
        HintLevel(level=4, text="This gets you O(n^2), which is a perfectly good stopping point. If you want true O(n), look up Manacher's algorithm as a stretch goal."),
    ],
    common_loopholes=[
        Loophole(id="even_center", description="Even-length palindromes have a center between two characters, easy to forget if you only check single-character centers.", related_test_case_id="even_length"),
        Loophole(id="multiple_answers", description="Multiple substrings of the same max length can be valid — grading must accept any of them.", related_test_case_id="multiple_valid_answers"),
        Loophole(id="whole_string", description="The entire string itself can be the answer if it's all one repeated character.", related_test_case_id="whole_string_palindrome"),
    ],
    comprehension_rubric=ComprehensionRubric(
        key_points=[
            "Must return the actual SUBSTRING, not its length",
            "Multiple correct answers of the same length can exist",
            "Palindromes can be odd length (single center) or even length (center between two chars)",
            "A single character is trivially a palindrome of length 1",
        ]
    ),
)

PROBLEM.test_cases.extend(load_bulk_cases("longest_palindromic_substring.json"))
