import io
import os
import pydot
from os.path import dirname, abspath
from rdflib import Graph, URIRef, Namespace
from rdflib.tools.rdf2dot import rdf2dot

example_ns = Namespace("http://openmodel.ontoflow/examples#")
example_individual_ns = Namespace("http://openmodel.ontoflow/examples/individuals#")

individual_count = 0
subclass_count = 0
generating_model_count = 0
input_count = 0


def visualize(g, name = "example.png"):
    import sys
    stream = io.StringIO()
    rdf2dot(g, stream)
    (graph,) = pydot.graph_from_dot_data(stream.getvalue())
    graph.write_png(os.path.join(dirname(dirname(abspath(__file__))), name))


def add_individual(graph, currentTarget):
    global individual_count
    individual_count += 1
    individual = URIRef(example_individual_ns["individual" + str(individual_count)])
    graph.add((currentTarget, URIRef(example_ns.hasIndividual), individual))
    return currentTarget

def add_subclass(graph, currentTarget):
    global subclass_count
    subclass_count += 1
    subclass = URIRef(example_ns["subclass" + str(subclass_count)])
    graph.add((subclass, URIRef(example_ns.subClassOf), currentTarget))
    return subclass

def add_generating_model(graph, currentTarget):
    global generating_model_count, input_count
    generating_model_count += 1
    input_count += 1
    generating_model = URIRef(example_ns["generating-model" + str(generating_model_count)])
    input = URIRef(example_ns["input" + str(input_count)])
    graph.add((generating_model, URIRef(example_ns.hasOutput), currentTarget))
    graph.add((generating_model, URIRef(example_ns.hasInput), input))
    return input



if __name__ == "__main__":
    g = Graph()
    g.bind("ontoflow", example_ns)
    g.bind("ontoflow_ind", example_individual_ns)

    target_node = URIRef(example_ns.Target)
    target_node = add_individual(g, target_node)
    target_node = add_subclass(g, target_node)
    target_node = add_generating_model(g, target_node)
    target_node = add_individual(g, target_node)

    # input_node_gm1 = add_generating_model(g, target_node)
    # input_node_gm2 = add_generating_model(g, target_node)
    # input_node_gm2 = add_subclass(g, input_node_gm2)


    print(g.serialize(format="turtle"))

    visualize(g)


