from __future__ import annotations

import html
import os
import secrets as _secrets
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse


APP_NAME = "遶ｶ鬥ｬ蛟ｶ讌ｽ驛ｨ"
SECRET_TOKEN = os.environ.get("SECRET_TOKEN", "")
_SESSION_NONCE = _secrets.token_hex(16)
_SESSION_COOKIE = "kc_auth"
TARGET_RACE_DATE = "2026-06-07"
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "keiba_club.db"
STATIC_DIR = BASE_DIR / "static"


@dataclass(frozen=True)
class HorsePrediction:
    horse: dict[str, Any]
    score: float
    win_probability: float
    place_probability: float
    expected_value: float
    notes: list[str]


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def initialize_database() -> None:
    with connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS races (
                id INTEGER PRIMARY KEY,
                race_date TEXT NOT NULL,
                venue TEXT NOT NULL,
                race_no INTEGER NOT NULL,
                title TEXT NOT NULL,
                grade TEXT NOT NULL,
                distance INTEGER NOT NULL,
                surface TEXT NOT NULL,
                going TEXT NOT NULL,
                start_time TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS horses (
                id INTEGER PRIMARY KEY,
                race_id INTEGER NOT NULL,
                gate INTEGER NOT NULL,
                number INTEGER NOT NULL,
                name TEXT NOT NULL,
                sex_age TEXT NOT NULL,
                jockey TEXT NOT NULL,
                trainer TEXT NOT NULL,
                weight REAL NOT NULL,
                odds REAL NOT NULL,
                popularity INTEGER NOT NULL,
                last3f REAL NOT NULL,
                avg_finish REAL NOT NULL,
                distance_fit INTEGER NOT NULL,
                going_fit INTEGER NOT NULL,
                course_fit INTEGER NOT NULL,
                days_since_last INTEGER NOT NULL,
                result_position INTEGER,
                FOREIGN KEY (race_id) REFERENCES races(id)
            );

            CREATE TABLE IF NOT EXISTS bets (
                id INTEGER PRIMARY KEY,
                race_id INTEGER NOT NULL,
                horse_id INTEGER NOT NULL,
                bet_type TEXT NOT NULL,
                stake INTEGER NOT NULL,
                payout INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                FOREIGN KEY (race_id) REFERENCES races(id),
                FOREIGN KEY (horse_id) REFERENCES horses(id)
            );
            """
        )
        # 譁ｰ繧ｫ繝ｩ繝繧偵∋縺咲ｭ峨↓霑ｽ蜉・域里蟄魯B縺ｸ縺ｮ蠕梧婿莠呈鋤繝槭う繧ｰ繝ｬ繝ｼ繧ｷ繝ｧ繝ｳ・・        existing_h = {r[1] for r in conn.execute("PRAGMA table_info(horses)")}
        for col, defn in [
            ("body_weight",       "INTEGER"),
            ("body_weight_change","INTEGER"),
            ("running_style",     "INTEGER"),
            ("blinker",           "INTEGER NOT NULL DEFAULT 0"),
            ("place_odds",        "REAL"),
        ]:
            if col not in existing_h:
                conn.execute(f"ALTER TABLE horses ADD COLUMN {col} {defn}")
        existing_r = {r[1] for r in conn.execute("PRAGMA table_info(races)")}
        for col, defn in [
            ("pace_bias", "TEXT NOT NULL DEFAULT 'even'"),
            ("draw_bias", "TEXT NOT NULL DEFAULT 'even'"),
        ]:
            if col not in existing_r:
                conn.execute(f"ALTER TABLE races ADD COLUMN {col} {defn}")

        row = conn.execute("SELECT race_date, title FROM races ORDER BY id LIMIT 1").fetchone()
        if not row or row["race_date"] != TARGET_RACE_DATE or row["title"] != "螳臥伐險伜ｿｵ":
            conn.execute("DELETE FROM bets")
            conn.execute("DELETE FROM horses")
            conn.execute("DELETE FROM races")
            seed_database(conn)

        seed_meguro_kinen_if_missing(conn)

        for entry in RACE_REGISTRY:
            seed_race_if_missing(conn, entry)


def seed_database(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        INSERT INTO races
        (id, race_date, venue, race_no, title, grade, distance, surface, going, start_time)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (1, TARGET_RACE_DATE, "譚ｱ莠ｬ", 11, "螳臥伐險伜ｿｵ", "G竇", 1600, "闃・, "譛ｪ螳・, "15:40"),
    )
    conn.executemany(
        """
        INSERT INTO horses
        (race_id, gate, number, name, sex_age, jockey, trainer, weight, odds, popularity,
         last3f, avg_finish, distance_fit, going_fit, course_fit, days_since_last, result_position)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        sample_horses(),
    )
    conn.executemany(
        """
        INSERT INTO bets
        (race_id, horse_id, bet_type, stake, payout, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        [
            (1, 14, "蜊伜享", 1000, 0, datetime.now().isoformat(timespec="seconds")),
            (1, 17, "隍・享", 1000, 0, datetime.now().isoformat(timespec="seconds")),
            (1, 9, "隍・享", 1000, 0, datetime.now().isoformat(timespec="seconds")),
        ],
    )


def seed_meguro_kinen_if_missing(conn: sqlite3.Connection) -> None:
    exists = conn.execute("SELECT 1 FROM races WHERE id = 2").fetchone()
    if exists:
        return
    conn.execute(
        """
        INSERT INTO races
        (id, race_date, venue, race_no, title, grade, distance, surface, going, start_time)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (2, "2026-05-31", "譚ｱ莠ｬ", 12, "逶ｮ鮟定ｨ伜ｿｵ", "G竇｡", 2500, "闃・, "濶ｯ", "邨ゆｺ・),
    )
    conn.executemany(
        """
        INSERT INTO horses
        (race_id, gate, number, name, sex_age, jockey, trainer, weight, odds, popularity,
         last3f, avg_finish, distance_fit, going_fit, course_fit, days_since_last, result_position)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        meguro_kinen_horses(),
    )


def seed_race_if_missing(conn: sqlite3.Connection, entry: dict) -> None:
    """RACE_REGISTRY 縺ｮ繧ｨ繝ｳ繝医Μ繧・DB 縺ｫ縺ｹ縺咲ｭ画兜蜈･縺吶ｋ縲・""
    race = entry["race"]
    if conn.execute("SELECT 1 FROM races WHERE id = ?", (race["id"],)).fetchone():
        return
    conn.execute(
        """
        INSERT INTO races
        (id, race_date, venue, race_no, title, grade, distance, surface, going, start_time, pace_bias, draw_bias)
        VALUES (:id, :race_date, :venue, :race_no, :title, :grade, :distance, :surface, :going,
                :start_time, :pace_bias, :draw_bias)
        """,
        {"pace_bias": "even", "draw_bias": "even", **race},
    )
    defaults: dict[str, Any] = {
        "race_id": race["id"],
        "result_position": None, "running_style": None, "blinker": 0,
        "body_weight": None, "body_weight_change": None, "place_odds": None,
    }
    for h in entry.get("horses", []):
        conn.execute(
            """
            INSERT INTO horses
            (race_id, gate, number, name, sex_age, jockey, trainer, weight, odds, popularity,
             last3f, avg_finish, distance_fit, going_fit, course_fit, days_since_last,
             result_position, running_style, blinker, body_weight, body_weight_change, place_odds)
            VALUES (:race_id, :gate, :number, :name, :sex_age, :jockey, :trainer, :weight, :odds, :popularity,
                   :last3f, :avg_finish, :distance_fit, :going_fit, :course_fit, :days_since_last,
                   :result_position, :running_style, :blinker, :body_weight, :body_weight_change, :place_odds)
            """,
            {**defaults, **h},
        )


# 笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武
# RACE_REGISTRY 窶・騾ｱ谺｡驥崎ｳ槭Ξ繝ｼ繧ｹ縺ｮ霑ｽ蜉縺ｯ縺薙％縺縺醍ｷｨ髮・＠縺ｦ繧ｵ繝ｼ繝舌・繧貞・襍ｷ蜍輔☆繧九・#
# 霑ｽ蜉謇矩・
#   1. 荳玖ｨ倥ユ繝ｳ繝励Ξ繝ｼ繝医ｒ蜿り・↓譁ｰ縺励＞繧ｨ繝ｳ繝医Μ繧定ｿｽ險倥☆繧・#   2. 繧ｵ繝ｼ繝舌・繧貞・襍ｷ蜍輔☆繧具ｼ亥・蝗櫁ｵｷ蜍墓凾縺ｫ閾ｪ蜍輔〒DB縺ｸ謚募・縺輔ｌ繧具ｼ・#   3. 繝ｬ繝ｼ繧ｹ蠕後↓繧ｪ繝・ぜ繝ｻ逹鬆・・pace_bias 縺ｪ縺ｩ繧貞挨騾疲峩譁ｰ繧ｹ繧ｯ繝ｪ繝励ヨ縺ｧ蜿肴丐縺吶ｋ
#
# 鬥ｬ縺斐→縺ｮ蠢・医ヵ繧｣繝ｼ繝ｫ繝・
#   gate, number, name, sex_age, jockey, trainer
#   weight(譁､驥・, odds(蜊伜享), popularity(莠ｺ豌・
#   last3f(逶ｴ霑台ｸ翫ｊ蟷ｳ蝮・, avg_finish(逶ｴ霑醍捩鬆・ｹｳ蝮・
#   distance_fit, going_fit, course_fit  (蜷・-100縲∵悴蜃ｺ襍ｰ=60)
#   days_since_last (蜑崎ｵｰ縺九ｉ縺ｮ譌･謨ｰ)
#
# 逵∫払蜿ｯ・亥ｾ後°繧画峩譁ｰ繧ｹ繧ｯ繝ｪ繝励ヨ縺ｧ謚募・縺励※繧ゅｈ縺・ｼ・
#   result_position, running_style, blinker, body_weight, body_weight_change, place_odds
# 笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武
RACE_REGISTRY: list[dict] = [
    # 笏笏 譚･騾ｱ莉･髯阪・繝ｬ繝ｼ繧ｹ縺ｯ莉･荳九・繝・Φ繝励Ξ繝ｼ繝医ｒ蜿り・↓霑ｽ險・笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏
    # {
    #     "race": {
    #         "id": 3,                      # 譌｢蟄・id 縺ｨ驥崎､・＠縺ｪ縺・％縺ｨ
    #         "race_date": "2026-06-14",    # 髢句ぎ譌･
    #         "venue": "譚ｱ莠ｬ",              # 髢句ぎ蝣ｴ
    #         "race_no": 11,               # 繝ｬ繝ｼ繧ｹ逡ｪ蜿ｷ
    #         "title": "繧ｨ繝励た繝繧ｫ繝・・",    # 繝ｬ繝ｼ繧ｹ蜷・    #         "grade": "G竇｢",
    #         "distance": 1800,
    #         "surface": "闃・,
    #         "going": "譛ｪ螳・,             # 蠖捺律遒ｺ螳壼ｾ後↓譖ｴ譁ｰ
    #         "start_time": "15:45",
    #         "pace_bias": "even",          # 繝ｬ繝ｼ繧ｹ蠕後↓螳滄圀縺ｮ蛯ｾ蜷代〒譖ｴ譁ｰ
    #         "draw_bias": "even",
    #     },
    #     "horses": [
    #         # 鬥ｬ譟ｱ謠蝉ｾ帛ｾ後↓霑ｽ險假ｼ井ｻ･荳九・1鬆ｭ蛻・・繧ｵ繝ｳ繝励Ν・・    #         # {
    #         #     "gate": 1, "number": 1, "name": "鬥ｬ蜷阪し繝ｳ繝励Ν",
    #         #     "sex_age": "迚｡4", "jockey": "C.繝ｫ繝｡繝ｼ繝ｫ", "trainer": "隱ｿ謨吝ｸｫ蜷・,
    #         #     "weight": 58.0, "odds": 3.5, "popularity": 1,
    #         #     "last3f": 33.8, "avg_finish": 2.5,
    #         #     "distance_fit": 85, "going_fit": 80, "course_fit": 82,
    #         #     "days_since_last": 28,
    #         # },
    #     ],
    # },
    {
        "race": {
            "id": 3,
            "race_date": "2026-06-28",
            "venue": "髦ｪ逾・,
            "race_no": 11,
            "title": "螳晏｡夊ｨ伜ｿｵ",
            "grade": "G竇",
            "distance": 2200,
            "surface": "闃・,
            "going": "譛ｪ螳・,
            "start_time": "15:40",
            "pace_bias": "even",
            "draw_bias": "even",
        },
        "horses": [
            # last3f=蜑崎ｵｰ荳翫ｊ(豬ｷ螟悶・逶ｴ霑大嵜蜀・縲∥vg_finish=逶ｴ霑・襍ｰ蟷ｳ蝮・捩鬆・            # distance_fit/going_fit/course_fit=髦ｪ逾櫁茅2200m蝓ｺ貅悶〒邂怜・
            # days_since_last=蜑崎ｵｰ縺九ｉ2026-06-28縺ｾ縺ｧ
            # odds/popularity=蜑肴律譛邨ゅが繝・ぜ縲｝lace_odds=隍・享繝ｬ繝ｳ繧ｸ荳ｭ螟ｮ蛟､
            {"gate": 1, "number": 1,  "name": "繝繝弱Φ繝・し繧､繝ｫ",    "sex_age": "迚｡5/譬・,   "jockey": "謌ｸ蟠主惆螟ｪ",   "trainer": "螳臥伐鄙比ｼ・,  "weight": 58.0, "odds":  10.1, "popularity":  5, "last3f": 34.9, "avg_finish": 3.50, "distance_fit": 75, "going_fit": 76, "course_fit": 72, "days_since_last":  84, "running_style": 2, "blinker": 0, "body_weight": 516, "body_weight_change": None, "place_odds":  1.75},
            {"gate": 1, "number": 2,  "name": "繝溘Η繝ｼ繧ｸ繧｢繝繝槭う繝ｫ","sex_age": "迚｡4/鮟帝ｹｿ", "jockey": "D.繝ｬ繝ｼ繝ｳ",   "trainer": "鬮俶浹螟ｧ霈・,  "weight": 58.0, "odds":   7.9, "popularity":  4, "last3f": 34.6, "avg_finish": 2.50, "distance_fit": 88, "going_fit": 82, "course_fit": 60, "days_since_last": 182, "running_style": 3, "blinker": 0, "body_weight": 502, "body_weight_change": None, "place_odds":  2.55},
            {"gate": 2, "number": 3,  "name": "繧ｷ繝･繧ｬ繝ｼ繧ｯ繝ｳ",      "sex_age": "迚｡5/鮟帝ｹｿ", "jockey": "蜷画搗隱荵句勧", "trainer": "貂・ｰｴ荵・ｩ・,  "weight": 58.0, "odds": 189.1, "popularity": 17, "last3f": 35.2, "avg_finish": 6.00, "distance_fit": 82, "going_fit": 75, "course_fit": 60, "days_since_last":  43, "running_style": 1, "blinker": 0, "body_weight": 518, "body_weight_change": None, "place_odds": 24.90},
            {"gate": 2, "number": 4,  "name": "繝溘け繝九う繝ｳ繧ｹ繝代う繧｢", "sex_age": "迚｡4/鮖ｿ",   "jockey": "荳ｹ蜀・･先ｬ｡",   "trainer": "譫怜ｾｹ",      "weight": 58.0, "odds":  56.2, "popularity":  9, "last3f": 35.7, "avg_finish": 1.25, "distance_fit": 70, "going_fit": 80, "course_fit": 60, "days_since_last":  92, "running_style": 2, "blinker": 0, "body_weight": 504, "body_weight_change": None, "place_odds":  8.00},
            {"gate": 3, "number": 5,  "name": "繧ｯ繝ｭ繝ｯ繝・Η繝弱・繝ｫ",  "sex_age": "迚｡4/髱帝ｹｿ", "jockey": "蛹玲搗蜿倶ｸ",   "trainer": "譁芽陸蟠・彰",  "weight": 58.0, "odds":   1.8, "popularity":  1, "last3f": 34.9, "avg_finish": 5.00, "distance_fit": 78, "going_fit": 82, "course_fit": 88, "days_since_last":  56, "running_style": 2, "blinker": 0, "body_weight": 514, "body_weight_change": None, "place_odds":  1.45},
            {"gate": 3, "number": 6,  "name": "繝薙じ繝ｳ繝√Φ繝峨Μ繝ｼ繝","sex_age": "迚｡5/譬・,   "jockey": "隘ｿ譚第ｷｳ荵・,   "trainer": "蝮ょ哨譎ｺ蠎ｷ",  "weight": 58.0, "odds":  39.0, "popularity":  7, "last3f": 34.9, "avg_finish": 3.75, "distance_fit": 78, "going_fit": 78, "course_fit": 65, "days_since_last": 134, "running_style": 3, "blinker": 0, "body_weight": None, "body_weight_change": None, "place_odds":  6.00},
            {"gate": 4, "number": 7,  "name": "繝輔ぃ繝溘Μ繝ｼ繧ｿ繧､繝",  "sex_age": "迚｡5/鮖ｿ",   "jockey": "蟷ｸ闍ｱ譏・,     "trainer": "遏ｳ蝮ょ・荳",  "weight": 58.0, "odds": 255.6, "popularity": 18, "last3f": 36.3, "avg_finish": 4.75, "distance_fit": 84, "going_fit": 76, "course_fit": 80, "days_since_last":  98, "running_style": 1, "blinker": 0, "body_weight": 482, "body_weight_change": None, "place_odds": 30.00},
            {"gate": 4, "number": 8,  "name": "繧ｿ繧ｬ繝弱ョ繝･繝ｼ繝・,    "sex_age": "迚｡5/鮖ｿ",   "jockey": "鬮俶揄蜷城ｺ・,   "trainer": "螳ｮ蠕ｹ",      "weight": 58.0, "odds":  60.1, "popularity": 10, "last3f": 35.2, "avg_finish": 3.00, "distance_fit": 68, "going_fit": 74, "course_fit": 70, "days_since_last":  56, "running_style": 3, "blinker": 0, "body_weight": 502, "body_weight_change": None, "place_odds":  7.50},
            {"gate": 5, "number": 9,  "name": "繧ｳ繧ｹ繝｢繧ｭ繝･繝ｩ繝ｳ繝",  "sex_age": "迚｡5/鮟帝ｹｿ", "jockey": "讓ｪ螻ｱ豁ｦ蜿ｲ",   "trainer": "蜉阯､螢ｫ豢･蜈ｫ", "weight": 58.0, "odds":  52.9, "popularity":  8, "last3f": 36.7, "avg_finish": 7.50, "distance_fit": 72, "going_fit": 68, "course_fit": 60, "days_since_last":  92, "running_style": 1, "blinker": 1, "body_weight": 520, "body_weight_change": None, "place_odds":  6.95},
            {"gate": 5, "number": 10, "name": "繧ｸ繝･繝ｼ繝ｳ繝・う繧ｯ",    "sex_age": "迚｡5/鮟帝ｹｿ", "jockey": "譚ｾ螻ｱ蠑伜ｹｳ",   "trainer": "豁ｦ闍ｱ譎ｺ",    "weight": 58.0, "odds": 156.9, "popularity": 15, "last3f": 34.8, "avg_finish": 4.00, "distance_fit": 88, "going_fit": 82, "course_fit": 65, "days_since_last":  63, "running_style": 1, "blinker": 0, "body_weight": 498, "body_weight_change": None, "place_odds": 21.05},
            {"gate": 6, "number": 11, "name": "繧ｷ繝ｳ繧ｨ繝ｳ繝壹Λ繝ｼ",    "sex_age": "迚｡5/譬・,   "jockey": "蝮ゆｺ慕蔵譏・,   "trainer": "遏｢菴懆患莠ｺ",  "weight": 58.0, "odds":  80.6, "popularity": 12, "last3f": 35.5, "avg_finish": 8.25, "distance_fit": 70, "going_fit": 72, "course_fit": 60, "days_since_last":  56, "running_style": 2, "blinker": 0, "body_weight": 508, "body_weight_change": None, "place_odds": 11.95},
            {"gate": 6, "number": 12, "name": "繝槭う繝阪Ν繧ｨ繝ｳ繝壹Λ繝ｼ", "sex_age": "迚｡6/鮟帝ｹｿ", "jockey": "蟾晉伐蟆・寉",   "trainer": "貂・ｰｴ荵・ｩ・,  "weight": 58.0, "odds": 104.7, "popularity": 13, "last3f": 35.3, "avg_finish": 7.50, "distance_fit": 62, "going_fit": 68, "course_fit": 68, "days_since_last":  98, "running_style": 2, "blinker": 0, "body_weight": 490, "body_weight_change": None, "place_odds": 11.75},
            {"gate": 7, "number": 13, "name": "繧ｷ繧ｧ繧､繧ｯ繝ｦ繧｢繝上・繝・,"sex_age": "迚｡6/譬・,   "jockey": "蜿､蟾晏翠豢・,   "trainer": "螳ｮ蠕ｹ",      "weight": 58.0, "odds":  71.2, "popularity": 11, "last3f": 33.5, "avg_finish": 2.00, "distance_fit": 80, "going_fit": 84, "course_fit": 65, "days_since_last": 105, "running_style": 2, "blinker": 0, "body_weight": 462, "body_weight_change": None, "place_odds":  8.40},
            {"gate": 7, "number": 14, "name": "繧ｹ繝・ぅ繝ｳ繧ｬ繝ｼ繧ｰ繝ｩ繧ｹ","sex_age": "迚｡5/鮖ｿ",   "jockey": "蟯ｩ逕ｰ譛帶擂",   "trainer": "蜿矩％蠎ｷ螟ｫ",  "weight": 58.0, "odds": 125.0, "popularity": 14, "last3f": 34.8, "avg_finish": 3.75, "distance_fit": 70, "going_fit": 80, "course_fit": 60, "days_since_last": 127, "running_style": 2, "blinker": 0, "body_weight": 484, "body_weight_change": None, "place_odds": 16.45},
            {"gate": 7, "number": 15, "name": "繝槭う繝ｦ繝九ヰ繝ｼ繧ｹ",    "sex_age": "迚｡4/鮖ｿ",   "jockey": "讓ｪ螻ｱ蜈ｸ蠑・,   "trainer": "豁ｦ蟷ｸ蝗幃ヮ",  "weight": 58.0, "odds":  18.5, "popularity":  6, "last3f": 35.0, "avg_finish": 4.25, "distance_fit": 72, "going_fit": 76, "course_fit": 60, "days_since_last":  92, "running_style": 3, "blinker": 0, "body_weight": 468, "body_weight_change": None, "place_odds":  4.35},
            {"gate": 8, "number": 16, "name": "繝｡繧､繧ｷ繝ｧ繧ｦ繧ｿ繝舌Ν",  "sex_age": "迚｡5/鮖ｿ",   "jockey": "豁ｦ雎・,       "trainer": "遏ｳ讖句ｮ・,    "weight": 58.0, "odds":   6.4, "popularity":  2, "last3f": 35.6, "avg_finish": 5.50, "distance_fit": 95, "going_fit": 86, "course_fit": 98, "days_since_last":  84, "running_style": 0, "blinker": 0, "body_weight": 500, "body_weight_change": None, "place_odds":  2.40},
            {"gate": 8, "number": 17, "name": "繝ｬ繧ｬ繝ｬ繧､繝ｩ",        "sex_age": "迚・/鮖ｿ",   "jockey": "C.繝ｫ繝｡繝ｼ繝ｫ", "trainer": "譛ｨ譚大憧荵・,  "weight": 56.0, "odds":   7.7, "popularity":  3, "last3f": 34.6, "avg_finish": 4.25, "distance_fit": 90, "going_fit": 86, "course_fit": 68, "days_since_last": 182, "running_style": 3, "blinker": 0, "body_weight": 482, "body_weight_change": None, "place_odds":  2.95},
            {"gate": 8, "number": 18, "name": "繝溘せ繝・Μ繝ｼ繧ｦ繧ｧ繧､",  "sex_age": "縺帙ｓ8/鮟帝ｹｿ","jockey": "譚ｾ譛ｬ螟ｧ霈・,   "trainer": "蟆乗棊逵滉ｹ・,  "weight": 58.0, "odds": 175.1, "popularity": 16, "last3f": 36.5, "avg_finish": 9.75, "distance_fit": 65, "going_fit": 72, "course_fit": 60, "days_since_last":  56, "running_style": 0, "blinker": 0, "body_weight": 506, "body_weight_change": None, "place_odds": 26.65},
        ],
    },
    {
        "race": {
            "id": 4,
            "race_date": "2026-06-13",
            "venue": "蜃ｽ鬢ｨ",
            "race_no": 11,
            "title": "蜃ｽ鬢ｨ繧ｹ繝励Μ繝ｳ繝医せ繝・・繧ｯ繧ｹ",
            "grade": "G竇｢",
            "distance": 1200,
            "surface": "闃・,
            "going": "遞埼㍾",
            "start_time": "15:45",
            "pace_bias": "even",
            "draw_bias": "even",
        },
        "horses": [
            # last3f=蜑崎ｵｰ荳翫ｊ(繝繝ｼ繝磯ｦｬ縺ｯ蜿り・､)縲“oing_fit=遞埼㍾驕ｩ諤ｧ縲…ourse_fit=蜃ｽ鬢ｨ闃・200m驕ｩ諤ｧ
            # 繝昴ャ繝峨・繧､繝繝ｼ(8逡ｪ)縺ｯ繝繝ｼ繝亥ｰる摩鬥ｬ縺ｮ縺溘ａ蜷・←諤ｧ繧ｹ繧ｳ繧｢繧剃ｽ弱ａ險ｭ螳・            {"gate": 1, "number": 1,  "name": "繝｢繧ｺ繝翫リ繧ｹ繧ｿ繝ｼ",           "sex_age": "迚・/譬・,   "jockey": "魄ｫ蟲ｶ蜈矩ｧｿ",   "trainer": "遏｢菴懆患莠ｺ", "weight": 55.0, "odds":  25.4, "popularity":  9, "last3f": 32.7, "avg_finish":  6.25, "distance_fit": 72, "going_fit": 74, "course_fit": 62, "days_since_last":  20, "running_style": 3, "blinker": 0, "body_weight": 460, "body_weight_change": None, "place_odds": None},
            {"gate": 2, "number": 2,  "name": "繝繝弱Φ繝槭ャ繧ｭ繝ｳ繝ｪ繝ｼ",       "sex_age": "迚｡5/鮖ｿ",   "jockey": "豎豺ｻ隰吩ｸ",   "trainer": "阯､蜴溯恭譏ｭ", "weight": 58.0, "odds":  33.2, "popularity": 11, "last3f": 32.7, "avg_finish": 11.00, "distance_fit": 58, "going_fit": 62, "course_fit": 60, "days_since_last":  42, "running_style": 3, "blinker": 0, "body_weight": 476, "body_weight_change": None, "place_odds": None},
            {"gate": 3, "number": 3,  "name": "繝ｬ繧､繝斐い",                 "sex_age": "迚｡4/鮖ｿ",   "jockey": "讓ｪ螻ｱ豁ｦ蜿ｲ",   "trainer": "荳ｭ遶ｹ蜥御ｹ・, "weight": 57.0, "odds":   4.5, "popularity":  2, "last3f": 33.4, "avg_finish":  3.25, "distance_fit": 82, "going_fit": 72, "course_fit": 65, "days_since_last":  76, "running_style": 2, "blinker": 0, "body_weight": 516, "body_weight_change": None, "place_odds": None},
            {"gate": 4, "number": 4,  "name": "繧ｫ繝ｫ繝励せ繝壹Ν繧ｷ繝･",         "sex_age": "迚・/鮖ｿ",   "jockey": "荳ｹ蜀・･先ｬ｡",   "trainer": "遏ｳ蝮ょ・荳", "weight": 55.0, "odds":   4.2, "popularity":  1, "last3f": 34.6, "avg_finish":  5.75, "distance_fit": 80, "going_fit": 72, "course_fit": 62, "days_since_last":  83, "running_style": 1, "blinker": 1, "body_weight": 474, "body_weight_change": None, "place_odds": None},
            {"gate": 4, "number": 5,  "name": "繧ｸ繝ｧ繝ｼ繝｡繝・ラ繝ｴ繧｣繝ｳ",       "sex_age": "迚｡5/譬・,   "jockey": "讓ｪ螻ｱ逅我ｺｺ",   "trainer": "貂・ｰｴ荵・ｩ・, "weight": 57.0, "odds":  32.4, "popularity": 10, "last3f": 33.4, "avg_finish":  5.75, "distance_fit": 68, "going_fit": 80, "course_fit": 62, "days_since_last":  48, "running_style": 2, "blinker": 0, "body_weight": 522, "body_weight_change": None, "place_odds": None},
            {"gate": 5, "number": 6,  "name": "繧ｦ繧､繝ｳ繧ｰ繝ｬ繧､繝・せ繝・,       "sex_age": "迚｡9/譬・,   "jockey": "譚ｾ蟯｡豁｣豬ｷ",   "trainer": "逡螻ｱ蜷牙ｮ・, "weight": 58.0, "odds":  34.2, "popularity": 12, "last3f": 34.6, "avg_finish":  6.25, "distance_fit": 72, "going_fit": 65, "course_fit": 65, "days_since_last": 105, "running_style": 1, "blinker": 1, "body_weight": 520, "body_weight_change": None, "place_odds": None},
            {"gate": 5, "number": 7,  "name": "繝斐Η繝ｼ繝ｭ繝槭ず繝・け",         "sex_age": "迚・/鮖ｿ",   "jockey": "蛹玲搗蜿倶ｸ",   "trainer": "螳臥伐鄙比ｼ・, "weight": 56.0, "odds":   6.9, "popularity":  3, "last3f": 34.5, "avg_finish": 11.75, "distance_fit": 62, "going_fit": 65, "course_fit": 62, "days_since_last":  76, "running_style": 1, "blinker": 0, "body_weight": 456, "body_weight_change": None, "place_odds": None},
            {"gate": 6, "number": 8,  "name": "繝昴ャ繝峨・繧､繝繝ｼ",           "sex_age": "迚｡4/鮖ｿ",   "jockey": "闕ｻ驥取･ｵ",     "trainer": "荳雁次菴醍ｴ", "weight": 57.0, "odds":  16.5, "popularity":  7, "last3f": 36.0, "avg_finish":  3.25, "distance_fit": 40, "going_fit": 50, "course_fit": 50, "days_since_last":  55, "running_style": 2, "blinker": 0, "body_weight": 484, "body_weight_change": None, "place_odds": None},
            {"gate": 6, "number": 9,  "name": "繧ｯ繝ｩ繧ｹ繝壹ョ繧｣繧｢",           "sex_age": "迚｡4/鮟帝ｹｿ", "jockey": "蟆丞ｴ守ｶｾ荵・,   "trainer": "豐ｳ蠍句ｮ乗ｨｹ", "weight": 57.0, "odds":  17.9, "popularity":  8, "last3f": 33.9, "avg_finish":  5.50, "distance_fit": 72, "going_fit": 74, "course_fit": 62, "days_since_last":  62, "running_style": 0, "blinker": 0, "body_weight": 532, "body_weight_change": None, "place_odds": None},
            {"gate": 7, "number": 10, "name": "繧ｨ繝ｼ繝・ぅ繝ｼ繝槭け繝輔ぅ",       "sex_age": "迚｡7/鮖ｿ",   "jockey": "蟇檎伐證・,     "trainer": "豁ｦ闍ｱ譎ｺ",   "weight": 58.0, "odds":   7.2, "popularity":  5, "last3f": 33.5, "avg_finish":  6.00, "distance_fit": 72, "going_fit": 70, "course_fit": 65, "days_since_last":  76, "running_style": 2, "blinker": 1, "body_weight": 476, "body_weight_change": None, "place_odds": None},
            {"gate": 7, "number": 11, "name": "繝槭Ν繧ｬ繧､繧､繝ｳ繝薙Φ繧ｷ繝悶Ν繝代ヱ","sex_age": "迚｡5/鮖ｿ",  "jockey": "菴舌・惠螟ｧ霈・, "trainer": "莨願陸螟ｧ螢ｫ", "weight": 58.0, "odds":   9.2, "popularity":  6, "last3f": 35.4, "avg_finish":  9.25, "distance_fit": 70, "going_fit": 65, "course_fit": 62, "days_since_last":  76, "running_style": 0, "blinker": 0, "body_weight": 522, "body_weight_change": None, "place_odds": None},
            {"gate": 8, "number": 12, "name": "繝ｫ繧ｷ繝ｼ繝・,                 "sex_age": "迚｡4/譬・,   "jockey": "讓ｪ螻ｱ蜥檎函",   "trainer": "逕ｰ蟲ｶ菫頑・", "weight": 57.0, "odds":   6.9, "popularity":  3, "last3f": 33.3, "avg_finish":  1.50, "distance_fit": 88, "going_fit": 70, "course_fit": 62, "days_since_last":  41, "running_style": 1, "blinker": 0, "body_weight": 500, "body_weight_change": None, "place_odds": None},
            {"gate": 8, "number": 13, "name": "繧ｷ繝･繧ｿ繝ｼ繝ｫ繝ｴ繧｣繝ｳ繝・,       "sex_age": "迚｡6/鮖ｿ",   "jockey": "蟯ｩ逕ｰ蠎ｷ隱",   "trainer": "遏｢菴懆患莠ｺ", "weight": 57.0, "odds":  80.6, "popularity": 13, "last3f": 32.6, "avg_finish":  9.00, "distance_fit": 60, "going_fit": 62, "course_fit": 60, "days_since_last":  13, "running_style": 3, "blinker": 1, "body_weight": 446, "body_weight_change": None, "place_odds": None},
        ],
    },
]


def sample_horses() -> list[tuple[Any, ...]]:
    # 繧ｪ繝・ぜ繝ｻ莠ｺ豌励・2026-06-06 22:27譎らせ縺ｮJRA繧ｪ繝・ぜ譖ｴ譁ｰ繧ｹ繝翫ャ繝励す繝ｧ繝・ヨ・域焔蜍募叙蠕励・螳溘ョ繝ｼ繧ｿ・峨・    # 繝ｬ繝ｼ繧ｹ逶ｴ蜑阪∪縺ｧ螟牙虚縺吶ｋ縺溘ａ縲∝ｽ捺律譛昴↓蜀榊叙蠕励＠縺ｦ荳頑嶌縺阪☆繧区Φ螳壹・    # last3f/avg_finish/distance_fit遲峨・蜃ｺ鬥ｬ陦ｨ縺ｮ蜑崎ｵｰ~4襍ｰ蜑阪ョ繝ｼ繧ｿ縺ｨ謨ｴ蜷医＠縺ｦ縺・◆縺溘ａ螟画峩縺ｪ縺励・    return [
        (1, 1, 1, "繝ｬ繝ｼ繝吶Φ繧ｹ繝・ぅ繝ｼ繝ｫ", "迚｡6", "謌ｸ蟠主惆螟ｪ", "逕ｰ荳ｭ蜊壼ｺｷ", 58.0, 8.2, 3, 34.1, 6.3, 78, 76, 84, 63, None),
        (1, 1, 2, "繝ｭ繝ｳ繧ｰ繝ｩ繝ｳ", "縺帙ｓ8", "F.繧ｴ繝ｳ繧ｵ繝ｫ繝吶せ", "蜥檎伐蜍・ｻ・, 58.0, 230.0, 17, 34.8, 15.7, 66, 68, 62, 42, None),
        (1, 2, 3, "繧ｪ繝輔ヨ繝ｬ繧､繝ｫ", "迚｡5", "闖・次譏手憶", "蜷画搗蝨ｭ蜿ｸ", 58.0, 42.9, 13, 33.9, 6.3, 82, 80, 78, 42, None),
        (1, 2, 4, "繧ｷ繝・け繧ｹ繝壹Φ繧ｹ", "迚｡5", "豁ｦ雎・, "逕ｰ荳ｭ蜊壼ｺｷ", 58.0, 24.9, 8, 34.2, 9.0, 75, 70, 76, 42, None),
        (1, 3, 5, "繧ｵ繧ｯ繝ｩ繝医ぇ繧ｸ繝･繝ｼ繝ｫ", "縺帙ｓ9", "菴舌・惠螟ｧ霈・, "蝣螳｣陦・, 58.0, 121.4, 15, 34.3, 10.0, 73, 72, 79, 105, None),
        (1, 3, 6, "繧ｹ繝・Ξ繝ｳ繝懊ャ繧ｷ繝･", "迚・", "D.繝ｬ繝ｼ繝ｳ", "螳ｮ逕ｰ謨ｬ莉・, 56.0, 9.0, 4, 34.2, 6.3, 80, 78, 82, 29, None),
        (1, 4, 7, "繧ｹ繧ｺ繝上Ο繝ｼ繝", "迚｡6", "阯､諛ｸ雋ｴ蠢・, "迚ｧ逕ｰ蜥悟ｼ･", 58.0, 25.7, 9, 33.8, 3.7, 86, 82, 75, 64, None),
        (1, 4, 8, "繧ｷ繝｣繝ｳ繝代Φ繧ｫ繝ｩ繝ｼ", "迚｡6", "蟯ｩ逕ｰ蠎ｷ隱", "逕ｰ荳ｭ蜑・, 58.0, 34.7, 11, 34.1, 7.7, 78, 76, 77, 42, None),
        (1, 5, 9, "繧ｦ繧ｩ繝ｼ繧ｿ繝ｼ繝ｪ繝偵ヨ", "迚｡5", "鬮俶揄蜷城ｺ・, "遏ｳ讖句ｮ・, 58.0, 28.4, 10, 33.7, 6.3, 89, 84, 80, 42, None),
        (1, 5, 10, "繝ｫ繧ｯ繧ｽ繝ｼ繝ｫ繧ｫ繝輔ぉ", "迚｡4", "蟯ｩ逕ｰ譛帶擂", "蝣螳｣陦・, 58.0, 70.9, 14, 34.4, 7.0, 68, 70, 72, 113, None),
        (1, 6, 11, "繝ｯ繝ｼ繝ｫ繧ｺ繧ｨ繝ｳ繝・, "迚｡5", "豢･譚第・遘", "豎豺ｻ蟄ｦ", 58.0, 20.7, 7, 33.4, 3.7, 88, 82, 86, 36, None),
        (1, 6, 12, "繧ｷ繝ｪ繧ｦ繧ｹ繧ｳ繝ｫ繝・, "迚｡5", "讓ｪ螻ｱ蜥檎函", "逕ｰ荳ｭ蜍晄丼", 58.0, 132.2, 16, 34.0, 7.7, 81, 77, 83, 36, None),
        (1, 7, 13, "繧ｻ繧､繧ｦ繝ｳ繝上・繝・せ", "迚｡7", "蟷ｸ闍ｱ譏・, "讖句哨諷惹ｻ・, 58.0, 13.8, 6, 34.7, 9.7, 72, 72, 75, 63, None),
        (1, 7, 14, "繧ｬ繧､繧｢繝輔か繝ｼ繧ｹ", "迚｡7", "讓ｪ螻ｱ豁ｦ蜿ｲ", "譚牙ｱｱ譎ｴ邏", 58.0, 2.9, 1, 33.5, 3.0, 94, 86, 91, 71, None),
        (1, 8, 15, "繝峨Λ繧ｴ繝ｳ繝悶・繧ｹ繝・, "迚｡4", "荳ｹ蜀・･先ｬ｡", "阯､驥主▼螟ｪ", 58.0, 36.9, 12, 33.6, 6.3, 86, 80, 79, 42, None),
        (1, 8, 16, "繝代Φ繧ｸ繝｣繧ｿ繝ｯ繝ｼ", "迚｡4", "譚ｾ螻ｱ蠑伜ｹｳ", "讖句哨諷惹ｻ・, 58.0, 9.5, 5, 33.9, 4.7, 82, 83, 78, 70, None),
        (1, 8, 17, "繝医Ο繝ｴ繧｡繝医・繝ｬ", "迚｡5", "C.繝ｫ繝｡繝ｼ繝ｫ", "鮖ｿ謌ｸ髮・ｸ", 58.0, 4.4, 2, 33.6, 2.0, 92, 85, 90, 29, None),
    ]


def meguro_kinen_horses() -> list[tuple[Any, ...]]:
    # 2026-05-31 譚ｱ莠ｬ12R 隨ｬ140蝗樒岼鮟定ｨ伜ｿｵ(G竇｡)繝ｻ讀懆ｨｼ逕ｨ縺ｮ螳滓命貂医∩繝ｬ繝ｼ繧ｹ縲・    # 繧ｪ繝・ぜ/莠ｺ豌・雋諡・㍾驥・鬨取焔/逹鬆・・螳滄圀縺ｮ蜃ｺ鬥ｬ陦ｨ繝ｻ邨先棡繝・・繧ｿ縺九ｉ霆｢險倥・    # last3f(逶ｴ霑台ｸ翫ｊ3F蟷ｳ蝮・繝ｻavg_finish(逶ｴ霑醍捩鬆・ｹｳ蝮・縺ｯ蜑崎ｵｰ縲・襍ｰ蜑阪・螳溽ｸｾ縺九ｉ邂怜・縲・    # distance_fit/course_fit 縺ｯ縲悟ｮ溽ｸｾ縲崎｡ｨ縺ｮ譚ｱ莠ｬ闃・400-2600m / 譚ｱ莠ｬ闃・500m縺ｮ騾夂ｮ玲・邵ｾ(1逹2逹3逹逹螟・繧・    # 0-100縺ｫ謠帷ｮ・40 + 蜉驥咲噪荳ｭ邇・60縲∵悴蜃ｺ襍ｰ縺ｯ60=荳ｭ遶・縲“oing_fit 縺ｯ濶ｯ鬥ｬ蝣ｴ諠ｳ螳壹〒蜈ｨ蝣ｴ闃昴・騾夂ｮ玲・邵ｾ繧剃ｻ｣逕ｨ縲・    # days_since_last 縺ｯ蜑崎ｵｰ譌･縺九ｉ繝ｬ繝ｼ繧ｹ蠖捺律(2026-05-31)縺ｾ縺ｧ縺ｮ螳滓律謨ｰ縲・    return [
        (2, 1, 1, "繧｢繝槭く繝・, "迚｡4", "豁ｦ雎・, "讖狗伐螳憺聞", 56.0, 14.4, 6, 34.8, 3.6, 62, 74, 60, 50, 9),
        (2, 2, 2, "繧ｷ繝ｧ繧ｦ繝翫Φ繝舌す繝・ヨ", "迚｡6", "豬應ｸｭ菫・, "鬆郁ｲ晏ｰ壻ｻ・, 57.0, 191.0, 14, 37.2, 5.5, 59, 62, 43, 98, 13),
        (2, 3, 3, "繝懊・繝ｳ繝・ぅ繧ｹ繧ｦ繧ｧ繧､", "迚｡7", "譚ｾ螻ｱ蠑伜ｹｳ", "迚ｧ蜈我ｺ・, 57.0, 129.7, 13, 34.7, 7.0, 43, 59, 43, 50, 11),
        (2, 3, 4, "繝輔ぃ繧､繧｢繝ｳ繧ｯ繝ｩ繝ｳ繝・, "迚｡4", "D.繝ｬ繝ｼ繝ｳ", "蝣螳｣陦・, 56.0, 4.6, 3, 34.9, 6.2, 67, 66, 60, 99, 1),
        (2, 4, 5, "繧ｮ繝｣繝ｳ繝悶Ν繝ｫ繝ｼ繝", "迚｡5", "蟷ｸ闍ｱ譏・, "螟ｧ荵・ｿ晞ｾ榊ｿ・, 55.0, 25.9, 8, 36.7, 6.8, 62, 63, 60, 63, 14),
        (2, 4, 6, "繧ｦ繧｣繧ｯ繝医Ν繧ｦ繧ｧ繝ｫ繧ｹ", "迚｡4", "C.繝ｫ繝｡繝ｼ繝ｫ", "螳ｮ逕ｰ謨ｬ莉・, 57.0, 3.0, 1, 33.3, 1.4, 100, 92, 60, 50, 2),
        (2, 5, 7, "繧｢繧ｹ繧ｯ繧ｻ繧ｯ繧ｷ繝ｼ繝｢繧｢", "迚｡4", "蛹玲搗蜿倶ｸ", "遖乗ｰｸ逾蝉ｸ", 55.0, 30.3, 9, 33.7, 4.4, 60, 70, 60, 28, 6),
        (2, 5, 8, "繝溘Λ繝ｼ繧ｸ繝･繝翫う繝・, "迚｡4", "隘ｿ譚第ｷｳ荵・, "霎ｻ驥取ｳｰ荵・, 56.0, 9.7, 4, 34.9, 2.8, 60, 77, 60, 106, 4),
        (2, 6, 9, "繝上・繝・さ繝ｳ繝√ぉ繝ｫ繝・, "迚｡6", "讓ｪ螻ｱ豁ｦ蜿ｲ", "豁ｦ莠穂ｺｮ", 54.0, 11.3, 5, 33.9, 3.3, 57, 57, 60, 15, 10),
        (2, 6, 10, "繝槭う繝阪Ν繧ｱ繝ｬ繝ｪ繧ｦ繧ｹ", "迚｡6", "荳ｹ蜀・･先ｬ｡", "螂･譚第ｭｦ", 55.0, 49.0, 10, 34.1, 6.2, 43, 55, 60, 21, 8),
        (2, 7, 11, "繝繝弱Φ繧ｷ繝ｼ繝・, "迚｡4", "蟾晉伐蟆・寉", "荳ｭ蜀・伐蜈・ｭ｣", 57.5, 3.8, 2, 34.2, 1.8, 91, 86, 60, 70, 3),
        (2, 7, 12, "繧ｭ繝ｳ繧ｰ繧ｺ繝代Ξ繧ｹ", "迚｡7", "譚ｾ蟯｡豁｣豬ｷ", "謌ｸ逕ｰ蜊壽枚", 57.0, 71.0, 11, 34.5, 5.6, 77, 69, 60, 77, 7),
        (2, 8, 13, "繝ｴ繧ｧ繝ｫ繝溘そ繝ｫ", "迚・", "F.繧ｴ繝ｳ繧ｵ繝ｫ繝吶せ", "蜷画搗蝨ｭ蜿ｸ", 54.0, 98.3, 12, 34.8, 7.8, 63, 56, 43, 28, 12),
        (2, 8, 14, "繧ｭ繝ｳ繧ｰ繧ｹ繧ｳ繝ｼ繝ｫ", "迚｡4", "蝮ゆｺ慕蔵譏・, "遏｢菴懆患莠ｺ", 55.0, 17.2, 7, 34.5, 5.2, 72, 66, 60, 15, 5),
    ]


# 鬨取焔縺ｮ隧穂ｾ｡蛟､・・-100縺ｮ讎らｮ暦ｼ峨・RA繝ｪ繝ｼ繝・ぅ繝ｳ繧ｰ鬆・ｽ阪ｄGI螳溽ｸｾ繧定ｸ上∪縺医◆逶ｮ螳峨〒縲・# 蟆・擂逧・↓縺ｯ蟷ｴ髢灘享邇・↑縺ｩ縺ｮ螳溘ョ繝ｼ繧ｿ縺ｫ鄂ｮ縺肴鋤縺医ｋ縺薙→繧呈Φ螳壹・JOCKEY_SKILL: dict[str, float] = {
    "C.繝ｫ繝｡繝ｼ繝ｫ": 97.0,
    "豁ｦ雎・: 93.0,
    "謌ｸ蟠主惆螟ｪ": 92.0,
    "讓ｪ螻ｱ豁ｦ蜿ｲ": 90.0,
    "D.繝ｬ繝ｼ繝ｳ": 89.0,
    "譚ｾ螻ｱ蠑伜ｹｳ": 86.0,
    "蟯ｩ逕ｰ譛帶擂": 82.0,
    "闖・次譏手憶": 81.0,
    "蟯ｩ逕ｰ蠎ｷ隱": 80.0,
    "蟷ｸ闍ｱ譏・: 78.0,
    "讓ｪ螻ｱ蜥檎函": 77.0,
    "豢･譚第・遘": 77.0,
    "鬮俶揄蜷城ｺ・: 76.0,
    "F.繧ｴ繝ｳ繧ｵ繝ｫ繝吶せ": 76.0,
    "荳ｹ蜀・･先ｬ｡": 74.0,
    "阯､諛ｸ雋ｴ蠢・: 73.0,
    "菴舌・惠螟ｧ霈・: 71.0,
    "蟾晉伐蟆・寉": 95.0,
    "蝮ゆｺ慕蔵譏・: 87.0,
    "豬應ｸｭ菫・: 85.0,
    "隘ｿ譚第ｷｳ荵・: 81.0,
    "蛹玲搗蜿倶ｸ": 80.0,
    "譚ｾ蟯｡豁｣豬ｷ": 76.0,
    "讓ｪ螻ｱ蜈ｸ蠑・: 88.0,
    "蜿､蟾晏翠豢・: 74.0,
    "譚ｾ譛ｬ螟ｧ霈・: 70.0,
    "蜷画搗隱荵句勧": 72.0,
    "魄ｫ蟲ｶ蜈矩ｧｿ": 78.0,
    "豎豺ｻ隰吩ｸ": 82.0,
    "讓ｪ螻ｱ逅我ｺｺ": 72.0,
    "闕ｻ驥取･ｵ": 72.0,
    "蟆丞ｴ守ｶｾ荵・: 70.0,
    "蟇檎伐證・: 72.0,
}
JOCKEY_SKILL_DEFAULT = 72.0


# 鬨取焔縺斐→縺ｮ蠕玲э閼夊ｳｪ (0=騾・￡, 1=蜈郁｡・ 2=蟾ｮ縺・ 3=霑ｽ霎ｼ, 荳ｭ髢灘､=荳｡蛻)
JOCKEY_PREF_STYLE: dict[str, float] = {
    "C.繝ｫ繝｡繝ｼ繝ｫ": 1.5,    # 蜈郁｡後懷ｷｮ縺・(荳・・蝙・
    "豁ｦ雎・: 1.0,          # 蜈郁｡・    "謌ｸ蟠主惆螟ｪ": 1.5,      # 蜈郁｡後懷ｷｮ縺・    "讓ｪ螻ｱ豁ｦ蜿ｲ": 2.0,      # 蟾ｮ縺・    "D.繝ｬ繝ｼ繝ｳ": 1.5,      # 蜈郁｡後懷ｷｮ縺・    "譚ｾ螻ｱ蠑伜ｹｳ": 1.0,      # 蜈郁｡・    "蟯ｩ逕ｰ譛帶擂": 2.0,      # 蟾ｮ縺・    "闖・次譏手憶": 2.0,      # 蟾ｮ縺・    "蟯ｩ逕ｰ蠎ｷ隱": 1.0,      # 蜈郁｡・    "蟷ｸ闍ｱ譏・: 1.0,        # 蜈郁｡・    "讓ｪ螻ｱ蜥檎函": 2.0,      # 蟾ｮ縺・    "豢･譚第・遘": 0.5,      # 騾・￡縲懷・陦・    "荳ｹ蜀・･先ｬ｡": 2.5,      # 蟾ｮ縺励懆ｿｽ霎ｼ
    "阯､諛ｸ雋ｴ蠢・: 2.0,      # 蟾ｮ縺・    "鬮俶揄蜷城ｺ・: 2.0,      # 蟾ｮ縺・    "F.繧ｴ繝ｳ繧ｵ繝ｫ繝吶せ": 1.0,# 蜈郁｡・    "菴舌・惠螟ｧ霈・: 1.5,    # 蜈郁｡後懷ｷｮ縺・    "蟾晉伐蟆・寉": 1.5,      # 蜈郁｡後懷ｷｮ縺・    "蝮ゆｺ慕蔵譏・: 2.0,      # 蟾ｮ縺・    "豬應ｸｭ菫・: 1.0,        # 蜈郁｡・    "隘ｿ譚第ｷｳ荵・: 2.0,      # 蟾ｮ縺・    "蛹玲搗蜿倶ｸ": 1.0,      # 蜈郁｡・    "譚ｾ蟯｡豁｣豬ｷ": 1.0,      # 蜈郁｡・    "讓ｪ螻ｱ蜈ｸ蠑・: 1.5,      # 蜈郁｡後懷ｷｮ縺・    "蜿､蟾晏翠豢・: 2.0,      # 蟾ｮ縺・    "譚ｾ譛ｬ螟ｧ霈・: 0.0,      # 騾・￡
    "蜷画搗隱荵句勧": 1.5,    # 蜈郁｡後懷ｷｮ縺・    "魄ｫ蟲ｶ蜈矩ｧｿ": 2.0,      # 蟾ｮ縺・    "豎豺ｻ隰吩ｸ": 2.0,      # 蟾ｮ縺・    "讓ｪ螻ｱ逅我ｺｺ": 2.0,      # 蟾ｮ縺・    "闕ｻ驥取･ｵ": 2.0,        # 蟾ｮ縺・    "蟆丞ｴ守ｶｾ荵・: 1.0,      # 蜈郁｡・    "蟇檎伐證・: 2.0,        # 蟾ｮ縺・}


def jockey_skill_score(jockey: str) -> float:
    return JOCKEY_SKILL.get(jockey, JOCKEY_SKILL_DEFAULT)


def _style_compat_score(horse_style: int | None, jockey_pref: float | None) -> float:
    """鬨取焔縺ｮ蠕玲э閼夊ｳｪ縺ｨ鬥ｬ縺ｮ閼夊ｳｪ縺ｮ逶ｸ諤ｧ繧・-100縺ｧ霑斐☆縲ょｷｮ縺悟､ｧ縺阪＞縺ｻ縺ｩ菴弱せ繧ｳ繧｢縲・""
    if horse_style is None or jockey_pref is None:
        return 65.0  # 繝・・繧ｿ縺ｪ縺励・繝九Η繝ｼ繝医Λ繝ｫ
    diff = abs(horse_style - jockey_pref)
    return max(20.0, 100.0 - diff * 40.0)


_PACE_TABLE: dict[tuple[str, int], float] = {
    ("front", 0): 95, ("front", 1): 82, ("front", 2): 48, ("front", 3): 28,
    ("even",  0): 65, ("even",  1): 70, ("even",  2): 70, ("even",  3): 58,
    ("close", 0): 28, ("close", 1): 48, ("close", 2): 82, ("close", 3): 95,
}
_STYLE_LABEL = {0: "騾・￡", 1: "蜈郁｡・, 2: "蟾ｮ縺・, 3: "霑ｽ霎ｼ"}


def _pace_match_score(running_style: int | None, pace_bias: str) -> float:
    if running_style is None:
        return 50.0
    return float(_PACE_TABLE.get((pace_bias, running_style), 60))


def _draw_match_score(gate: int | None, draw_bias: str) -> float:
    if gate is None or draw_bias == "even":
        return 50.0
    inside_pct = max(0.0, min(100.0, (9 - gate) / 8.0 * 100))
    return inside_pct if draw_bias == "inside" else (100.0 - inside_pct)


def calculate_prediction(horse: dict[str, Any], race: dict[str, Any] | None = None) -> HorsePrediction:
    # 讓呎ｺ夜・蛻・ 鬥ｬ縺ｮ蜉・ : 鬨取焔縺ｮ蜉・ : 繝ｬ繝ｼ繧ｹ螻暮幕縺ｪ縺ｩ縺昴・莉悶・隕∝屏2 (= 0.6 / 0.2 / 0.2)縲・    # 3隕∫ｴ繧偵◎繧後◇繧・-100縺ｮ繧ｹ繧ｱ繝ｼ繝ｫ縺ｫ謠・∴縺ｦ縺九ｉ蜉驥榊ｹｳ蝮・☆繧九・    fitness = (horse["distance_fit"] + horse["going_fit"] + horse["course_fit"]) / 3
    recent_form = min(100.0, max(0.0, 8.0 - horse["avg_finish"]) / 8.0 * 100)
    recent_speed = min(100.0, max(0.0, 42.0 - horse["last3f"]) / 10.0 * 100)
    horse_score = fitness * 0.5 + recent_form * 0.3 + recent_speed * 0.2

    # 鬨取焔繧ｳ繝ｳ繝昴・繝阪Φ繝・ 繧ｹ繧ｭ繝ｫ75% + 鬨取焔ﾃ鈴ｦｬ縺ｮ閼夊ｳｪ逶ｸ諤ｧ25%
    jockey_pref = JOCKEY_PREF_STYLE.get(horse["jockey"])
    style_compat = _style_compat_score(horse.get("running_style"), jockey_pref)
    jockey_score = jockey_skill_score(horse["jockey"]) * 0.75 + style_compat * 0.25

    pace_bias = (race or {}).get("pace_bias", "even")
    draw_bias = (race or {}).get("draw_bias", "even")
    freshness   = min(100.0, max(0.0, 70.0 - horse["days_since_last"]) / 70.0 * 100)
    market_read = min(100.0, max(0.0, 18.0 - horse["popularity"]) / 17.0 * 100)
    pace_score  = _pace_match_score(horse.get("running_style"), pace_bias)
    draw_score  = _draw_match_score(horse.get("gate"), draw_bias)
    context_score = freshness * 0.30 + market_read * 0.30 + pace_score * 0.25 + draw_score * 0.15

    blinker_bonus = 2.0 if horse.get("blinker") else 0.0
    score = horse_score * 0.6 + jockey_score * 0.2 + context_score * 0.2 + blinker_bonus
    score = max(1.0, round(score, 1))

    win_probability = min(42.0, max(2.0, round(score / 2.55, 1)))
    place_probability = min(72.0, round(win_probability * 1.72, 1))
    expected_value = round((win_probability / 100) * horse["odds"], 2)

    notes: list[str] = []
    if horse["distance_fit"] >= 85:
        notes.append("霍晞屬驕ｩ諤ｧ縺碁ｫ倥＞")
    if horse["going_fit"] >= 82:
        notes.append("鬥ｬ蝣ｴ驕ｩ諤ｧ縺碁ｫ倥＞")
    if horse["last3f"] <= 35.2:
        notes.append("荳翫ｊ3繝上Ο繝ｳ縺悟ｮ牙ｮ・)
    if horse["avg_finish"] <= 3.3:
        notes.append("霑題ｵｰ縺ｮ逹鬆・′蝣・＞")
    if jockey_skill_score(horse["jockey"]) >= 88:
        notes.append("鬨取焔縺ｮ菫｡鬆ｼ蠎ｦ縺碁ｫ倥＞")
    if horse.get("running_style") is not None and jockey_pref is not None:
        if style_compat >= 85:
            notes.append("鬨取焔縺ｨ鬥ｬ縺ｮ閼夊ｳｪ逶ｸ諤ｧ縺瑚憶縺・)
        elif style_compat <= 40:
            notes.append("鬨取焔縺ｨ鬥ｬ縺ｮ閼夊ｳｪ逶ｸ諤ｧ縺後ｄ繧・が縺・)
    rs = horse.get("running_style")
    if rs is not None and pace_bias != "even":
        label = _STYLE_LABEL.get(rs, "")
        bias_label = "蜑肴怏蛻ｩ" if pace_bias == "front" else "蟾ｮ縺玲怏蛻ｩ"
        if _PACE_TABLE.get((pace_bias, rs), 60) >= 75:
            notes.append(f"{bias_label}縺ｮ鬥ｬ蝣ｴ縺ｨ{label}閼夊ｳｪ縺御ｸ閾ｴ")
        elif _PACE_TABLE.get((pace_bias, rs), 60) <= 40:
            notes.append(f"{bias_label}縺ｮ鬥ｬ蝣ｴ縺ｨ{label}閼夊ｳｪ縺御ｸ堺ｸ閾ｴ")
    if horse.get("blinker"):
        notes.append("繝悶Μ繝ｳ繧ｫ繝ｼ逹逕ｨ")
    if expected_value >= 1:
        notes.append("繧ｪ繝・ぜ螯吝袖縺ゅｊ")
    if not notes:
        notes.append("邱丞粋繝舌Λ繝ｳ繧ｹ蝙・)

    return HorsePrediction(horse, score, win_probability, place_probability, expected_value, notes)


def get_races() -> list[dict[str, Any]]:
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT r.*,
                   COUNT(h.id) AS horse_count,
                   MIN(h.odds) AS min_odds
            FROM races r
            LEFT JOIN horses h ON h.race_id = r.id
            GROUP BY r.id
            ORDER BY r.race_date, r.start_time
            """
        ).fetchall()
    return [dict(row) for row in rows]


def get_race(race_id: int) -> dict[str, Any] | None:
    with connect() as conn:
        row = conn.execute("SELECT * FROM races WHERE id = ?", (race_id,)).fetchone()
    return dict(row) if row else None


def get_horses(race_id: int) -> list[dict[str, Any]]:
    with connect() as conn:
        rows = conn.execute(
            "SELECT * FROM horses WHERE race_id = ? ORDER BY number",
            (race_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def get_report() -> dict[str, Any]:
    with connect() as conn:
        row = conn.execute(
            """
            SELECT
                COUNT(*) AS bet_count,
                COALESCE(SUM(stake), 0) AS total_stake,
                COALESCE(SUM(payout), 0) AS total_payout
            FROM bets
            """
        ).fetchone()
        bets = conn.execute(
            """
            SELECT b.*, r.venue, r.race_no, r.title, h.name AS horse_name,
                   h.result_position
            FROM bets b
            JOIN races r ON r.id = b.race_id
            JOIN horses h ON h.id = b.horse_id
            ORDER BY b.created_at DESC
            """
        ).fetchall()
    total_stake = row["total_stake"]
    total_payout = row["total_payout"]
    return {
        "bet_count": row["bet_count"],
        "total_stake": total_stake,
        "total_payout": total_payout,
        "profit": total_payout - total_stake,
        "roi": round(total_payout / total_stake * 100, 1) if total_stake else 0,
        "bets": [dict(bet) for bet in bets],
    }


def esc(value: Any) -> str:
    return html.escape(str(value), quote=True)


def money(value: int | float) -> str:
    return f"{int(value):,}蜀・


def layout(title: str, body: str, active: str = "races") -> bytes:
    nav = {
        "races": "",
        "report": "",
    }
    nav[active] = "active"
    page = f"""<!doctype html>
<html lang="ja">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(title)} | {APP_NAME}</title>
  <link rel="stylesheet" href="/static/style.css">
</head>
<body>
  <header class="topbar">
    <a class="brand" href="/">
      <span class="brand-mark">K</span>
      <span>{APP_NAME}</span>
    </a>
    <nav>
      <a class="{nav['races']}" href="/">繝ｬ繝ｼ繧ｹ</a>
      <a class="{nav['report']}" href="/report">蝗槫庶邇・/a>
    </nav>
  </header>
  <main>
    {body}
  </main>
</body>
</html>"""
    return page.encode("utf-8")


def render_home() -> bytes:
    races = get_races()
    cards = []
    for race in races:
        cards.append(
            f"""
            <a class="race-card" href="/race?id={race['id']}">
              <div class="race-meta">
                <span>{esc(race['venue'])} {race['race_no']}R</span>
                <span>{esc(race['start_time'])}</span>
              </div>
              <h2>{esc(race['title'])}</h2>
              <p>{esc(race['race_date'])} / {esc(race['grade'])} / {esc(race['surface'])}{race['distance']}m / {esc(race['going'])}</p>
              <div class="race-stats">
                <span>蜃ｺ襍ｰ {race['horse_count']}鬆ｭ</span>
                <span>譛菴弱が繝・ぜ {race['min_odds']:.1f}</span>
              </div>
            </a>
            """
        )
    body = f"""
    <section class="hero">
      <div>
        <p class="eyebrow">Data driven racing desk</p>
        <h1>{APP_NAME}</h1>
        <p class="lead">JRA驥崎ｳ槭Ξ繝ｼ繧ｹ縺ｮ莠域Φ繝ｻ讀懆ｨｼ繝励Ο繝医ち繧､繝励〒縺吶・/p>
      </div>
      <div class="hero-panel">
        <span>謗ｲ霈蛾㍾雉・/span>
        <strong>{len(races)}</strong>
      </div>
    </section>
    <section class="section-head">
      <div>
        <p class="eyebrow">Graded Stakes</p>
        <h2>驥崎ｳ槭Ξ繝ｼ繧ｹ荳隕ｧ</h2>
      </div>
    </section>
    <section class="race-grid">
      {''.join(cards)}
    </section>
    """
    return layout("6譛・譌･縺ｮ驥崎ｳ・, body)


def render_race(race_id: int) -> bytes:
    race = get_race(race_id)
    if not race:
        return layout("Not Found", "<section class='empty'>繝ｬ繝ｼ繧ｹ縺瑚ｦ九▽縺九ｊ縺ｾ縺帙ｓ縲・/section>")

    predictions = [calculate_prediction(horse, race) for horse in get_horses(race_id)]
    predictions.sort(key=lambda item: item.score, reverse=True)
    top = predictions[0] if predictions else None
    is_finished = any(prediction.horse["result_position"] is not None for prediction in predictions)

    rows = []
    for index, prediction in enumerate(predictions, start=1):
        horse = prediction.horse
        badge = "譛ｬ蜻ｽ" if index == 1 else "蟇ｾ謚・ if index == 2 else "豕ｨ逶ｮ" if index == 3 else ""
        # 莠ｺ豌励′菴弱＞(7逡ｪ莠ｺ豌嶺ｻ･荳・縺ｮ縺ｫ縲、I隧穂ｾ｡縺ｮ鬆・ｽ阪′莠ｺ豌鈴・ｽ阪ｈ繧・縺､莉･荳願憶縺・ｦｬ繧偵檎ｩｴ縲阪→縺励※陦ｨ遉ｺ縺吶ｋ縲・        is_longshot = horse["popularity"] >= 7 and (horse["popularity"] - index) >= 4
        marks = []
        if badge:
            marks.append(f'<span class="pill">{badge}</span>')
        if is_longshot:
            marks.append('<span class="pill pill-longshot" title="莠ｺ豌嶺ｻ･荳翫↓AI隧穂ｾ｡縺碁ｫ倥＞遨ｴ鬥ｬ蛟呵｣・>遨ｴ</span>')
        mark_html = f'<div class="marks">{"".join(marks)}</div>' if marks else ""

        result_cell = ""
        if is_finished:
            position = horse["result_position"]
            hit = position is not None and index <= 3 and position <= 3
            label = f"{position}逹" if position is not None else "--"
            result_cell = f'<td class="result {"hit" if hit else ""}">{esc(label)}</td>'

        rows.append(
            f"""
            <tr>
              <td class="rank">{index}</td>
              <td>
                <div class="horse-name">{esc(horse['number'])}. {esc(horse['name'])}</div>
                <div class="muted">{esc(horse['sex_age'])} / {esc(horse['jockey'])} / {esc(horse['trainer'])}{
                    (f" / {horse['body_weight']}kg({'ﾂｱ0' if horse['body_weight_change'] == 0 else ('+' + str(horse['body_weight_change']) if horse['body_weight_change'] > 0 else str(horse['body_weight_change']))})"
                     if horse.get('body_weight_change') is not None
                     else f" / {horse['body_weight']}kg")
                    if horse.get('body_weight') else ''
                }</div>
              </td>
              <td>{horse['odds']:.1f}<span class="muted">蛟・/span></td>
              <td>{prediction.score:.1f}</td>
              <td>{prediction.win_probability:.1f}%</td>
              <td>{prediction.place_probability:.1f}%</td>
              <td class="ev {'good' if prediction.expected_value >= 1 else ''}">{prediction.expected_value:.2f}</td>
              <td>{mark_html}</td>
              {result_cell}
            </tr>
            <tr class="detail-row">
              <td></td>
              <td colspan="{8 if is_finished else 7}">{' / '.join(esc(note) for note in prediction.notes)}</td>
            </tr>
            """
        )

    side_panel = ""
    if is_finished:
        winner = next((p for p in predictions if p.horse["result_position"] == 1), None)
        winner_rank = next((i for i, p in enumerate(predictions, start=1) if p.horse["result_position"] == 1), None)
        top3_hit = sum(1 for i, p in enumerate(predictions[:3], start=1) if (p.horse["result_position"] or 99) <= 3)
        top6_hit = sum(1 for i, p in enumerate(predictions[:6], start=1) if (p.horse["result_position"] or 99) <= 6)
        if top and winner and winner_rank:
            side_panel = f"""
            <aside class="pick-panel verify-panel">
              <span>讀懆ｨｼ - 莠域Φ vs 邨先棡</span>
              <strong>AI譛ｬ蜻ｽ {esc(top.horse['name'])} 竊・螳滄圀{top.horse['result_position']}逹</strong>
              <p>螳滄圀縺ｮ1逹 {esc(winner.horse['name'])} 縺ｯAI隧穂ｾ｡{winner_rank}菴阪〒縺励◆</p>
              <p>荳贋ｽ・鬆ｭ竊定､・享蝨・{top3_hit}/3 逧・ｸｭ 繝ｻ 荳贋ｽ・鬆ｭ竊・逹蜀・{top6_hit}/6 逧・ｸｭ</p>
            </aside>
            """
    elif top:
        side_panel = f"""
        <aside class="pick-panel">
          <span>AI謗ｨ螂ｨ</span>
          <strong>{esc(top.horse['name'])}</strong>
          <p>蜍晉紫 {top.win_probability:.1f}% / 隍・享邇・{top.place_probability:.1f}% / 譛溷ｾ・､ {top.expected_value:.2f}</p>
        </aside>
        """

    result_header = "<th>邨先棡</th>" if is_finished else ""
    note_panel = ""
    if is_finished:
        note_panel = """
        <p class="lead verify-note">
          縺薙・繝ｬ繝ｼ繧ｹ縺ｯ邨ゆｺ・ｸ医∩縺ｧ縺吶・I隧穂ｾ｡縺ｫ繧医ｋ莠域Φ鬆・ｽ阪→螳滄圀縺ｮ逹鬆・ｒ荳ｦ縺ｹ縺ｦ謗ｲ霈峨＠縲√Δ繝・Ν縺ｮ遲斐∴蜷医ｏ縺帙ｒ陦後▲縺ｦ縺・∪縺吶・        </p>
        """

    body = f"""
    <section class="race-detail-head">
      <div>
        <a class="back-link" href="/">竊・繝ｬ繝ｼ繧ｹ荳隕ｧ</a>
        <p class="eyebrow">{esc(race['race_date'])} / {esc(race['venue'])} {race['race_no']}R / {esc(race['start_time'])}</p>
        <h1>{esc(race['title'])}</h1>
        <p class="lead">{esc(race['grade'])} / {esc(race['surface'])}{race['distance']}m / 鬥ｬ蝣ｴ {esc(race['going'])}</p>
        {note_panel}
      </div>
      {side_panel}
    </section>
    <section class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>蜊ｰ</th>
            <th>鬥ｬ</th>
            <th>繧ｪ繝・ぜ</th>
            <th>繧ｹ繧ｳ繧｢</th>
            <th>蜍晉紫</th>
            <th>隍・享邇・/th>
            <th>譛溷ｾ・､</th>
            <th></th>
            {result_header}
          </tr>
        </thead>
        <tbody>{''.join(rows)}</tbody>
      </table>
    </section>
    """
    return layout(race["title"], body)


# AI鬆・ｽ阪＃縺ｨ縺ｮ雉ｼ蜈･繝励Λ繝ｳ (ai_rank_index, 蛻ｸ遞ｮ, 莠育ｮ鈴・蛻・)  笏 蜷郁ｨ・100%
# 蜊伜享蜷郁ｨ・30% / 隍・享蜷郁ｨ・70%
_BET_PLAN = [
    (0, "蜊伜享", 18), (0, "隍・享", 22),
    (1, "蜊伜享", 12), (1, "隍・享", 18),
    (2, "隍・享", 12), (3, "隍・享",  9),
    (4, "隍・享",  6), (5, "隍・享",  3),
]


def _simulate_race(preds: list[HorsePrediction], budget: int) -> tuple[list[dict], int, int]:
    """莠育ｮ鈴・蛻・・繝ｩ繝ｳ縺ｫ蠕薙▲縺ｦ繧ｷ繝溘Η繝ｬ繝ｼ繝医＠縲・陦後Μ繧ｹ繝・ 蜷郁ｨ域兜雉・ 蜷郁ｨ域鴛謌ｻ) 繧定ｿ斐☆縲・""
    rows: list[dict] = []
    total_bet = 0
    total_payout = 0
    for idx, bet_type, wpct in _BET_PLAN:
        if idx >= len(preds):
            continue
        horse = preds[idx].horse
        amount = max(100, (int(budget * wpct / 100) // 100) * 100)
        total_bet += amount
        pos = horse.get("result_position")
        is_done = pos is not None
        hit = payout = estimated = False
        if is_done:
            if bet_type == "蜊伜享":
                hit = pos == 1
                payout = int(amount * horse["odds"]) if hit else 0
            else:
                hit = pos <= 3
                if hit:
                    po = horse.get("place_odds")
                    if po:
                        payout = int(amount * po)
                    else:
                        payout = int(amount * max(1.1, horse["odds"] * 0.38))
                        estimated = True
                else:
                    payout = 0
            total_payout += payout
        rows.append({
            "rank": idx + 1, "name": horse["name"], "bet_type": bet_type,
            "amount": amount, "odds": horse["odds"],
            "pos": pos, "hit": hit, "payout": payout,
            "is_done": is_done, "estimated": estimated,
        })
    return rows, total_bet, total_payout


def render_report(budget: int = 10000) -> bytes:
    # --- 繝ｬ繝ｼ繧ｹ縺斐→縺ｮ繧ｷ繝溘Η繝ｬ繝ｼ繧ｷ繝ｧ繝ｳ ---
    race_sections = []
    grand_payout = 0
    num_finished = 0

    for race_info in get_races():
        race = get_race(race_info["id"])
        horses = get_horses(race_info["id"])
        preds = sorted(
            [calculate_prediction(h, race) for h in horses],
            key=lambda p: p.score, reverse=True,
        )
        is_finished = any(h.get("result_position") is not None for h in horses)
        sim_rows, total_bet, total_payout = _simulate_race(preds, budget)
        if is_finished:
            grand_payout += total_payout
            num_finished += 1

        tr_list = []
        for r in sim_rows:
            if r["is_done"]:
                pos_str = f"{r['pos']}逹"
                result_cls = "result hit" if r["hit"] else "result"
                result_txt = "逧・ｸｭ" if r["hit"] else "螟悶ｌ"
                est_mark = "<sup>謗ｨ螳・/sup>" if r["estimated"] else ""
                payout_str = f"{money(r['payout'])}{est_mark}"
            else:
                pos_str = "譛ｪ遒ｺ螳・
                result_cls = "result"
                result_txt = "--"
                payout_str = "--"
            tr_list.append(f"""
                <tr>
                  <td class="rank">{r['rank']}</td>
                  <td>{esc(r['name'])}</td>
                  <td><span class="pill pill-{'tansho' if r['bet_type'] == '蜊伜享' else 'fukusho'}">{esc(r['bet_type'])}</span></td>
                  <td>{money(r['amount'])}</td>
                  <td class="muted">{r['odds']:.1f}蛟・/td>
                  <td>{pos_str}</td>
                  <td class="{result_cls}">{result_txt}</td>
                  <td>{payout_str}</td>
                </tr>
            """)

        roi = round(total_payout / total_bet * 100, 1) if (is_finished and total_bet) else None
        roi_html = (
            f'<p class="sim-roi ev {"good" if roi and roi >= 100 else ""}">蝗槫庶邇・{roi}%'
            f' ・域兜雉・{money(total_bet)} / 謇墓綾 {money(total_payout)}・・/p>'
            if roi is not None else
            f'<p class="sim-roi muted">謚戊ｳ・粋險・{money(total_bet)}・医Ξ繝ｼ繧ｹ譛ｪ遒ｺ螳夲ｼ・/p>'
        )
        race_sections.append(f"""
        <section class="section-head" style="margin-top:32px;">
          <div>
            <p class="eyebrow">{esc(race_info['race_date'])} / {esc(race_info['title'])}</p>
          </div>
        </section>
        <section class="table-wrap">
          <table>
            <thead>
              <tr>
                <th>AI鬆・ｽ・/th><th>鬥ｬ</th><th>蛻ｸ遞ｮ</th><th>謚戊ｳ・/th>
                <th>繧ｪ繝・ぜ</th><th>螳溽ｵ先棡</th><th>蛻､螳・/th><th>謇墓綾</th>
              </tr>
            </thead>
            <tbody>{''.join(tr_list)}</tbody>
          </table>
          {roi_html}
        </section>
        """)

    grand_bet = budget * num_finished
    grand_roi = round(grand_payout / grand_bet * 100, 1) if grand_bet else 0

    budget_form = f"""
    <form class="budget-form" method="GET" action="/report">
      <label for="budget-input">1繝ｬ繝ｼ繧ｹ莠育ｮ・/label>
      <input id="budget-input" type="number" name="budget" value="{budget}"
             step="1000" min="1000" max="1000000">
      <span>蜀・/span>
      <button type="submit">譖ｴ譁ｰ</button>
    </form>
    """

    body = f"""
    <section class="section-head">
      <div>
        <p class="eyebrow">Performance</p>
        <h1>蝗槫庶邇・Ξ繝昴・繝・/h1>
      </div>
    </section>
    {budget_form}
    <section class="kpi-grid">
      <div class="kpi"><span>1繝ｬ繝ｼ繧ｹ莠育ｮ・/span><strong>{money(budget)}</strong></div>
      <div class="kpi"><span>螳滓命繝ｬ繝ｼ繧ｹ謨ｰ</span><strong>{num_finished}</strong></div>
      <div class="kpi"><span>蜷郁ｨ域鴛謌ｻ</span><strong>{money(grand_payout)}</strong></div>
      <div class="kpi"><span>邱丞粋蝗槫庶邇・/span><strong class="{'ev good' if grand_roi >= 100 else ''}">{grand_roi}%</strong></div>
    </section>
    {''.join(race_sections)}
    """
    return layout("蝗槫庶邇・Ξ繝昴・繝・, body, active="report")


class KeibaClubHandler(BaseHTTPRequestHandler):
    def _get_cookies(self) -> dict[str, str]:
        cookies: dict[str, str] = {}
        for part in self.headers.get("Cookie", "").split(";"):
            part = part.strip()
            if "=" in part:
                k, v = part.split("=", 1)
                cookies[k.strip()] = v.strip()
        return cookies

    def _authenticated(self) -> bool:
        if not SECRET_TOKEN:
            return True
        return self._get_cookies().get(_SESSION_COOKIE) == _SESSION_NONCE

    def do_GET(self) -> None:
        parsed = urlparse(self.path)

        if SECRET_TOKEN and parsed.path in (f"/{SECRET_TOKEN}", f"/{SECRET_TOKEN}/"):
            self.send_response(302)
            self.send_header("Location", "/")
            self.send_header(
                "Set-Cookie",
                f"{_SESSION_COOKIE}={_SESSION_NONCE}; Path=/; HttpOnly; SameSite=Strict",
            )
            self.end_headers()
            return

        if not self._authenticated():
            self.respond(404, b"Not Found", "text/plain; charset=utf-8")
            return

        try:
            if parsed.path == "/":
                self.respond(200, render_home())
            elif parsed.path == "/race":
                race_id = int(parse_qs(parsed.query).get("id", ["0"])[0])
                self.respond(200, render_race(race_id))
            elif parsed.path == "/report":
                try:
                    budget = max(1000, min(1_000_000, int(parse_qs(parsed.query).get("budget", ["10000"])[0])))
                except (ValueError, KeyError):
                    budget = 10000
                self.respond(200, render_report(budget))
            elif parsed.path.startswith("/static/"):
                self.serve_static(parsed.path.removeprefix("/static/"))
            else:
                self.respond(404, layout("Not Found", "<section class='empty'>繝壹・繧ｸ縺瑚ｦ九▽縺九ｊ縺ｾ縺帙ｓ縲・/section>"))
        except Exception as exc:
            message = f"<section class='empty'>繧ｨ繝ｩ繝ｼ: {esc(exc)}</section>"
            self.respond(500, layout("Error", message))

    def log_message(self, format: str, *args: Any) -> None:
        return

    def respond(self, status: int, content: bytes, content_type: str = "text/html; charset=utf-8") -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def serve_static(self, filename: str) -> None:
        path = (STATIC_DIR / filename).resolve()
        if not str(path).startswith(str(STATIC_DIR.resolve())) or not path.exists():
            self.respond(404, b"Not found", "text/plain; charset=utf-8")
            return
        content_type = "text/css; charset=utf-8" if path.suffix == ".css" else "application/octet-stream"
        self.respond(200, path.read_bytes(), content_type)


def main() -> None:
    initialize_database()
    port = int(os.environ.get("PORT", "8000"))
    server = ThreadingHTTPServer(("0.0.0.0", port), KeibaClubHandler)
    print(f"{APP_NAME} is running at http://127.0.0.1:{port}")
    server.serve_forever()


if __name__ == "__main__":
    main()

