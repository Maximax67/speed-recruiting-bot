"""
Dependency Injection Container
================================
Single place that constructs and owns all service singletons.
Handlers receive services via aiogram's dependency injection middleware.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from src.config import Settings
from src.services.scheduler import SchedulerService
from src.services.visualizer import VisualizerService


@dataclass(frozen=True)
class Container:
    settings: Settings
    scheduler: SchedulerService = field(default_factory=SchedulerService)
    visualizer: VisualizerService = field(default_factory=VisualizerService)


def build_container(settings: Settings) -> Container:
    return Container(settings=settings)
