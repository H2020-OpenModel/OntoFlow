import json
import yaml
from tripper import Triplestore


class Node:
    def __init__(self, depth: int, iri: str, parentPredicate: str):
        """Initialise a node in the ontology tree.

        Args:
            depth (int): the depth of the node in the tree.
            iri (str): the IRI of the node.
            parent_predicate (str): the relation the parent node.
        """
        self.depth = depth
        self.iri = iri
        self.parentPredicate = parentPredicate
        self.children = []

    def addChild(self, iri: str, predicate: str) -> 'Node':
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

    def __str__(self) -> str:
        """String representation of the node structure.

        Returns:
            str: the string representation of the node structure.
        """

        result = f"""Depth: {self.depth}, IRI: {self.iri}, Parent Predicate: {self.parentPredicate}, 
Children ({len(self.children)}) {":" if len(self.children) > 0 else ""}\n"""
        for child in self.children:
            result += str(child)
        return result
    
    def export_node_as_json(self, fileName: str) -> None:
        """Serialize a node as JSON and export it to a file.

        Args:
            node (Node): The node to be serialized.
            file_name (str): The name of the file to export the JSON data.
        """
        with open(fileName, "w") as file:
            json.dump(self.__dict__, file, indent=4)


class OntoFlowEngine:
    def __init__(self, triplestore: Triplestore) -> None:
        """Initialise the OntoFlow engine. Sets the triplestore and the data dictionary.

        Args:
            triplestore (Triplestore): Triplestore to be used for the engine.
        """

        self.triplestore = triplestore
        self.data = []
        self.mapping = {}

    def loadOntology(self, path: str, format: str = "turtle") -> None:
        """Load the ontology from a file.

        Args:
            path (str): Path to the ontology file.
            format (str, optional): Format of the ontology file. Defaults to "turtle".
        """
        self.triplestore.parse(path, format=format)

    def generateYaml(self) -> None:
        """Generate a YAML file from the mapping."""

        with open("output.yaml", "w") as file:
            yaml.dump(self.mapping, file, sort_keys=False)

    def getMappingRoute(self, target: str) -> dict:
        """Get the mapping route from the target to all the possible sources.

        Args:
            target (str): The target data to be found.

        Returns:
            dict: The mapping route.
        """

        root = Node(0, target, "")

        self.__exploreNode(root)

        print("RES", root)

        with open("data.json", "w") as file:
            json.dump(self.data, file, sort_keys=False)

        with open("output.json", "w") as file:
            json.dump(root, file, sort_keys=False)

        return self.mapping

    def __exploreNode(self, node):
        """Explore a node in the ontology and generate the tree

        Args:
            node (str): The node to explore.
        """

        # Step 1: check if the node is an individual.
        # If it is, return
        # print("INDIVIDUAL")
        if self.__isIndividual(node.iri):
            return

        # Step 2: check if the node is a model.
        # If it is, get the inputs and explore them
        inputs = self.__model(node.iri)
        # print(f"MODEL\n{inputs}")
        for input in inputs:
            if input in self.data:
                continue
            child = node.addChild(input, "hasInput")
            self.data.append(input)
            self.__exploreNode(child)

        # Step 3: check if the node is a subclass.
        # If it is, get the subclass and explore it
        else:
            subclasses = self.__subClass(node.iri)
            # print(f"SUBCLASS\n{subclasses}")
            for subclass in subclasses:
                child = node.addChild(subclass, "subClassOf")
                self.data.append(subclass)
                self.__exploreNode(child)

    def __isIndividual(self, iri: str) -> bool:
        """Check if the node is an individual

        Args:
            iri (str): The IRI of the node to check.

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

        res = self.__query(patterns, iri)

        return len(res) > 0

    def __model(self, iri: str) -> list:
        """Check if the node is a model.
        In case it is accessed via its output and gets the inputs

        Args:
            iri (str): The IRI of the node to check.
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

        outputs = self.__query(patternsOutput, iri)
        print(outputs)

        for output in outputs:
            inputs = self.__query(patternsInput, output[0])
            res += [el[0] for el in inputs]

        print(res)

        return res

    def __subClass(self, iri: str) -> list:
        """Check if the node is a subclass.

        Args:
            iri (str): The IRI of the node to check.
        """

        patterns = [
            """SELECT ?sub ?rel ?obj WHERE {{
                ?sub rdf:type owl:Class ;
                        rdfs:subClassOf {iri} .
                BIND(rdfs:subClassOf AS ?rel) .
                BIND({iri} as ?obj) .
            }}"""
        ]

        res = self.__query(patterns, iri)

        return [el[0] for el in res]

    def __query(self, patterns: list[str], iri: str) -> list:
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
