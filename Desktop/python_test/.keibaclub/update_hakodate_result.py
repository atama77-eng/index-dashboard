import sqlite3
from pathlib import Path

DB = Path(__file__).parent / "keiba_club.db"

# 函館スプリントS (race_id=4) 確定結果
# (result_position, place_odds_actual, body_weight, body_weight_change, number)
# 複勝払戻: 7→270円, 10→220円, 3→160円
# 除外: 9番クラスペディア → result_position=0
results = [
    (11, None,  448, -12,  1),   # モズナナスター
    ( 4, None,  478,  +2,  2),   # ダノンマッキンリー
    ( 3, 1.60,  510,  -6,  3),   # レイピア
    ( 5, None,  474,   0,  4),   # カルプスペルシュ
    ( 8, None,  522,   0,  5),   # ジョーメッドヴィン
    ( 6, None,  506, -14,  6),   # ウイングレイテスト
    ( 1, 2.70,  458,  +2,  7),   # ピューロマジック
    ( 7, None,  480,  -4,  8),   # ポッドベイダー
    ( 0, None,  526,  -6,  9),   # クラスペディア（除外）
    ( 2, 2.20,  474,  -2, 10),   # エーティーマクフィ
    (10, None,  526,  +4, 11),   # マルガイインビンシブルパパ
    (12, None,  498,  -2, 12),   # ルシード
    ( 9, None,  438,  -8, 13),   # シュタールヴィント
]

with sqlite3.connect(str(DB)) as conn:
    for pos, place_odds, bw, bw_change, number in results:
        conn.execute(
            """UPDATE horses
               SET result_position=?, place_odds=?, body_weight=?, body_weight_change=?
               WHERE race_id=4 AND number=?""",
            (pos, place_odds, bw, bw_change, number),
        )
    print(f"Updated {conn.total_changes} rows")
