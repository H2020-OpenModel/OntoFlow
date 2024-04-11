import json
import os
from io import StringIO
from math import prod
from pathlib import Path
from typing import Optional

from ontoflow.cost_converters.converters import init_converter_triplestore
from ontoflow.log.logger import logger
from ontoflow.mco import Mco
from ontoflow.node import Node

from tripper import Namespace, Triplestore


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
        ontoflowKpiNs = Namespace("http://open-model.eu/ontoflow/kpa#")
        self.triplestore.bind("kpa", ontoflowKpiNs)

        # Setup internal knowldedge base for KPAs converters
        ontoflowKpiConvertersNs = Namespace(
            "http://open-model.eu/ontoflow/kpa-converters#"
        )
        self.__kpaTriplestore: Triplestore = Triplestore(
            backend="rdflib", base_iri=ontoflowKpiConvertersNs._iri
        )
        self.__kpaTriplestore.parse(
            os.path.join(
                Path(os.path.abspath(__file__)).parent.parent, "ontologies", "kpa.ttl"
            ),
            "turtle",
        )
        self.__kpaTriplestore.bind("kpa", ontoflowKpiNs)
        self.__kpaTriplestore.bind("kpa-converters", ontoflowKpiConvertersNs)
        init_converter_triplestore(self.__kpaTriplestore)

        self.triplestore.parse(
            StringIO(self.__kpaTriplestore.serialize(format="turtle")), "turtle"
        )

        self.__kpaTriplestore.serialize(
            os.path.join(
                Path(os.path.abspath(__file__)).parent.parent,
                "ontologies",
                "kpa-converters.ttl",
            ),
            "turtle",
        )

    def getBestRoute(
        self, target: str, kpis: list[dict], foldername: Optional[str] = None
    ) -> Node:
        """Get the mapping route from the target to all the possible sources.
        Step 1: Build the tree.
        Step 2: Extract the routes and their KPIs.
        Step 3: Pass the routes to the MCO to get the ranking.

        Args:
            target (str): The target data to be found.
            kpis (list[dict]): The KPIs to be used for the MCO.
            foldername (str): The folder where to save the results. Defaults to None.

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
        nodeKpis = self._getNodeKpis(iri)
        logger.info("Node KPIs: {}".format(nodeKpis))

        for kpi in self.kpis:
            _kpis[kpi] = nodeKpis[kpi]["value"] if kpi in nodeKpis else 0

        return _kpis

    def _getNodeKpis(self, iri: str) -> dict:
        """
        Get the KPIs of the node.

        Args:
            iri (str): The IRI of the node to get the KPIs.

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
            """SELECT ?kpa_class ?kpa_value ?kpa_ind WHERE {{
                {iri} kpa:hasKPA ?kpa_ind .
                ?kpa_ind rdf:type ?kpa_class .
                ?kpa_ind kpa:KPAValue ?kpa_value .
                FILTER(STRSTARTS(STR(?kpa_class), "{kpa_ns}"))
            }}""",
        ]

        internalPatters = [
            """SELECT ?base_kpa_class ?converter_fun ?kpa_class WHERE {{
                ?kpa_class rdfs:subClassOf+ ?base_kpa_class .
                ?base_kpa_class rdfs:subClassOf kpa:KPA .
                ?converter_fun emmo:EMMO_36e69413_8c59_4799_946c_10b05d266e22 ?kpa_class .

                VALUES ?kpa_class {{{kpa_classes}}}
            }}""",
        ]

        nodeKpis = {}
        triplesKpis = self._query(patterns, iri)
        kpaClassesFound = ["<{}>".format(kpi[0]) for kpi in triplesKpis]
        kpaValues = {kpi[0]: kpi[1] for kpi in triplesKpis}

        if len(kpaClassesFound) == 0:
            return nodeKpis

        # FIXME: Adjust the query function to be general with respect to the variable to substitute.
        q = internalPatters[0].format(kpa_classes=" ".join(kpaClassesFound))
        triplesKpisConverters = self.__kpaTriplestore.query(q)

        for info in triplesKpisConverters:
            idx = info[0].split("#")[-1]
            nodeKpis[idx] = {}
            nodeKpis[idx]["value"] = self.__kpaTriplestore.eval_function(
                info[1], args=(str(kpaValues[info[2]]),)
            )

        return nodeKpis

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
            q = pattern.format(
                iri=iriForm, kpa_ns=str(self.__kpaTriplestore.namespaces["kpa"])
            )
            logger.info("\n{}\n".format(q))
            results += self.triplestore.query(q)

        logger.info(results)
        return results
