import pytest

from app.services.coding_author import materialize_coding_problem
from tests.conftest import _AUTHORED_PROBLEM


def test_reference_solution_supplies_expected_output():
    problem = materialize_coding_problem(_AUTHORED_PROBLEM, "medium")
    visible = [case for case in problem.tests if not case.hidden]
    assert problem.difficulty == "medium"
    assert problem.slug.startswith("authored-")
    assert visible[0].expected == "3"
    assert visible[1].expected == "30"
    assert sum(case.hidden for case in problem.tests) == 2
    assert "print(a + b)" not in problem.starters["python"]


def test_reference_that_touches_the_system_is_rejected():
    spec = {**_AUTHORED_PROBLEM, "reference_python": "import os\nos.system('echo no')\n"}
    with pytest.raises(ValueError, match="disallowed"):
        materialize_coding_problem(spec, "easy")
