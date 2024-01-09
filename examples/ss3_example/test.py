import sys

sys.path.append("../../")

from ontoflow.engine import generateYaml

generateYaml(
    "http://webprotege.stanford.edu/WaterDensityDatasetInput1",
    "http://webprotege.stanford.edu/Density",
)