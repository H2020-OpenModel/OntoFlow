import os
from importlib import import_module
from pkgutil import iter_modules

from ontoflow.node import Node


class Mco:
    def __init__(self) -> None:
        pass

    def mco_calc(self) -> list[int]:
        return []


def mco_ranking(engine: str, kpas: list[dict], node: Node) -> list[int]:
    """Factory method for creating an MCO and getting the ranking of the routes.

    Args:
        engine (str): The engine to use for the MCO.
        kpas (list[dict]): The KPAs to be used for the MCO.
        node (Node): The node to be used for the MCO.

    Returns:
        list[int]: The ranking of the routes.
    """

    mcos_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mcos")

    # Load all modules in the ontoflow.mcos package
    mco_modules = {
        name: import_module(f"ontoflow.mcos.{name}")
        for _, name, _ in iter_modules(path=[mcos_dir])
    }

    # Check if the engine exists in the loaded modules
    mco_engine = mco_modules.get(engine)

    if mco_engine is not None:
        return getattr(mco_engine, engine.capitalize())(kpas, node).mco_calc()
    else:
        raise ValueError(f"Unknown MCO engine: {engine}")
