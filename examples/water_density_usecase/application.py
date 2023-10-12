import os

from ontoflow.engine import OntoFlowDMEngine
from ontoflow.mco_strategies.minimumCostStrategy import MinimumCostStrategy
from tripper import Triplestore

ONTOLOGY_FOLDER = __file__
ONTOLOGY_FILENAME = "openmodel-inferred.ttl"
INDIVIDUALS_FILENAME = "individuals2.ttl"


if __name__ == "__main__":
    mco_strategy = MinimumCostStrategy()

    ## Init triplestore
    Triplestore.remove_database(
        backend="fuseki", database="ontoflow", triplestore_url="http://localhost:3030"
    )
    Triplestore.create_database(
        backend="fuseki", database="ontoflow", triplestore_url="http://localhost:3030"
    )
    ts = Triplestore(
        backend="fuseki", triplestore_url="http://localhost:3030", database="ontoflow"
    )

    # Add ontology and individuals
    print(os.path.join(ONTOLOGY_FILENAME))
    ts.parse(os.path.join(ONTOLOGY_FILENAME), format="turtle")
    ts.parse(os.path.join(INDIVIDUALS_FILENAME), format="turtle")

    engine = OntoFlowDMEngine(
        triplestore=ts,
        cost_file="/home/pinter/Documents/OpenModel/OntoFlow/examples/datamodel_generation/cost_definitions.yaml",
        mco_interface=mco_strategy,
    )

    target_IRI = "http://emmo.info/emmo#FluidDensity"
    sources_IRIs = {}
    route = engine.getmappingroute(target_IRI, sources_IRIs)

    print(route[target_IRI].show())
