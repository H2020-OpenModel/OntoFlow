import json
import yaml
from tripper import Triplestore

# podman run -i --rm -p 3030:3030 -v databases:/fuseki/databases -t fuseki --update --loc databases/openmodel /openmodel

# Setup queries adding onClass, and other cases


class OntoFlowEngine:
    __PATTERNS = [
        """SELECT ?sub ?rel ?obj WHERE {{
            ?sub rdf:type owl:Class ;
                    rdfs:subClassOf {node} .
            BIND(rdfs:subClassOf AS ?rel) .
            BIND({node} as ?obj) .
        }}""",
        """SELECT ?sub ?rel ?obj WHERE {{
            ?sub rdf:type owl:Class ;
                    rdfs:subClassOf ?restriction .
            ?restriction rdf:type owl:Restriction ;
                         owl:onProperty base:hasOutput ;
                         owl:someValuesFrom {node} .
            BIND(base:hasOutput AS ?rel) .
            BIND({node} AS ?obj) .
        }}""",
        """SELECT ?sub ?rel ?obj WHERE {{
            ?sub rdf:type owl:Class ;
                    rdfs:subClassOf ?restriction .
            ?restriction rdf:type owl:Restriction ;
                         owl:onProperty base:hasInput ;
                         owl:someValuesFrom {node} .
            BIND(base:hasOutput AS ?rel) .
            BIND({node} AS ?obj) .
        }}""",
        """SELECT ?sub ?rel ?obj WHERE {{
            {node} rdf:type owl:Class ;
                   rdfs:subClassOf ?restriction .
            ?restriction rdf:type owl:Restriction ;
                         owl:onProperty base:hasOutput ;
                         owl:someValuesFrom ?sub .
            BIND(base:hasOutput AS ?rel) .
            BIND({node} AS ?obj) .
        }}""",
        """SELECT ?sub ?rel ?obj WHERE {{
            {node} rdf:type owl:Class ;
                   rdfs:subClassOf ?restriction .
            ?restriction rdf:type owl:Restriction ;
                         owl:onProperty base:hasInput ;
                         owl:someValuesFrom ?sub .
            BIND(base:hasInput AS ?rel) .
            BIND({node} AS ?obj) .
        }}""",
        """SELECT ?sub ?rel ?obj WHERE {{
            ?sub rdf:type {node}, owl:NamedIndividual .
            BIND(rdf:type AS ?rel) .
            BIND({node} AS ?obj) .
        }}""",
    ]

    def __init__(self, triplestore: Triplestore) -> None:
        """Initialise the OntoFlow engine. Sets the triplestore and the data dictionary.

        Args:
            triplestore (Triplestore): Triplestore to be used for the engine.
        """

        self.triplestore = triplestore
        self.data = {}
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

        # self.mapping = {"Step": self.__exploreNode(target)}

        self.__exploreNode(target)
        self.mapping = {"Step": self.__generateHierarchy(target)}

        with open("data.json", "w") as file:
            json.dump(self.data, file, sort_keys=False)

        with open("output.json", "w") as file:
            json.dump(self.mapping, file, sort_keys=False)

        return self.mapping

    def __exploreNode(self, node, parent=None):
        """Explore a node in the ontology using predefined patterns, and add the results to the data dictionary.

        Args:
            node (str): The node to explore.
            parent (str, optional): The parent node. Defaults to None.

        Returns:
            dict: The flat mapping route.
        """

        if node not in self.data:
            self.data[node] = {"routes": [], "relations": []}
        else:
            return

        common = {"_parents": {}}

        for pattern in self.__PATTERNS:
            nodeForm = f"<{node}>" if node[0] != "<" else node
            q = pattern.format(node=nodeForm)
            results = self.triplestore.query(q)
            # check if valid results
            if results == []:
                continue
            # check if there are multiple results with the same relation
            # in this case they have common subtrees

            if len(results) > 1:
                first = results[0]
                for more in results[1:]:
                    if more[0] not in common and more[2] == first[2]:
                        common[more[0]] = first[0]
                        common["_parents"][first[0]] = more[0]
                        self.data[more[0]] = {}
            for result in results:
                sub, rel, obj = result
                if (
                    sub not in self.data[obj]["routes"]
                    and sub != parent
                    and (
                        parent not in common["_parents"]
                        or sub not in common["_parents"][parent]
                    )
                ):
                    self.data[obj]["routes"].append(sub)
                    self.data[obj]["relations"].append(rel)
                self.__exploreNode(sub, obj)
            for k, v in common.items():
                if k != "_parents":
                    self.data[k] = self.data[v]

    def __generateHierarchy(self, node):
        """Generate a hierarchical mapping route from the flat data.

        Args:
            node (str): The node to start from.

        Returns:
            dict: The hierarchical mapping route.
        """

        if node not in self.data or not self.data[node]["routes"]:
            return None
        hierarchy = {node: {}}
        for route in self.data[node]["routes"]:
            hierarchy[node][route] = self.__generateHierarchy(route)
        return hierarchy
