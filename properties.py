import os
from rdflib import Graph, URIRef, Literal, BNode
from rdflib.namespace import RDF, OWL

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

SOURCE = os.path.join(BASE_DIR, "philosurfical.ttl")
OUTPUT = os.path.join(BASE_DIR, "philosurfical_modified.ttl")

graph = Graph()
graph.parse(SOURCE, format="turtle")

predicate_types = {}

for subject, predicate, obj in graph:
    if predicate == RDF.type:
        continue

    if isinstance(obj, Literal):
        value_type = "datatype"
    elif isinstance(obj, (URIRef, BNode)):
        value_type = "object"
    else:
        continue

    predicate_types.setdefault(predicate, set()).add(value_type)

object_count = 0
datatype_count = 0
mixed = []

for predicate, types in predicate_types.items():
    if types == {"object"}:
        graph.add((predicate, RDF.type, OWL.ObjectProperty))
        object_count += 1

    elif types == {"datatype"}:
        graph.add((predicate, RDF.type, OWL.DatatypeProperty))
        datatype_count += 1

    else:
        mixed.append(str(predicate))

graph.serialize(OUTPUT, format="turtle")

print("Файл сохранён:", OUTPUT)
print("Объектных свойств объявлено:", object_count)
print("Свойств данных объявлено:", datatype_count)
print("Предикатов требуют проверки:", len(mixed))

for predicate in mixed:
    print("Проверить:", predicate)