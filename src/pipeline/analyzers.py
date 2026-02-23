from __future__ import annotations

import importlib
from typing import Any

from pipeline.config import AnalyzerConfig
from pipeline.types import Analyzer


def load_analyzer(analyzer_config: AnalyzerConfig) -> Analyzer:
    module = importlib.import_module(analyzer_config.module)
    analyzer_cls = getattr(module, analyzer_config.class_name, None)
    if analyzer_cls is None:
        raise RuntimeError(
            f"Analyzer class '{analyzer_config.class_name}' was not found in module '{analyzer_config.module}'."
        )

    instance = analyzer_cls(**dict(analyzer_config.settings))
    if not isinstance(instance, Analyzer):
        raise TypeError(
            f"Analyzer '{analyzer_config.module}.{analyzer_config.class_name}' does not satisfy the Analyzer protocol."
        )
    return instance

