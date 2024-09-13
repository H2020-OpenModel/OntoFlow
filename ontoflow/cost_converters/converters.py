from tripper import Triplestore


def init_converter_triplestore(ts: Triplestore):
    kpa_ns = ts.namespaces["kpa"]
    ts.add_function(
        ordinalaccuracy_converter,
        expects=kpa_ns.OrdinalAccuracy,
        returns=kpa_ns.NumericalAccuracy,
        standard="emmo",
    )
    ts.add_function(
        mirror_converter,
        expects=kpa_ns.NumericalAccuracy,
        returns=kpa_ns.NumericalAccuracy,
        standard="emmo",
    )
    ts.add_function(
        mirror_converter,
        expects=kpa_ns.NumericalSimulationTime,
        returns=kpa_ns.NumericalSimulationTime,
        standard="emmo",
    )
    ts.add_function(
        mirror_converter,
        expects=kpa_ns.NormalizedSimulationTime,
        returns=kpa_ns.NormalizedSimulationTime,
        standard="emmo",
    )
    ts.add_function(
        mirror_converter,
        expects=kpa_ns.SystemSize,
        returns=kpa_ns.SystemSize,
        standard="emmo",
    )
    ts.add_function(
        boolopensource_converter,
        expects=kpa_ns.BoolOpenSource,
        returns=kpa_ns.NumericalOpenSource,
        standard="emmo",
    )


## Mirror converters for NumericalKPAs
def mirror_converter(value):
    return float(value)


## Accuracy Converters
def ordinalaccuracy_converter(accuracy):
    if accuracy.lower() == "high":
        return 50
    elif accuracy.lower() == "medium":
        return 25
    elif accuracy.lower() == "low":
        return 5
    else:
        return 0


## OpenSource Converters
def boolopensource_converter(opensource_value):
    if opensource_value.lower() == "true":
        return 1
    else:
        return 0
