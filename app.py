from flask import Flask, request, render_template, jsonify, redirect, url_for
import networkx as nx
from geopy.geocoders import Nominatim
import folium
import os

app = Flask(__name__)

# Inicializar el grafo dirigido
G = nx.DiGraph()

# Diccionario de ubicaciones iniciales vacío
locations = {
}
# Agregar nodos al grafo
for name, coords in locations.items():
    G.add_node(name, pos=coords)

# Geolocalizador
geolocator = Nominatim(user_agent="route_planner")

@app.route('/')
def index():
    return render_template('index.html', locations=G.nodes)

@app.route('/planificar', methods=['POST'])
def planificar():
    origen = request.form['origen']
    destino = request.form['destino']

    try:
        path = nx.dijkstra_path(G, origen, destino)
        coords = [G.nodes[n]['pos'] for n in path]

        # Crear mapa con Folium
        mapa = folium.Map(location=coords[0], zoom_start=13)
        folium.Marker(coords[0], tooltip="Inicio: " + origen).add_to(mapa)

        for i in range(1, len(coords)):
            folium.Marker(coords[i], tooltip=path[i]).add_to(mapa)
            folium.PolyLine([coords[i-1], coords[i]], color="blue", weight=2.5).add_to(mapa)

        os.makedirs("templates", exist_ok=True)
        mapa.save("templates/mapa.html")

        return render_template("mapa.html")

    except nx.NetworkXNoPath:
        return "No hay ruta disponible entre los puntos seleccionados."

@app.route('/agregar_paquete', methods=['POST'])
def agregar_paquete():
    nombre = request.form['nombre']
    direccion = request.form['direccion']

    location = geolocator.geocode(direccion)
    if location:
        coords = (location.latitude, location.longitude)
        G.add_node(nombre, pos=coords)

        # Conectar nuevo nodo con todos los existentes (distancias ficticias)
        for nodo in G.nodes:
            if nodo != nombre:
                G.add_edge(nombre, nodo, weight=5.0)
                G.add_edge(nodo, nombre, weight=5.0)

        return redirect(url_for('index'))
    else:
        return "No se pudo geolocalizar la dirección proporcionada."

if __name__ == '__main__':
    app.run(debug=True)
