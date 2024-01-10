import os
import sys

sys.path.append("../../")

from ontoflow.engine import generateYaml, loadOntology

ONTOLOGY_PATH = os.path.abspath("openmodel_example.ttl")

# loadOntology(ONTOLOGY_PATH)

generateYaml(
    "http://webprotege.stanford.edu/WaterDensityDatasetInput1",
    "http://webprotege.stanford.edu/Density",
)
