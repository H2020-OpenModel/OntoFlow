import sys
import os
from pathlib import Path

sys.path.append(os.path.join(Path(os.path.abspath(__file__)).parent, "ontoflow"))

import io
import unittest
from tripper import Triplestore
from rdflib import Graph, Namespace, URIRef
from tests.utils.ontology_generator import (
    add_individual,
    add_subclass,
    add_generating_model,
)
from ontoflow.engine import OntoFlowEngine

example_ns = Namespace("http://openmodel.ontoflow/examples#")
example_individual_ns = Namespace("http://openmodel.ontoflow/examples/individuals#")
rdf = Namespace("http://www.w3.org/1999/02/22-rdf-syntax-ns#")
rdfs = Namespace("http://www.w3.org/2000/01/rdf-schema#")
webprotege = Namespace("http://webprotege.stanford.edu/")


def visitor_flat_structure(node):
    """Visitor to flatten the structure of the ontology tree.

    Args:
        node: The node to visit.

    Returns:
        list: The flattened structure of the ontology tree.
    """
    flat_nodes = [node.iri]

    for child in node.children:
        flat_nodes += visitor_flat_structure(child)

    return flat_nodes


class SearchAlgorithm_TestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        pass

    def setUp(self):
        self.__database_name = "openmodel"  # Fixed in the backend - make parametric
        self.__triplestore_url = os.getenv("TRIPLESTORE_URL", "http://localhost:3030")
        self.__triplestore = Triplestore(
            backend="fuseki",
            base_iri="http://example.com/ontology#",
            triplestore_url=self.__triplestore_url,
            database=self.__database_name,
        )
        self.__triplestore.bind("base", "http://webprotege.stanford.edu/")
        self.__triplestore.bind("emmo", "http://emmo.info/emmo#")
        self.__graph = Graph()
        self.__graph.bind("ontoflow", str(example_ns))
        self.__graph.bind("ontoflow_ind", str(example_individual_ns))
        self.__graph.bind("base", str(webprotege))
        self.__ontoflow_engine = OntoFlowEngine(self.__triplestore)

    @classmethod
    def tearDownClass(cls):
        pass

    def tearDown(self):
        self.__triplestore.remove_database(
            backend="fuseki",
            triplestore_url=self.__triplestore_url,
            database="openmodel",
        )
        pass

    def test_T1(self):
        target_node = URIRef(example_ns.Target)
        individual_node = add_individual(self.__graph, target_node)

        ontology_stream = io.StringIO(self.__graph.serialize(format="turtle"))
        self.__triplestore.parse(source=ontology_stream, format="turtle")

        expected_structure = [str(target_node), str(individual_node)]

        print(self.__graph.serialize(format="turtle"))

        routes = self.__ontoflow_engine.getMappingRoute(str(target_node))
        print(routes)

        # [] - Assert on number of routes, how to disitnguish between them?
        self.assertEqual(routes.accept(visitor_flat_structure), expected_structure)
        self.assertEqual(routes.routeChoices, 1)

    def test_T2(self):
        target_node = URIRef(example_ns.Target)
        subclass_node = add_subclass(self.__graph, target_node)
        individual_node = add_individual(self.__graph, subclass_node)

        ontology_stream = io.StringIO(self.__graph.serialize(format="turtle"))
        self.__triplestore.parse(source=ontology_stream, format="turtle")

        expected_structure = [
            str(target_node),
            str(subclass_node),
            str(individual_node),
        ]

        print(self.__graph.serialize(format="turtle"))

        routes = self.__ontoflow_engine.getMappingRoute(str(target_node))
        print(routes)

        print(routes.accept(visitor_flat_structure))
        print(expected_structure)

        self.assertEqual(routes.accept(visitor_flat_structure), expected_structure)
        self.assertEqual(routes.routeChoices, 1)

    def test_T4(self):
        target_node = URIRef(example_ns.Target)
        generating_model, inputs = add_generating_model(self.__graph, target_node)
        individual_node = add_individual(self.__graph, inputs[0])

        ontology_stream = io.StringIO(self.__graph.serialize(format="turtle"))
        self.__triplestore.parse(source=ontology_stream, format="turtle")

        expected_structure = [
            str(target_node),
            str(generating_model),
            str(inputs[0]),
            str(individual_node),
        ]

        print(self.__graph.serialize(format="turtle"))

        routes = self.__ontoflow_engine.getMappingRoute(str(target_node))
        print(routes)

        print(routes.accept(visitor_flat_structure))
        print(expected_structure)

        self.assertEqual(routes.accept(visitor_flat_structure), expected_structure)
        self.assertEqual(routes.routeChoices, 1)

    def test_T5(self):
        target_node = URIRef(example_ns.Target)
        generating_model, inputs = add_generating_model(self.__graph, target_node, 1)
        subclass = add_subclass(self.__graph, inputs[0])
        individual_node = add_individual(self.__graph, subclass)

        ontology_stream = io.StringIO(self.__graph.serialize(format="turtle"))
        self.__triplestore.parse(source=ontology_stream, format="turtle")

        expected_structure = [
            str(target_node),
            str(generating_model),
            str(inputs[0]),
            str(subclass),
            str(individual_node),
        ]

        print(self.__graph.serialize(format="turtle"))

        routes = self.__ontoflow_engine.getMappingRoute(str(target_node))
        print(routes)

        print(routes.accept(visitor_flat_structure))
        print(expected_structure)

        self.assertEqual(routes.accept(visitor_flat_structure), expected_structure)
        self.assertEqual(routes.routeChoices, 1)

    def test_T7(self):
        target_node = URIRef(example_ns.Target)
        generating_model, inputs = add_generating_model(self.__graph, target_node, 2)
        individual_node_a = add_individual(self.__graph, inputs[0])
        individual_node_b = add_individual(self.__graph, inputs[1])

        ontology_stream = io.StringIO(self.__graph.serialize(format="turtle"))
        self.__triplestore.parse(source=ontology_stream, format="turtle")

        expected_structure_a = [
            str(target_node),
            str(generating_model),
            str(inputs[0]),
            str(individual_node_a),
            str(inputs[1]),
            str(individual_node_b),
        ]
        expected_structure_b = [
            str(target_node),
            str(generating_model),
            str(inputs[1]),
            str(individual_node_b),
            str(inputs[0]),
            str(individual_node_a),
        ]

        print(self.__graph.serialize(format="turtle"))

        routes = self.__ontoflow_engine.getMappingRoute(str(target_node))
        print(routes)

        print(routes.accept(visitor_flat_structure))

        self.assertIn(
            routes.accept(visitor_flat_structure),
            [expected_structure_a, expected_structure_b],
        )
        self.assertEqual(routes.routeChoices, 1)

    def test_T8(self):
        target_node = URIRef(example_ns.Target)
        generating_model, inputs = add_generating_model(self.__graph, target_node, 2)
        individual_node_a = add_individual(self.__graph, inputs[0])
        subclass_b = add_subclass(self.__graph, inputs[1])
        individual_node_b = add_individual(self.__graph, subclass_b)

        ontology_stream = io.StringIO(self.__graph.serialize(format="turtle"))
        self.__triplestore.parse(source=ontology_stream, format="turtle")

        expected_structure_a = [
            str(target_node),
            str(generating_model),
            str(inputs[0]),
            str(individual_node_a),
            str(inputs[1]),
            str(subclass_b),
            str(individual_node_b),
        ]
        expected_structure_b = [
            str(target_node),
            str(generating_model),
            str(inputs[1]),
            str(subclass_b),
            str(individual_node_b),
            str(inputs[0]),
            str(individual_node_a),
        ]

        print(self.__graph.serialize(format="turtle"))

        routes = self.__ontoflow_engine.getMappingRoute(str(target_node))
        print(routes)

        print(routes.accept(visitor_flat_structure))

        self.assertIn(
            routes.accept(visitor_flat_structure),
            [expected_structure_a, expected_structure_b],
        )
        self.assertEqual(routes.routeChoices, 1)

    def test_T9(self):
        target_node = URIRef(example_ns.Target)
        generating_model_a, inputs_a = add_generating_model(
            self.__graph, target_node, 1
        )
        generating_model_b, inputs_b = add_generating_model(
            self.__graph, target_node, 1, inputs_a
        )
        individual_node_a = add_individual(self.__graph, inputs_a[0])

        ontology_stream = io.StringIO(self.__graph.serialize(format="turtle"))
        self.__triplestore.parse(source=ontology_stream, format="turtle")

        expected_structure_a = [
            str(target_node),
            str(generating_model_a),
            str(inputs_a[0]),
            str(individual_node_a),
            str(generating_model_b),
            str(inputs_b[0]),
            str(individual_node_a),
        ]
        expected_structure_b = [
            str(target_node),
            str(generating_model_b),
            str(inputs_b[0]),
            str(individual_node_a),
            str(generating_model_a),
            str(inputs_a[0]),
            str(individual_node_a),
        ]

        print(self.__graph.serialize(format="turtle"))

        routes = self.__ontoflow_engine.getMappingRoute(str(target_node))
        print(routes)

        print(routes.accept(visitor_flat_structure))

        self.assertIn(
            routes.accept(visitor_flat_structure),
            [expected_structure_a, expected_structure_b],
        )
        self.assertEqual(routes.routeChoices, 2)

    def test_T10(self):
        target_node = URIRef(example_ns.Target)
        generating_model_a, inputs_a = add_generating_model(
            self.__graph, target_node, 1
        )
        generating_model_b, inputs_b = add_generating_model(
            self.__graph, target_node, 1, inputs_a
        )
        subclass_a = add_subclass(self.__graph, inputs_a[0])
        individual_node_a = add_individual(self.__graph, subclass_a)

        ontology_stream = io.StringIO(self.__graph.serialize(format="turtle"))
        self.__triplestore.parse(source=ontology_stream, format="turtle")

        expected_structure_a = [
            str(target_node),
            str(generating_model_a),
            str(inputs_a[0]),
            str(subclass_a),
            str(individual_node_a),
            str(generating_model_b),
            str(inputs_b[0]),
            str(subclass_a),
            str(individual_node_a),
        ]
        expected_structure_b = [
            str(target_node),
            str(generating_model_b),
            str(inputs_b[0]),
            str(subclass_a),
            str(individual_node_a),
            str(generating_model_a),
            str(inputs_a[0]),
            str(subclass_a),
            str(individual_node_a),
        ]

        print(self.__graph.serialize(format="turtle"))

        routes = self.__ontoflow_engine.getMappingRoute(str(target_node))
        print(routes)

        print(routes.accept(visitor_flat_structure))

        self.assertIn(
            routes.accept(visitor_flat_structure),
            [expected_structure_a, expected_structure_b],
        )
        self.assertEqual(routes.routeChoices, 2)

    def test_T11(self):
        target_node = URIRef(example_ns.Target)
        generating_model_a, inputs_a = add_generating_model(
            self.__graph, target_node, 1
        )
        generating_model_b, inputs_b = add_generating_model(
            self.__graph, target_node, 1, inputs_a
        )
        generating_model_c, inputs_c = add_generating_model(
            self.__graph, inputs_a[0], 1
        )
        subclass_a = add_subclass(self.__graph, inputs_c[0])
        individual_node_a = add_individual(self.__graph, subclass_a)

        ontology_stream = io.StringIO(self.__graph.serialize(format="turtle"))
        self.__triplestore.parse(source=ontology_stream, format="turtle")

        expected_structure_a = [
            str(target_node),
            str(generating_model_a),
            str(inputs_a[0]),
            str(generating_model_c),
            str(inputs_c[0]),
            str(subclass_a),
            str(individual_node_a),
            str(generating_model_b),
            str(inputs_b[0]),
            str(generating_model_c),
            str(inputs_c[0]),
            str(subclass_a),
            str(individual_node_a),
        ]
        expected_structure_b = [
            str(target_node),
            str(generating_model_b),
            str(inputs_b[0]),
            str(generating_model_c),
            str(inputs_c[0]),
            str(subclass_a),
            str(individual_node_a),
            str(generating_model_a),
            str(inputs_a[0]),
            str(generating_model_c),
            str(inputs_c[0]),
            str(subclass_a),
            str(individual_node_a),
        ]

        print(self.__graph.serialize(format="turtle"))

        routes = self.__ontoflow_engine.getMappingRoute(str(target_node))
        print(routes)

        print(routes.accept(visitor_flat_structure))

        self.assertIn(
            routes.accept(visitor_flat_structure),
            [expected_structure_a, expected_structure_b],
        )
        self.assertEqual(routes.routeChoices, 2)

    def test_T12(self):
        target_node = URIRef(example_ns.Target)
        subclass_node_a = add_subclass(self.__graph, target_node)
        subclass_node_b = add_subclass(self.__graph, target_node)
        individual_node_a = add_individual(self.__graph, subclass_node_a)
        individual_node_b = add_individual(self.__graph, subclass_node_a)
        individual_node_c = add_individual(self.__graph, subclass_node_b)

        ontology_stream = io.StringIO(self.__graph.serialize(format="turtle"))
        self.__triplestore.parse(source=ontology_stream, format="turtle")

        expected_structure_a = [
            str(target_node),
            str(subclass_node_a),
            str(individual_node_a),
            str(individual_node_b),
            str(subclass_node_b),
            str(individual_node_c),
        ]
        expected_structure_b = [
            str(target_node),
            str(subclass_node_b),
            str(individual_node_c),
            str(subclass_node_a),
            str(individual_node_a),
            str(individual_node_b),
        ]

        expected_structure_c = [
            str(target_node),
            str(subclass_node_a),
            str(individual_node_b),
            str(individual_node_a),
            str(subclass_node_b),
            str(individual_node_c),
        ]
        expected_structure_d = [
            str(target_node),
            str(subclass_node_b),
            str(individual_node_c),
            str(subclass_node_a),
            str(individual_node_b),
            str(individual_node_a),
        ]

        print(self.__graph.serialize(format="turtle"))

        routes = self.__ontoflow_engine.getMappingRoute(str(target_node))
        print(routes)

        self.assertIn(
            routes.accept(visitor_flat_structure),
            [
                expected_structure_a,
                expected_structure_b,
                expected_structure_c,
                expected_structure_d,
            ],
        )
        self.assertEqual(routes.routeChoices, 3)
