from numpy import diff
from ontoflow.log.logger import logger
from ontoflow.node import Node
from ontoflow.mco import Mco


class Basic(Mco):
    def __init__(self, kpas: list[dict], node: Node):
        """Initialise the MCO.

        Args:
            kpas (list[dict]): The KPAs to be used for the MCO.
            node (Node): The node to be used for the MCO.
        """

        self.kpas = kpas
        self.data = [r.costs for r in node.routes]

    def mco_calc(self) -> list[int]:
        """Calculate the MCO ranking using normalised values.

        Returns:
            list[int]: The ranking of the routes.
        """

        logger.info("################ Start: MCO Calc ################")

        # Normalize the values
        for kpa in self.kpas:
            values = [item[kpa["name"]] for item in self.data]
            minVal, maxVal = min(values), max(values)
            diffVal = maxVal - minVal
            for item in self.data:
                if diffVal != 0:
                    if kpa["maximise"]:
                        normalisedValue = (item[kpa["name"]] - minVal) / diffVal
                    else:
                        normalisedValue = 1 - (
                            (item[kpa["name"]] - minVal) / diffVal
                        )
                else:
                    normalisedValue = 0
                item[f"Normalised{kpa['name']}"] = normalisedValue * kpa["weight"]

        # Calculate the weighted sum
        for item in self.data:
            item["WeightedSum"] = sum(
                item[f"Normalised{kpa['name']}"] for kpa in self.kpas
            )

        logger.info("################ End: MCO Calc ################")

        # Rank the entries and extract IDs
        return [
            item["Id"]
            for item in sorted(self.data, key=lambda x: x["WeightedSum"], reverse=True)
        ]
