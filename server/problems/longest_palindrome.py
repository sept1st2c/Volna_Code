from problems._authored import load_authored_problem
from problems._bulk import load_bulk_cases

PROBLEM = load_authored_problem("longest_palindromic_substring.json")
PROBLEM.test_cases.extend(load_bulk_cases("longest_palindromic_substring.json"))
