from io import BufferedReader
import os
from typing import Union, Literal
import yaml
import requests

# Definizione interfaccia per chiamare metodo
# Input: ex. Density (root, albero parte, si lavora "al contrario", si parte da output e si ottengono input)
# Output: tutto il precorso trovato (struttura ad albero con input, nodi intermedi, e valore finale)
# Risultato: v. Public/Deliverable5.5/ontoKB/ontoflow_output.txt formato yaml
# Vedi lookup table in tripper/mappings
# Per interfacciamento a Triplestore usare Tripper
# Testare in cartella di examples

# podman run -i --rm -p 3030:3030 -v databases:/fuseki/databases -t fuseki --update --loc databases/openmodel /openmodel

ENDPOINT = f"http://localhost:3030/openmodel"
DATABASE = "openmodel"
GRAPH = "graph://main"
PATH = os.path.abspath("openmodel_example.ttl")
NAMESPACES = {
    "owl": "http://www.w3.org/2002/07/owl#",
    "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
    "schema": "http://schema.org/",
    "base": "http://webprotege.stanford.edu/",
}

data = {}


def exploreNode(node: str, target: str):
    """Explore a node in the ontology using predefined patterns, and add the results to the data dictionary.

    Args:
        node (str): The node to explore.
        target (str): The node to be found.
    """

    patterns = [
        """SELECT ?result WHERE {{
            ?result rdf:type owl:Class .
            ?result rdfs:subClassOf {node} .
        }}""",
        """SELECT ?result WHERE {{
            ?result rdf:type owl:Class .
            ?result rdfs:subClassOf ?restriction .
            ?restriction rdf:type owl:Restriction .
            ?restriction owl:onProperty base:hasInput .
            ?restriction owl:someValuesFrom {node} .
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
            ?result rdf:type {node}, owl:NamedIndividual .
        }}""",
    ]

    for pattern in patterns:
        nodeForm = f"<{node}>" if node[0] != "<" else node
        q = pattern.format(node=nodeForm)
        results = query(q)["results"]["bindings"]
        for result in results:
            val = result["result"]["value"]
            print("RES", val)
            print("NODE", node)
            print("DATA", data)
            print()
            if not val in data:
                data[val] = {"from": node}
                if val != target:
                    exploreNode(val, target)
                else:
                    print(f"TARGET {target} FOUND!")
                    return


def generateYaml(input: str, output: str):
    """
    Generate a YAML file based on the search of the input starting from the output.

    Args:
        input (str): The input data to be found.
        output (str): The output data, which is the starting point.
    """
    data[output] = {}

    exploreNode(output, input)

    # Save the YAML data to a file
    with open("output.yaml", "w") as file:
        yaml.dump(data, file, default_flow_style=False)


def query(q: str):
    """
    Executes a SPARQL query with the given query string.

    Args:
        q (str): The SPARQL query string.

    Returns:
        The result of the query.
    """

    iw = q.index("WHERE")
    queryStr = f"{q[:iw]}FROM <{GRAPH}> {q[iw:]}".strip()

    return __request("GET", queryStr)


def __request(
    method: Literal["GET", "POST"],
    cmd: Union[str, BufferedReader] = "",
    prefix: bool = True,
    headers: dict = {},
    plainData: bool = False,
    graph: bool = False,
    json: bool = True,
) -> dict:
    """Generic REST method caller for the Triplestore

    Args:
        method (Literal["GET", "POST"]): Method of the request.
        cmd (Union[str, BufferedReader], optional): Command to be executed. Defaults to "".
        prefix (bool, optional): If the prefixes need to be added to the query. Defaults to True.
        headers (dict, optional): Custom headers. Defaults to {}.
        plainData (bool, optional): If data needs a format or is plain. Defaults to False.
        graph (bool, optional): If the endpoint needs to specify the graph. Defaults to False.
        json (bool, optional): If the result is a JSON or a dict containing the result as string. Defaults to True.

    Returns:
        dict: Dict containing the result as JSON or text
    """

    if method not in ["GET", "POST"]:
        print("Method unknown")
        return {}

    ep = ENDPOINT if not graph else f"{ENDPOINT}?graph={GRAPH}"

    if prefix and isinstance(cmd, str):
        cmd = " ".join(f"PREFIX {k}: <{v}>" for k, v in NAMESPACES.items()) + cmd

    try:
        r: requests.Response = requests.request(
            method=method,
            url=ep,
            headers=headers,
            params=({"query": cmd} if method == "GET" and cmd else None),
            data=(
                cmd
                if method == "POST" and plainData
                else {"update": cmd}
                if method == "POST" and not plainData
                else None
            ),
        )
        r.raise_for_status()
        if r.status_code == 200:
            return r.json() if json else {"response": r.text}
        return {}
    except requests.RequestException as e:
        print(e)
        return {}
