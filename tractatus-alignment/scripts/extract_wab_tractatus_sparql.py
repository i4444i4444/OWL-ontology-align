from pathlib import Path

from rdflib import OWL, RDF, RDFS, BNode, Graph, Namespace, URIRef
from rdflib.namespace import XSD


# Configuration

BASE_DIR = Path(__file__).resolve().parent.parent
ONTOLOGY_PATH = BASE_DIR / "data" / "wittgenstein.owl"
OUTPUT_PATH = BASE_DIR / "data" / "wab_tractatus_subgraph.ttl"

WAB = Namespace("http://purl.org/wittgensteinsource/ont/")
INSTANCES = Namespace("http://purl.org/wittgensteinsource/ont/instances/")


# Load source

print(f"Loading: {ONTOLOGY_PATH}")

source = Graph()
source.parse(str(ONTOLOGY_PATH), format="xml")

print(f"Source triples: {len(source):,}")

target = Graph()

target.bind("wab", WAB)
target.bind("inst", INSTANCES)
target.bind("rdf", RDF)
target.bind("rdfs", RDFS)
target.bind("owl", OWL)
target.bind("xsd", XSD)


# SPARQL queries

# 1. Everything directly attached to W-TLP

Q1 = """
PREFIX wab: <http://purl.org/wittgensteinsource/ont/>
PREFIX inst: <http://purl.org/wittgensteinsource/ont/instances/>

CONSTRUCT {
    ?s ?p ?o .
}
WHERE {
    {
        inst:W-TLP ?p ?o .
        BIND(inst:W-TLP AS ?s)
    }
    UNION
    {
        ?s ?p inst:W-TLP .
    }
}
"""


# 2. Direct parts of W-TLP + their immediate triples

Q2 = """
PREFIX wab: <http://purl.org/wittgensteinsource/ont/>
PREFIX inst: <http://purl.org/wittgensteinsource/ont/instances/>

CONSTRUCT {
    ?part ?p ?o .
    ?s ?p2 ?part .
}
WHERE {
    inst:W-TLP wab:hasPart ?part .

    {
        ?part ?p ?o .
    }
    UNION
    {
        ?s ?p2 ?part .
    }
}
"""


# 3. Resources published in W-TLP + their triples

Q3 = """
PREFIX wab: <http://purl.org/wittgensteinsource/ont/>
PREFIX inst: <http://purl.org/wittgensteinsource/ont/instances/>

CONSTRUCT {
    ?res ?p ?o .
    ?s ?p2 ?res .
}
WHERE {
    ?res wab:isPublishedInWork inst:W-TLP .

    {
        ?res ?p ?o .
    }
    UNION
    {
        ?s ?p2 ?res .
    }
}
"""


# 4. Resources from which W-TLP was published + their triples

Q4 = """
PREFIX wab: <http://purl.org/wittgensteinsource/ont/>
PREFIX inst: <http://purl.org/wittgensteinsource/ont/instances/>

CONSTRUCT {
    ?res ?p ?o .
    ?s ?p2 ?res .
}
WHERE {
    inst:W-TLP wab:isWorkPublishedFrom ?res .

    {
        ?res ?p ?o .
    }
    UNION
    {
        ?s ?p2 ?res .
    }
}
"""


# Execute queries

def run_construct(query: str, label: str):
    print(f"\nRunning: {label}")

    result = source.query(query)
    before = len(target)

    for triple in result:
        target.add(triple)

    print(
        f"  +{len(target) - before:,} triples "
        f"(total: {len(target):,})"
    )


run_construct(Q1, "Q1 – triples directly involving W-TLP")
run_construct(Q2, "Q2 – hasPart neighbourhood")
run_construct(Q3, "Q3 – isPublishedInWork neighbourhood")
run_construct(Q4, "Q4 – isWorkPublishedFrom neighbourhood")


# Add hasAuthor relationships only for resources already selected by Q1-Q4

HAS_AUTHOR = URIRef(
    "http://purl.org/wittgensteinsource/ont/scholar/0.1/hasAuthor"
)

print("\nAdding hasAuthor relationships to selected resources...")

selected_resources = {
    s
    for s in target.subjects()
    if isinstance(s, URIRef)
}

before = len(target)

for resource in selected_resources:
    for author in source.objects(resource, HAS_AUTHOR):
        target.add((resource, HAS_AUTHOR, author))

print(
    f"  +{len(target) - before:,} hasAuthor triples "
    f"(total: {len(target):,})"
)


# Collect classes already present in the extracted graph

classes = set()

for obj in target.objects(None, RDF.type):
    if isinstance(obj, URIRef):
        classes.add(obj)

classes.update(
    s
    for s in target.subjects(RDF.type, RDFS.Class)
    if isinstance(s, URIRef)
)

classes.update(
    s
    for s in target.subjects(RDF.type, OWL.Class)
    if isinstance(s, URIRef)
)

classes.add(WAB.WittgensteinExternalSource)

# Restore the complete superclass hierarchy

print("\nRestoring class hierarchy...")

hierarchy_triples = set()
classes_to_process = set(classes)
processed_classes = set()

while classes_to_process:
    current_class = classes_to_process.pop()

    if current_class in processed_classes:
        continue

    processed_classes.add(current_class)

    for parent in source.objects(current_class, RDFS.subClassOf):
        hierarchy_triples.add(
            (current_class, RDFS.subClassOf, parent)
        )

        if isinstance(parent, URIRef):
            classes_to_process.add(parent)

before = len(target)

for triple in hierarchy_triples:
    target.add(triple)

print(
    f"  +{len(target) - before:,} hierarchy triples "
    f"(total: {len(target):,})"
)


# Collect classes and properties used in the current target graph

used = set()

for s, p, o in target:
    if isinstance(s, URIRef):
        used.add(s)

    if isinstance(p, URIRef):
        used.add(p)

    if isinstance(o, URIRef):
        used.add(o)

used.update(processed_classes)


# Filter ontology terms

schema_entities = [
    entity
    for entity in used
    if str(entity).startswith(str(WAB))
    or str(entity).startswith("http://www.w3.org/")
]

# Restore WittgensteinExternalSource hierarchy

EXTERNAL_SOURCE = WAB.WittgensteinExternalSource
PRIMARY_SOURCE = WAB.PrimarySource

if (EXTERNAL_SOURCE, RDFS.subClassOf, PRIMARY_SOURCE) in source:
    target.add(
        (EXTERNAL_SOURCE, RDFS.subClassOf, PRIMARY_SOURCE)
    )
    print("Restored: WittgensteinExternalSource -> PrimarySource")
else:
    print("Warning: hierarchy relation not found in source")
    
# Schema information for classes and properties

Q5_TEMPLATE = """
PREFIX rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX owl:  <http://www.w3.org/2002/07/owl#>

CONSTRUCT {
    ?entity rdf:type ?type .
    ?entity rdfs:label ?label .
    ?entity rdfs:comment ?comment .
    ?entity rdfs:subClassOf ?super .
    ?entity rdfs:domain ?domain .
    ?entity rdfs:range ?range .
}
WHERE {
    VALUES ?entity { %s }

    OPTIONAL { ?entity rdf:type ?type }
    OPTIONAL { ?entity rdfs:label ?label }
    OPTIONAL { ?entity rdfs:comment ?comment }
    OPTIONAL { ?entity rdfs:subClassOf ?super }
    OPTIONAL { ?entity rdfs:domain ?domain }
    OPTIONAL { ?entity rdfs:range ?range }
}
"""


if schema_entities:
    chunk_size = 200

    for i in range(0, len(schema_entities), chunk_size):
        chunk = schema_entities[i:i + chunk_size]

        values_str = " ".join(
            f"<{entity}>"
            for entity in chunk
        )

        q5 = Q5_TEMPLATE % values_str

        run_construct(
            q5,
            f"Q5 – schema declarations (chunk {i // chunk_size + 1})"
        )


# Clean empty blank nodes in rdfs:domain / rdfs:range

print("\nCleaning empty blank nodes in rdfs:domain / rdfs:range...")

empty_bnodes = {
    o
    for s, p, o in target
    if p in (RDFS.domain, RDFS.range)
    and isinstance(o, BNode)
    and not any(target.triples((o, None, None)))
}

removed = 0

for s, p, o in list(target):
    if o in empty_bnodes:
        target.remove((s, p, o))
        removed += 1

print(f"  removed {removed} empty domain/range triples")


# Save

print(f"\nSaving subgraph → {OUTPUT_PATH}")

OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

target.serialize(
    destination=str(OUTPUT_PATH),
    format="turtle"
)

print(f"Done. Final size: {len(target):,} triples")