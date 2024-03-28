import logging
from dotenv import load_dotenv

import osp.core.utils.simple_search as search

from osp.core.namespaces import mods, cuba
from osp.core.utils import pretty_print
from osp.wrappers.sim_cmcl_mods_wrapper import mods_session as ms

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)
logger.addHandler(logging.StreamHandler())
logger.handlers[0].setFormatter(
    logging.Formatter("%(levelname)s %(asctime)s [%(name)s]: %(message)s")
)


def mco_calc(data):
    logger.info("################ Start: MCO Calc ################")
    logger.info("Setting up the simulation inputs")

    mcdm_simulation = mods.MultiCriteriaDecisionMaking()
    mcdm_algorithm = mods.Algorithm(name="algorithm1", type="MCDM")

    mcdm_algorithm.add(
        # A value uniquely identifying the model (curretnly must be numerical)
        mods.Variable(name="Id", type="input"),
        # Optional (e.g. step size) can have multiple of these
        mods.Variable(name="ModelParameter", type="input"),
        # First cost of model (e.g. time)
        mods.Variable(
            name="Cost1",
            type="output",
            objective="Minimise",
            maximum="35.0",
            weight="1",
        ),
        # Second cost of model (e.g. uncertainty of final result)
        mods.Variable(
            name="Cost2",
            type="output",
            objective="Minimise",
            maximum="35.0",
            weight="3",
        ),
    )

    mcdm_simulation.add(mcdm_algorithm)

    # data = [
    #     ["Id", "ModelParameter", "Cost1", "Cost2"],
    #     [1.0, 0.2, 20.0, 0.001],
    #     [2.0, 0.4, 17.0, 0.003],
    #     [3.0, 0.6, 16.0, 0.03],
    #     [4.0, 0.8, 10.0, 0.09],
    #     [5.0, 1.0, 5.0, 0.1],
    # ]

    data_header = data[0]
    data_values = data[1:]

    input_data = mods.InputData()

    for row in data_values:
        data_point = mods.DataPoint()
        for header, value in zip(data_header, row):
            data_point.add(
                mods.DataPointItem(name=header, value=value),
                rel=mods.hasPart,
            )
        input_data.add(data_point, rel=mods.hasPart)

    mcdm_simulation.add(input_data)

    logger.info("Invoking the wrapper session")
    # Construct a wrapper and run a new session
    with ms.MoDS_Session() as session:
        load_dotenv()
        wrapper = cuba.wrapper(session=session)
        wrapper.add(mcdm_simulation, rel=cuba.relationship)
        wrapper.session.run()

        pareto_front = search.find_cuds_objects_by_oclass(
            mods.ParetoFront, wrapper, rel=None
        )

        ranking = []

        if pareto_front:
            pretty_print(pareto_front[0])
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
