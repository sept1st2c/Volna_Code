from problems._authored import load_authored_problem
from problems._bulk import load_bulk_cases

PROBLEM = load_authored_problem("median_of_two_sorted_arrays.json")
PROBLEM.test_cases.extend(load_bulk_cases("median_of_two_sorted_arrays.json"))
