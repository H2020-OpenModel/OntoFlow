import yaml
from tripper import Triplestore

# podman run -i --rm -p 3030:3030 -v databases:/fuseki/databases -t fuseki --update --loc databases/openmodel /openmodel

# Sistemare query facendo test, v. onClass, v. inversione responabilità


class OntoFlowEngine:
    __PATTERNS = [
        """SELECT ?result ?property ?node WHERE {{
            ?result rdf:type owl:Class ;
                    rdfs:subClassOf {node} .
            BIND(rdfs:subClassOf AS ?property)
            BIND({node} as ?node) .
        }}""",
        """SELECT ?result ?property ?node WHERE {{
            ?result rdf:type owl:Class ;
                    rdfs:subClassOf ?restriction .
            ?restriction rdf:type owl:Restriction ;
                         owl:onProperty base:hasOutput ;
                         owl:someValuesFrom {node} .
            BIND(base:hasOutput AS ?property) .
            BIND({node} AS ?node) .
        }}""",
        """SELECT ?result ?property ?node WHERE {{
            {node} rdf:type owl:Class ;
                   rdfs:subClassOf ?restriction .
            ?restriction rdf:type owl:Restriction ;
                         owl:onProperty base:hasInput ;
                         owl:someValuesFrom ?result .
            BIND(base:hasInput AS ?property) .
            BIND({node} AS ?node) .
        }}""",
        """SELECT ?result ?property ?node WHERE {{
            {node} rdf:type owl:Class ;
                   rdfs:subClassOf ?restriction .
            ?restriction rdf:type owl:Restriction ;
                         owl:onProperty base:hasOutput ;
                         owl:someValuesFrom ?result .
            BIND(base:hasOutput AS ?property) .
            BIND({node} AS ?node) .
        }}""",
        """SELECT ?result ?property ?node WHERE {{
            {node} rdf:type owl:Class ;
                   rdfs:subClassOf ?restriction .
            ?restriction rdf:type owl:Restriction ;
                         owl:onProperty base:hasInput ;
                         owl:someValuesFrom ?result .
            BIND(base:hasInput AS ?property) .
            BIND({node} AS ?node) .
        }}""",
        """SELECT ?result ?property ?node WHERE {{
            {node} rdf:type owl:Class ;
                   rdfs:subClassOf ?restriction .
            ?restriction rdf:type owl:Restriction ;
                         owl:onProperty base:hasOutput ;
                         owl:someValuesFrom ?result .
            BIND(base:hasOutput AS ?property) .
            BIND({node} AS ?node) .
        }}""",
        """SELECT ?result ?property ?node WHERE {{
            ?result rdf:type {node}, owl:NamedIndividual .
            BIND(rdf:type AS ?property) .
            BIND({node} AS ?node) .
        }}""",
    ]

    def __init__(self, triplestore: Triplestore) -> None:
        """Initialise the OntoFlow engine. Sets the triplestore and the data dictionary.

        Args:
            triplestore (Triplestore): Triplestore to be used for the engine.
        """

        self.triplestore = triplestore
        self.data = {}

    def loadOntology(self, path: str, format: str = "turtle") -> None:
        """Load the ontology from a file.

        Args:
            path (str): Path to the ontology file.
            format (str, optional): Format of the ontology file. Defaults to "turtle".
        """
        self.triplestore.parse(path, format=format)

    def generateYaml(self, root: str) -> None:
        """Generate a hierarchical YAML file from the given data.

        Args:
            root (str): The root node of the hierarchy.
        """

        hierarchy = self.__convertToHierarchy(self.data, root)

        hierarchy = {"Step": hierarchy}

        with open("output.yaml", "w") as file:
            yaml.dump(hierarchy, file, sort_keys=False)

    def getMappingRoute(self, target: str) -> dict:
        """Get the mapping route from the target to all the possible sources.

        Args:
            target (str): The target data to be found.

        Returns:
            dict: The mapping route.
        """

        self.data[target] = {}

        self.__exploreNode(target)

        return self.data

    def __exploreNode(self, node: str) -> None:
        """Explore a node in the ontology using predefined patterns, and add the results to the data dictionary.

        Args:
            node (str): The node to explore.
        """

        for pattern in self.__PATTERNS:
            nodeForm = f"<{node}>" if node[0] != "<" else node
            q = pattern.format(node=nodeForm)
            results = self.triplestore.query(q)
            for result in results:
                val, prop, node = result
                if not val in self.data:
                    self.data[val] = {"node": node, "property": prop}
                    self.__exploreNode(val)

    def __convertToHierarchy(self, data: dict, base: str) -> dict:
        """
        Convert the given dictionary into a hierarchical structure.

        Args:
            data (dict): The data to convert.
            base (str): The base element of the hierarchy.

        Returns:
            dict: The hierarchical structure.
        """

        hierarchy = {"output_iri": base, "routes": []}

        for key, value in data.items():
            if value.get("node") == base:
                hierarchy["routes"].append(
                    {
                        "output_iri": key,
                        "relation": value.get("property"),
                        "routes": self.__convertToHierarchy(data, key)["routes"],
                    }
                )

        return hierarchy
