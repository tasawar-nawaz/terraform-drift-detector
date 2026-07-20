from __future__ import annotations

from typing import Any

from drift_detector.model.resources import AttributeDiff


def _normalize_scalar(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value
    if isinstance(value, str):
        return value.strip()
    return value


def _normalize_list(items: list[Any]) -> list[Any]:
    normalized = [_normalize_value(x) for x in items]
    try:
        return sorted(normalized, key=lambda x: repr(x))
    except TypeError:
        return normalized


def _normalize_value(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: _normalize_value(v) for k, v in sorted(value.items())}
    if isinstance(value, list):
        return _normalize_list(value)
    return _normalize_scalar(value)


def deep_diff(
    expected: dict[str, Any],
    actual: dict[str, Any],
    prefix: str = "",
) -> list[AttributeDiff]:
    diffs: list[AttributeDiff] = []
    keys = sorted(set(expected.keys()) | set(actual.keys()))
    for key in keys:
        path = f"{prefix}.{key}" if prefix else key
        ev = expected.get(key)
        av = actual.get(key)
        if key not in expected:
            diffs.append(AttributeDiff(path=path, expected=None, actual=av))
            continue
        if key not in actual:
            diffs.append(AttributeDiff(path=path, expected=ev, actual=None))
            continue
        if isinstance(ev, dict) and isinstance(av, dict):
            diffs.extend(deep_diff(ev, av, path))
            continue
        nev = _normalize_value(ev)
        nav = _normalize_value(av)
        if nev != nav:
            diffs.append(AttributeDiff(path=path, expected=ev, actual=av))
    return diffs


def tag_diff(
    expected: dict[str, str],
    actual: dict[str, str],
) -> list[AttributeDiff]:
    diffs: list[AttributeDiff] = []
    keys = sorted(set(expected.keys()) | set(actual.keys()))
    for key in keys:
        ev = expected.get(key)
        av = actual.get(key)
        if ev != av:
            diffs.append(AttributeDiff(path=f"tags.{key}", expected=ev, actual=av))
    return diffs
