import json
import math
import subprocess
from copy import deepcopy, copy
from typing import List

import yaml
from tripper import Triplestore

from ontoflow.log.logger import logger


class Node:
    def __init__(self, depth: int, iri: str, predicate: str, route_choices: int = 1, local_choices: int = 0):
        """Initialise a node in the ontology tree.

        Args:
            depth (int): the depth of the node in the tree.
            iri (str): the IRI of the node.
            predicate (str): the relation the parent node.
            route_choices (int): the number of routes underlying the node.
            local_choices (int): the number of possible elements you can select from the node.
        """

        self.depth: int = depth
        self.iri: str = iri
        self.predicate: str = predicate
        self.route_choices = route_choices
        self.local_choices = local_choices
        self.children: List["Node"] = []

    def __str__(self) -> str:
        """String representation of the node structure.

        Returns:
            str: the string representation of the node structure.
        """

        result = f"""Depth: {self.depth}, IRI: {self.iri}, Parent Predicate: {self.predicate}, Route choices: {self.route_choices}, Local choices: {self.local_choices},  Children ({len(self.children)}){":" if len(self.children) > 0 else ""}\n"""
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

        ser["choices"] = self.route_choices
        ser["local_choices"] = self.local_choices

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

    def addChild(self, iri: str, predicate: str, route_choices: int = 1, local_choices: int = 0) -> "Node":
        """Add a child to the node.

        Args:
            iri (str): the IRI of the child node.
            predicate (str): the relation to the child node.

        Returns:
            Node: the child node.
        """

        node = Node(self.depth + 1, iri, predicate, route_choices, local_choices)
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

    def visualize(self, output = None,  format = "png") -> str:
        node_string = "digraph G {\n" + "\n".join(list(set(self._visualize()))) + "\n}"

        if output is not None:
           subprocess.run(
                args=["dot", f"-T{format}", "-o", output],
                shell=False,
                check=True,
                input=node_string.encode(),
            ) 

        return node_string

    def _visualize(self):

        node_string = []
        node_string.append("\"{}\" [shape=box] [xlabel=\"r: {}\nl: {}\"]".format(self.iri, self.route_choices, self.local_choices))

        for child in self.children:
            node_string += child._visualize()
            dir_back = "back" if child.predicate == "hasOutput" else "forward"
            node_string.append("\"{}\" -> \"{}\" [label=\"{}\", dir=\"{}\", color=\"{}\"]".format(self.iri, child.iri, child.predicate, dir_back, "black"))

        return node_string
    
    # Older version: if you want to separate this logic from the search algorithm 
    # def get_number_routes(self):
    #     if len(self.children) > 0:
    #         if self.children[0].predicate == "individual":
    #             return len(self.children)
    #         elif self.children[0].predicate == "hasInput":
    #             return math.prod([child.get_number_routes() for child in self.children])
    #         else:
    #             return sum([child.get_number_routes() for child in self.children])
    #     else:
    #         return 1
    def get_number_routes(self):
        return self.route_choices
    

    def get_route_mappings(self):
        route_mapping = []

        if self.route_choices > 1:
            if self.local_choices >= self.route_choices:
                # Sono l'ultimo punto di scelta
                route_mapping = [[idx] for idx, _ in enumerate(self.children)]

            else:
                if self.local_choices > 1:
                    # Sono un punto di scelta ma non l'ultimo
                    for idx, child in enumerate(self.children):
                        temp_route = child.get_route_mappings()
                        for el in temp_route:
                            el.insert(0, idx)
                            route_mapping.append(el)
                else:
                    # Non sono un punto di scelta, ma ci sono altre route da trovare, delego
                    for idx, child in enumerate(self.children):
                        temp = child.get_route_mappings()
                        route_mapping += temp
            route_mapping = list(filter(lambda x: len(x) > 0, route_mapping))
        else:
            route_mapping = [[]]

        return route_mapping
    

    def get_route(self, route_idx = 0):
        routes_mapping = self.get_route_mappings() #FIXME: Cache the routes mapping so that we do not compute it each time
        selected_mapping = routes_mapping[route_idx]

        route_node = self.__choose_node(selected_mapping)

        return route_node
    

    def __choose_node(self, mapping):
        logger.info("Choosing node {}".format(self.iri))
        if self.local_choices > 1:
            copy_node = copy(self)
            copy_node.children = []
            copy_children = self.children[mapping[0]].__choose_node(mapping[1:])
            copy_node.children.append(copy_children)
            return copy_node
        else:
            copy_node = copy(self)
            copy_node.children = []
            for child in self.children:
                copy_children = child.__choose_node(mapping)
                copy_node.children.append(copy_children)
            return copy_node
            


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
        
        if len(individuals) > 0:
            node.route_choices = sum([child.route_choices for child in node.children])
            node.local_choices = len(individuals)

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
                        logger.info("Exploring {}, choices {}".format(iiri, ichild.route_choices))
                        self._exploreNode(ichild)
                        logger.info("Explored {}, choices {}".format(iiri, ichild.route_choices))
                        self.explored[iiri] = ichild

                if len(inputs) > 0:
                    ochild.route_choices = math.prod([child.route_choices for child in ochild.children])
                    ochild.local_choices = 1
        if len(outputs) > 0:
            node.route_choices = sum([child.route_choices for child in node.children])
            node.local_choices = len(outputs)

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

        if len(subclasses) > 0:
            node.route_choices = sum([child.route_choices for child in node.children])
            node.local_choices = len(subclasses)

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
