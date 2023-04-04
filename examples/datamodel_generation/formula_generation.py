import sys
sys.path.append("C:\\Users\\alexc\\Desktop\\Universita\\Ricerca\\OpenModel\\OntoFlow")
print(sys.path)

from pathlib import Path

import ase
import dlite
import pint
from ase.calculators.emt import EMT
from ase.symbols import Symbols, symbols2numbers
from tripper import DM, EMMO, Triplestore
from oteapi.datacache import DataCache
from oteapi.models.resourceconfig import ResourceConfig
from oteapi.plugins import load_strategies
from oteapi_asmod.strategies.parse import AtomisticStructureParseStrategy
from ontoflow.engine import OntoFlowDMEngine
from ontoflow.mco_strategies.minimumCostStrategy import MinimumCostStrategy


#################################### EXAMPLE ######################################
# This example showcase a practical usage of OntoFlow with respect to a concrete scenario.
# The use-case regards the automatic generation of datamodels starting from data already present
# in the ontology. In particular the aim of this script is to istantiate the formula propriety
# of the Molecule datamodel. To achieve this, several steps are required:

# 1. Popolate the triplestore knowledge with the user-case-specifc ontological concepts
# 2. Configure the OntoFlow engine
# 3. Generate the YAML file with the declarative workflow
###################################################################################

################# FORMULA CONVERSION ####################
#
#    CCCHHHHHH -> C3H6
#
#########################################################

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

# Convert the atoms object to a DLite instance
# --------------------------------------------

# Add entity definitions to the metadata search path - not nessesary when we
# get a proper centralised entity storage
dlite.storage_path.append(f"{entitydir}/*.json")

# Use dlite.objectfactory to do the conversion
# Consider to add a convenient function for this to dlite.factory

ASEAtoms = dlite.get_instance("http://onto-ns.com/meta/0.1/ASEAtoms")
print(atoms)
print(ASEAtoms)
aseatoms = dlite.objectfactory(atoms, meta=ASEAtoms)
inst = aseatoms.dlite_inst

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


# Register missing units
ureg = pint.UnitRegistry()
ureg.define("Angstrom  = 1e-10 * m")


# Input
ASEAtoms = dlite.get_instance("http://onto-ns.com/meta/0.1/ASEAtoms")

# Reference to the target datamodel
Molecule = dlite.get_instance("http://onto-ns.com/meta/0.1/Molecule")

# Initialization of triplestore

Triplestore.remove_database(backend="stardog", database="ontoflow", base_iri="http://localhost:5820")
Triplestore.create_database(backend="stardog", database="ontoflow", base_iri="http://localhost:5820")
ts = Triplestore(backend="stardog", base_iri="http://localhost:5820", database="ontoflow")

# Namespace binding
DON = ts.bind("don", "http://example.com/demo-ontology#")
ASE = ts.bind("ase", "http://onto-ns.com/meta/0.1/ASEAtoms#")


# Add mappings
# Add "simple" function
def get_formula(symbols):
    """Convert a list of atomic symbols to a chemical formula."""
    s = Symbols(symbols2numbers(symbols.m))
    return s.get_chemical_formula()

func1_iri = ts.add_function(
    get_formula,
    expects=[DON.Symbols],
    returns=[DON.Formula],
)

ts.add([DON.Formula, DON.hasAccuracy, DON.Low])
ts.add([DON.Formula, DON.hasComputationalEffort, DON.Low])

# Add more "complex" function
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

ts.add([DON.Formula_Complex, DON.hasAccuracy, DON.High])
ts.add([DON.Formula_Complex, DON.hasComputationalEffort, DON.High])

# Add mappings
ts.add_mapsTo(DON.Symbols, ASEAtoms, "symbols")
ts.add_mapsTo(DON.Formula, Molecule, "formula")
ts.add_mapsTo(DON.Formula_Complex, Molecule, "formula")
ts.add_mapsTo(DON.SymbolsComplex, ASEAtoms, "symbols")

ts.add([ASE.symbols, DON.hasReference, "http://aseatomdb.com/data/aseatom.json"])


# Configuration of the engine
mco_strategy = MinimumCostStrategy()

engine = OntoFlowDMEngine(triplestore = ts, cost_file = r"C:\Users\alexc\Desktop\Universita\Ricerca\OpenModel\OntoFlow\examples\datamodel_generation\cost_definitions.yaml", mco_interface = mco_strategy)

# Run the engine
molecule_routes = engine.getmappingroute(
    meta=Molecule,
    instances=[inst],
    quantity=ureg.Quantity,
    allow_incomplete = True
)


# Show the results
print("-------------FORMULA ROUTE------------")
print(molecule_routes["formula"].show())
print("------------YAML WORKFLOW-------------")
print(molecule_routes["formula"].get_workflow_yaml(0))