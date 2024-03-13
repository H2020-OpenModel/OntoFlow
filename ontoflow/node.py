import json
import yaml
from copy import deepcopy
from random import random
from typing import Union


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
        self.kpis = self._getKPIs(iri, kpis)

    def __str__(self) -> str:
        """String representation of the node structure.

        Returns:
            str: the string representation of the node structure.
        """

        result = f"""Depth: {self.depth}, IRI: {self.iri}, Parent Predicate: {self.predicate}, Children ({len(self.children)}){":" if len(self.children) > 0 else ""}\n"""
        for child in self.children:
            result += str(child)

        return result

    def _serialize(self, path: Union[list, None] = None) -> dict:
        """Dictionary representation of the node structure.

        Args:
            path (list): the path to be serialised. Defaults to None.

        Returns:
            dict: the dictionary representation of the node structure.
        """

        ser = {
            "depth": self.depth,
            "iri": self.iri,
            "kpis": self.kpis,
        }

        if self.pathId is not None:
            ser["pathId"] = self.pathId

        if self.predicate:
            ser["predicate"] = self.predicate

        if len(self.children) > 0:
            if path and self.children[0].pathId is not None:
                p = path.pop(0)
                ser["children"] = [self.children[p]._serialize(path)]
            else:
                ser["children"] = [child._serialize(path) for child in self.children]

        return ser

    def _updateChildrenDepth(self, node: "Node") -> None:
        """Recursively update the depth of all children of a node.

        Args:
            node (Node): The Node object whose children's depth is to be updated.
        """

        for child in node.children:
            child.depth = node.depth + 1
            self._updateChildrenDepth(child)

    def _getKPIs(self, iri: str, kpis: list) -> dict:
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

    def addChild(
        self, iri: str, predicate: str, pathId: Union[int, None] = None, kpis: list = []
    ) -> "Node":
        """Add a child to the node.

        Args:
            iri (str): the IRI of the child node.
            predicate (str): the relation to the child node.
            pathId (int): the pathId of the child node. Defaults to None.
            kpis (list): the KPIs of the child node. Defaults to [].

        Returns:
            Node: the child node.
        """

        node = Node(self.depth + 1, iri, predicate, pathId, kpis)
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
