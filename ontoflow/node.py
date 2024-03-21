from typing import Union, Optional
from copy import deepcopy
from random import random
import json
import yaml


class RouteKPI:
    def __init__(self, route: "Node", kpis: dict[str, float]):
        self.route = route
        self.kpis = kpis


class Node:
    def __init__(
        self,
        depth: int,
        iri: str,
        predicate: str,
        pathId: Union[int, None] = None,
        kpis: list = [],
    ):
        """Initialise a node in the ontology tree.

        Args:
            depth (int): the depth of the node in the tree.
            iri (str): the IRI of the node.
            predicate (str): the relation the parent node.
            pathId (int): the id of the path. Defaults to None.
            kpis (list): the KPIs of the node. Defaults to [].
        """

        self.depth: int = depth
        self.iri: str = iri
        self.predicate: str = predicate
        self.pathId: Union[int, None] = pathId
        self.children: list["Node"] = []
        self.kpisList: list = kpis
        self.kpis = self._getKpis(iri, kpis)
        self.routes: list[RouteKPI] = []

    def addChild(
        self, iri: str, predicate: str, pathId: Union[int, None] = None
    ) -> "Node":
        """Add a child to the node.

        Args:
            iri (str): the IRI of the child node.
            predicate (str): the relation to the child node.
            pathId (int): the pathId of the child node. Defaults to None.

        Returns:
            Node: the child node.
        """

        node = Node(self.depth + 1, iri, predicate, pathId, self.kpisList)
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
        paths = self._getPathsKpis()

        for i, path in enumerate(paths):
            route = {"route": self._getRoute(path["path"]), "kpis": path["kpis"]}
            route["kpis"]["ModelId"] = i
            routes.append(route)

        self.routes = routes

    def export(self, fileName: str) -> None:
        """Serialize a node as JSON and export it to a file.

        Args:
            fileName (str): The name of the file to export the JSON data.
        """

        with open(f"{fileName}.json", "w") as file:
            json.dump(self._serialize(), file, indent=4)

        with open(f"{fileName}.yaml", "w") as file:
            yaml.dump(self._serialize(), file, indent=4, sort_keys=False)

    def accept(self, visitor):
        """Accept a visitor and visit the node.

        Args:
            visitor: The visitor to be accepted.
        """

        return visitor(self)

    def _getKpis(self, iri: str, kpis: list) -> dict:
        """Get the KPIs of a node.

        Args:
            iri (str): The IRI of the node.
            kpis (list): The KPIs to be retrieved.

        Returns:
            dict: The KPIs of the node.
        """

        _kpis = {}

        for kpi in kpis:
            _kpis[kpi] = round(random(), 2)

        return _kpis

    def _getPathsKpis(
        self, node: Optional["Node"] = None, path: list = [], kpis: dict = None
    ) -> list:
        """Get all the possible paths and their KPIs.

        Args:
            node (Node): The starting node.
            path (list): List of nodes with pathId in the path.
            kpis (dict): The KPIs of the path.

        Returns:
            list: The list of all possible routes and their KPIs.
        """

        if not node:
            node = self

        if kpis is None:
            kpis = {kpi: 0 for kpi in node.kpis.keys()}

        # Add pathId to path if it exists
        if node.pathId is not None:
            path.append(node.pathId)

        # If this node has KPIs, sum them to the current KPIs
        for kpi in node.kpis.keys():
            kpis[kpi] += node.kpis[kpi]

        # If this node is a leaf (has no children), add the path and KPIs to the results
        if not node.children:
            return [{"path": path, "kpis": kpis}]

        # Otherwise, recurse on the children
        results = []
        for child in node.children:
            results.extend(
                self._getPathsKpis(
                    child,
                    list(path),
                    {kpi: values for kpi, values in kpis.items()},
                )
            )

        return results

    def _getRoute(self, path: list) -> "Node":
        """Get all the possible routes from a node.

        Args:
            path (list): the path to be serialised. Defaults to [].

        Returns:
            Node: the node representing the route.
        """

        node = Node(self.depth, self.iri, self.predicate)

        if len(self.children) > 0:
            if path and self.children[0].pathId is not None:
                p: int = path.pop(0)
                node.children = [self.children[p]._getRoute(path)]
            else:
                node.children = [child._getRoute(path) for child in self.children]

        return node

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

        if self.kpis:
            ser["kpis"] = self.kpis

        if self.pathId is not None:
            ser["pathId"] = self.pathId

        if self.predicate:
            ser["predicate"] = self.predicate

        if len(self.children) > 0:
            ser["children"] = [child._serialize() for child in self.children]

        return ser

    def __str__(self) -> str:
        """String representation of the node structure.

        Returns:
            str: the string representation of the node structure.
        """

        result = f"""Depth: {self.depth}, IRI: {self.iri}, Parent Predicate: {self.predicate}, Children ({len(self.children)}){":" if len(self.children) > 0 else ""}\n"""
        for child in self.children:
            result += str(child)

        return result
