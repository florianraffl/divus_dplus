"""Pytest configuration and fixtures."""
import sys
from unittest.mock import MagicMock
from pathlib import Path

# Mock homeassistant before any imports
sys.modules['homeassistant'] = MagicMock()
sys.modules['homeassistant.config_entries'] = MagicMock()
sys.modules['homeassistant.core'] = MagicMock()
sys.modules['homeassistant.helpers'] = MagicMock()
sys.modules['homeassistant.helpers.update_coordinator'] = MagicMock()

# Add custom_components to path
custom_components_path = str(Path(__file__).parent.parent / "custom_components")
if custom_components_path not in sys.path:
    sys.path.insert(0, custom_components_path)
