import os
import sys
from pathlib import Path

sys.path.append(
    os.path.join(Path(os.path.abspath(__file__)).parent.parent.parent.parent)
)
from OntoFlow.ontoflow.engine import OntoFlowEngine

from tripper import Triplestore

# podman run -i --rm -p 3030:3030 -v databases:/fuseki/databases -t fuseki --update --loc databases/openmodel /openmodel

ONTOLOGY_PATH = os.path.join(Path(os.path.abspath(__file__)).parent, "ss3_v2.ttl")

ROOT = "http://open-model.eu/ontologies/ss3#FenicsOutput"

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

engine = OntoFlowEngine(triplestore=ts)

bestRoute = engine.getBestRoute(ROOT, ["ModelParameter", "Cost1", "Cost2"])
bestRoute.export(os.path.join(Path(os.path.abspath(__file__)).parent, "output"))
bestRoute.visualize(
    output=os.path.join(Path(os.path.abspath(__file__)).parent, "output.png")
)
