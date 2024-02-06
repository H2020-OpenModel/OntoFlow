import json
from copy import deepcopy
from typing import List

import yaml
from tripper import Triplestore

from ontoflow.log.logger import logger


class Node:
    def __init__(self, depth: int, iri: str, predicate: str):
        """Initialise a node in the ontology tree.

        Args:
            depth (int): the depth of the node in the tree.
            iri (str): the IRI of the node.
            predicate (str): the relation the parent node.
        """

        self.depth: int = depth
        self.iri: str = iri
        self.predicate: str = predicate
        self.children: List["Node"] = []

    def __str__(self) -> str:
        """String representation of the node structure.

        Returns:
            str: the string representation of the node structure.
        """

        result = f"""Depth: {self.depth}, IRI: {self.iri}, Parent Predicate: {self.predicate}, Children ({len(self.children)}){":" if len(self.children) > 0 else ""}\n"""
        for child in self.children:
            result += str(child)

        return result

    def _serialize(self) -> dict:
        """Dictionary representation of the node structure.

        Returns:
            dict: the dictionary representation of the node structure.
        """

        ser = {
            "depth": self.depth,
            "iri": self.iri,
        }

        if self.predicate:
            ser["predicate"] = self.predicate

        if len(self.children) > 0:
            ser["children"] = [child._serialize() for child in self.children]

        return ser

    def _updateChildrenDepth(self, node: "Node") -> None:
        """Recursively update the depth of all children of a node.

        Args:
            node (Node): The Node object whose children's depth is to be updated.
        """

        for child in node.children:
            child.depth = node.depth + 1
            self._updateChildrenDepth(child)

    def addChild(self, iri: str, predicate: str) -> "Node":
        """Add a child to the node.

        Args:
            iri (str): the IRI of the child node.
            predicate (str): the relation to the child node.

        Returns:
            Node: the child node.
        """

        node = Node(self.depth + 1, iri, predicate)
        self.children.append(node)

        return node

    def addNodeChild(self, node: "Node", predicate: str) -> None:
        """Add a Node object as a child and, if necessary, update the depth of all its children.

        Args:
            node (Node): The Node object to be added as a child.
            predicate (str): The relation to the child node.
        """

        if node.depth == self.depth + 1 and node.predicate == predicate:
            self.children.append(node)
        else:
            node = deepcopy(node)
            node.predicate = predicate
            node.depth = self.depth + 1
            self.children.append(node)
            self._updateChildrenDepth(node)

    def export(self, fileName: str) -> None:
        """Serialize a node as JSON and export it to a file.

        Args:
            node (Node): The node to be serialized.
            fileName (str): The name of the file to export the JSON data.
        """

        with open(f"{fileName}.json", "w") as file:
            json.dump(self._serialize(), file, indent=4)

        with open(f"{fileName}.yaml", "w") as file:
            yaml.dump(self._serialize(), file, indent=4, sort_keys=False)

    def accept(self, visitor):
        """Accept a visitor and visit the node.

        Args:
            visitor: The visitor to be accepted.
        """

        return visitor(self)


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
        Step 1: check if the node is an individual and, if it is, return.
        Step 2: check if the node is a model and explore the inputs.
        Step 3: check if the node is a subclass and explore it.

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

        for output in outputs:
            oiri = output[0]
            if oiri in self.explored:
                node.addNodeChild(self.explored[oiri], "hasOutput")
            else:
                ochild = node.addChild(oiri, "hasOutput")
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
            patterns (str | list[str]): The patterns to query the triplestore.
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

    def getMappingRoute(self, target: str) -> Node:
        """Get the mapping route from the target to all the possible sources.

        Args:
            target (str): The target data to be found.

        Returns:
            Node: The mapping starting from the root node.
        """

        logger.info(f"Getting mapping route for {target}")
        root = Node(0, target, "")

        self._exploreNode(root)

        return root
