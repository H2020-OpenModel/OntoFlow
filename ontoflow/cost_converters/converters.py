from tripper import Triplestore


def init_converter_triplestore(ts: Triplestore):
    kpa_ns = ts.namespaces["kpa"]
    ts.add_function(ordinalaccuracy_converter, expects=kpa_ns.OrdinalAccuracy, returns=kpa_ns.NumericalAccuracy, standard="emmo")
    ts.add_function(mirror_converter, expects=kpa_ns.NumericalAccuracy, returns=kpa_ns.NumericalAccuracy, standard="emmo")
    ts.add_function(mirror_converter, expects=kpa_ns.NumericalSimulationTime, returns=kpa_ns.NumericalSimulationTime, standard="emmo")


## Mirror converters for NumericalKPAs
def mirror_converter(value):
    return int(value)

## Accuracy Converters
def ordinalaccuracy_converter(accuracy):
    if accuracy == "High":
        return 50
    elif accuracy == "Medium":
        return 25
    elif accuracy == "Low":
        return 5
    else:
        return 0