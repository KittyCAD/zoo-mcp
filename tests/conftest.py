from pathlib import Path

import pytest


@pytest.fixture
def cube_kcl():
    test_file = Path(__file__).parent / "data" / "cube.kcl"
    yield f"{test_file.resolve()}"


@pytest.fixture
def cube_stl():
    test_file = Path(__file__).parent / "data" / "cube.stl"
    yield f"{test_file.resolve()}"


@pytest.fixture
def empty_kcl():
    test_file = Path(__file__).parent / "data" / "empty.kcl"
    yield f"{test_file.resolve()}"


@pytest.fixture
def empty_step():
    test_file = Path(__file__).parent / "data" / "empty.step"
    yield f"{test_file.resolve()}"


@pytest.fixture
def kcl_project():
    project_path = Path(__file__).parent / "data" / "test_kcl_project"
    yield f"{project_path.resolve()}"


@pytest.fixture
def box_with_linter_errors():
    test_file = Path(__file__).parent / "data" / "box_with_linter_errors.kcl"
    yield f"{test_file.resolve()}"


@pytest.fixture
def cube2_step_uppercase():
    """Fixture for a STEP file with uppercase extension to test case insensitivity."""
    test_file = Path(__file__).parent / "data" / "cube2.STEP"
    yield f"{test_file.resolve()}"
