from dotenv import load_dotenv

from osp.core.namespaces import mods, cuba
import osp.core.utils.simple_search as search
from osp.wrappers.sim_cmcl_mods_wrapper import mods_session as ms

from ontoflow.log.logger import logger
from ontoflow.node import Node
from ontoflow.mco import Mco


class Mods(Mco):
    def __init__(self, kpis: list[dict], node: Node):
        """Initialise the MCO.

        Args:
            kpis (list[dict]): The KPIs to be used for the MCO.
            node (Node): The node to be used for the MCO.
        """

        # Setup algorithm
        self.mcdm_simulation = mods.MultiCriteriaDecisionMaking()
        mcdm_algorithm = mods.Algorithm(name="algorithm1", type="MCDM")

        mcdm_algorithm.add(mods.Variable(name="Id", type="input"))

        for kpi in kpis:
            mcdm_algorithm.add(
                mods.Variable(
                    name=kpi["name"],
                    type="output",
                    objective="Maximise" if kpi["maximise"] else "Minimise",
                    weight=kpi["weight"],
                )
            )

        self.mcdm_simulation.add(mcdm_algorithm)

        # Setup data
        kpis_list = [kpi["name"] for kpi in kpis]
        kpis_list.append("Id")

        self.data: list = [kpis_list]

        for r in node.routes:
            self.data.append([r.costs[kpi] for kpi in kpis_list])

    def mco_calc(self) -> list[int]:
        """Calculate the MCO.

        Returns:
            list[int]: The ranking of the routes.
        """

        logger.info("################ Start: MCO Calc ################")
        logger.info("Setting up the simulation inputs")

        data_header = self.data[0]
        data_values = self.data[1:]

        input_data = mods.InputData()

        for row in data_values:
            data_point = mods.DataPoint()
            for header, value in zip(data_header, row):
                data_point.add(
                    mods.DataPointItem(name=header, value=value),
                    rel=mods.hasPart,
                )
            input_data.add(data_point, rel=mods.hasPart)

        self.mcdm_simulation.add(input_data)

        logger.info("Invoking the wrapper session")
        # Construct a wrapper and run a new session
        with ms.MoDS_Session() as session:
            load_dotenv()
            wrapper = cuba.wrapper(session=session)
            wrapper.add(self.mcdm_simulation, rel=cuba.relationship)
            wrapper.session.run()

            pareto_front = search.find_cuds_objects_by_oclass(
                mods.ParetoFront, wrapper, rel=None
            )

            ranking = []

            if pareto_front:
                rank = search.find_cuds_objects_by_oclass(
                    mods.RankedDataPoint, pareto_front[0], rel=None
                )
                if rank and len(rank) > 0:  # Add a check for non-empty list
                    for el in rank:
                        items = search.find_cuds_objects_by_oclass(
                            mods.DataPointItem, el, rel=mods.hasPart
                        )
                        if items and len(items) > 0:  # Add a check for non-empty item
                            for item in items:
                                if item.name == "Id":
                                    ranking.append(int(item.value.split(".")[0]))

        logger.info("################ End: MCO Calc ################")

        return ranking
