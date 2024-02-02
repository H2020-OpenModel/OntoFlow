import io
import os
import pydot
from os.path import dirname, abspath
from rdflib import Graph, URIRef, Namespace, BNode
from rdflib.tools.rdf2dot import rdf2dot

example_ns = Namespace("http://openmodel.ontoflow/examples#")
example_individual_ns = Namespace("http://openmodel.ontoflow/examples/individuals#")
owl = Namespace("http://www.w3.org/2002/07/owl#")
rdf = Namespace("http://www.w3.org/1999/02/22-rdf-syntax-ns#")
rdfs = Namespace("http://www.w3.org/2000/01/rdf-schema#")
webprotege = Namespace("http://webprotege.stanford.edu/")

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
    graph.add((individual, rdf.type, currentTarget))
    graph.add((individual, rdf.type, owl.NamedIndividual))
    return individual

def add_subclass(graph, currentTarget):
    global subclass_count
    subclass_count += 1
    subclass = URIRef(example_ns["subclass" + str(subclass_count)])
    graph.add((subclass, rdf.type, owl.Class))
    graph.add((subclass, URIRef(rdfs.subClassOf), currentTarget))
    return subclass

def add_generating_model(graph, currentTarget, n_inputs = 1, useinputs = []):
    global generating_model_count, input_count
    generating_model_count += 1
    generating_model = URIRef(example_ns["generating-model" + str(generating_model_count)])
    graph.add((generating_model, rdf.type, owl.Class))
    output_bnode = BNode()
    graph.add((output_bnode, rdf.type, owl.Restriction))
    graph.add((output_bnode, owl.onProperty, webprotege.hasOutput))
    graph.add((output_bnode, owl.someValuesFrom, currentTarget))
    graph.add((generating_model, rdfs.subClassOf, output_bnode))

    input_nodes = []
    for i in range(0, n_inputs):
        input_count += 1
        input_bnode = BNode()
        if len(useinputs) > 0:
            input = useinputs[i] if isinstance(useinputs[i], URIRef) else URIRef(useinputs[i])
        else:
            input = URIRef(example_ns["input" + str(input_count)])
        graph.add((input_bnode, rdf.type, owl.Restriction))
        graph.add((input_bnode, owl.onProperty, webprotege.hasInput))
        graph.add((input_bnode, owl.someValuesFrom, input))
        graph.add((generating_model, rdfs.subClassOf, input_bnode))

        input_nodes.append(input)
    return (generating_model, input_nodes)


if __name__ == "__main__":
    g = Graph()
    g.bind("ontoflow", example_ns)
    g.bind("ontoflow_ind", example_individual_ns)
    g.bind("www", webprotege)

    target_node = URIRef(example_ns.Target)
    generating_model_a, inputs_a = add_generating_model(g, target_node, 1)
    generating_model_b, inputs_b = add_generating_model(g, target_node, 1, inputs_a)
    individual_node_a = add_individual(g, inputs_a[0])

    # input_node_gm1 = add_generating_model(g, target_node)
    # input_node_gm2 = add_generating_model(g, target_node)
    # input_node_gm2 = add_subclass(g, input_node_gm2)

    print(g.serialize(format="turtle"))

    visualize(g)


