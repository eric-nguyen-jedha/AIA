import pytest
from unittest.mock import MagicMock

@pytest.fixture
def mock_ti():
    """Fixture pour mocker le TaskInstance (XCom)."""
    ti = MagicMock()
    yield ti
