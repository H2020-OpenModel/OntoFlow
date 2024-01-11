import os
import sys

sys.path.append("../../")

from ontoflow.engine import OntoFlowEngine
from tripper import Triplestore

ONTOLOGY_PATH = os.path.abspath("openmodel_example.ttl")

ts = Triplestore(
    backend="fuseki", triplestore_url="http://localhost:3030", database="openmodel"
)

ts.bind("base", "http://webprotege.stanford.edu/")

engine = OntoFlowEngine(triplestore=ts)

# engine.loadOntology(ONTOLOGY_PATH)

engine.getMappingRoute(
    "http://webprotege.stanford.edu/Density",
)

engine.generateYaml()
