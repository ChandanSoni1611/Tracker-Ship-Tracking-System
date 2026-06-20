from flask import Flask, jsonify, request
from flask_cors import CORS
import asyncio
import websockets
import json
import threading
import time
import sqlite3
from datetime import datetime, UTC
from dotenv import load_dotenv
import os

load_dotenv()

api_key = os.getenv("AIS_API_KEY")

DB_NAME = "ships.db"

app = Flask(__name__)
CORS(app)

# =========================
# GLOBALS
# =========================

ships_data = {}
is_connected = False

# =========================
# SQLITE DATABASE
# =========================

conn = sqlite3.connect(DB_NAME, check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS ships (
    mmsi TEXT PRIMARY KEY,
    name TEXT,
    lat REAL,
    lon REAL,
    speed REAL,
    course REAL,
    heading REAL,
    nav_status TEXT,
    ship_type TEXT,
    last_update TEXT
)
""")

conn.commit()

print("✅ SQLite database initialized")


# =========================
# SAVE SHIP TO SQLITE
# =========================

def save_ship_to_db(ship):

    try:
        db = sqlite3.connect("ships.db")

        cursor = db.cursor()

        cursor.execute("""
        INSERT OR REPLACE INTO ships (
            mmsi,
            name,
            lat,
            lon,
            speed,
            course,
            heading,
            nav_status,
            ship_type,
            last_update
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            ship["mmsi"],
            ship["name"],
            ship["lat"],
            ship["lon"],
            ship["speed"],
            ship["course"],
            ship["heading"],
            str(ship["nav_status"]),
            ship["type"],
            ship["time_utc"]
        ))

        db.commit()
        db.close()

    except Exception as e:
        print("❌ Database insert error:", e)


# =========================
# AIS STREAM CONNECTION
# =========================

async def connect_ais_stream():
    global ships_data, is_connected

    if not api_key:
        raise ValueError(
            "AIS_API_KEY not found in .env file"
        )

    while True:
        try:
            async with websockets.connect(
                "wss://stream.aisstream.io/v0/stream"
            ) as websocket:

                subscribe_message = {
                    "APIKey": api_key,
                    "BoundingBoxes": [[[-90, -180], [90, 180]]],
                    "FilterMessageTypes": [
                        "PositionReport",
                        "StandardClassBPositionReport",
                        "ExtendedClassBPositionReport"
                    ]
                }

                await websocket.send(json.dumps(subscribe_message))

                is_connected = True

                print("✅ Connected to AISStream")

                async for message_json in websocket:
                    try:
                        message = json.loads(message_json)

                        message_type = message.get("MessageType")

                        metadata = message.get("MetaData", {})

                        ship_data = None

                        # =========================
                        # POSITION REPORT
                        # =========================

                        if message_type == "PositionReport":
                            ship_data = message["Message"]["PositionReport"]

                        elif message_type == "StandardClassBPositionReport":
                            ship_data = message["Message"]["StandardClassBPositionReport"]

                        elif message_type == "ExtendedClassBPositionReport":
                            ship_data = message["Message"]["ExtendedClassBPositionReport"]

                        else:
                            continue

                        lat = ship_data.get("Latitude")
                        lon = ship_data.get("Longitude")

                        if lat is None or lon is None:
                            continue

                        mmsi = str(
                            metadata.get(
                                "MMSI",
                                ship_data.get("UserID", "Unknown")
                            )
                        )

                        ship = {
                            "mmsi": mmsi,
                            "name": metadata.get("ShipName", "Unknown Vessel").strip(),
                            "lat": lat,
                            "lon": lon,
                            "speed": round(ship_data.get("Sog", 0), 1),
                            "course": round(ship_data.get("Cog", 0), 1),
                            "heading": ship_data.get("TrueHeading", 0),
                            "nav_status": ship_data.get("NavigationalStatus", 15),
                            "time_utc": metadata.get(
                                "time_utc",
                                datetime.now(UTC).isoformat()
                            ),
                            "type": metadata.get("ShipType", "Unknown")
                        }

                        # =========================
                        # RAM CACHE
                        # =========================

                        ships_data[mmsi] = ship

                        # =========================
                        # SQLITE STORAGE
                        # =========================

                        save_ship_to_db(ship)

                        print(f"🚢 {ship['name']} | MMSI: {mmsi}")

                    except Exception as e:
                        print("⚠️ Message parse error:", e)

        except Exception as e:
            is_connected = False
            print("❌ AISStream error:", e)
            print("🔄 Reconnecting in 5 seconds...")

            await asyncio.sleep(5)


# =========================
# BACKGROUND THREAD
# =========================

def start_ais_background():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(connect_ais_stream())


# =========================
# HOME
# =========================

@app.route("/")
def home():
    return jsonify({
        "status": "Ship Tracker API Running",
        "connected": is_connected,
        "live_cache_ships": len(ships_data)
    })


# =========================
# GET ALL SHIPS
# =========================

@app.route("/api/ships/all")
def get_all_ships():

    limit = request.args.get("limit", default=5000, type=int)

    cursor.execute("""
    SELECT * FROM ships
    ORDER BY last_update DESC
    LIMIT ?
    """, (limit,))

    rows = cursor.fetchall()

    ships = []

    for row in rows:
        ships.append({
            "mmsi": row[0],
            "name": row[1],
            "lat": row[2],
            "lon": row[3],
            "speed": row[4],
            "course": row[5],
            "heading": row[6],
            "nav_status": row[7],
            "type": row[8],
            "time_utc": row[9]
        })

    return jsonify({
        "success": True,
        "connected": is_connected,
        "count": len(ships),
        "ships": ships
    })


# =========================
# SEARCH SHIPS
# =========================

@app.route("/api/ships/search")
def search_ships():

    query = request.args.get("query", "").strip()

    if not query:
        return jsonify([])

    try:

        db = sqlite3.connect(DB_NAME)
        db.row_factory = sqlite3.Row

        cur = db.cursor()

        cur.execute("""
            SELECT *
            FROM ships
            WHERE
                name LIKE ?
                OR mmsi LIKE ?
            ORDER BY last_update DESC
            LIMIT 100
        """, (
            f"%{query}%",
            f"%{query}%"
        ))

        rows = cur.fetchall()

        ships = []

        for row in rows:
            ships.append({
                "mmsi": row["mmsi"],
                "name": row["name"],
                "lat": row["lat"],
                "lon": row["lon"],
                "speed": row["speed"],
                "course": row["course"],
                "heading": row["heading"],
                "nav_status": row["nav_status"],
                "type": row["ship_type"],
                "time_utc": row["last_update"]
            })

        db.close()

        return jsonify({
            "success": True,
            "count": len(ships),
            "ships": ships
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# =========================
# HEALTH CHECK
# =========================

@app.route("/api/health")
def health():

    cursor.execute("SELECT COUNT(*) FROM ships")
    total_ships = cursor.fetchone()[0]

    return jsonify({
        "status": "healthy",
        "connected": is_connected,
        "database_ships": total_ships,
        "live_cache_ships": len(ships_data),
        "timestamp": datetime.now(UTC).isoformat()
    })


# =========================
# MAIN
# =========================

if __name__ == "__main__":

    print("🚢 Starting Ship Tracker Backend...")

    thread = threading.Thread(
        target=start_ais_background,
        daemon=True
    )

    thread.start()

    time.sleep(2)

    print("🌐 Backend running on http://localhost:5000")

    app.run(
        debug=True,
        host="0.0.0.0",
        port=5000,
        use_reloader=False
    )