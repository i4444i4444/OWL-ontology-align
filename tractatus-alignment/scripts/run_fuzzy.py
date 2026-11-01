import json
from pathlib import Path

from ontoaligner import encoder, ontology
from ontoaligner.aligner import (
    SimpleFuzzySMLightweight,
    TokenSetFuzzySMLightweight,
    WeightedFuzzySMLightweight,
)
from rdflib import OWL, RDF, RDFS, Graph

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
TEMP_DIR = BASE_DIR / "temp"
RESULTS_DIR = BASE_DIR / "results" / "fuzzy"

TEMP_DIR.mkdir(exist_ok=True)
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

FILES = {
    "Wittgensteiniana": DATA_DIR / "wittgensteiniana_final.ttl",
    "WAB": DATA_DIR / "wab_tractatus_subgraph.ttl",
}


def prepare_ontology(name, source_path):
    graph = Graph()
    graph.parse(str(source_path), format="turtle")

    classes = set(graph.subjects(RDF.type, OWL.Class))
    classes.update(graph.subjects(RDF.type, RDFS.Class))

    for class_uri in classes:
        graph.add((class_uri, RDF.type, OWL.Class))

    xml_path = TEMP_DIR / f"{name.lower()}.rdf"
    graph.serialize(destination=str(xml_path), format="xml")

    parser = ontology.GenericOntology()
    return parser.parse(str(xml_path))


source_data = prepare_ontology(
    "Wittgensteiniana",
    FILES["Wittgensteiniana"]
)

target_data = prepare_ontology(
    "WAB",
    FILES["WAB"]
)

print("Wittgensteiniana classes:", len(source_data))
print("WAB classes:", len(target_data))

concept_encoder = encoder.ConceptParentLightweightEncoder()

encoded_data = concept_encoder(
    source=source_data,
    target=target_data
)

aligners = {
    "simple_fuzzy": SimpleFuzzySMLightweight(
        fuzzy_sm_threshold=0.3
    ),
    "weighted_fuzzy": WeightedFuzzySMLightweight(
        fuzzy_sm_threshold=0.3
    ),
    "token_set_fuzzy": TokenSetFuzzySMLightweight(
        fuzzy_sm_threshold=0.3
    ),
}

for name, aligner in aligners.items():
    print(f"\nRunning {name}...")

    results = aligner.generate(input_data=encoded_data)

    output_path = RESULTS_DIR / f"{name}.json"

    with open(output_path, "w", encoding="utf-8") as file:
        json.dump(results, file, ensure_ascii=False, indent=4, default=str)

    print("Results saved to:", output_path)