import os
from pathlib import Path

import sys
sys.path.append(os.path.join(Path(os.path.abspath(__file__)).parent.parent.parent))

from ontoflow.engine import OntoFlowEngine
from ontoflow.node import Node

from tripper import Triplestore

# podman run -i --rm -p 3030:3030 -v databases:/fuseki/databases -t fuseki --update --loc databases/openmodel /openmodel

# Initialize the knowledge base
ONTOLOGIES = ["ss3.ttl"]

__triplestore_url = os.getenv("TRIPLESTORE_URL", "http://localhost:3030")
ts = Triplestore(
    backend="fuseki", triplestore_url=__triplestore_url, database="openmodel"
)

ts.remove_database(
    backend="fuseki", triplestore_url=__triplestore_url, database="openmodel"
)

for ontology in ONTOLOGIES:
    ts.parse(os.path.join(Path(os.path.abspath(__file__)).parent, ontology), "turtle")


ts.bind("emmo", "https://w3id.org/emmo#")
ts.bind("simsoft", "http://open-model.eu/domain/simulationsoftware#")

# Initialize the engine
engine = OntoFlowEngine(triplestore=ts)

TARGET = "http://open-model.eu/ontologies/ss3#FenicsOutput"
KPAS = [
    {"name": "Accuracy", "weight": 3, "maximise": True},
    {"name": "SimulationTime", "weight": 2, "maximise": False},
    {"name": "OpenSource", "weight": 1, "maximise": True},
]
MCO = "mods"
FOLDER = str(Path(os.path.abspath(__file__)).parent)

# Get the routes ordered according to the MCO ranking
routes: list["Node"] = engine.getRoutes(TARGET, KPAS, MCO, foldername=FOLDER)

filtered: list["Node"] = Node.filterIncompleteRoutes(routes)

for i, route in enumerate(filtered):
    route.visualize(f"filtered_{i}", "png")
