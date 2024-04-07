import json
import os
from pathlib import Path
from math import prod
from random import random

from tripper import Triplestore, Namespace

from .log.logger import logger
from .mco import Mco
from .node import Node
from .cost_converters.converters import init_converter_triplestore


class OntoFlowEngine:
    def __init__(self, triplestore: Triplestore) -> None:
        """Initialise the OntoFlow engine. Sets the triplestore and the data dictionary.

        Args:
            triplestore (Triplestore): Triplestore to be used for the engine.
        """

        self.triplestore: Triplestore = triplestore
        self.explored: dict = {}
        self.kpis: list = []

        # Bind the namespace used for the KPI definition
        ontoflow_kpi_ns = Namespace("http://open-model.eu/ontoflow/kpa#")
        self.triplestore.bind("kpa", ontoflow_kpi_ns)

        # Setup internal knowldedge base for KPAs converters
        ontoflow_kpi_converters_ns = Namespace("http://open-model.eu/ontoflow/kpa-converters#")
        self.__kpa_triplestore: Triplestore = Triplestore(backend="rdflib", base_iri=ontoflow_kpi_converters_ns)
        self.__kpa_triplestore.bind("kpa", ontoflow_kpi_ns)
        self.__kpa_triplestore.bind("kpa-converters", ontoflow_kpi_converters_ns)
        self.__kpa_triplestore.parse(os.path.join(Path(os.path.abspath(__file__)).parent.parent, "ontologies", "kpa.ttl"), "turtle")
        init_converter_triplestore(self.__kpa_triplestore)

        # Just test
        import io
        self.triplestore.parse(io.StringIO(self.__kpa_triplestore.serialize(format="turtle")), "turtle")

        self.__kpa_triplestore.serialize(os.path.join(Path(os.path.abspath(__file__)).parent.parent, "ontologies", "kpa-converters.ttl"), "turtle")


    def getBestRoute(self, target: str, kpis: list[dict], foldername: str = None) -> Node:
        """Get the mapping route from the target to all the possible sources.
        Step 1: Build the tree.
        Step 2: Extract the routes and their KPIs.
        Step 3: Pass the routes to the MCO to get the ranking.

        Args:
            target (str): The target data to be found.
            kpis (list[dict]): The KPIs to be used for the MCO.
            foldername (str): The folder to save the results. Defaults to None.

        Returns:
            Node: The mapping starting from the root node.
        """

        logger.info(f"Getting mapping route for {target}")
        self.kpis = [kpi["name"] for kpi in kpis]

        # Build the tree and get the routes
        root = Node(0, target, "", kpis=self._getKpis(target))
        self._exploreNode(root)
        root.generateRoutes()
        self.kpis.append("Id")

        # Pass the routes to the MCO to get the ranking
        mco = Mco(kpis)

        values: list = [self.kpis]

        for r in root.routes:
            values.append([r.costs[kpi] for kpi in self.kpis])

        ranking = mco.mco_calc(values)

        if foldername is not None:
            logger.info("Printing the results")
            root.export(os.path.join(foldername, "root"))
            root.visualize(os.path.join(foldername, "root"))

            for i, route in enumerate(root.routes):
                route.visualize(os.path.join(foldername, f"route_{i}"))

            with open(os.path.join(foldername, f"result.json"), "w") as file:
                json.dump(
                    {
                        "routes": [route._serialize() for route in root.routes],
                        "ranking": ranking,
                    },
                    file,
                    indent=4,
                )

        return root.routes[ranking[0]]

    def _exploreNode(self, node: Node) -> None:
        """Explore a node in the ontology and generate the tree.
        Step 1: Check if the node is an individual and, if it is, return.
        Step 2: Check if the node is a model and explore the inputs.
        Step 3: Check if the node is a subclass and explore it.

        Args:
            node (Node): The node to explore.
        """

        if self._individual(node):
            logger.info(f"Node {node.iri} has an individual")
            return

        self._model(node)

        self._subClass(node)

    def _individual(self, node: Node) -> bool:
        """Check if the node is an individual, add it to the mapping and return.

        Args:
            node (Node): The node to check.

        Returns:
            bool: True if the node is an individual, False otherwise
        """

        patterns = [
            """SELECT ?sub ?rel ?obj WHERE {{
                ?sub rdf:type {iri} .
                BIND(rdf:type AS ?rel) .
                BIND({iri} AS ?obj) .
            }}"""
        ]

        individuals = self._query(patterns, node.iri)

        for individual in individuals:
            node.addChild(individual[0], "individual", self._getKpis(individual[0]))

        if len(individuals) > 0:
            node.routeChoices = sum([child.routeChoices for child in node.children])
            node.localChoices = len(individuals)

        return len(individuals) > 0

    def _model(self, node: Node) -> None:
        """Check if the node is a model.
        In case it is accessed via its output and explores the inputs.
        The outputs and inputs are added to the mapping.

        Args:
            node (Node): The node to check.
        """

        patternsOutput = [
            """SELECT ?sub ?rel ?obj WHERE {{
                ?sub rdf:type owl:Class ;
                        rdfs:subClassOf ?restriction .
                ?restriction rdf:type owl:Restriction ;
                            owl:onProperty emmo:EMMO_c4bace1d_4db0_4cd3_87e9_18122bae2840 ;
                            ?p {iri} .
                FILTER (?p IN (owl:onClass, owl:someValuesFrom))
                BIND(emmo:EMMO_c4bace1d_4db0_4cd3_87e9_18122bae2840 AS ?rel) .
                BIND({iri} AS ?obj) .
            }}""",
        ]
        patternsInput = [
            """SELECT ?sub ?rel ?obj WHERE {{
                {iri} rdf:type owl:Class ;
                    rdfs:subClassOf ?restriction .
                ?restriction rdf:type owl:Restriction ;
                            owl:onProperty emmo:EMMO_36e69413_8c59_4799_946c_10b05d266e22 ;
                            ?p ?sub .
                FILTER (?p IN (owl:onClass, owl:someValuesFrom))
                BIND(emmo:EMMO_36e69413_8c59_4799_946c_10b05d266e22 AS ?rel) .
                BIND({iri} AS ?obj) .
            }}""",
        ]

        outputs = self._query(patternsOutput, node.iri)

        logger.info(f"Outputs models of {node.iri}: {outputs}")

        for output in outputs:
            oiri = output[0]
            if oiri in self.explored:
                node.addNodeChild(self.explored[oiri], "hasOutput")
            else:
                ochild = node.addChild(oiri, "hasOutput", self._getKpis(oiri))
                self.explored[oiri] = ochild
                inputs = self._query(patternsInput, oiri)
                for input in inputs:
                    iiri = input[0]
                    if iiri in self.explored:
                        ochild.addNodeChild(self.explored[iiri], "hasInput")
                    else:
                        ichild = ochild.addChild(iiri, "hasInput", self._getKpis(iiri))
                        self._exploreNode(ichild)
                        self.explored[iiri] = ichild

                if len(inputs) > 0:
                    ochild.routeChoices = prod(
                        [child.routeChoices for child in ochild.children]
                    )
                    ochild.localChoices = 1

        if len(outputs) > 0:
            node.routeChoices = sum([child.routeChoices for child in node.children])
            node.localChoices = len(outputs)

    def _subClass(self, node: Node) -> None:
        """Check if the node is a subclass. If it is explore the subclass and add it to the mapping.

        Args:
            node (Node): The node to check.
        """

        patterns = [
            """SELECT ?sub ?rel ?obj WHERE {{
                ?sub rdf:type owl:Class ;
                        rdfs:subClassOf {iri} .
                BIND(rdfs:subClassOf AS ?rel) .
                BIND({iri} as ?obj) .
            }}"""
        ]

        subclasses = self._query(patterns, node.iri)

        logger.info(f"Subclasses of {node.iri}: {subclasses}")

        for subclass in subclasses:
            iri = subclass[0]
            if iri in self.explored:
                node.addNodeChild(self.explored[iri], "subClassOf")
            else:
                child = node.addChild(iri, "subClassOf", self._getKpis(iri))
                self._exploreNode(child)
                self.explored[iri] = child

        if len(subclasses) > 0:
            node.routeChoices = sum([child.routeChoices for child in node.children])
            node.localChoices = len(subclasses)

    def _getKpis(self, iri: str) -> dict:
        """Get the KPIs of the node.

        Args:
            iri (str): The IRI of the node to get the KPIs.

        Returns:
            dict: The KPIs of the node.
        """

        # COMMENT: We get all the KPIs of the node and then filter. We could retrieve only the ones we need.
        _kpis = {}
        node_kpis = self._get_node_kpis(iri)
        logger.info("Node KPIs: {}".format(node_kpis))

        for kpi in self.kpis:
            _kpis[kpi] = node_kpis[kpi]["value"] if kpi in node_kpis else 0

        return _kpis
    
    def _get_node_kpis(self, iri: str, option_1: bool = True):
        """
        Get the KPIs of the node.
        Implemented: Option 1. The cost is specified in an KPI individual
        which is associated to the node class via a value restriction.

        Alternative: the relation between the class and the KPI is specified only
        at the individual level.

        Args:
            iri (str): The IRI of the node to get the KPIs.
            option_1 (bool): Whether to use option 1. Defaults to True.

        Returns:
            dict: The KPIs of the node.
        """
        logger.info("Getting KPIs for {}".format(iri))

        patterns = [
            """SELECT ?kpa_class ?kpa_value WHERE {{
                {iri} rdfs:subClassOf ?bnode .
                ?bnode rdf:type owl:Restriction .
                ?bnode owl:onProperty kpa:hasKPA .
                ?bnode owl:hasValue ?kpa_ind .
                ?kpa_ind rdf:type ?kpa_class .
                ?kpa_ind kpa:KPAValue ?kpa_value .
                FILTER(STRSTARTS(STR(?kpa_class), "{kpa_ns}"))
            }}""",
        ]

        # FIXME: The bind call for the kpa namespace is not working properly. Why?
        # FIXME: Need to explicitly specify the namespace in the query.
        internal_patters = [
            """PREFIX kpa: <http://open-model.eu/ontoflow/kpa#>
                PREFIX emmo: <http://emmo.info/emmo#>
                SELECT ?base_kpa_class ?converter_fun ?kpa_class WHERE {{
                ?kpa_class rdfs:subClassOf+ ?base_kpa_class .
                ?base_kpa_class rdfs:subClassOf kpa:KPA .
                ?converter_fun emmo:EMMO_36e69413_8c59_4799_946c_10b05d266e22 ?kpa_class .

                VALUES ?kpa_class {{{kpa_classes}}}
            }}""",
        ]

        node_kpis = {}
        triples_kpis = self._query(patterns, iri)
        kpa_classes_found = ["<{}>".format(kpi[0]) for kpi in triples_kpis]
        kpa_values = {kpi[0]: kpi[1] for kpi in triples_kpis}

        if len(kpa_classes_found) == 0:
            return node_kpis

        # FIXME: Adjust the query function to be general with respect to the variable to substitute.
        q = internal_patters[0].format(kpa_classes=" ".join(kpa_classes_found))
        triples_kpis_converters = self.__kpa_triplestore.query(q)

        for kpi_info in triples_kpis_converters:
            idx =  kpi_info[0].split("#")[-1]
            node_kpis[idx] = {} 
            node_kpis[idx]["value"] = self.__kpa_triplestore.eval_function(kpi_info[1], args=(str(kpa_values[kpi_info[2]]),))

        return node_kpis


    def _query(self, patterns: list[str], iri: str) -> list:
        """Query the triplestore using the given patterns.

        Args:
            patterns (list[str]): The patterns to query the triplestore.
            iri (str): The IRI of the node to query.

        Returns:
            list: The results of the query.
        """

        results = []

        for pattern in patterns:
            iriForm = f"<{iri}>" if iri[0] != "<" else iri
            q = pattern.format(iri=iriForm, kpa_ns=str(self.__kpa_triplestore.namespaces["kpa"]))
            logger.info("\n{}\n".format(q))
            results += self.triplestore.query(q)

        logger.info(results)
        return results
