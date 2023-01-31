"""Test mapping routes."""
# pylint: disable=invalid-name
from tripper import EMMO, Triplestore
from tripper.mappings import mapping_routes

# Prepare triplestore
ts = Triplestore(backend="rdflib")

# Namespace for domain ontology
DO = ts.bind("do", "http://example.com/do#")

# Namespace for individuals standing for actual data
DATA = ts.bind("data", "http://example.com/data#")

# Namespace for registered models
MOD = ts.bind("mod", "http://example.com/models#")


def model1(position):  # XXX - just testing
    """A simple model."""
    # pylint: disable=unused-argument
    return 1  # J


def cost2(ts, input_iris, output_iri):
    """Custom cost function."""
    # pylint: disable=unused-argument
    return 5.0


ts.add_mapsTo(EMMO.Position, DATA.pos1)
ts.add_mapsTo(EMMO.Position, DATA.pos2)
ts.add_mapsTo(EMMO.Energy, DATA.energy1)
ts.add_mapsTo(DO.Efficiency, DATA.efficiency1)
fun1 = ts.add_function(
    model1,  # MOD.model1
    expects=[EMMO.Position],
    returns=[EMMO.Energy],
    cost=3.0,
)
fun2 = ts.add_function(
    MOD.model2,
    expects=[EMMO.Energy],
    returns=[DO.Efficiency],
    cost=cost2,
)

routes = mapping_routes(
    target=DATA.efficiency1,
    # TODO: make sources a sequence - put mappings to actual data in the
    # triplestore
    sources={DATA.pos1: None, DATA.pos2: None, DATA.energy1: None},
    triplestore=ts,
)


assert routes.number_of_routes() == 3
assert routes.output_iri == DATA.efficiency1
for n in range(3):
    assert routes.get_input_iris(n) == {"arg1": DO.Efficiency}
assert routes.lowest_costs() == [(13.0, 0), (20.0, 1), (20.0, 2)]
