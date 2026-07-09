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
    id=3,
    slug="longest-substring-without-repeating-characters",
    title="Longest Substring Without Repeating Characters",
    difficulty="Medium",
    statement=(
        "Given a string `s`, find the length of the longest substring without repeating "
        "characters. A substring must be contiguous — you can't skip characters."
    ),
    constraints=[
        "0 <= s.length <= 5 * 10^4",
        "s consists of English letters, digits, symbols, and spaces",
    ],
    entry_point="lengthOfLongestSubstring",
    starter_code="def lengthOfLongestSubstring(s):\n    pass\n",
    reference_solution=(
        "def lengthOfLongestSubstring(s):\n"
        "    last_seen = {}\n"
        "    left = 0\n"
        "    longest = 0\n"
        "    for right, ch in enumerate(s):\n"
        "        if ch in last_seen and last_seen[ch] >= left:\n"
        "            left = last_seen[ch] + 1\n"
        "        last_seen[ch] = right\n"
        "        longest = max(longest, right - left + 1)\n"
        "    return longest\n"
    ),
    test_cases=[
        TestCase(id="basic_repeat", args={"s": "abcabcbb"}, expected=3),
        TestCase(id="all_same", args={"s": "bbbbb"}, expected=1, is_edge_case=True, edge_case_tag="all_repeating"),
        TestCase(id="overlap_jump", args={"s": "pwwkew"}, expected=3),
        TestCase(id="empty_string", args={"s": ""}, expected=0, is_edge_case=True, edge_case_tag="empty_input"),
        TestCase(id="no_repeats", args={"s": "abc"}, expected=3),
        TestCase(
            id="left_pointer_jump_back",
            args={"s": "abcad"},
            expected=4,
            is_edge_case=True,
            edge_case_tag="stale_last_seen_index",
            explanation_if_failed=(
                "'a' appears at index 0 and again at index 3, but by the time we see the "
                "second 'a', the window has already moved past index 0. A solution that "
                "jumps `left` to `last_seen[ch] + 1` without checking that `last_seen[ch]` "
                "is still inside the current window will incorrectly shrink the window and "
                "under-count the answer."
            ),
        ),
        TestCase(id="single_char", args={"s": "a"}, expected=1, is_edge_case=True, edge_case_tag="minimal_size"),
    ],
    brute_force=BruteForce(
        description="Check every possible substring (O(n^2) of them), and for each one scan it to verify all characters are unique (O(n)).",
        complexity="O(n^3) time (or O(n^2) with a smarter uniqueness check)",
        why_insufficient="At n = 5*10^4, even O(n^2) is 2.5 billion operations — this needs to run in roughly linear time.",
    ),
    optimal_approach=OptimalApproach(
        description=(
            "Sliding window with two pointers: expand the right pointer each step; keep a "
            "map of each character's last-seen index; when a repeat is found inside the "
            "current window, jump the left pointer just past that repeat's previous position."
        ),
        complexity="O(n) time, O(min(n, charset size)) space",
    ),
    hint_ladder=[
        HintLevel(level=1, text="Instead of checking every substring from scratch, can you extend a window one character at a time and only shrink it when you hit a repeat?"),
        HintLevel(level=2, text="Keep a map from character to the last index where you saw it."),
        HintLevel(level=3, text="When the current character is already in your map, move the left edge of your window to just after that character's last occurrence."),
        HintLevel(level=4, text="Watch out: only jump the left pointer forward if that last-seen index is actually still inside the current window — otherwise you can move left backward by mistake."),
    ],
    common_loopholes=[
        Loophole(id="empty", description="Empty string input should return 0.", related_test_case_id="empty_string"),
        Loophole(id="all_repeat", description="A string of all-identical characters should return 1, not 0.", related_test_case_id="all_same"),
        Loophole(id="stale_index", description="A character seen before but now outside the current window must not incorrectly shrink it.", related_test_case_id="left_pointer_jump_back"),
    ],
    comprehension_rubric=ComprehensionRubric(
        key_points=[
            "Answer is a LENGTH, not the substring itself",
            "Substring must be CONTIGUOUS",
            "'Without repeating characters' means every character in the window is unique",
            "Empty string is a valid input (answer 0)",
        ]
    ),
)

PROBLEM.test_cases.extend(load_bulk_cases("longest_substring_without_repeating_characters.json"))
