"""Agent core package exposing main entry points."""

import sys
import types


def _ensure_email_validator():
    try:
        import email_validator  # type: ignore # noqa: F401
        return
    except ImportError:
        module = types.ModuleType("email_validator")

        class EmailNotValidError(ValueError):
            """Fallback exception mirroring the optional dependency."""

        def validate_email(email, *_, **__):
            if "@" not in email:
                raise EmailNotValidError("Invalid email format")
            return types.SimpleNamespace(email=email, original_email=email)

        module.EmailNotValidError = EmailNotValidError
        module.validate_email = validate_email
        sys.modules["email_validator"] = module


_ensure_email_validator()

from .agent import app as agent_app
from .integrated_agent import IntegratedCoffeeAgent
from .visualization_agent_v2 import CoffeeBrewVisualizationAgent

__all__ = [
    "agent_app",
    "IntegratedCoffeeAgent",
    "CoffeeBrewVisualizationAgent",
]
