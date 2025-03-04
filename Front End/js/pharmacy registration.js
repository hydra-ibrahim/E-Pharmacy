var map = L.map('map', {
    center: [35.53168, 35.79011],
    zoom: 13
})


L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>'
}).addTo(map);


map.on('click', function (e) {
    document.getElementById('pharmacy-longitude').value = e.latlng.lng
    document.getElementById('pharmacy-latitude').value = e.latlng.lat
})