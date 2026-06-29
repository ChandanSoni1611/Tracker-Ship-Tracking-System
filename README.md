 🚢 Tracker - Real-Time Ship Tracking System

ShipTrack is a real-time vessel tracking web application that streams live AIS (Automatic Identification System) data, stores ship information locally using SQLite, and displays ships interactively on a map.

The application allows users to search vessels by ship name or MMSI number and view their latest position, speed, course, heading, and other navigation details.

---

 📸 Features

- 🌍 Real-time AIS ship tracking
- 🔎 Search ships by Name or MMSI
- 🛰️ Satellite Map views
- 📍 Interactive ship markers
- 📦 SQLite database storage
- 🔄 Automatic live updates
- ⚡ Fast local search
- 📊 Ship information popup
- 🌐 REST API built with Flask
- 🎯 Responsive frontend

---

 🛠️ Tech Stack

 Frontend

- HTML5
- CSS3
- JavaScript
- Leaflet.js
- OpenStreetMap
- Esri Satellite Tiles

 Backend

- Python
- Flask
- Flask-CORS
- WebSockets
- SQLite
- AISStream API

---

 📁 Project Structure

```
Project MM2/
│
├── backend/
│   ├── app.py
│   ├── ships.db
│   ├── requirements.txt
│   └── .env
│
├── frontend/
│   ├── index.html
│   ├── tracker.html
│   ├── css/
│   └── js/
│
├── .gitignore
└── README.md
```

---

 ⚙️ Installation

 1. Clone Repository

```bash
git clone https://github.com/YOUR_USERNAME/ShipTrack.git
```

```bash
cd ShipTrack
```

---

 2. Create Virtual Environment

Windows

```bash
python -m venv venv
```

Activate

```bash
venv\Scripts\activate
```

---

 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

 4. Create Environment File

Create a file named:

```
.env
```

Add your AISStream API key:

```env
AIS_API_KEY=YOUR_AISSTREAM_API_KEY
```

---

 5. Run Backend

```bash
python app.py
```

Backend runs at

```
http://localhost:5000
```

---

 6. Open Frontend

Open

```
frontend/index.html
```

or

```
frontend/tracker.html
```

using Live Server or any local web server.

---

 API Endpoints

 Home

```
GET /
```

Returns backend status.

---

 Health

```
GET /api/health
```

Returns

- Connection status
- Database ship count
- Live cache count

---

 Get Ships

```
GET /api/ships/all
```

Example

```
/api/ships/all?limit=5000
```

---

 Search Ship

```
GET /api/ships/search?query=EVER GIVEN
```

or

```
GET /api/ships/search?query=224936000
```

---

 Database

SQLite stores the latest information for every ship.

Table:

```
ships
```

Columns

- MMSI
- Name
- Latitude
- Longitude
- Speed
- Course
- Heading
- Navigation Status
- Ship Type
- Last Update

---

 Security

The project uses a `.env` file to securely store the AISStream API key.

The following files are ignored by Git:

```
.env
ships.db
ships.db-journal
```
---

 Future Improvements

- Ship route history
- Historical playback
- Vessel destination
- IMO lookup
- Flag detection
- Ship details panel
- Weather integration
- Port information
- User authentication
- Firebase/PostgreSQL support
- Docker deployment