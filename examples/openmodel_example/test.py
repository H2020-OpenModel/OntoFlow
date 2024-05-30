import os
from pathlib import Path

import sys
sys.path.append(os.path.join(Path(os.path.abspath(__file__)).parent.parent.parent))

from ontoflow.engine import OntoFlowEngine

from ontoflow.engine import OntoFlowEngine
from tripper import Triplestore

# Initialize the knowledge base
ONTOLOGY_PATH = os.path.join(
    Path(os.path.abspath(__file__)).parent, "openmodel_example.ttl"
)

TARGET = "http://webprotege.stanford.edu/Density"
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

KPAS = [
    {"name": "Accuracy", "weight": 3, "maximise": True},
    {"name": "SimulationTime", "weight": 5, "maximise": False},
    {"name": "OpenSource", "weight": 4, "maximise": True},
]

FOLDER = str(Path(os.path.abspath(__file__)).parent)

# Get the best route
bestRoute = engine.getBestRoute(TARGET, KPAS, MCO, FOLDER)

bestRoute.export(os.path.join(Path(os.path.abspath(__file__)).parent, "best"))
bestRoute.visualize(output=os.path.join(Path(os.path.abspath(__file__)).parent, "best"))
