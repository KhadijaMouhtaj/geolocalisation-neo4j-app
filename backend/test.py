from flask import Flask, request, jsonify
from neo4j_conn import Neo4jConnection
from flask_cors import CORS
import requests
import polyline
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "http://localhost:3000"}})


# Connexion Neo4j
neo4j = Neo4jConnection("bolt://localhost:7687", "neo4j", "")

# Ta clé OpenRouteService (remplace par ta clé personnelle)
ORS_API_KEY = '5b3ce3597851110001cf62481d3e59f364a84824b098bd8fec245c9b'

@app.route('/place-types', methods=['GET'])
def list_place_types():
    query = "MATCH (p:Place) RETURN DISTINCT p.type AS type"
    results = neo4j.query(query)
    types = [r['type'] for r in results]
    return jsonify({"types": types})

@app.route('/places/nearby', methods=['POST'])
def places_nearby():
    data = request.get_json()
    lat = data.get('latitude')
    lon = data.get('longitude')
    place_type = data.get('type')

    if lat is None or lon is None or not place_type:
        return jsonify({'error': 'latitude, longitude et type sont requis'}), 400

    query = """
WITH point({latitude: $lat, longitude: $lon}) AS userLocation
MATCH (p:Place {type: $type, city: $city})
WHERE p.latitude IS NOT NULL AND p.longitude IS NOT NULL
WITH p, point.distance(userLocation, point({latitude: p.latitude, longitude: p.longitude})) AS dist
RETURN p.name AS name, p.latitude AS latitude, p.longitude AS longitude, dist
ORDER BY dist ASC
LIMIT 10
"""



    params = {'lat': lat, 'lon': lon, 'type': place_type}
    results = neo4j.query(query, params)
    return jsonify(results)

@app.route('/route', methods=['POST'])
def route():
    data = request.get_json()
    start = data.get('start')
    end = data.get('end')
    profile = data.get('mode', 'driving-car')  # facultatif si mode passé

    print("Start:", start)
    print("End:", end)

    if start is None or end is None:
        return {"error": "Missing required keys: 'start' and 'end'"}, 400

    url = f"https://api.openrouteservice.org/v2/directions/{profile}"
    headers = {
        'Authorization': ORS_API_KEY,
        'Content-Type': 'application/json'
    }
    body = {
        "coordinates": [
            [start['longitude'], start['latitude']],
            [end['longitude'], end['latitude']]
        ],
       
    }

    try:
        response = requests.post(url, json=body, headers=headers)
        response.raise_for_status()
        return jsonify(response.json())
    except requests.exceptions.RequestException as e:
        print("⚠️ ERREUR ORS :", e)
        if e.response is not None:
            print("Contenu réponse ORS :", e.response.text)
        return jsonify({'error': 'Error contacting OpenRouteService'}), 500


@app.route('/build-near-relationships', methods=['POST'])
def build_near_relationships():
    data = request.get_json()
    place_type = data.get('type')

    if not place_type:
        return jsonify({'error': 'type requis'}), 400

    query = """
MATCH (p:Place {type: $type, city: 'Fès'})
RETURN p.name AS name, p.latitude AS latitude, p.longitude AS longitude
"""

    places = neo4j.query(query, {"type": place_type})

    for i, place1 in enumerate(places):
        for j, place2 in enumerate(places):
            if i >= j:
                continue
            url = f"http://router.project-osrm.org/route/v1/driving/{place1['longitude']},{place1['latitude']};{place2['longitude']},{place2['latitude']}?overview=false"
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                if data["routes"]:
                    duration = round(data["routes"][0]["duration"] / 60)
                    if duration <= 10:
                        query_rel = """
                        MATCH (a:Place {name: $name1, type: $type, city: 'Fès'})
                        MATCH (b:Place {name: $name2, type: $type, city: 'Fès'})
                        MERGE (a)-[:NEAR {duration: $duration}]->(b)

                        """
                        neo4j.query(query_rel, {
                            "name1": place1["name"],
                            "name2": place2["name"],
                            "duration": duration,
                            "type": place_type
                        })

    return jsonify({"message": "Relations NEAR créées avec succès."})

@app.route('/places/near-places', methods=['POST'])
def near_places():
    data = request.get_json()

    def parse_coord(value):
        try:
            return float(str(value).replace(',', '.'))
        except:
            return None

    lat = parse_coord(data.get("latitude"))
    lon = parse_coord(data.get("longitude"))
    place_type = data.get("type")
    max_duration = data.get("max_duration", 5)
    city = data.get("city", "Fès")  # Valeur par défaut

    print("🔍 Données reçues :", data)
    print("Latitude :", lat)
    print("Longitude :", lon)
    print("Type :", place_type)
    print("Ville :", city)

    if lat is None or lon is None or not place_type:
        return jsonify({'error': 'latitude, longitude, type requis'}), 400

    query = """
WITH point({latitude: $lat, longitude: $lon}) AS userLocation
MATCH (start:Place {type: $type, city: $city})
WITH start, point.distance(userLocation, point({latitude: start.latitude, longitude: start.longitude})) AS dist
ORDER BY dist
LIMIT 1
MATCH (start)-[r:NEAR]->(target:Place)
WHERE r.duration <= $max_duration
RETURN target.name AS name, target.latitude AS latitude, target.longitude AS longitude, r.duration AS duration
ORDER BY r.duration ASC
"""

    results = neo4j.query(query, {
        "lat": lat,
        "lon": lon,
        "type": place_type,
        "max_duration": max_duration,
        "city": city
    })

    filtered_results = [r for r in results if r["name"] != "Unknown"]
    return jsonify(filtered_results)



if __name__ == "__main__":
    app.run(debug=True, port=5001)
