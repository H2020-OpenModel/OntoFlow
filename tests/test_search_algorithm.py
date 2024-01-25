import io
import unittest
from tripper import Triplestore
from rdflib import Graph, Namespace, URIRef
from utils.ontology_generator import add_individual, add_subclass, add_generating_model

example_ns = Namespace("http://openmodel.ontoflow/examples#")
example_individual_ns = Namespace("http://openmodel.ontoflow/examples/individuals#")

class SearchAlgorithm_TestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        pass

    def setUp(self):
        self.__database_name = "ontoflow_test"
        self.__triplestore = Triplestore(backend = "fuseki", base_iri="http://example.com/ontology#", triplestore_url = "http://localhost:3030", database = self.__database_name)
        self.__graph = Graph()
        self.__graph.bind("ontoflow", example_ns)
        self.__graph.bind("ontoflow_ind", example_individual_ns)

    @classmethod
    def tearDownClass(cls):
        pass

    def tearDown(self):
        pass

    def test_T1(self):
        target_node = URIRef(example_ns.Target)
        target_node = add_individual(self.__graph, target_node)

        ontology_stream = io.StringIO(self.__graph.serialize(format="turtle"))
        self.__triplestore.parse(source = ontology_stream, format = "turtle")



