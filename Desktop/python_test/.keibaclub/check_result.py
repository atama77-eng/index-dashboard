import sqlite3
from pathlib import Path

DB = Path(__file__).parent / "keiba_club.db"
with sqlite3.connect(str(DB)) as conn:
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT number, name, result_position, place_odds, body_weight, body_weight_change "
        "FROM horses WHERE race_id=4 ORDER BY result_position, number"
    ).fetchall()
    for r in rows:
        pos = r["result_position"]
        label = "除外" if pos == 0 else f"{pos}着"
        po = f"複勝{r['place_odds']:.2f}" if r["place_odds"] else "-"
        bwc = f"{r['body_weight_change']:+d}" if r["body_weight_change"] is not None else "?"
        print(f"{label:4s} 馬番{r['number']:2d} {r['name']:16s} {r['body_weight']}kg({bwc}) {po}")
