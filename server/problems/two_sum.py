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
    id=1,
    slug="two-sum",
    title="Two Sum",
    difficulty="Easy",
    statement=(
        "You're given an array of integers `nums` and an integer `target`. "
        "Return the indices of the two numbers in `nums` that add up to `target`. "
        "You may assume each input has exactly one valid answer, and you cannot use "
        "the same element twice. You can return the answer in any order."
    ),
    constraints=[
        "2 <= nums.length <= 10^4",
        "-10^9 <= nums[i] <= 10^9",
        "-10^9 <= target <= 10^9",
        "Exactly one valid answer exists",
    ],
    entry_point="twoSum",
    starter_code="def twoSum(nums, target):\n    pass\n",
    reference_solution=(
        "def twoSum(nums, target):\n"
        "    seen = {}\n"
        "    for i, num in enumerate(nums):\n"
        "        complement = target - num\n"
        "        if complement in seen:\n"
        "            return [seen[complement], i]\n"
        "        seen[num] = i\n"
        "    return []\n"
    ),
    compare_fn=(
        "def _compare(result, expected, args):\n"
        "    if not isinstance(result, list) or len(result) != 2:\n"
        "        return False\n"
        "    i, j = result\n"
        "    if not isinstance(i, int) or not isinstance(j, int) or isinstance(i, bool) or isinstance(j, bool):\n"
        "        return False\n"
        "    if i == j:\n"
        "        return False\n"
        "    nums = args['nums']\n"
        "    if not (0 <= i < len(nums) and 0 <= j < len(nums)):\n"
        "        return False\n"
        "    return nums[i] + nums[j] == args['target']\n"
    ),
    test_cases=[
        TestCase(id="basic", args={"nums": [2, 7, 11, 15], "target": 9}, expected=[0, 1]),
        TestCase(
            id="duplicate_value",
            args={"nums": [2, 7, 11, 7, 15], "target": 14},
            expected=[1, 3],
            is_edge_case=True,
            edge_case_tag="duplicate_values",
            explanation_if_failed=(
                "The array has the value 7 twice. If your hash map overwrites the first "
                "occurrence's index before checking for the complement, or checks the "
                "complement after inserting the current number, you can accidentally "
                "pair an element with itself or pick the wrong duplicate."
            ),
        ),
        TestCase(
            id="negative_and_zero",
            args={"nums": [-3, 4, 3, 90], "target": 0},
            expected=[0, 2],
            is_edge_case=True,
            edge_case_tag="negative_numbers",
            explanation_if_failed="Negative numbers and a zero target are valid inputs — make sure your complement math handles negatives correctly.",
        ),
        TestCase(
            id="zero_values",
            args={"nums": [0, 4, 3, 0], "target": 0},
            expected=[0, 3],
            is_edge_case=True,
            edge_case_tag="zero_values",
            explanation_if_failed="Zero is a valid array value and a valid target — a solution that treats 0 as falsy (e.g. `if complement:`) will fail here.",
        ),
        TestCase(id="minimal_array", args={"nums": [3, 3], "target": 6}, expected=[0, 1], is_edge_case=True, edge_case_tag="minimal_size"),
    ],
    brute_force=BruteForce(
        description="Check every pair (i, j) with a nested loop, testing if nums[i] + nums[j] == target.",
        complexity="O(n^2) time, O(1) space",
        why_insufficient=(
            "With up to 10^4 elements, checking every pair is up to ~10^8 comparisons — "
            "it works but is far slower than necessary, and it doesn't scale. There's a way "
            "to solve this in a single pass."
        ),
    ),
    optimal_approach=OptimalApproach(
        description=(
            "Walk the array once, keeping a hash map of value -> index seen so far. At each "
            "element, compute the complement (target - current value) and check if it's "
            "already in the map before adding the current value."
        ),
        complexity="O(n) time, O(n) space",
    ),
    hint_ladder=[
        HintLevel(level=1, text="Think about what information you'd need to instantly know if you've already seen the right number before."),
        HintLevel(level=2, text="A hash map lets you look up 'have I seen X before' in O(1) instead of scanning again."),
        HintLevel(level=3, text="For each number, compute target minus that number (the complement) and check if the complement is already in your map."),
        HintLevel(level=4, text="Check for the complement BEFORE inserting the current number into the map — otherwise you might match an element with itself."),
    ],
    common_loopholes=[
        Loophole(id="dup_values", description="Duplicate values in the array requiring the correct pair of distinct indices.", related_test_case_id="duplicate_value"),
        Loophole(id="negatives", description="Negative numbers and negative/zero targets are valid.", related_test_case_id="negative_and_zero"),
        Loophole(id="zero_value", description="Zero itself is a valid array value — don't treat it as 'no value'.", related_test_case_id="zero_values"),
    ],
    comprehension_rubric=ComprehensionRubric(
        key_points=[
            "Must return TWO distinct indices, not the values themselves",
            "The two values must sum to EXACTLY the target",
            "Exactly one valid answer is guaranteed to exist",
            "The same element cannot be used twice",
        ]
    ),
)

PROBLEM.test_cases.extend(load_bulk_cases("two_sum.json"))
