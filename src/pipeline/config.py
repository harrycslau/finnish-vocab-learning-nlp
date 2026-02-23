from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping


@dataclass(frozen=True)
class LanguageConfig:
    short_code: str
    locale: str
    lookup_table: str
    rank_table: str


@dataclass(frozen=True)
class AnalyzerConfig:
    module: str
    class_name: str
    settings: Mapping[str, Any]


@dataclass(frozen=True)
class PathConfig:
    freq_list: Path
    output_dir: Path


@dataclass(frozen=True)
class OutputNameConfig:
    lemma_with_limit: str
    lemma_default: str
    rank_with_limit: str
    rank_default: str
    sqlite_default: str


@dataclass(frozen=True)
class PipelineConfig:
    base_dir: Path
    language: LanguageConfig
    analyzer: AnalyzerConfig
    paths: PathConfig
    output_names: OutputNameConfig
    defaults: Mapping[str, Any]

    def lemma_output_path(self, limit: int | None) -> Path:
        template = (
            self.output_names.lemma_with_limit
            if limit is not None
            else self.output_names.lemma_default
        )
        filename = template.format(short_code=self.language.short_code, limit=limit)
        return self.paths.output_dir / filename

    def rank_output_path(self, limit: int | None) -> Path:
        template = (
            self.output_names.rank_with_limit
            if limit is not None
            else self.output_names.rank_default
        )
        filename = template.format(short_code=self.language.short_code, limit=limit)
        return self.paths.output_dir / filename

    def sqlite_output_path(self) -> Path:
        filename = self.output_names.sqlite_default.format(
            short_code=self.language.short_code, locale=self.language.locale
        )
        return self.paths.output_dir / filename

    def resolve_default_path(self, key: str) -> Path | None:
        value = self.defaults.get(key)
        if not isinstance(value, str) or not value.strip():
            return None
        return _resolve_path(value.strip(), self.base_dir)


def _as_mapping(value: Any, key: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"Config field '{key}' must be a mapping.")
    return value


def _as_non_empty_str(value: Any, key: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Config field '{key}' must be a non-empty string.")
    return value.strip()


def _resolve_path(value: str, base_dir: Path) -> Path:
    path = Path(value)
    if not path.is_absolute():
        path = (base_dir / path).resolve()
    return path


def load_pipeline_config(config_path: str | Path) -> PipelineConfig:
    config_file = Path(config_path).resolve()
    if not config_file.exists():
        raise FileNotFoundError(f"Config file not found: {config_file}")

    try:
        import yaml
    except ImportError as exc:
        raise RuntimeError("PyYAML is required to load YAML configs. Install with: pip install pyyaml") from exc

    with config_file.open("r", encoding="utf-8") as fh:
        raw = yaml.safe_load(fh) or {}

    root = _as_mapping(raw, "root")
    base_dir = config_file.parent

    language_raw = _as_mapping(root.get("language"), "language")
    locale = _as_non_empty_str(language_raw.get("locale"), "language.locale")
    language = LanguageConfig(
        short_code=_as_non_empty_str(language_raw.get("short_code"), "language.short_code"),
        locale=locale,
        lookup_table=_as_non_empty_str(
            language_raw.get("lookup_table", f"{locale}_lemma_lookup"),
            "language.lookup_table",
        ),
        rank_table=_as_non_empty_str(
            language_raw.get("rank_table", f"{locale}_lemma_rank"),
            "language.rank_table",
        ),
    )

    analyzer_raw = _as_mapping(root.get("analyzer"), "analyzer")
    settings = analyzer_raw.get("settings", {})
    if settings is None:
        settings = {}
    settings = _as_mapping(settings, "analyzer.settings")
    analyzer = AnalyzerConfig(
        module=_as_non_empty_str(analyzer_raw.get("module"), "analyzer.module"),
        class_name=_as_non_empty_str(analyzer_raw.get("class"), "analyzer.class"),
        settings=settings,
    )

    paths_raw = _as_mapping(root.get("paths"), "paths")
    freq_list = _resolve_path(
        _as_non_empty_str(paths_raw.get("freq_list"), "paths.freq_list"),
        base_dir,
    )
    output_dir = _resolve_path(
        _as_non_empty_str(paths_raw.get("output_dir"), "paths.output_dir"),
        base_dir,
    )
    if not freq_list.exists():
        raise FileNotFoundError(f"Configured freq list does not exist: {freq_list}")
    if not freq_list.is_file():
        raise ValueError(f"Configured freq list is not a file: {freq_list}")

    paths = PathConfig(freq_list=freq_list, output_dir=output_dir)

    output_raw = _as_mapping(root.get("output_names", {}), "output_names")
    output_names = OutputNameConfig(
        lemma_with_limit=_as_non_empty_str(
            output_raw.get("lemma_with_limit", "{short_code}_{limit}_lemmas.csv"),
            "output_names.lemma_with_limit",
        ),
        lemma_default=_as_non_empty_str(
            output_raw.get("lemma_default", "{short_code}_100k_lemmas.csv"),
            "output_names.lemma_default",
        ),
        rank_with_limit=_as_non_empty_str(
            output_raw.get("rank_with_limit", "{short_code}_{limit}_lemmas_rank.csv"),
            "output_names.rank_with_limit",
        ),
        rank_default=_as_non_empty_str(
            output_raw.get("rank_default", "{short_code}_lemmas_rank.csv"),
            "output_names.rank_default",
        ),
        sqlite_default=_as_non_empty_str(
            output_raw.get("sqlite_default", "{locale}.sqlite"),
            "output_names.sqlite_default",
        ),
    )

    defaults_raw = root.get("defaults", {})
    if defaults_raw is None:
        defaults_raw = {}
    defaults = _as_mapping(defaults_raw, "defaults")

    return PipelineConfig(
        base_dir=base_dir,
        language=language,
        analyzer=analyzer,
        paths=paths,
        output_names=output_names,
        defaults=defaults,
    )
