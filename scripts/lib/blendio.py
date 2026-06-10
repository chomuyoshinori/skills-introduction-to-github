"""blend ファイルを安全に開く共通モジュール（bpy 必須）。

.blend にはドライバや登録ハンドラとして Python コードを埋め込める。
外部由来のファイル（PR で追加されたアセット等）を検査・レンダリングする際に
そのコードが自動実行されると任意コード実行になるため、
すべての読み込みでスクリプト自動実行を無効化する。

リポジトリ内のスクリプトが .blend を開くときは必ずこのモジュールを使うこと。
"""
from __future__ import annotations

import os


def open_blend(path: str) -> None:
    """スクリプト自動実行を無効化した上で blend を開く。"""
    import bpy

    # 環境設定とファイル単位の両方で無効化する（二重の防御）
    try:
        bpy.context.preferences.filepaths.use_scripts_auto_execute = False
    except AttributeError:
        pass  # 将来のバージョンで属性が移動しても use_scripts=False が効く
    bpy.ops.wm.open_mainfile(filepath=os.path.abspath(path), use_scripts=False)
