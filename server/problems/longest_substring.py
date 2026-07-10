from problems._authored import load_authored_problem
from problems._bulk import load_bulk_cases

PROBLEM = load_authored_problem("longest_substring_without_repeating_characters.json")
PROBLEM.test_cases.extend(load_bulk_cases("longest_substring_without_repeating_characters.json"))
