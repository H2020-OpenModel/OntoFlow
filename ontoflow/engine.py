import json
import yaml
from tripper import Triplestore


class Node:
    def __init__(self, depth: int, iri: str, predicate: str):
        """Initialise a node in the ontology tree.

        Args:
            depth (int): the depth of the node in the tree.
            iri (str): the IRI of the node.
            predicate (str): the relation the parent node.
        """

        self.depth = depth
        self.iri = iri
        self.predicate = predicate
        self.children = []

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

    def _dict(self) -> dict:
        """Dictionary representation of the node structure.

        Returns:
            dict: the dictionary representation of the node structure.
        """
        return {
            "depth": self.depth,
            "iri": self.iri,
            "predicate": self.predicate,
            "children": [child._dict() for child in self.children],
        }

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

    def export(self, fileName: str) -> None:
        """Serialize a node as JSON and export it to a file.

        Args:
            node (Node): The node to be serialized.
            file_name (str): The name of the file to export the JSON data.
        """
        with open(f"{fileName}.json", "w") as file:
            json.dump(self._dict(), file, indent=4)

        with open(f"{fileName}.yaml", "w") as file:
            yaml.dump(self._dict(), file, indent=4, sort_keys=False)


class OntoFlowEngine:
    def __init__(self, triplestore: Triplestore) -> None:
        """Initialise the OntoFlow engine. Sets the triplestore and the data dictionary.

        Args:
            triplestore (Triplestore): Triplestore to be used for the engine.
        """

        self.triplestore = triplestore
        self.data = []
        self.mapping = {}

    def _exploreNode(self, node):
        """Explore a node in the ontology and generate the tree

        Args:
            node (str): The node to explore.
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
                            owl:someValuesFrom {iri} .
                BIND(base:hasOutput AS ?rel) .
                BIND({iri} AS ?obj) .
            }}""",
            """SELECT ?sub ?rel ?obj WHERE {{
                {iri} rdf:type owl:Class ;
                    rdfs:subClassOf ?restriction .
                ?restriction rdf:type owl:Restriction ;
                            owl:onProperty base:hasOutput ;
                            owl:someValuesFrom ?sub .
                BIND(base:hasOutput AS ?rel) .
                BIND({iri} AS ?obj) .
            }}""",
        ]
        patternsInput = [
            """SELECT ?sub ?rel ?obj WHERE {{
                ?sub rdf:type owl:Class ;
                        rdfs:subClassOf ?restriction .
                ?restriction rdf:type owl:Restriction ;
                            owl:onProperty base:hasInput ;
                            owl:someValuesFrom {iri} .
                BIND(base:hasOutput AS ?rel) .
                BIND({iri} AS ?obj) .
            }}""",
            """SELECT ?sub ?rel ?obj WHERE {{
                {iri} rdf:type owl:Class ;
                    rdfs:subClassOf ?restriction .
                ?restriction rdf:type owl:Restriction ;
                            owl:onProperty base:hasInput ;
                            owl:someValuesFrom ?sub .
                BIND(base:hasInput AS ?rel) .
                BIND({iri} AS ?obj) .
            }}""",
        ]

        res = []

        outputs = self._query(patternsOutput, node.iri)

        for output in outputs:
            child = node.addChild(output[0], "hasOutput")
            inputs = self._query(patternsInput, output[0])
            for input in inputs:
                res.append(child.addChild(input[0], "hasInput"))

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
            res.append(node.addChild(subclass[0], "subClassOf"))

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

    def loadOntology(self, path: str, format: str = "turtle") -> None:
        """Load the ontology from a file.

        Args:
            path (str): Path to the ontology file.
            format (str, optional): Format of the ontology file. Defaults to "turtle".
        """
        self.triplestore.parse(path, format=format)

    def getMappingRoute(self, target: str) -> dict:
        """Get the mapping route from the target to all the possible sources.

        Args:
            target (str): The target data to be found.

        Returns:
            dict: The mapping route.
        """

        root = Node(0, target, "")

        self._exploreNode(root)

        root.export("output")

        return self.mapping
