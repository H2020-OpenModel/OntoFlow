import yaml
from tripper import Triplestore

# Definizione interfaccia per chiamare metodo
# Input: ex. Density (root, albero parte, si lavora "al contrario", si parte da output e si ottengono input)
# Output: tutto il precorso trovato (struttura ad albero con input, nodi intermedi, e valore finale)
# Risultato: v. Public/Deliverable5.5/ontoKB/ontoflow_output.txt formato yaml
# Vedi lookup table in tripper/mappings
# Per interfacciamento a Triplestore usare Tripper
# Testare in cartella di examples

# podman run -i --rm -p 3030:3030 -v databases:/fuseki/databases -t fuseki --update --loc databases/openmodel /openmodel

# Struttura ad albero v. _output.yaml
# Sistemare query facendo test, v. onClass, v. inversione responabilità


class OntoFlowEngine:
    __PATTERNS = [
        """SELECT ?result WHERE {{
            ?result rdf:type owl:Class .
            ?result rdfs:subClassOf {node} .
        }}""",
        """SELECT ?result WHERE {{
            ?result rdf:type owl:Class .
            ?result rdfs:subClassOf ?restriction .
            ?restriction rdf:type owl:Restriction .
            ?restriction owl:onProperty base:hasOutput .
            ?restriction owl:someValuesFrom {node} .
        }}""",
        """SELECT ?result WHERE {{
            {node} rdf:type owl:Class .
            {node} rdfs:subClassOf ?restriction .
            ?restriction rdf:type owl:Restriction .
            ?restriction owl:onProperty base:hasInput .
            ?restriction owl:someValuesFrom ?result .
        }}""",
        """SELECT ?result WHERE {{
            {node} rdf:type owl:Class .
            {node} rdfs:subClassOf ?restriction .
            ?restriction rdf:type owl:Restriction .
            ?restriction owl:onProperty base:hasOutput .
            ?restriction owl:someValuesFrom ?result .
        }}""",
        """SELECT ?result WHERE {{
            ?result rdf:type {node}, owl:NamedIndividual .
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

    def generateYaml(self, data: dict = {}):
        """
        Generate a YAML file based on the search of the input starting from the output.

        Args:
            data (dict): The data used for generating the yaml file. Defaults to {}
        """

        if not data:
            data = self.data

        # Save the YAML data to a file
        with open("output.yaml", "w") as file:
            yaml.dump(data, file, default_flow_style=False)

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
            print("RES:",results)
            for result in results:
                val = result[0]
                print("RES", val)
                print("NODE", node)
                print("DATA", self.data)
                print()
                if not val in self.data:
                    self.data[val] = {"from": node}
                    self.__exploreNode(val)
