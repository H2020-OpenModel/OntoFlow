import os

from tripper import Triplestore
from ontoflow.engine import OntoFlowDMEngine, OntoFlowEngineMappingStep, OntoFlowEngineValue
from ontoflow.mco_strategies.minimumCostStrategy import MinimumCostStrategy
from tripper.mappings import mapping_routes as tripper_mapping_routes


ONTOLOGY_FOLDER = r"C:\Users\alexc\Desktop\Universita\Ricerca\OpenModel\ExecFlowDemo\OntoKB"
ONTOLOGY_FILENAME = "openmodel-inferred.ttl"
INDIVIDUALS_FILENAME = "individuals2.ttl"


if __name__ == "__main__":
    
    mco_strategy = MinimumCostStrategy()

    ## Init triplestore
    Triplestore.remove_database(backend="stardog", database="d55_usecase", triplestore_url="http://localhost:5820")
    Triplestore.create_database(backend="stardog", database="d55_usecase", triplestore_url="http://localhost:5820")
    ts = Triplestore(backend="stardog", triplestore_url="http://localhost:5820", database="d55_usecase")

    # Add ontology and individuals
    ts.parse(os.path.join(ONTOLOGY_FOLDER, ONTOLOGY_FILENAME), format="turtle")
    ts.parse(os.path.join(ONTOLOGY_FOLDER, INDIVIDUALS_FILENAME), format="turtle")


    engine = OntoFlowDMEngine(triplestore = ts, cost_file = r"C:\Users\alexc\Desktop\Universita\Ricerca\OpenModel\OntoFlow\examples\datamodel_generation\cost_definitions.yaml", mco_interface = mco_strategy)

    target_IRI = "http://emmo.info/emmo#FluidDensity"
    sources_IRIs = {}
    route = engine.getmappingroute(target_IRI, sources_IRIs)

    print(route[target_IRI].show())



    # route = tripper_mapping_routes(target_IRI, sources_IRIs, triplestore=ts, mappingstep_class=OntoFlowEngineMappingStep, value_class=OntoFlowEngineValue)


    # print(route.show())
