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
    id=2,
    slug="add-two-numbers",
    title="Add Two Numbers",
    difficulty="Medium",
    statement=(
        "You're given two non-empty linked lists representing two non-negative integers. "
        "The digits are stored in reverse order (least significant digit first), and each "
        "node contains a single digit. Add the two numbers and return the sum as a linked "
        "list in the same reverse-digit format."
    ),
    constraints=[
        "The number of nodes in each list is in the range [1, 100]",
        "0 <= Node.val <= 9",
        "It is guaranteed that the list represents a number that does not have leading zeros, except the number 0 itself",
    ],
    entry_point="_wrapped_add_two_numbers",
    starter_code=(
        "# l1 and l2 are ListNode objects (a definition is provided by the test harness).\n"
        "# Each represents a number with digits stored in reverse order.\n"
        "def addTwoNumbers(l1, l2):\n"
        "    pass\n"
    ),
    reference_solution=(
        "def addTwoNumbers(l1, l2):\n"
        "    dummy = ListNode()\n"
        "    cur = dummy\n"
        "    carry = 0\n"
        "    while l1 or l2 or carry:\n"
        "        v1 = l1.val if l1 else 0\n"
        "        v2 = l2.val if l2 else 0\n"
        "        total = v1 + v2 + carry\n"
        "        carry = total // 10\n"
        "        cur.next = ListNode(total % 10)\n"
        "        cur = cur.next\n"
        "        l1 = l1.next if l1 else None\n"
        "        l2 = l2.next if l2 else None\n"
        "    return dummy.next\n"
    ),
    extra_harness_helpers=(
        "class ListNode:\n"
        "    def __init__(self, val=0, next=None):\n"
        "        self.val = val\n"
        "        self.next = next\n"
        "\n"
        "def _to_linked_list(values):\n"
        "    dummy = ListNode()\n"
        "    cur = dummy\n"
        "    for v in values:\n"
        "        cur.next = ListNode(v)\n"
        "        cur = cur.next\n"
        "    return dummy.next\n"
        "\n"
        "def _to_list(node):\n"
        "    out = []\n"
        "    while node:\n"
        "        out.append(node.val)\n"
        "        node = node.next\n"
        "    return out\n"
        "\n"
        "def _wrapped_add_two_numbers(l1, l2):\n"
        "    return _to_list(addTwoNumbers(_to_linked_list(l1), _to_linked_list(l2)))\n"
    ),
    test_cases=[
        TestCase(id="basic", args={"l1": [2, 4, 3], "l2": [5, 6, 4]}, expected=[7, 0, 8]),
        TestCase(
            id="single_zero",
            args={"l1": [0], "l2": [0]},
            expected=[0],
            is_edge_case=True,
            edge_case_tag="single_zero_node",
            explanation_if_failed="Both lists are a single zero node — the classic 'is my loop condition right for the minimal case' check.",
        ),
        TestCase(
            id="final_carry_overflow",
            args={"l1": [9, 9, 9, 9, 9, 9, 9], "l2": [9, 9, 9, 9]},
            expected=[8, 9, 9, 9, 0, 0, 0, 1],
            is_edge_case=True,
            edge_case_tag="trailing_carry_and_length_mismatch",
            explanation_if_failed=(
                "Both lists have different lengths AND the final addition leaves a leftover "
                "carry that needs an entirely new node at the end. A solution that stops "
                "iterating once the longer list runs out, or that forgets to check `carry` "
                "after the loop, fails here."
            ),
        ),
        TestCase(
            id="simple_carry",
            args={"l1": [5], "l2": [5]},
            expected=[0, 1],
            is_edge_case=True,
            edge_case_tag="single_digit_carry",
            explanation_if_failed="5 + 5 = 10 — a single-digit addition that still produces a new node from the carry.",
        ),
        TestCase(id="different_lengths", args={"l1": [1, 8], "l2": [0]}, expected=[1, 8]),
    ],
    brute_force=BruteForce(
        description="Convert both linked lists fully into integers, add them with native arithmetic, then convert the sum back into a linked list.",
        complexity="O(m+n) time, but relies on the language's integer type having no size limit",
        why_insufficient=(
            "This technically works in Python since ints are arbitrary precision, but it "
            "sidesteps the point of the exercise: production languages (and most interview "
            "settings) cap native integer width, and the digit-by-digit carry technique this "
            "problem is testing doesn't generalize if you shortcut through big-int conversion."
        ),
    ),
    optimal_approach=OptimalApproach(
        description=(
            "Simulate elementary-school column addition: walk both lists simultaneously, "
            "carrying a running `carry` value, producing one output digit per step, "
            "continuing until both lists AND the carry are exhausted."
        ),
        complexity="O(max(m, n)) time, O(max(m, n)) space for the output list",
    ),
    hint_ladder=[
        HintLevel(level=1, text="How would you add two numbers by hand, digit by digit, starting from the ones place?"),
        HintLevel(level=2, text="Since digits are already stored least-significant-first, you can walk both lists directly from the head without reversing anything."),
        HintLevel(level=3, text="Keep a running carry: at each step, sum = val1 + val2 + carry, new digit = sum % 10, new carry = sum // 10."),
        HintLevel(level=4, text="Don't stop when one list runs out before the other — treat its missing digits as 0. And after both lists are exhausted, check if a carry is still left over and add one more node if so."),
    ],
    common_loopholes=[
        Loophole(id="diff_lengths", description="The two lists can have different lengths.", related_test_case_id="final_carry_overflow"),
        Loophole(id="trailing_carry", description="A leftover carry after both lists end needs one more node.", related_test_case_id="final_carry_overflow"),
        Loophole(id="bigint_shortcut", description="Converting to native ints sidesteps the actual digit-carry technique being tested.", related_test_case_id="basic"),
    ],
    comprehension_rubric=ComprehensionRubric(
        key_points=[
            "Digits are stored in REVERSE order (least significant digit first)",
            "Must track a carry across additions",
            "The two lists can be different lengths",
            "A leftover carry after both lists end requires one more node",
        ]
    ),
)

PROBLEM.test_cases.extend(load_bulk_cases("add_two_numbers.json"))
