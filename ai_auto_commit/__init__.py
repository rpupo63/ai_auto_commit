"""AI Auto Commit - AI-powered git commit and push tool."""

import warnings

# Suppress Pydantic V1 compatibility warning from langchain-core on Python 3.14+
warnings.filterwarnings("ignore", message="Core Pydantic V1")

from .ai_auto_commit import auto_commit_and_push
from .api_client import init
from .models import get_all_providers, get_default_model, set_default_model

__all__ = ["auto_commit_and_push", "init", "get_all_providers", "get_default_model", "set_default_model"]

