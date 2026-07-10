from problems._authored import load_authored_problem
from problems._bulk import load_bulk_cases

PROBLEM = load_authored_problem("two_sum.json")
PROBLEM.test_cases.extend(load_bulk_cases("two_sum.json"))
