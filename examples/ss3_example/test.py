import os
import sys
from pathlib import Path

sys.path.append(f"{str(Path.home())}/Workspace/OpenModel/OntoFlow")

from ontoflow.engine import OntoFlowEngine
from tripper import Triplestore

# podman run -i --rm -p 3030:3030 -v databases:/fuseki/databases -t fuseki --update --loc databases/openmodel /openmodel

ONTOLOGY_PATH = os.path.abspath("ss3_complete.ttl")

ROOT = "http://open-model.eu/ontologies/ss3#FenicsOutput"

ts = Triplestore(
    backend="fuseki", triplestore_url="http://localhost:3030", database="openmodel"
)

ts.remove_database(
    backend="fuseki", triplestore_url="http://localhost:3030", database="openmodel"
)
ts.parse(ONTOLOGY_PATH, "turtle")

ts.bind("emmo", "http://emmo.info/emmo#")
ts.bind("ss3", "http://open-model.eu/ontologies/ss3#")

engine = OntoFlowEngine(triplestore=ts)

mapping = engine.getMappingRoute(ROOT)

mapping.export("output")
