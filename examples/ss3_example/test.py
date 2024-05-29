import os
from pathlib import Path

import sys
sys.path.append(os.path.join(Path(os.path.abspath(__file__)).parent.parent.parent))

from ontoflow.engine import OntoFlowEngine

from tripper import Triplestore

# podman run -i --rm -p 3030:3030 -v databases:/fuseki/databases -t fuseki --update --loc databases/openmodel /openmodel

# Initialize the knowledge base
ONTOLOGIES = ["ss3.ttl", "ss3kb.ttl"]
TARGET = "http://open-model.eu/ontologies/ss3#FenicsOutput"
MCO = "mods"

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
ts.bind("ss3", "http://open-model.eu/ontologies/ss3#")

# Initialize the engine
engine = OntoFlowEngine(triplestore=ts)

kpas = [
    {"name": "Accuracy", "weight": 3, "maximise": True},
    {"name": "SimulationTime", "weight": 2, "maximise": False},
    {"name": "OpenSource", "weight": 1, "maximise": True},
]

# Get the best route
bestRoute = engine.getBestRoute(
    TARGET, kpas, MCO, str(Path(os.path.abspath(__file__)).parent)
)
bestRoute.export(os.path.join(Path(os.path.abspath(__file__)).parent, "best"))
bestRoute.visualize(output=os.path.join(Path(os.path.abspath(__file__)).parent, "best"))
