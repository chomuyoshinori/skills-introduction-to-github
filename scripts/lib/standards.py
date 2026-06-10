"""standards.yaml を読み込む共通モジュール。

Blender(bpy) からも、CI の素の Python からも import できるよう、
依存は標準ライブラリのみ + PyYAML (任意) に留める。
PyYAML が無い環境では最小限の YAML サブセットパーサにフォールバックする。
"""
from __future__ import annotations

import os
from typing import Any

# config/standards.yaml への既定パス（このファイルからの相対）
_DEFAULT_PATH = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "..", "config", "standards.yaml")
)


def load_standards(path: str | None = None) -> dict[str, Any]:
    """規格定義を dict で返す。"""
    path = path or _DEFAULT_PATH
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    try:
        import yaml  # type: ignore

        return yaml.safe_load(text) or {}
    except ModuleNotFoundError:
        return _mini_yaml_parse(text)


def _mini_yaml_parse(text: str) -> dict[str, Any]:
    """PyYAML が無い時用の、本リポジトリの standards.yaml に十分な簡易パーサ。

    対応: ネストしたマッピング（2スペースインデント）、リスト(- item)、
    スカラー(int/float/bool/str)。コメントと空行は無視。
    """
    root: dict[str, Any] = {}
    # (indent, container) のスタック
    stack: list[tuple[int, Any]] = [(-1, root)]

    for raw in text.splitlines():
        line = raw.split("#", 1)[0].rstrip()
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip(" "))
        content = line.strip()

        while stack and indent <= stack[-1][0]:
            stack.pop()
        container = stack[-1][1]

        if content.startswith("- "):
            value = _coerce(content[2:].strip())
            # _PendingChild は最初の項目でリストとして親に再登録される
            if not isinstance(container, (list, _PendingChild)):
                raise ValueError(f"list item in non-list context: {raw!r}")
            container.append(value)
            continue

        key, _, rest = content.partition(":")
        key = key.strip()
        rest = rest.strip()
        if rest == "":
            # 子はマッピングかリスト。次行のインデント/内容で確定するため、
            # まずマッピングを置き、最初のリスト項目が来たら差し替える。
            child: Any = _PendingChild(container, key)
            stack.append((indent, child))
        else:
            container[key] = _coerce(rest)

    return root


class _PendingChild(dict):
    """値の種類（dict / list）が次行まで未確定な子コンテナ。

    最初に append が呼ばれたらリストとして親に再登録する。
    それ以外は dict として親に登録される。
    """

    def __init__(self, parent: Any, key: str):
        super().__init__()
        self._parent = parent
        self._key = key
        parent[key] = self
        self._as_list: list[Any] | None = None

    def append(self, value: Any) -> None:  # type: ignore[override]
        if self._as_list is None:
            self._as_list = []
            self._parent[self._key] = self._as_list
        self._as_list.append(value)


def _coerce(token: str) -> Any:
    low = token.lower()
    if low in ("true", "false"):
        return low == "true"
    if low in ("null", "~", ""):
        return None
    try:
        return int(token)
    except ValueError:
        pass
    try:
        return float(token)
    except ValueError:
        pass
    return token.strip("'\"")
