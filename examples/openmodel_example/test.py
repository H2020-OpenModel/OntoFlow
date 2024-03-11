import os
import sys
from pathlib import Path

# sys.path.append(os.path.join(Path(os.path.abspath(__file__)).parent.parent.parent))
# from ontoflow.engine import OntoFlowEngine

sys.path.append(os.path.join(Path(os.path.abspath(__file__)).parent.parent.parent.parent))
from OntoFlow.ontoflow.engine import OntoFlowEngine


from tripper import Triplestore

# podman run -i --rm -p 3030:3030 -v databases:/fuseki/databases -t fuseki --update --loc databases/openmodel /openmodel

ONTOLOGY_PATH = os.path.join(Path(os.path.abspath(__file__)).parent, "openmodel_example.ttl")

ROOT = "http://webprotege.stanford.edu/Density"

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

engine = OntoFlowEngine(triplestore=ts)

mapping = engine.getMappingRoute(ROOT)

mapping.export(os.path.join(Path(os.path.abspath(__file__)).parent, "output"))
