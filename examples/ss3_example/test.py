import os
import sys

sys.path.append("/home/mbrigadoi/Workspace/OpenModel/OntoFlow")

from ontoflow.engine import OntoFlowEngine
from tripper import Triplestore

ONTOLOGY_PATH = os.path.abspath("openmodel_example.ttl")
# ONTOLOGY_PATH = os.path.abspath("ss3_complete.ttl")

ROOT = "http://webprotege.stanford.edu/Density"

ts = Triplestore(
    backend="fuseki", triplestore_url="http://localhost:3030", database="openmodel"
)

ts.bind("base", "http://webprotege.stanford.edu/")

engine = OntoFlowEngine(triplestore=ts)

# engine.loadOntology(ONTOLOGY_PATH)

engine.getMappingRoute(ROOT)

engine.generateYaml()
