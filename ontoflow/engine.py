import json
from copy import deepcopy

from ontoflow.log.logger import logger

from tripper import Triplestore

from .mco import mco_calc
from .node import Node

from osp.core.utils import pretty_print


class OntoFlowEngine:
    def __init__(self, triplestore: Triplestore) -> None:
        """Initialise the OntoFlow engine. Sets the triplestore and the data dictionary.

        Args:
            triplestore (Triplestore): Triplestore to be used for the engine.
        """

        self.triplestore: Triplestore = triplestore
        self.explored: dict = {}

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

        for i, individual in enumerate(individuals):
            node.addChild(individual[0], "individual")

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

        n = len(outputs)

        for i, output in enumerate(outputs):
            oiri = output[0]
            if oiri in self.explored:
                node.addNodeChild(self.explored[oiri], "hasOutput")
            else:
                ochild = node.addChild(oiri, "hasOutput", i if n > 1 else None)
                self.explored[oiri] = ochild
                inputs = self._query(patternsInput, oiri)
                for input in inputs:
                    iiri = input[0]
                    if iiri in self.explored:
                        ochild.addNodeChild(self.explored[iiri], "hasInput")
                    else:
                        ichild = ochild.addChild(iiri, "hasInput")
                        self._exploreNode(ichild)
                        self.explored[iiri] = ichild

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
                child = node.addChild(iri, "subClassOf")
                self._exploreNode(child)
                self.explored[iri] = child

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
            q = pattern.format(iri=iriForm)
            logger.info("\n{}\n".format(q))
            results += self.triplestore.query(q)

        logger.info(results)
        return results

    def _getPathsKpis(self, node: Node, path: dict, paths: list) -> None:
        """Get all the possible paths and their KPIs.

        Args:
            node (Node): The starting node.
            path (dict): Dict containing the path and KPIs.
            paths (list): The resulting list of paths with their KPIs.
        """

        if node.pathId is not None:
            path = deepcopy(path)
            path["path"].append(node.pathId)
            paths.append(path)
        for k, v in node.kpis.items():
            if k not in path["kpis"]:
                path["kpis"][k] = []
            path["kpis"][k].append(v)
        for child in node.children:
            self._getPathsKpis(child, path, paths)

    def getMappingRoute(self, target: str) -> Node:
        """Get the mapping route from the target to all the possible sources.
        Step 1: Build the tree.
        Step 2: Extract the routes and their KPIs.
        Step 3: Pass the routes to the MCO to get the ranking.

        Args:
            target (str): The target data to be found.

        Returns:
            Node: The mapping starting from the root node.
        """

        logger.info(f"Getting mapping route for {target}")
        kpis = ["ModelParameter", "Cost1", "Cost2"]

        # Build the tree
        root = Node(0, target, "", kpis=kpis)
        self._exploreNode(root)

        # Extract the routes and their KPIs
        paths = []
        path = {"path": [], "kpis": {}}
        self._getPathsKpis(root, path, paths)

        res = {"routes": []}

        for i, path in enumerate(paths):
            route = {
                "path": root._serialize(path["path"]),
                "kpis": {kpi: sum(path["kpis"][kpi]) for kpi in kpis},
            }
            route["kpis"]["ModelId"] = i
            res["routes"].append(route)

        kpis.append("ModelId")

        # Pass the routes to the MCO to get the ranking
        mco = []
        mco.append(kpis)

        for r in res["routes"]:
            mco.append([r["kpis"][kpi] for kpi in kpis])

        ranking = mco_calc(mco)

        res["ranking"] = ranking

        # Print the results
        with open(f"res.json", "w") as file:
            json.dump(res, file, indent=4)

        return root
