"""
Simple demo
===========
This demo shows the following steps:
- use oteapi-asmod to load an atomistic structure (a C3H6 molecule)
- use ase to calculate the energy and the forces on each atom
- describe the structure and results as instances of two data models
  (ASEAtoms and CalcResults)
- populate an minimal triplestore with mappings
- instantiate a Molecule datamodel via ontological mappings from the
  existing data

Steps to install the requirements (preferrably in a virtual environment):

```shell
git clone git@github.com:EMMC-ASBL/oteapi-asmod.git
cd oteapi-asmod
pip install -U -e .
pip install oteapi-dlite
```

Run the demo:

```shell
python simple.py
```

"""
import sys
sys.path.append("C:\\Users\\alexc\\Desktop\\Universita\\Ricerca\\OpenModel\\OntoFlow")
print(sys.path)

from pathlib import Path

import ase
import dlite
import numpy as np
import pint
from ase.calculators.emt import EMT
from ase.symbols import Symbols, symbols2numbers
from tripper import DM, EMMO, Triplestore, Literal
from tripper.mappings import MappingStep, Value, mapping_routes
from oteapi.datacache import DataCache
from oteapi.models.resourceconfig import ResourceConfig
from oteapi.plugins import load_strategies
from oteapi_asmod.strategies.parse import AtomisticStructureParseStrategy
from ontoflow.engine import OntoFlowDMEngine
from mco_strategies.minimumCostStrategy import MinimumCostStrategy


thisdir = Path(__file__).absolute().parent
datadir = thisdir / "data"
entitydir = thisdir / "entities"

load_strategies()


# Load atoms object with oteapi
# -----------------------------
structure = "C3H6"
print((datadir / f"{structure}.xyz").as_uri())
print((datadir / f"{structure}.xyz"))
config = ResourceConfig(
    downloadUrl=(datadir / f"{structure}.xyz").as_uri(),
    mediaType="chemical/x-xyz",
)

cache = DataCache()
parser = AtomisticStructureParseStrategy(config)
parser.initialize()

key = parser.get().cached_atoms_key
atoms = cache.get(key)  # ase.Atoms object
# print(atoms)

# Convert the atoms object to a DLite instance
# --------------------------------------------

# Add entity definitions to the metadata search path - not nessesary when we
# get a proper centralised entity storage
dlite.storage_path.append(f"{entitydir}/*.json")

# Use dlite.objectfactory to do the conversion
# Consider to add a convenient function for this to dlite.factory
ASEAtoms = dlite.get_instance("http://onto-ns.com/meta/0.1/ASEAtoms")
aseatoms = dlite.objectfactory(atoms, meta=ASEAtoms)
inst = aseatoms.dlite_inst
# print(ASEAtoms)
# print(aseatoms)
# print(inst)


# Perform calculation
# -------------------

# First, recreate an ase.Atoms object from the DLite instance
at = ase.Atoms(**inst.properties)

# Assign simple EMT calculator
at.calc = EMT()

# Create result instance, perform calculation and populate result instance
Result = dlite.get_instance("http://onto-ns.com/meta/0.1/CalcResults")
result = Result(inst.dimensions)
result.potential_energy = at.get_potential_energy()  # Trigger simulation
result.forces = at.get_forces()

# print(at)
# print(Result)
# print(result)


# Instantiate new entity via ontological mappings
# -----------------------------------------------
# Lets assume that we need a Molecule instance for the next simulation.
# We instantiate this instance from existing data via ontological mappings.


# Register missing units
#
# Right now we are using pint, but the ambition is to either add
# functionality for populating an empty pint unit registry from
# e.g. QUDT, implement our own ontology-driven Quantity class with the
# same functionality as pint.Quantity.
#
# A nice thing about pint.Quantity is that it handles both units and
# shapes a simple and transparent way (supporting all standard mathematical
# operations as well as numpy ufuncs).
ureg = pint.UnitRegistry()
ureg.define("Angstrom  = 1e-10 * m")


Molecule = dlite.get_instance("http://onto-ns.com/meta/0.1/Molecule")


def get_formula(symbols):
    """Convert a list of atomic symbols to a chemical formula."""
    # Note that `symbols` is a Quantity object.  Use `symbols.m` to
    # get only the magnitude without unit.
    s = Symbols(symbols2numbers(symbols.m))
    return s.get_chemical_formula()


def get_maxforce(forces):
    """Returns the magnitude of the largest force in forces."""
    # Note that `forces` is a Quantity object.  The returned value
    # will also be a Quantity object with the same unit.  Hence, the
    # unit is always handled explicitly.  This makes it possible for
    # conversion function to change unit as well.
    return np.sqrt(np.sum(forces**2, axis=1).max())


# ts = Triplestore(backend="rdflib")
Triplestore.remove_database(backend="stardog", database="ontoflow", base_iri="http://localhost:5820")
Triplestore.create_database(backend="stardog", database="ontoflow", base_iri="http://localhost:5820")

ts = Triplestore(backend="stardog", base_iri="http://localhost:5820", database="ontoflow")
# ts = Triplestore(name="rdflib", base_iri="http://example.com/demo-ontology#")
DON = ts.bind("don", "http://example.com/demo-ontology#")
ASE = ts.bind("ase", "http://onto-ns.com/meta/0.1/ASEAtoms#")


# Add mappings

# Add mappings
func1_iri = ts.add_function(
    get_formula,
    expects=[DON.Symbols],
    returns=[DON.Formula],
)
ts.add_function(
    get_maxforce,
    expects=[EMMO.Force],
    returns=[DON.MaxForce],
)
ts.add_mapsTo(EMMO.PotentialEnergy, Result, "potential_energy")
ts.add_mapsTo(EMMO.PotentialEnergy, Molecule, "energy")
ts.add_mapsTo(DON.Symbols, ASEAtoms, "symbols")
ts.add_mapsTo(DON.Formula, Molecule, "formula")
ts.add_mapsTo(EMMO.Force, Result, "forces")
ts.add_mapsTo(DON.MaxForce, Molecule, "maxforce")
ts.add([ASE.symbols, DON.hasReference, "http://aseatomdb.com/data/aseatom.json"])
ts.add([DON.Formula, DON.hasAccuracy, DON.Low])
ts.add([DON.Formula, DON.hasComputationalEffort, DON.Low])
# ts.add([DON.Symbols, DM.hasCost, "\"15\""])
print(ts.serialize())

## Add second route
def get_formula_complex(symbols):
    """Convert a list of atomic symbols to a chemical formula."""
    # Note that `symbols` is a Quantity object.  Use `symbols.m` to
    # get only the magnitude without unit.
    s = Symbols(symbols2numbers(symbols.m))
    return s.get_chemical_formula()

func2_iri = ts.add_function(
    get_formula_complex,
    expects=[DON.SymbolsComplex],
    returns=[DON.Formula_Complex],
)
ts.add_mapsTo(DON.Formula_Complex, Molecule, "formula")
ts.add_mapsTo(DON.SymbolsComplex, ASEAtoms, "symbols")
ts.add([DON.Formula_Complex, DON.hasAccuracy, DON.High])
ts.add([DON.Formula_Complex, DON.hasComputationalEffort, DON.High])

mco_strategy = MinimumCostStrategy()

engine = OntoFlowDMEngine(triplestore = ts, cost_file = r"C:\Users\alexc\Desktop\Universita\Ricerca\OpenModel\OntoFlow\examples\datamodel_generation\cost_definitions.yaml", mco_interface = mco_strategy)

molecule_routes = engine.getmappingroute(
    meta=Molecule,
    instances=[inst, result],  # Available data
    quantity=ureg.Quantity,  # Quantity class with our extended unit registry
)

print("-----------ROUTES--------------")
print(molecule_routes)
print("-------------------------")
print("-------------FORMULA------------")
print(molecule_routes["formula"].show())
print("-------------------------")
print(molecule_routes["formula"].get_workflow_yaml(0))
# # print(molecule_routes["formula"].visualise(0))


# import copy
# print("-------------------------")
# print("-------------------------")
# print(molecule_routes["formula"].show())
# print("-------------------------")
# el = copy.copy(molecule_routes["formula"])
# el.input_routes = []
# print(el.show())