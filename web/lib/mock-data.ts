import type { ChatMessage, ProblemDetail, ProblemSummary, SubmissionResult } from "./types";

/**
 * Standalone fallback data used when the FastAPI backend (http://localhost:8000)
 * is unreachable. Shape matches the real `GET /problems` / `GET /problems/{slug}`
 * contract exactly so swapping in the real backend later is a no-op for the UI.
 *
 * This lets the tutor UI be built, viewed, and reviewed before the backend team
 * finishes their side.
 */

export const MOCK_PROBLEM_SUMMARIES: ProblemSummary[] = [
  { slug: "two-sum", title: "Two Sum", difficulty: "easy" },
  { slug: "valid-parentheses", title: "Valid Parentheses", difficulty: "easy" },
  { slug: "binary-search", title: "Binary Search", difficulty: "medium" },
];

export const MOCK_PROBLEM_DETAILS: Record<string, ProblemDetail> = {
  "two-sum": {
    slug: "two-sum",
    title: "Two Sum",
    difficulty: "easy",
    language: "python",
    statement:
      "You're given a list of integers and a target value. Find the indices of the two numbers " +
      "that add up to the target. You may assume each input has exactly one valid pair, and you " +
      "can't use the same element twice.",
    constraints: [
      "2 <= nums.length <= 10^4",
      "-10^9 <= nums[i] <= 10^9",
      "Exactly one valid answer exists",
      "You may not use the same element twice",
    ],
    starter_code:
      "def two_sum(nums, target):\n" +
      "    # Return a list of the two indices whose values sum to target.\n" +
      "    pass\n",
    hint_ladder: [
      { level: 1, text: "What would you have to do to check every possible pair of numbers?" },
      { level: 2, text: "For each number, what's the one other value you actually need to find?" },
      { level: 3, text: "Could a hash map let you check 'have I seen the complement?' in O(1)?" },
      { level: 4, text: "Store each number's index as you scan; look up target - num before inserting." },
    ],
    test_cases: [
      { id: "tc-1", description: "nums=[2,7,11,15], target=9", is_edge_case: false },
      { id: "tc-2", description: "nums=[3,2,4], target=6", is_edge_case: false },
      {
        id: "tc-3",
        description: "duplicate values summing to target",
        is_edge_case: true,
        edge_case_tag: "duplicate_values",
      },
    ],
    brute_force: {
      description: "Check every pair of indices with a nested loop and test if they sum to target.",
      complexity: "O(n^2) time, O(1) space",
    },
    optimal_approach: {
      description:
        "Walk the array once, keeping a hash map of value -> index seen so far; at each step check " +
        "whether target - nums[i] is already in the map.",
      complexity: "O(n) time, O(n) space",
    },
  },
  "valid-parentheses": {
    slug: "valid-parentheses",
    title: "Valid Parentheses",
    difficulty: "easy",
    language: "python",
    statement:
      "Given a string containing just the characters '(', ')', '{', '}', '[' and ']', determine if " +
      "the input is valid. Brackets must close in the correct order, and every opening bracket must " +
      "have a matching closing bracket of the same type.",
    constraints: [
      "1 <= s.length <= 10^4",
      "s consists only of bracket characters '()[]{}'",
    ],
    starter_code:
      "def is_valid(s):\n" +
      "    # Return True if the brackets in s are balanced and properly nested.\n" +
      "    pass\n",
    hint_ladder: [
      { level: 1, text: "What order do closing brackets need to arrive in, relative to opens?" },
      { level: 2, text: "Which data structure naturally gives you 'most recently opened, first closed'?" },
      { level: 3, text: "Push opens onto a stack; on a close, pop and check it matches." },
      { level: 4, text: "Don't forget: an empty stack at the end (or a pop on empty) both matter." },
    ],
    test_cases: [
      { id: "tc-1", description: "s = '()[]{}'", is_edge_case: false },
      { id: "tc-2", description: "s = '(]'", is_edge_case: false },
      {
        id: "tc-3",
        description: "unmatched trailing open bracket, e.g. '([)'",
        is_edge_case: true,
        edge_case_tag: "unmatched_close_on_nonempty_stack",
      },
    ],
    brute_force: {
      description: "Repeatedly scan the string removing any adjacent matching pair until no change occurs.",
      complexity: "O(n^2) time worst case, O(n) space",
    },
    optimal_approach: {
      description: "Single pass with an explicit stack, pushing opens and matching/popping on closes.",
      complexity: "O(n) time, O(n) space",
    },
  },
  "binary-search": {
    slug: "binary-search",
    title: "Binary Search",
    difficulty: "medium",
    language: "python",
    statement:
      "Given a sorted array of distinct integers and a target value, return the index of target if " +
      "it exists in the array, otherwise return -1. Your solution must run faster than checking every " +
      "element one at a time.",
    constraints: [
      "1 <= nums.length <= 10^4",
      "nums is sorted in strictly ascending order",
      "-10^4 <= nums[i], target <= 10^4",
    ],
    starter_code:
      "def search(nums, target):\n" +
      "    # Return the index of target in nums, or -1 if it isn't present.\n" +
      "    pass\n",
    hint_ladder: [
      { level: 1, text: "The array is sorted. Does that let you rule out half of it after one check?" },
      { level: 2, text: "What should you compare the target against to decide which half to keep?" },
      { level: 3, text: "Track a low/high pointer pair and repeatedly narrow to the midpoint." },
      { level: 4, text: "Watch the loop condition: low <= high, and update low/high to mid +/- 1, not mid." },
    ],
    test_cases: [
      { id: "tc-1", description: "nums=[-1,0,3,5,9,12], target=9", is_edge_case: false },
      { id: "tc-2", description: "nums=[-1,0,3,5,9,12], target=2", is_edge_case: false },
      {
        id: "tc-3",
        description: "target equal to the first or last element",
        is_edge_case: true,
        edge_case_tag: "boundary_index",
      },
    ],
    brute_force: {
      description: "Scan every element left to right until target is found.",
      complexity: "O(n) time, O(1) space",
    },
    optimal_approach: {
      description: "Classic binary search: repeatedly compare target to the midpoint and halve the search range.",
      complexity: "O(log n) time, O(1) space",
    },
  },
};

export const DEFAULT_MOCK_SLUG = "two-sum";

/**
 * Placeholder transcript shown in the ChatPanel before the LiveKit agent
 * worker exists. Once voice is wired up (M7), these are replaced by real
 * streamed messages published over the room's data channel / transcription.
 */
export const PLACEHOLDER_CHAT_MESSAGES: ChatMessage[] = [
  {
    id: "msg-1",
    role: "tutor",
    text:
      "Let's start with the problem in your own words. What is this problem asking you to find, " +
      "and what do you get to assume about the input?",
    timestamp: "example",
  },
  {
    id: "msg-2",
    role: "user",
    text:
      "I need to find two numbers in the list that add up to the target, and return their indices. " +
      "There's always exactly one answer.",
    timestamp: "example",
  },
];

/**
 * Sample populated result, used only for local layout preview in dev (see the
 * "Preview sample result" toggle on the tutor page). Shape matches exactly
 * what the agent worker will eventually publish after a real Piston run.
 */
export const SAMPLE_SUBMISSION_RESULT: SubmissionResult = {
  submittedAt: new Date().toISOString(),
  allPassed: false,
  cases: [
    { id: "tc-1", label: "nums=[2,7,11,15], target=9", status: "pass" },
    { id: "tc-2", label: "nums=[3,2,4], target=6", status: "pass" },
    {
      id: "tc-3",
      label: "duplicate values summing to target",
      status: "fail",
      isEdgeCase: true,
      message: "Expected [0, 1] but got [1, 1] — you matched an element with itself.",
    },
  ],
};
