"""Tastee core: the taste layer as a library. JSON in, JSON out.

The deterministic engine (gate, learn) lives in scripts/ so the v0.1 Claude
plug-in keeps working unchanged. This package wraps it with one stable,
versioned interface that the MCP server, REST API and SDKs all call.

    from tastee_core import profile_from_folder, check, learn, critique
"""
from .profile import Profile, profile_from_folder, profile_from_dict, profile_from_samples
from .engine import check, learn, backtest
from .critique import critique, AXES, CHECKABLE, TASTE

__version__ = "0.4.1"
__all__ = ["Profile", "profile_from_folder", "profile_from_dict", "profile_from_samples",
           "check", "learn", "backtest", "critique", "AXES", "CHECKABLE", "TASTE", "__version__"]
