 # -*- coding: utf-8 -*-
import sys
import re
import glob
import itertools
import json
import os
import sqlite3

FILENAME = 'congreso.sqlite'
PROVINCIAS = '''
Ciudad de Buenos Aires
Cdad. Aut. Bs. As.
Buenos Aires
Catamarca
Chaco
Chubut
Córdoba
Corrientes
Entre Ríos
Formosa
Jujuy
La Pampa
La Rioja
Mendoza
Misiones
Neuquén
Río Negro
Rio Negro
Salta
San Juan
San Luis
Santa Cruz
Santa Fe
Santiago del Estero
Tierra del Fuego
Tucumán
'''.strip().split('\n')
try:
    os.unlink(FILENAME)
except:
    pass

conn = sqlite3.connect(FILENAME)

c = conn.cursor()

c.execute('CREATE TABLE nodes (id INTEGER PRIMARY KEY AUTOINCREMENT, label TEXT, bloque TEXT, provincia TEXT)')
c.execute('CREATE TABLE edges (source INTEGER, target INTEGER, weight INT)')

legisladores = {}
edges = {}
for _, _, files in os.walk('.'):
    for f in files:
        if not f.endswith('.txt'):
            continue

        with open(f) as fp:
            data = fp.read()

        votacion = {}
        for nombre, bloque, provincia, voto in re.findall(r'(.+)\n\n(.+)\n\n(.+)\n\n(AUSENTE|NEGATIVO|AFIRMATIVO|ABSTENCION)', data):
            if nombre in ('MIRKIN, Beatriz Graciela', 'ELICECHE, Carlos Tomas', 'DOMINGUEZ, Julián Andrés'):
                continue
            votacion[nombre] = voto
            if nombre not in legisladores:
                if 'Hora:' in nombre:
                    continue
                if nombre == 'Buenos Aires' or provincia not in PROVINCIAS:
                    continue
                legisladores[nombre] = {
                    'id': len(legisladores) + 1,
                    'nombre': nombre,
                    'bloque': bloque,
                    'provincia': provincia,
                }
                c.execute('INSERT INTO nodes (id, label, bloque, provincia) VALUES (?, ?, ?, ?)', (
                            legisladores[nombre]['id'],
                            unicode(legisladores[nombre]['nombre'], 'utf-8'),
                            unicode(legisladores[nombre]['bloque'], 'utf-8'),
                            unicode(legisladores[nombre]['provincia'], 'utf-8'),
                            ))

        for l1, l2 in itertools.combinations(votacion.keys(), 2):
            if votacion[l1] != votacion[l2]:
                continue
            l1, l2 = min(l1, l2), max(l1, l2)
            if l1 not in edges:
                edges[l1] = {}
            if l2 in edges[l1]:
                edges[l1][l2] += 1
            else:
                edges[l1][l2] = 1

for l1, l2 in itertools.combinations(legisladores.keys(), 2):
    l1, l2 = min(l1, l2), max(l1, l2)
    edge = edges.get(l1, {}).get(l2, 0)
    c.execute('INSERT INTO edges (source, target, weight) VALUES (?, ?, ?)', (legisladores[l1]['id'], legisladores[l2]['id'], edge))

conn.commit()
c.close()
