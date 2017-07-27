import pytest
from tempfile import TemporaryDirectory


@pytest.fixture
def tempdirpath():
    with TemporaryDirectory() as tmpdir:
        yield tmpdir
