import json
from typing import List

import yaml
from tripper import Triplestore

# TODO
# - [X] Optimize using a structure for the already explored nodes
# - [X] Manage the onClass relation for hasInput and hasOutput
# - [ ] Test the engine on the example and ss3 ontologies
# - [ ] Package the engine as a library and test it on the infrastructure


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

        result = f"""Depth: {self.depth}, IRI: {self.iri}, Parent Predicate: {self.predicate}, 
Children ({len(self.children)}) {":" if len(self.children) > 0 else ""}\n"""
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

    def addNodeChild(self, node: "Node", predicate: str = "") -> None:
        """Add a Node object as a child and, if necessary, update the depth of all its children.

        Args:
            node (Node): The Node object to be added as a child.
            predicate (str): The relation to the child node.
        """

        if predicate and node.predicate != predicate:
            node.predicate = predicate

        if node.depth == self.depth + 1:
            self.children.append(node)
        else:
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


class OntoFlowEngine:
    def __init__(self, triplestore: Triplestore) -> None:
        """Initialise the OntoFlow engine. Sets the triplestore and the data dictionary.

        Args:
            triplestore (Triplestore): Triplestore to be used for the engine.
        """

        self.triplestore: Triplestore = triplestore
        self.data: dict = {}

    def _exploreNode(self, node: Node) -> None:
        """Explore a node in the ontology and generate the tree

        Args:
            node (Node): The node to explore.
        """

        # Step 1: check if the node is an individual.
        # If it is, return
        if self._individual(node):
            return

        # Step 2: check if the node is a model.
        # If it is, get the inputs and explore them
        inputs = self._model(node)
        for input in inputs:
            self._exploreNode(input)

        # Step 3: check if the node is a subclass.
        # If it is, get the subclass and explore it
        else:
            subclasses = self._subClass(node)
            for subclass in subclasses:
                self._exploreNode(subclass)

    def _individual(self, node: Node) -> bool:
        """Check if the node is an individual, add it to the mapping and return.

        Args:
            node (Node): The node to check.

        Returns:
            bool: True if the node is an individual, False otherwise
        """

        patterns = [
            """SELECT ?sub ?rel ?obj WHERE {{
                ?sub rdf:type {iri}, owl:NamedIndividual .
                BIND(rdf:type AS ?rel) .
                BIND({iri} AS ?obj) .
            }}"""
        ]

        individuals = self._query(patterns, node.iri)

        for individual in individuals:
            node.addChild(individual[0], "individual")

        return len(individuals) > 0

    def _model(self, node: Node) -> list:
        """Check if the node is a model.
        In case it is accessed via its output and gets the inputs.
        The outputs and inputs are added to the mapping.

        Args:
            node (Node): The node to check.

        Returns:
            list: The inputs of the model
        """

        patternsOutput = [
            """SELECT ?sub ?rel ?obj WHERE {{
                ?sub rdf:type owl:Class ;
                        rdfs:subClassOf ?restriction .
                ?restriction rdf:type owl:Restriction ;
                            owl:onProperty base:hasOutput ;
                            ?p {iri} .
                FILTER (?p IN (owl:onClass, owl:someValuesFrom))
                BIND(base:hasOutput AS ?rel) .
                BIND({iri} AS ?obj) .
            }}""",
        ]
        patternsInput = [
            """SELECT ?sub ?rel ?obj WHERE {{
                {iri} rdf:type owl:Class ;
                    rdfs:subClassOf ?restriction .
                ?restriction rdf:type owl:Restriction ;
                            owl:onProperty base:hasInput ;
                            ?p ?sub .
                FILTER (?p IN (owl:onClass, owl:someValuesFrom))
                BIND(base:hasInput AS ?rel) .
                BIND({iri} AS ?obj) .
            }}""",
        ]

        res = []

        outputs = self._query(patternsOutput, node.iri)

        for output in outputs:
            oiri = output[0]
            if oiri in self.data:
                node.addNodeChild(self.data[oiri], "hasOutput")
            else:
                ochild = node.addChild(oiri, "hasOutput")
                self.data[oiri] = ochild
                inputs = self._query(patternsInput, oiri)
                for input in inputs:
                    iiri = input[0]
                    if iiri in self.data:
                        ochild.addNodeChild(self.data[iiri], "hasInput")
                    else:
                        ichild = ochild.addChild(iiri, "hasInput")
                        self.data[iiri] = ichild
                        res.append(ichild)

        return res

    def _subClass(self, node: Node) -> list:
        """Check if the node is a subclass. If it is, get the subclass and add it to the mapping.

        Args:
            node (Node): The node to check.

        Returns:
            list: The subclasses of the node.
        """

        patterns = [
            """SELECT ?sub ?rel ?obj WHERE {{
                ?sub rdf:type owl:Class ;
                        rdfs:subClassOf {iri} .
                BIND(rdfs:subClassOf AS ?rel) .
                BIND({iri} as ?obj) .
            }}"""
        ]

        res = []

        subclasses = self._query(patterns, node.iri)

        for subclass in subclasses:
            iri = subclass[0]
            if iri in self.data:
                node.addNodeChild(self.data[iri], "subClassOf")
            else:
                child = node.addChild(iri, "subClassOf")
                self.data[iri] = child
                res.append(child)

        return res

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
            results += self.triplestore.query(q)

        return results

    def getMappingRoute(self, target: str) -> Node:
        """Get the mapping route from the target to all the possible sources.

        Args:
            target (str): The target data to be found.

        Returns:
            Node: The mapping starting from the root node.
        """

        root = Node(0, target, "")

        self._exploreNode(root)

        root.export("output")

        return root
