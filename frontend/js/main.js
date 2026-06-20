// Landing page — animated satellite background map
const map = L.map('bg-map', {
  zoomControl: false,
  dragging: false,
  scrollWheelZoom: false,
  doubleClickZoom: false,
  keyboard: false,
  attributionControl: false
}).setView([20, 0], 2);

// Esri World Imagery (free satellite tiles)
L.tileLayer(
  'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
  { maxZoom: 19 }
).addTo(map);

// Slow auto-pan for cinematic effect
let lng = 0;
setInterval(() => {
  lng += 0.04;
  map.panTo([20, lng], { animate: true, duration: 1 });
}, 1000);