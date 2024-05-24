import sys
import os
from pathlib import Path

sys.path.append(os.path.join(Path(os.path.abspath(__file__)).parent, "ontoflow"))

from io import StringIO
import unittest
from tripper import Triplestore
from rdflib import Graph, Namespace, URIRef
from tests.utils.ontology_generator import (
    add_individual,
    add_subclass,
    add_generating_model,
    add_kpa,
    visualize,
)
from ontoflow.engine import OntoFlowEngine
from ontoflow.node import Node

example_ns = Namespace("http://openmodel.ontoflow/examples#")
example_individual_ns = Namespace("http://openmodel.ontoflow/examples/individuals#")
rdf = Namespace("http://www.w3.org/1999/02/22-rdf-syntax-ns#")
rdfs = Namespace("http://www.w3.org/2000/01/rdf-schema#")
webprotege = Namespace("http://webprotege.stanford.edu/")
kpa = Namespace("http://open-model.eu/ontoflow/kpa#")
owl = Namespace("http://www.w3.org/2002/07/owl#")


def visitor_flat_structure(node):
    """Visitor to flatten the structure of the ontology tree.

    Args:
        node: The node to visit.

    Returns:
        list: The flattened structure of the ontology tree.
    """
    flat_nodes = [str(node.iri)]

    for child in node.children:
        flat_nodes += visitor_flat_structure(child)

    return flat_nodes


def converter_mock_a(mock_value):
    """Mock function to convert the KPA value.

    Args:
        mock_value (str): The KPA value to convert.

    Returns:
        int: The converted KPA value.
    """

    if mock_value == "Mock_KPA_Value_A":
        return 10
    elif mock_value == "Mock_KPA_Value_B":
        return 20
    else:
        return 30


def converter_mock_b(mock_value):
    """Mock function to convert the KPA value.

    Args:
        mock_value (int): The KPA value to convert.

    Returns:
        int: The converted KPA value.
    """

    return int(mock_value) * 2


class SearchAlgorithm_TestCase(unittest.TestCase):
    """
    This test suite is used to test the KPA and cost association module of the OntoFlow engine.
    In particular, it test whether the KPA and cost are retrieved and converted correctly.

    """

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

        # Create Mock KPA: KPA_A, KPA_B
        # Create its subclasses: Mock_KPA_A, Mock_KPA_B
        self.__ontoflow_engine._OntoFlowEngine__kpaTriplestore.add_triples(
            [(kpa.KPA_A, rdf.type, owl.Class), (kpa.KPA_A, rdfs.subClassOf, kpa.KPA)]
        )
        self.__ontoflow_engine._OntoFlowEngine__kpaTriplestore.add_triples(
            [(kpa.KPA_B, rdf.type, owl.Class), (kpa.KPA_B, rdfs.subClassOf, kpa.KPA)]
        )
        self.__ontoflow_engine._OntoFlowEngine__kpaTriplestore.add_triples(
            [
                (kpa.Mock_KPA_A, rdfs.subClassOf, kpa.KPA_A),
                (kpa.Mock_KPA_B, rdfs.subClassOf, kpa.KPA_B),
                (kpa.Numerical_Mock_KPA_B, rdfs.subClassOf, kpa.KPA_B),
            ]
        )
        self.__ontoflow_engine._OntoFlowEngine__kpaTriplestore.add_function(
            converter_mock_a,
            expects=kpa.Mock_KPA_A,
            returns=kpa.Numerical_Mock_KPA_A,
            standard="emmo",
        )
        self.__ontoflow_engine._OntoFlowEngine__kpaTriplestore.add_function(
            converter_mock_b,
            expects=kpa.Numerical_Mock_KPA_B,
            returns=kpa.Numerical_Mock_KPA_B,
            standard="emmo",
        )
        # with open(os.path.join(Path(os.path.abspath(__file__)).parent, "openmodel_example.ttl"), "w") as f:
        #            f.write(self.__ontoflow_engine._OntoFlowEngine__kpaTriplestore.serialize(format="turtle"))
        self.__ontoflow_engine.kpas.extend(["KPA_A", "KPA_B"])

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

    def test_T9(self):
        target_node = URIRef(example_ns.Target)
        generating_model_a, inputs_a = add_generating_model(
            self.__graph, target_node, 1
        )
        generating_model_b, inputs_b = add_generating_model(
            self.__graph, target_node, 1, inputs_a
        )
        individual_node_a = add_individual(self.__graph, inputs_a[0])

        kpa_ind_a, kpa_bnode_a = add_kpa(
            self.__graph, generating_model_a, "Mock_KPA_A", "Mock_KPA_Value_A"
        )
        kpa_ind_a, kpa_bnode_a = add_kpa(
            self.__graph, generating_model_a, "Numerical_Mock_KPA_B", "20"
        )

        kpa_ind_b, kpa_bnode_b = add_kpa(
            self.__graph, generating_model_b, "Mock_KPA_A", "Mock_KPA_Value_D"
        )
        kpa_ind_b, kpa_bnode_b = add_kpa(
            self.__graph, generating_model_b, "Numerical_Mock_KPA_B", "40"
        )

        route_a = [
            str(target_node),
            str(generating_model_a),
            str(inputs_a[0]),
            str(individual_node_a),
        ]
        route_b = [
            str(target_node),
            str(generating_model_b),
            str(inputs_b[0]),
            str(individual_node_a),
        ]

        ontology_stream = StringIO(self.__graph.serialize(format="turtle"))
        self.__triplestore.parse(source=ontology_stream, format="turtle")

        kpas = [
            {"name": "KPA_A", "weight": 3, "maximise": True},
            {"name": "KPA_B", "weight": 1, "maximise": False},
        ]

        # Get the best route
        bestRoute = self.__ontoflow_engine.getBestRoute(str(target_node), kpas)
        t = visitor_flat_structure(bestRoute)

        self.assertEqual(bestRoute.routeChoices, 2)
        self.assertEqual(visitor_flat_structure(bestRoute), route_b)

        kpas = [
            {"name": "KPA_A", "weight": 1, "maximise": True},
            {"name": "KPA_B", "weight": 3, "maximise": False},
        ]

        # Get the best route
        bestRoute = self.__ontoflow_engine.getBestRoute(str(target_node), kpas)
        t = visitor_flat_structure(bestRoute)

        self.assertEqual(bestRoute.routeChoices, 2)
        self.assertEqual(visitor_flat_structure(bestRoute), route_a)
