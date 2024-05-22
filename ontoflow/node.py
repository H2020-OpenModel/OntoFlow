import json
import yaml
import subprocess

from copy import deepcopy
from typing import Optional


class Node:
    def __init__(
        self,
        depth: int,
        iri: str,
        predicate: str,
        kpis: dict[str, float] = {},
        routeChoices: int = 1,
        localChoices: int = 0,
    ):
        """Initialise a node in the ontology tree.

        Args:
            depth (int): the depth of the node in the tree.
            iri (str): the IRI of the node.
            predicate (str): the relation the parent node.
            kpis (dict[str, float]): the KPIs of the node. Defaults to [].
            routeChoices (int): the number of routes underlying the node. Defaults to 1.
            localChoices (int): the number of possible elements you can select from the node. Defaults to 0.
        """

        self.depth: int = depth
        self.iri: str = iri
        self.predicate: str = predicate
        self.kpis: dict[str, float] = kpis
        self.routeChoices: int = routeChoices
        self.localChoices: int = localChoices
        self.costs: dict[str, float] = deepcopy(kpis)
        self.children: list["Node"] = []
        self.routes: list["Node"] = []

    def addChild(
        self,
        iri: str,
        predicate: str,
        kpis: dict[str, float],
    ) -> "Node":
        """Creates a node instance using IRI, predicate, and KPIs, and adds it to the node as a child.

        Args:
            iri (str): the IRI of the child node.
            predicate (str): the relation to the child node.
            kpis (dict[str, float]): the KPIs of the child node.

        Returns:
            Node: the child node.
        """

        node = Node(self.depth + 1, iri, predicate, kpis)
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
        """Generate all the possible routes and their KPIs, and save the structure in the Node as routes."""

        routes = []
        paths = self._getPaths()

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

    def export(self, fileName: str) -> None:
        """Serialize a node as JSON and YAML and saves them in a file.

        Args:
            fileName (str): The name of the file to export the JSON data.
        """

        with open(f"{fileName}.json", "w") as file:
            json.dump(self._serialize(), file, indent=4)

        with open(f"{fileName}.yaml", "w") as file:
            yaml.dump(self._serialize(), file, indent=4, sort_keys=False)

    def accept(self, visitor) -> None:
        """Accept a visitor and visit the node.

        Args:
            visitor: The visitor to be accepted.
        """

        return visitor(self)

    def _getPaths(self) -> list[list[int]]:
        """Get all the possible paths from a node.

        Returns:
            list[list[int]]: the list of all possible paths as list of integers.
        """

        paths = []

        if self.routeChoices > 1:
            if self.localChoices >= self.routeChoices:
                # Last choice point
                paths = [[i] for i in range(len(self.children))]

            else:
                if self.localChoices > 1:
                    # Choice point, and there are other routes to find
                    for i, child in enumerate(self.children):
                        tmp = child._getPaths()
                        for el in tmp:
                            el.insert(0, i)
                            paths.append(el)
                else:
                    # Not a choice point, and there are other routes to find
                    for i, child in enumerate(self.children):
                        tmp = child._getPaths()
                        paths += tmp

            paths = list(filter(lambda x: len(x) > 0, paths))
        else:
            paths = [[]]

        return paths

    def _getRoute(self, path: list[int]) -> "Node":
        """Get a route from the node following the path.

        Args:
            path (list[int]): the path representing the route. Defaults to [].

        Returns:
            Node: the node representing the route.
        """

        cpy = deepcopy(self)
        cpy.children = []

        if self.localChoices > 1:
            cpy.children.append(self.children[path[0]]._getRoute(path[1:]))
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

        if self.kpis:
            ser["kpis"] = self.kpis

        if self.predicate:
            ser["predicate"] = self.predicate

        if len(self.children) > 0:
            ser["children"] = [child._serialize() for child in self.children]

        return ser

    def _visualize(self) -> str:
        """Generate the elements of the graph to be exported from the Node.

        Returns:
            str: the string representation of the graph.
        """

        colormap = {
            "hasOutput": "orange",
            "individual": "lightblue",
        }

        nodeString = set()
        nodeString.add(
            '"{}" [shape=box] [xlabel="r: {}\nl: {}"] [style=filled, fillcolor={}]'.format(
                self.iri, self.routeChoices, self.localChoices, colormap.get(self.predicate, "white")
            )
        )

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

    def __str__(self) -> str:
        """String representation of the node structure.

        Returns:
            str: the string representation of the node structure.
        """

        result = f"""Depth: {self.depth}, IRI: {self.iri}, Parent Predicate: {self.predicate}, Children ({len(self.children)}){":" if len(self.children) > 0 else ""}\n"""
        for child in self.children:
            result += str(child)

        return result
