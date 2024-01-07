# TODO test ricerca
# 1. Creare ontologia come foto
# 2. Creare query per ottenere individuals da Density

# Definizione interfaccia per chiamare metodo
# Input: ex. Density (root, albero parte, si lavora "al contrario", si parte da output e si ottengono input)
# Output: tutto il precorso trovato (struttura ad albero con input, nodi intermedi, e valore finale)
# Risultato: v. Public/Deliverable5.5/ontoKB/ontoflow_output.txt formato yaml
# Vedi lookup table in tripper/mappings
# Per interfacciamento a Triplestore usare Tripper
# Testare in cartella di examples

# Scaricare nuova versione Fuseki Docker

import yaml

PREFIXES = ["PREFIX base: <http://webprotege.stanford.edu/>"]


def addPrefixes(query):
    pref = "\n".join(PREFIXES)
    return f"{pref}\n{query}"


def executeQuery(query):
    sparql = SPARQLWrapper(
        "http://localhost:3030/ds/query"
    )  # replace with your Fuseki server address
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    return results["results"]["bindings"]


def exploreNode(node: str, data: dict):
    """Explore a node in the ontology using predefined patterns, and add the results to the data dictionary.

    Args:
        node (str): The node to explore.
        data (dict): The dictionary to add the results to.
    """ 
    
    patterns = [
        """SELECT ?subject WHERE {
            # Pattern for querying using the subClassOf. 
            # base:Density is the argument
            # subject is the result
            ?subject rdf:type owl:Class .
            ?subject rdfs:subClassOf base:Density .
        }""",
        """SELECT ?subject WHERE {
            # Pattern for querying using the custom property hasInput. 
            # base:LAMMPSLog is the argument.
            # ?subject is the result.
            ?subject rdf:type owl:Class .
            ?subject rdfs:subClassOf ?restriction .
            ?restriction rdf:type owl:Restriction .
            ?restriction owl:onProperty base:hasInput .
            ?restriction owl:someValuesFrom base:LAMMPSLog .
        }""",
        """SELECT ?subject WHERE {
            # Pattern for querying using the custom property hasOutput. 
            # base:LAMMPSLog is the argument.
            # ?subject is the result.
            ?subject rdf:type owl:Class .
            ?subject rdfs:subClassOf ?restriction .
            ?restriction rdf:type owl:Restriction .
            ?restriction owl:onProperty base:hasOutput .
            ?restriction owl:someValuesFrom base:FluidDensity .
        }""",
        """SELECT ?object WHERE {
            # Inverting the result with the argument the results the patterns makes an inversion of responsibility
            # Example with hasInput
            # ?object is the result
            base:MoltemplateProcess1 rdf:type owl:Class .
            base:MoltemplateProcess1 rdfs:subClassOf ?restriction .
            ?restriction rdf:type owl:Restriction .
            ?restriction owl:onProperty base:hasInput .
            ?restriction owl:someValuesFrom ?object .
        }""",
        """SELECT ?subject WHERE {
            # Pattern for finding an individual of a class
            # Example: individual of MoltemplateProcess1
            # ?subject is the result.
            ?subject rdf:type base:MoltemplateProcess1, owl:NamedIndividual .
        }""",
    ]

    for pattern in patterns:
        query = pattern % node
        results = executeQuery(query)
        for result in results:
            subject = result["subject"]["value"]
            data[node][subject] = {}
            exploreNode(subject, data[node])


def generateYaml(input, output):
    data = {output: {}}
    exploreNode(output, data)

    # Save the YAML data to a file
    with open("output.yaml", "w") as file:
        yaml.dump(data, file, default_flow_style=False)


# Use the function
generateYaml("LAMMPSLog", "Density")

