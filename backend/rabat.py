import overpy
from neo4j_conn import Neo4jConnection

def get_way_center(way):
    lat_sum = 0
    lon_sum = 0
    count = len(way.nodes)
    for node in way.nodes:
        lat_sum += float(node.lat)
        lon_sum += float(node.lon)
    return lat_sum / count, lon_sum / count

def fetch_places(area_id, amenities):
    api = overpy.Overpass()
    all_places = []

    for amenity in amenities:
        query = f"""
        area({area_id})->.searchArea;
        (
          node["amenity"="{amenity}"](area.searchArea);
          way["amenity"="{amenity}"](area.searchArea);
          relation["amenity"="{amenity}"](area.searchArea);
        );
        out body;
        >;
        out skel qt;
        """
        print(f"Fetching {amenity} in area {area_id}...")
        result = api.query(query)

        for node in result.nodes:
            all_places.append({
                "name": node.tags.get("name", "Unknown"),
                "latitude": float(node.lat),
                "longitude": float(node.lon),
                "type": amenity
            })

        for way in result.ways:
            lat, lon = get_way_center(way)
            all_places.append({
                "name": way.tags.get("name", "Unknown"),
                "latitude": lat,
                "longitude": lon,
                "type": amenity
            })

    return all_places

if __name__ == "__main__":
    area_id = 3602799557  # ID de l'aire administrative de Rabat (prefecture)
    amenities = ["cafe", "pharmacy", "school", "restaurant"]

    places = fetch_places(area_id, amenities)
    print(f"Total places found: {len(places)}")
    for p in places[:10]:
        print(p)

    neo4j = Neo4jConnection("bolt://localhost:7687", "neo4j", "")
    for place in places:
        place['city'] = 'Fès'
        query = """
        MERGE (p:Place {name: $name, type: $type, latitude: $latitude, longitude: $longitude})
        """
        neo4j.query(query, place)
    neo4j.close()
