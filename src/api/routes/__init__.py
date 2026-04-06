"""API route modules."""

from src.api.routes import health
from src.api.routes import actions
from src.api.routes import config
from src.api.routes import metrics
from src.api.routes import audit
from src.api.routes import plugins
from src.api.routes import templates

__all__ = ["health", "actions", "config", "metrics", "audit", "plugins", "templates"]
