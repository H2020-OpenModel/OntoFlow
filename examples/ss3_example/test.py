import os
import sys
from pathlib import Path

sys.path.append(os.path.join(Path(os.path.abspath(__file__)).parent.parent.parent))
from ontoflow.engine import OntoFlowEngine

from tripper import Triplestore

# podman run -i --rm -p 3030:3030 -v databases:/fuseki/databases -t fuseki --update --loc databases/openmodel /openmodel

# Initialize the knowledge base
ONTOLOGY_PATH = os.path.join(Path(os.path.abspath(__file__)).parent, "ss3_v2.ttl")

ROOT = "http://open-model.eu/ontologies/ss3#FenicsOutput"
MCO = "mods"

__triplestore_url = os.getenv("TRIPLESTORE_URL", "http://localhost:3030")
ts = Triplestore(
    backend="fuseki", triplestore_url=__triplestore_url, database="openmodel"
)

ts.remove_database(
    backend="fuseki", triplestore_url=__triplestore_url, database="openmodel"
)

ts.parse(ONTOLOGY_PATH, "turtle")

ts.bind("emmo", "http://emmo.info/emmo#")
ts.bind("ss3", "http://open-model.eu/ontologies/ss3#")

# Initialize the engine
engine = OntoFlowEngine(triplestore=ts)

kpis = [
    {"name": "Cost1", "weight": 1, "maximise": True},
    {"name": "Cost2", "weight": 3, "maximise": False},
]

# Get the best route
bestRoute = engine.getBestRoute(
    ROOT, kpis, MCO, str(Path(os.path.abspath(__file__)).parent)
)
bestRoute.export(os.path.join(Path(os.path.abspath(__file__)).parent, "best"))
bestRoute.visualize(output=os.path.join(Path(os.path.abspath(__file__)).parent, "best"))
