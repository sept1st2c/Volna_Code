from problems._authored import load_authored_problem
from problems._bulk import load_bulk_cases

PROBLEM = load_authored_problem("add_two_numbers.json")
PROBLEM.test_cases.extend(load_bulk_cases("add_two_numbers.json"))
