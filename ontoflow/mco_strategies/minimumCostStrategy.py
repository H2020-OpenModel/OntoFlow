import math
import copy
from ontoflow.engine import OntoFlowEngineMappingStep, OntoFlowEngineValue


class MinimumCostStrategy:

    def __init__(self):
        pass

    def _get_minimum_cost_node(self, nodes):

        minimum = math.inf
        minimum_node = None
        for node in nodes:
            if node["cost"] < minimum:
                minimum = node["cost"]
                minimum_node = node

        return minimum_node

    def _build_path(self, path):

        route = path["route"]
        if path["parent"] is None:
            route_copy = copy.copy(route)
            route_copy.input_routes = []
            return {"root": route_copy, "attach": route_copy}
        else:
            node = self._build_path(path["parent"])
            root = node["root"]
            attach = node["attach"]
            route_copy = copy.copy(route)
            if isinstance(route_copy, OntoFlowEngineMappingStep):
                route_copy.input_routes = []

            attach.add_input(route_copy)
            return {"root": root, "attach": route_copy}

    def get_best_route(self, routes):
        #####
        # Return the route with the minimum cost
        # Tree traversal algorithm
        #####

        open_set = [{"route": routes, "cost": routes.cost, "parent": None}]
        closed_set = []

        while open_set:
            minimum_cost_node = self._get_minimum_cost_node(open_set)

            if isinstance(minimum_cost_node["route"], OntoFlowEngineValue):
                return self._build_path(minimum_cost_node)

            open_set.remove(minimum_cost_node)
            closed_set.append(minimum_cost_node)

            for input in minimum_cost_node["route"].input_routes:
                node_ist = list(input.values())[0]
                if node_ist not in closed_set:
                    open_set.append(
                        {
                            "route": node_ist,
                            "cost": minimum_cost_node["cost"] + node_ist.cost,
                            "parent": minimum_cost_node,
                        }
                    )

        raise Exception("No path found")
