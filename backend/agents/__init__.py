"""Arus ADK agents — MCP-based drone command + player-facing coach.

v3 exports two pipelines:
- AUTO mode: `auto_commander.build_pipeline` (5-stage full autonomy)
- COACH mode: `coach.build_coach_pipeline` (2-stage advisor)
"""
from .auto_commander import build_pipeline as build_auto_pipeline, root_agent
from .coach import build_coach_pipeline

__all__ = ["build_auto_pipeline", "build_coach_pipeline", "root_agent"]
