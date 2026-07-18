"""Shared pytest fixtures and paths."""

from __future__ import annotations

import os
import sys

import pytest

# Make the package importable when running from the repo root without install.
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

FIXTURES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures")


@pytest.fixture
def fixtures_dir() -> str:
    return FIXTURES


@pytest.fixture
def projects_and_tasks_text() -> str:
    with open(os.path.join(FIXTURES, "projects-and-tasks.org"), encoding="utf-8") as fh:
        return fh.read()


@pytest.fixture
def three_projects_text() -> str:
    with open(os.path.join(FIXTURES, "three-projects.org"), encoding="utf-8") as fh:
        return fh.read()
