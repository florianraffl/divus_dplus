import pytest
import logging
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# conftest.py handles the sys.path and mocking setup
from divus_dplus.api import DivusDplusApi


# Configuration - loaded from .env file
TEST_HOST = os.getenv("TEST_HOST", "")
TEST_USERNAME = os.getenv("TEST_USERNAME", "")
TEST_PASSWORD = os.getenv("TEST_PASSWORD", "")


@pytest.fixture
def logger():
    """Create a logger for tests."""
    return logging.getLogger("test")


@pytest.fixture(scope="function")
async def api(logger):
    """Create a real API instance for integration testing."""
    api_instance = DivusDplusApi(TEST_HOST, TEST_USERNAME, TEST_PASSWORD, logger)
    yield api_instance
    # Cleanup: close the session after tests
    await api_instance._session.close()


class TestDivusDplusApi:
    """Integration test cases for DivusDplusApi class."""

    @pytest.mark.asyncio
    async def test_init(self, logger):
        """Test API initialization."""
        api = DivusDplusApi(TEST_HOST, TEST_USERNAME, TEST_PASSWORD, logger)

        assert api._base == f"http://{TEST_HOST}/"
        assert api._username == TEST_USERNAME
        assert api._password == TEST_PASSWORD
        assert api._session_id is None

        # Clean up
        await api._session.close()

    @pytest.mark.asyncio
    async def test_login(self, api):
        """Test login and session ID retrieval."""
        session_id = await api._getSessionId()

        assert session_id is not None
        assert len(session_id) > 0
        assert api._sessionId == session_id

    @pytest.mark.asyncio
    async def test_login_cached(self, api):
        """Test that session ID is cached after first login."""
        session_id1 = await api._getSessionId()
        session_id2 = await api._getSessionId()

        assert session_id1 == session_id2

    @pytest.mark.asyncio
    async def test_get_devices(self, api):
        """Test getting devices from the API."""
        devices = await api.get_devices()

        assert devices is not None
        # Add more specific assertions based on your expected data
        print(f"Found {len(devices)} devices")
        for device in devices:
            print(f"Device: {device}")

    @pytest.mark.asyncio
    async def test_get_states(self, api):
        """Test getting states for devices."""

        states = await api.get_states(list(["10790", "10788"]))

        assert states is not None
        # Add more specific assertions based on your expected data
        print(f"States: {states}")

    @pytest.mark.asyncio
    async def test_set_value(self, api):
        """Test setting value for a device."""

        await api.set_value("10790", "0")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
