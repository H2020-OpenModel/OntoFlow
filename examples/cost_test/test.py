import os
import io
import sys
import pydot

from pathlib import Path
from tripper.triplestore import Triplestore, XSD
from os.path import dirname, abspath
from rdflib.tools.rdf2dot import rdf2dot
from rdflib import Graph, URIRef, Namespace, BNode, Literal

sys.path.append(
    os.path.join(Path(os.path.abspath(__file__)).parent.parent.parent.parent)
)
from OntoFlow.ontoflow.engine import OntoFlowEngine

example_ns = Namespace("http://openmodel.ontoflow/examples#")
example_individual_ns = Namespace("http://openmodel.ontoflow/examples/individuals#")
owl = Namespace("http://www.w3.org/2002/07/owl#")
rdf = Namespace("http://www.w3.org/1999/02/22-rdf-syntax-ns#")
rdfs = Namespace("http://www.w3.org/2000/01/rdf-schema#")
emmo = Namespace("http://emmo.info/emmo#")
webprotege = Namespace("http://webprotege.stanford.edu/")


# PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
# PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
# SELECT * WHERE {
#   GRAPH <graph://main> {
#  	?sub ?pred ?obj . 
#   }
# }

def accuracy_converter(accuracy_str):
    if accuracy_str == "Low":
        return 10
    elif accuracy_str == "Medium":
        return 20
    elif accuracy_str == "High":
        return 30
    else:
        return 0
    
def mirror_converter(value):
    return int(value)

def cpu_time_converter(cpu_time_str):
    return int(cpu_time_str)

def visualize(g, name="example.png"):
    stream = io.StringIO()
    rdf2dot(g, stream)
    (graph,) = pydot.graph_from_dot_data(stream.getvalue())
    graph.write_png(os.path.join(Path(os.path.abspath(__file__)).parent, name))

if __name__ == "__main__":
    g = Graph()
    g.bind("example", example_ns)

    __triplestore_url = os.getenv("TRIPLESTORE_URL", "http://localhost:3030")
    ts = Triplestore(backend="fuseki", triplestore_url=__triplestore_url, database="openmodel", base_iri=example_ns)
    ts.remove_database(backend="fuseki", triplestore_url=__triplestore_url, database="openmodel")
    ts.bind("example", example_ns)
    # ts.bind("rdf", rdf)
    # ts.bind("rdfs", rdfs)
    # ts.bind("owl", owl)
    # ts.bind("emmo", emmo)

    # Option 1
    model = URIRef(example_ns.Model)
    kpi = URIRef(example_ns.KPI)
    accuracy_kpi = URIRef(example_ns.Accuracy)
    ordinal_accuracy = URIRef(example_ns.OrdinalAccuracy)
    numerical_accuracy = URIRef(example_ns.NumericalAccuracy)
    g.add((model, rdf.type, owl.Class))
    g.add((kpi, rdf.type, owl.Class))
    g.add((accuracy_kpi, rdf.type, owl.Class))
    g.add((ordinal_accuracy, rdf.type, owl.Class))
    g.add((numerical_accuracy, rdf.type, owl.Class))

    g.add((accuracy_kpi, rdfs.subClassOf, kpi))
    g.add((ordinal_accuracy, rdfs.subClassOf, accuracy_kpi))
    g.add((numerical_accuracy, rdfs.subClassOf, accuracy_kpi))

    cpu_time = URIRef(example_ns.CPUTime)
    numerical_cpu_time = URIRef(example_ns.NumericalCPUTime)
    g.add((cpu_time, rdf.type, owl.Class))
    g.add((numerical_cpu_time, rdf.type, owl.Class))
    g.add((cpu_time, rdfs.subClassOf, kpi))
    g.add((numerical_cpu_time, rdfs.subClassOf, cpu_time))

    KPI_accuracy_1 = URIRef(example_ns.KPI_accuracy_1)
    g.add((KPI_accuracy_1, rdf.type, owl.NamedIndividual))
    # g.add((KPI_accuracy_1, rdf.type, example_ns.OrdinalAccuracy))
    # g.add((KPI_accuracy_1, example_ns.KPIValue, Literal("High", datatype=XSD.string)))
    g.add((KPI_accuracy_1, rdf.type, example_ns.NumericalAccuracy))
    g.add((KPI_accuracy_1, example_ns.KPIValue, Literal("77", datatype=XSD.integer)))

    KPI_cpu_time_1 = URIRef(example_ns.KPI_cpu_time_1)
    g.add((KPI_cpu_time_1, rdf.type, owl.NamedIndividual))
    g.add((KPI_cpu_time_1, rdf.type, example_ns.NumericalCPUTime))
    g.add((KPI_cpu_time_1, example_ns.KPIValue, Literal("200", datatype=XSD.integer)))

    kpi_restriction_bnode = BNode()
    g.add((kpi_restriction_bnode, rdf.type, owl.Restriction))
    g.add((kpi_restriction_bnode, owl.onProperty, example_ns.hasKPI))
    g.add((kpi_restriction_bnode, owl.hasValue, KPI_accuracy_1))
    g.add((model, rdfs.subClassOf, kpi_restriction_bnode))

    kpi_restriction_bnode_2 = BNode()
    g.add((kpi_restriction_bnode_2, rdf.type, owl.Restriction))
    g.add((kpi_restriction_bnode_2, owl.onProperty, example_ns.hasKPI))
    g.add((kpi_restriction_bnode_2, owl.hasValue, KPI_cpu_time_1))
    g.add((model, rdfs.subClassOf, kpi_restriction_bnode_2))


    # Save to triplestore
    ontology_stream = io.StringIO(g.serialize(format="turtle"))
    ts.parse(source=ontology_stream, format="turtle")

    func_iri = ts.add_function(accuracy_converter, expects=ordinal_accuracy, returns=numerical_accuracy, standard="emmo")
    func_iri_2 = ts.add_function(mirror_converter, expects=numerical_cpu_time, returns=numerical_cpu_time, standard="emmo")
    func_iri_3 = ts.add_function(mirror_converter, expects=numerical_accuracy, returns=numerical_accuracy, standard="emmo")

    ## Visualization and debug
    complete_ontology = Graph()
    complete_ontology.parse(data=ts.serialize(format="turtle"), format="turtle")
    print(complete_ontology.serialize(format="turtle"))
    visualize(complete_ontology)