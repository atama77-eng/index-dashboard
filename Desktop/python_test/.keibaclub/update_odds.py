import sqlite3
from pathlib import Path

DB = Path(__file__).parent / "keiba_club.db"

rows = [
    (10.1,   5,  1.75, "ダノンデサイル",        1),
    ( 7.9,   4,  2.55, "ミュージアムマイル",    2),
    (189.1, 17, 24.90, "シュガークン",          3),
    ( 56.2,  9,  8.00, "ミクニインスパイア",    4),
    (  1.8,  1,  1.45, "クロワデュノール",      5),
    ( 39.0,  7,  6.00, "ビザンチンドリーム",    6),
    (255.6, 18, 30.00, "ファミリータイム",      7),
    ( 60.1, 10,  7.50, "タガノデュード",        8),
    ( 52.9,  8,  6.95, "コスモキュランダ",      9),
    (156.9, 15, 21.05, "ジューンテイク",       10),
    ( 80.6, 12, 11.95, "シンエンペラー",       11),
    (104.7, 13, 11.75, "マイネルエンペラー",   12),
    ( 71.2, 11,  8.40, "シェイクユアハート",   13),
    (125.0, 14, 16.45, "スティンガーグラス",   14),
    ( 18.5,  6,  4.35, "マイユニバース",       15),
    (  6.4,  2,  2.40, "メイショウタバル",     16),
    (  7.7,  3,  2.95, "レガレイラ",           17),
    (175.1, 16, 26.65, "ミステリーウェイ",     18),
]

with sqlite3.connect(str(DB)) as conn:
    for odds, pop, place_odds, name, number in rows:
        conn.execute(
            "UPDATE horses SET odds=?, popularity=?, place_odds=?, name=? WHERE race_id=3 AND number=?",
            (odds, pop, place_odds, name, number),
        )
    print(f"Updated {conn.total_changes} rows")
