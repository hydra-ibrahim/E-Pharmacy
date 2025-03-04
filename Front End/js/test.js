if (sessionStorage.getItem('mapCenter') == null) sessionStorage.setItem('mapCenter', JSON.stringify([35.53168, 35.79011]))

if (sessionStorage.getItem('point') == null) sessionStorage.setItem('point', JSON.stringify([36.53168, 36.79011]))


var map = L.map('map', {
    center: JSON.parse(sessionStorage.getItem('mapCenter')),
    zoom: 13
})

L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>'
}).addTo(map);

let layerGroup = L.layerGroup().addTo(map);


// Function to calculate icon size based on a percentage of the map container's size
function calculateIconSize() {
    var mapContainer = document.getElementById('map');
    var width = mapContainer.clientWidth;
    var height = mapContainer.clientHeight;

    // Define the relative size you want (e.g., 10% of map container's width and height)
    var relativeWidth = width * 0.03;
    var relativeHeight = width * 0.04;

    return [relativeWidth, relativeHeight];
}

// Function to calculate icon anchor based on the icon size
function calculateIconAnchor(iconSize) {
    // For bottom-center anchor
    return [iconSize[0] / 2, iconSize[1]];
}

// Function to calculate popup anchor based on the icon size
function calculatePopupAnchor(iconSize) {
    // Popup anchor at the top of the icon
    return [0, -iconSize[1]];
}

function onEachFeature(feature) {
    latlng = feature.geometry.coordinates

    sessionStorage.setItem('mapCenter', JSON.stringify(latlng))

    // Calculate initial icon size
    var iconSize = calculateIconSize();

    // Calculate initial icon anchor
    var iconAnchor = calculateIconAnchor(iconSize);

    // Calculate popup anchor
    var popupAnchor = calculatePopupAnchor(iconSize);

    // Create a marker with the custom icon and add it to the layer
    const pharmacy_marker = L.marker([latlng[1], latlng[0]], {
        icon: L.icon({
            iconUrl: './img/pharmacy.png',
            iconAnchor: iconAnchor,
            iconSize: iconSize,
            popupAnchor: popupAnchor
        })
    }).addTo(layerGroup);

    pharmacy = feature.properties.name;
    pharmacist = feature.properties.pharmacist;
    phone_number = feature.properties.phone_number;
    email = feature.properties.email;

    let popup = L.popup()
        .setLatLng(latlng)
        .setContent(`
                    <h1><center>${pharmacy}</center></h1>
                    <p><center>${pharmacist['first_name']} ${pharmacist['last_name']}</center></p>
                    <p>Phone Number: ${phone_number}</p>
                    <p>Email: ${email}</p>
                `)

    pharmacy_marker.bindPopup(popup);
}

function request(apiUrl) {
    fetch(apiUrl,
        {
            method: "GET",
            headers: {
                'Authorization': 'Token ' + sessionStorage.getItem('token')
            },
            mode: "cors",
        }
    )
        .then(response => {
            if (!response.ok) {
                if (response.status == 401) open('sign in.html', '_top')
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            layerGroup.clearLayers();
            data['features'].forEach(feature => {
                onEachFeature(feature)
            })

            document.getElementById('previous').addEventListener('click', function ff() { sessionStorage.setItem('url', data['previous'] == null ? apiUrl : data['previous']); open('nearest pharmacies.html', '_top') })
            document.getElementById('next').addEventListener('click', function ff() { sessionStorage.setItem('url', data['next'] == null ? apiUrl : data['next']); open('nearest pharmacies.html', '_top') })

            const queryString = data['next'];

            const urlParams = new URLSearchParams(queryString);

            const coords = data['features'][0]['geometry']['coordinates']

            const page = urlParams.get('page')

            document.getElementById('pointer').innerText = page == null ? data['count'] : page - 1

            let point = L.latLng(JSON.parse(sessionStorage.getItem('point')))
            let mapCenter = L.latLng(JSON.parse(sessionStorage.getItem('mapCenter')))
            let bounds = L.latLngBounds(L.latLng(point.lng, point.lat), L.latLng(mapCenter.lng, mapCenter.lat))

            // Calculate initial icon size
            var iconSize = calculateIconSize();

            // Calculate initial icon anchor
            var iconAnchor = calculateIconAnchor(iconSize);

            L.marker(L.latLng(point.lng, point.lat), {
                icon: L.icon({
                    iconUrl: './img/user.png',
                    iconAnchor: iconAnchor,
                    iconSize: iconSize
                })
            }).addTo(layerGroup)

            map.fitBounds(bounds);

            let modal_body = document.getElementById('modal-body')
            modal_body.replaceChildren()

            let table = document.createElement('table')
            table.setAttribute('class', 'table text-center table-bordered')
            modal_body.appendChild(table)

            let table_head = document.createElement('tr')
            table.appendChild(table_head)

            let week_day = document.createElement('th')
            week_day.innerText = 'Day'
            table_head.appendChild(week_day)

            let opens = document.createElement('th')
            opens.innerText = 'Opens'
            table_head.appendChild(opens)

            let closes = document.createElement('th')
            closes.innerText = 'Closes'
            table_head.appendChild(closes)

            data['features'][0]['properties']['business_hours'].forEach(day => {
                let d = document.createElement('tr')
                table.appendChild(d)

                let w_d = document.createElement('td')
                w_d.innerText = day.day_of_the_week
                d.appendChild(w_d)
                
                let os = document.createElement('td')
                os.innerText = day.opened_at != null && day.opened_at !== day.closes ? day.opened_at : 'open all day long'
                d.appendChild(os)
                if (os.innerText === 'open all day long') os.colSpan = 2
                else {
                    let cs = document.createElement('td')
                    cs.innerText = day.closed_at
                    d.appendChild(cs)
                }
            })
        })
        .catch(error => {
            console.error('Error:', error);
        });
}



let apiUrl;

if (sessionStorage.getItem('url') != null) onload = request(sessionStorage.getItem('url'))

map.on('click', function (e) {
    sessionStorage.setItem('point', JSON.stringify([e.latlng.lng, e.latlng.lat]))
    const point = JSON.parse(sessionStorage.getItem('point'))

    sessionStorage.setItem('url', `http://127.0.0.1:8000/api/pharmacies/?point=${point[0]},${point[1]}&format=json`)
    const apiUrl = sessionStorage.getItem('url');

    request(apiUrl);
})