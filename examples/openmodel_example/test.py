import os
from pathlib import Path

from ontoflow.engine import OntoFlowEngine

from tripper import Triplestore

# podman run -i --rm -p 3030:3030 -v databases:/fuseki/databases -t fuseki --update --loc databases/openmodel /openmodel

# Initialize the knowledge base
ONTOLOGY_PATH = os.path.join(
    Path(os.path.abspath(__file__)).parent, "openmodel_example.ttl"
)

ROOT = "http://webprotege.stanford.edu/Density"
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
ts.bind("base", "http://webprotege.stanford.edu/")

# Initialize the engine
engine = OntoFlowEngine(triplestore=ts)

kpis = [
    {"name": "Accuracy", "weight": 3, "maximise": True},
    {"name": "SimulationTime", "weight": 1, "maximise": False},
    {"name": "OpenSource", "weight": 5, "maximise": False},
]

# Get the best route
bestRoute = engine.getBestRoute(
    ROOT, kpis, MCO, str(Path(os.path.abspath(__file__)).parent)
)

bestRoute.export(os.path.join(Path(os.path.abspath(__file__)).parent, "best"))
bestRoute.visualize(output=os.path.join(Path(os.path.abspath(__file__)).parent, "best"))
