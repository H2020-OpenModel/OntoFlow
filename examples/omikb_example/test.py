import os
from pathlib import Path

import sys

sys.path.append(os.path.join(Path(os.path.abspath(__file__)).parent.parent.parent))

from ontoflow.engine import OntoFlowEngine
from ontoflow.node import Node

from tripper import Triplestore


ts = Triplestore(
    backend="omikb",
    base_iri="http://example.com/omikb#",
    triplestore_url="https://openmodel.app/kb",
    database="dataset",
)

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
MCO = "basic"
FOLDER = str(Path(os.path.abspath(__file__)).parent)

# Get the routes ordered according to the MCO ranking
routes: list["Node"] = engine.getRoutes(TARGET, KPAS, MCO, foldername=FOLDER)

filtered: list["Node"] = Node.filterRoutes(routes)

for i, route in enumerate(filtered):
    route.visualize(f"ss3_lite_filtered_{i}", "png")
