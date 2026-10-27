import os
import re
import unicodedata

from rdflib import Graph, Namespace, URIRef, Literal
from rdflib.namespace import RDF, RDFS, OWL

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

SOURCE = os.path.join(BASE_DIR, "philosurfical_modified.ttl")
OUTPUT = os.path.join(BASE_DIR, "philosurfical_final.ttl")

graph = Graph()
graph.parse(SOURCE, format="turtle")

SCHEMA = Namespace("https://schema.org/")
EX = Namespace("http://example.org/philosurfical/")

graph.bind("ex", EX)

graph.add((EX.Thesis, RDF.type, OWL.Class))
graph.add((EX.TextFragment, RDF.type, OWL.Class))

graph.add((EX.hasTextFragment, RDF.type, OWL.ObjectProperty))
graph.add((EX.hasTextFragment, RDFS.domain, EX.Thesis))
graph.add((EX.hasTextFragment, RDFS.range, EX.TextFragment))

thesis_count = 0

for unit, _, number in list(graph.triples((None, SCHEMA.name, None))):
    if not isinstance(number, Literal):
        continue

    number_text = str(number).strip()

    if not re.fullmatch(r"\d+(?:\.\d+)*", number_text):
        continue

    if not str(unit).startswith(
        "http://wittgensteiniana.michelepasin.org/id/unit/"
    ):
        continue

    graph.add((unit, RDF.type, EX.Thesis))
    thesis_count += 1

fragment_count = 0

for fragment, _, unit in list(
    graph.triples((None, SCHEMA.exampleOfWork, None))
):
    if not str(fragment).startswith(
        "http://wittgensteiniana.michelepasin.org/id/fragment/"
    ):
        continue

    if (unit, RDF.type, EX.Thesis) not in graph:
        continue

    graph.add((fragment, RDF.type, EX.TextFragment))
    graph.add((unit, EX.hasTextFragment, fragment))
    fragment_count += 1

graph.add((EX.Author, RDF.type, OWL.Class))
graph.add((EX.hasAuthor, RDF.type, OWL.ObjectProperty))
graph.add((EX.hasAuthor, RDFS.range, EX.Author))


def make_uri(kind, owner, value):
    normalized = unicodedata.normalize("NFKD", value)
    slug = normalized.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", slug).strip("_")

    if not slug:
        slug = "entity"

    return URIRef(EX[f"{kind}/{slug}"])


author_triples = list(
    graph.triples((None, SCHEMA.author, None))
)

for subject, predicate, value in author_triples:
    if not isinstance(value, Literal):
        continue

    author_text = str(value).strip()

    if author_text == "D.F. Pears and B.F. McGuinness":
        authors = ["D.F. Pears", "B.F. McGuinness"]
    else:
        authors = [author_text]

    graph.remove((subject, predicate, value))

    for author_name in authors:
        author_entity = make_uri(
            "author", subject, author_name
        )

        graph.add((subject, EX.hasAuthor, author_entity))
        graph.add((author_entity, RDF.type, EX.Author))
        graph.add((
            author_entity,
            RDFS.label,
            Literal(author_name)
        ))

graph.serialize(OUTPUT, format="turtle")

print("Готово.")
print("Тезисов размечено:", thesis_count)
print("Связей с текстовыми фрагментами:", fragment_count)
print("Записей об авторах обработано:", len(author_triples))
print("Всего триплетов:", len(graph))
print("Файл:", OUTPUT)