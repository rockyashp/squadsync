"""
Re-export application settings from app.core.config for module backwards-compatibility.
"""

from app.core.config import Settings, get_settings, parse_cors, settings

__all__ = ["Settings", "get_settings", "settings", "parse_cors"]
