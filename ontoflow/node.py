import json
import yaml
import subprocess
import itertools
import random

from copy import deepcopy
from typing import Optional


class Node:
    def __init__(
        self,
        depth: int,
        iri: str,
        predicate: str,
        kpas: dict[str, float] = {},
        routeChoices: int = 1,
        localChoices: int = 0,
    ):
        """Initialise a node in the ontology tree.

        Args:
            depth (int): the depth of the node in the tree.
            iri (str): the IRI of the node.
            predicate (str): the relation the parent node.
            kpas (dict[str, float]): the KPAs of the node. Defaults to [].
            routeChoices (int): the number of routes underlying the node. Defaults to 1.
            localChoices (int): the number of possible elements you can select from the node. Defaults to 0.
        """

        self.depth: int = depth
        self.iri: str = iri
        self.predicate: str = predicate
        self.kpas: dict[str, float] = kpas
        self.routeChoices: int = routeChoices
        self.localChoices: int = localChoices
        self.costs: dict[str, float] = deepcopy(kpas)
        self.children: list["Node"] = []
        self.routes: list["Node"] = []

    def addChild(
        self,
        iri: str,
        predicate: str,
        kpas: dict[str, float],
    ) -> "Node":
        """Creates a node instance using IRI, predicate, and KPAs, and adds it to the node as a child.

        Args:
            iri (str): the IRI of the child node.
            predicate (str): the relation to the child node.
            kpas (dict[str, float]): the KPAs of the child node.

        Returns:
            Node: the child node.
        """

        node = Node(self.depth + 1, iri, predicate, kpas)
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

    def generateRoutes(self) -> None:
        """Generate all the possible routes and their KPAs, and save the structure in the Node as routes."""

        routes = []
        paths = self._getPaths()
        print(f"Paths: {paths}")

        for i, path in enumerate(paths):
            route = self._getRoute(path)
            route.costs["Id"] = i
            routes.append(route)

        self.routes = routes

    def visualize(self, output: Optional[str] = None, format: str = "png") -> str:
        """Saves an image of the node and its children as a graph.

        Args:
            output (str): The name of the file to export the graph. Defaults to None.
            format (str): The format of the file to export the graph. Defaults to "png".

        Returns:
            str: the string representation of the graph.
        """

        nodeString = "digraph G {\n" + "\n".join(self._visualize()) + "\n}"

        if output is not None:
            subprocess.run(
                args=["dot", f"-T{format}", "-o", f"{output}.{format}"],
                shell=False,
                check=True,
                input=nodeString.encode(),
            )

        return nodeString

    def export(self, fileName: str, format: str = "yaml") -> None:
        """Serialize a node as YAML or JSON and saves them in a file.

        Args:
            fileName (str): The name of the file to export the data.
            format (str): The format of the file to export. Defaults to "yaml".
        """
        if format == "json":
            with open(f"{fileName}.json", "w") as file:
                json.dump(self._serialize(), file, indent=4)
        if format == "yaml":
            with open(f"{fileName}.yaml", "w") as file:
                yaml.dump(self._serialize(), file, indent=4, sort_keys=False)

    def accept(self, visitor) -> None:
        """Accept a visitor and visit the node.

        Args:
            visitor: The visitor to be accepted.
        """

        return visitor(self)

    def _getPaths(self) -> list[dict[str, str]]:
        """Get all the possible paths from a node.

        Returns:
            list[list[int]]: the list of all possible paths as list of integers.
        """

        paths = []

        if self.routeChoices > 1:
            if self.localChoices >= self.routeChoices:
                # Last choice point
                paths = [{self.iri: child.iri} for child in self.children]

            else:
                if self.localChoices > 1:
                    # Choice point, and there are other routes to find
                    for child in self.children:
                        tmp = child._getPaths()
                        for el in tmp:
                            el.update({self.iri: child.iri})
                            paths.append(el)
                else:
                    # Not a choice point, and there are other choices to be made
                    childrenChoices = []
                    for child in self.children:
                        tmp = child._getPaths()
                        childrenChoices.append(tmp)
                    combinations = list(itertools.product(*childrenChoices))
                    for comb in combinations:
                        combChoice = {}
                        for choice in comb:
                            combChoice.update(choice)

                        paths.append(combChoice)

            paths = list(filter(lambda x: len(x.keys()) > 0, paths))
        else:
            paths = [{}]

        return paths

    def _getRoute(self, path: dict[str, str]) -> "Node":
        """Get a route from the node following the path.

        Args:
            path (list[int]): the path representing the route. Defaults to [].

        Returns:
            Node: the node representing the route.
        """

        cpy = deepcopy(self)
        cpy.children = []

        if self.localChoices > 1:
            childrenToBeSelected = path.get(self.iri)
            for child in self.children:
                if child.iri == childrenToBeSelected:
                    cpy.children.append(child._getRoute(path))
        else:
            for child in self.children:
                cpy.children.append(child._getRoute(path))

        for child in cpy.children:
            for k, v in child.costs.items():
                cpy.costs[k] = round(cpy.costs[k] + v, 2)

        return cpy

    def _updateChildrenDepth(self, node: "Node") -> None:
        """Recursively update the depth of all children of a node.

        Args:
            node (Node): The Node object whose children's depth is to be updated.
        """

        for child in node.children:
            child.depth = node.depth + 1
            self._updateChildrenDepth(child)

    def _serialize(self) -> dict:
        """Dictionary representation of the node structure.

        Returns:
            dict: the dictionary representation of the node structure.
        """

        ser = {"depth": self.depth, "iri": self.iri}

        ser["routeChoices"] = self.routeChoices
        ser["localChoices"] = self.localChoices

        if self.kpas:
            ser["kpas"] = self.kpas

        if self.predicate:
            ser["predicate"] = self.predicate

        if len(self.children) > 0:
            ser["children"] = [child._serialize() for child in self.children]

        return ser

    def _visualize(self) -> set[str]:
        """Generate the elements of the graph to be exported from the Node.

        Returns:
            set[str]: the string representation for the visualization of the graph.
        """

        colormap = {
            "hasOutput": "orange",
            "individual": "lightblue",
        }
        nodeChoicePointColor = "red"

        nodeString = set()
        mainString = '"{}" [shape=box] [xlabel="r: {}\nl: {}"] [style=filled, fillcolor={}]'.format(
            self.iri,
            self.routeChoices,
            self.localChoices,
            colormap.get(self.predicate, "white"),
        )
        if self.localChoices > 1:
            mainString = "subgraph cluster_{} {{ {} color={}}}".format(
                random.randint(0, 100), mainString, nodeChoicePointColor
            )

        nodeString.add(mainString)

        for child in self.children:
            nodeString.update(child._visualize())
            dirBack = (
                "back" if child.predicate in ["hasOutput", "subClassOf"] else "forward"
            )
            nodeString.add(
                '"{}" -> "{}" [label="{}", dir="{}", color="{}"]'.format(
                    self.iri, child.iri, child.predicate, dirBack, "black"
                )
            )

        return nodeString

    @staticmethod
    def filterRoutes(
        routes: list["Node"], nodes: Optional[list[str]] = None
    ) -> list["Node"]:
        """Filter the routes to only keep those with individuals as leaves and containing all specified nodes.

        Args:
            routes (list[Node]): the list of routes to be filtered.
            nodes (Optional[list[str]]): the list of node IRIs to be checked.

        Returns:
            list[Node]: the list of routes with only the individuals as leaves and containing all specified nodes.
        """

        def _checkNodes(node: "Node", requiredNodes: set[str]) -> bool:
            """Check if the node has only individuals as leaves and contains all specified nodes using the _traverse function.

            Args:
                node (Node): the node to be checked.
                requiredNodes (set[str]): the set of node IRIs to be checked.

            Returns:
                bool: True if the node has only individuals as leaves and contains all specified nodes, False otherwise.
            """
            found = set()

            def _traverse(node: "Node") -> bool:
                if node.iri in requiredNodes:
                    found.add(node.iri)
                if len(node.children) == 0:
                    return node.predicate == "individual"
                else:
                    return all(_traverse(child) for child in node.children)

            return _traverse(node) and found == requiredNodes

        return list(
            filter(
                lambda node: _checkNodes(node, set(nodes) if nodes else set()), routes
            )
        )

    def __str__(self) -> str:
        """String representation of the node structure.

        Returns:
            str: the string representation of the node structure.
        """

        result = f"""Depth: {self.depth}, IRI: {self.iri}, Parent Predicate: {self.predicate}, Children ({len(self.children)}){":" if len(self.children) > 0 else ""}\n"""
        for child in self.children:
            result += str(child)

        return result
