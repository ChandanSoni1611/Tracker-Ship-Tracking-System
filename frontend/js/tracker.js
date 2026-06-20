console.log("TRACKER JS LOADED");

window.addEventListener("beforeunload", () => {
    console.log("PAGE RELOAD DETECTED");
});

const API_BASE = "http://127.0.0.1:5000";

// =========================
// MAP
// =========================

const map = L.map("map", {
    zoomControl: true
}).setView([20, 0], 2);

// Street Layer
const streetLayer = L.tileLayer(
    "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
    {
        attribution: "&copy; OpenStreetMap contributors"
    }
);

// Satellite Layer
const satelliteLayer = L.tileLayer(
    "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
    {
        attribution: "Tiles © Esri"
    }
);

// Default = Satellite
satelliteLayer.addTo(map);

// Layer Switcher
L.control.layers(
    {
        "🗺️ Street Map": streetLayer,
        "🛰️ Satellite": satelliteLayer
    }
).addTo(map);

const markers = {};

const shipCount = document.getElementById("ship-count");
const listCount = document.getElementById("list-count");
const shipList = document.getElementById("ship-list");
const statusBox = document.getElementById("status-box");

const btnTrack = document.getElementById("btn-track");
const btnStop = document.getElementById("btn-stop");

const inpName = document.getElementById("inp-name");
const inpMmsi = document.getElementById("inp-mmsi");

let refreshInterval = null;

function setStatus(text, type = "idle") {
    statusBox.innerText = text;
    statusBox.className = `status ${type}`;
}

function clearMarkers() {
    for (const key in markers) {
        map.removeLayer(markers[key]);
    }

    Object.keys(markers).forEach(k => delete markers[k]);

    shipList.innerHTML = "";
}

function addShipToMap(ship) {

    if (!ship.lat || !ship.lon) return;

    const lat = parseFloat(ship.lat);
    const lon = parseFloat(ship.lon);

    if (isNaN(lat) || isNaN(lon)) return;

const popup = `
<div class="ship-popup">

    <h3>🛳️ ${ship.name || "Unknown Vessel"}</h3>

    <table>
        <tr>
            <td>MMSI</td>
            <td>${ship.mmsi || "-"}</td>
        </tr>

        <tr>
            <td>Speed</td>
            <td>${ship.speed || 0} knots</td>
        </tr>

        <tr>
            <td>Course</td>
            <td>${ship.course || 0}°</td>
        </tr>

        <tr>
            <td>Heading</td>
            <td>${ship.heading || "-"}</td>
        </tr>

        <tr>
            <td>Latitude</td>
            <td>${Number(ship.lat).toFixed(5)}</td>
        </tr>

        <tr>
            <td>Longitude</td>
            <td>${Number(ship.lon).toFixed(5)}</td>
        </tr>

        <tr>
            <td>Status</td>
            <td>${ship.nav_status || "-"}</td>
        </tr>

        <tr>
            <td>Type</td>
            <td>${ship.type || "Unknown"}</td>
        </tr>

        <tr>
            <td>Updated</td>
            <td>${ship.time_utc || "-"}</td>
        </tr>
    </table>

</div>
`;

    if (markers[ship.mmsi]) {

        markers[ship.mmsi].setLatLng([lat, lon]);
        markers[ship.mmsi].setPopupContent(popup);

    } else {

        const marker = L.marker([lat, lon]).addTo(map);

        marker.bindPopup(popup);

        markers[ship.mmsi] = marker;
    }
}

function updateShipList(ships) {

    shipList.innerHTML = "";

    ships.slice(0, 100).forEach(ship => {

        const li = document.createElement("li");

        li.innerHTML = `
            <strong>${ship.name || "Unknown"}</strong><br>
            MMSI: ${ship.mmsi}
        `;

        li.onclick = () => {

            if (markers[ship.mmsi]) {

                map.setView(
                    [ship.lat, ship.lon],
                    8
                );

                markers[ship.mmsi].openPopup();
            }
        };

        shipList.appendChild(li);
    });

    listCount.innerText = `(${ships.length})`;
}

async function fetchShips() {

    try {

        const name = inpName.value.trim();
        const mmsi = inpMmsi.value.trim();

        let url = `${API_BASE}/api/ships/all`;

        if (name || mmsi) {

            const query = mmsi || name;

            url =
                `${API_BASE}/api/ships/search?query=` +
                encodeURIComponent(query);
        }

        const response = await fetch(url);
        const data = await response.json();

        let ships = [];

        // Search endpoint returns array
        if (Array.isArray(data)) {
            ships = data;
        }
        // All ships endpoint returns object
        else {
            ships = data.ships || [];
        }

        clearMarkers();

        ships.forEach(ship => {
            addShipToMap(ship);
        });

        updateShipList(ships);

        shipCount.innerText = ships.length;

        // =========================
        // AUTO FIT TO SHIPS
        // =========================

        if (ships.length === 1) {

            const ship = ships[0];

            map.setView(
                [
                    parseFloat(ship.lat),
                    parseFloat(ship.lon)
                ],
                10
            );
        }
        else if (ships.length > 1) {

            const bounds = [];

            ships.forEach(ship => {

                if (
                    ship.lat &&
                    ship.lon
                ) {
                    bounds.push([
                        parseFloat(ship.lat),
                        parseFloat(ship.lon)
                    ]);
                }
            });

            if (bounds.length > 0) {

                map.fitBounds(
                    bounds,
                    {
                        padding: [50, 50],
                        maxZoom: 8
                    }
                );
            }
        }

        if (ships.length > 0) {

            setStatus(
                `Showing ${ships.length} ships`,
                "active"
            );

        } else {

            setStatus(
                "No matching ships found",
                "error"
            );
        }

    } catch (err) {

        console.error(err);

        setStatus(
            "Backend connection failed",
            "error"
        );
    }
}

btnTrack.addEventListener("click", () => {

    fetchShips();

    if (refreshInterval) {
        clearInterval(refreshInterval);
    }

    refreshInterval = setInterval(fetchShips, 10000);

    btnTrack.disabled = true;
    btnStop.disabled = false;
});

btnStop.addEventListener("click", () => {

    clearInterval(refreshInterval);

    refreshInterval = null;

    clearMarkers();

    shipCount.innerText = "0";
    listCount.innerText = "(0)";

    setStatus("Tracking stopped", "idle");

    btnTrack.disabled = false;
    btnStop.disabled = true;
});