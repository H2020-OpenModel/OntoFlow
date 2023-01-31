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

from pathlib import Path

import ase
import dlite
import numpy as np
import pint
from ase.calculators.emt import EMT
from ase.symbols import Symbols, symbols2numbers
from tripper import DM, EMMO, Triplestore
from oteapi.datacache import DataCache
from oteapi.models.resourceconfig import ResourceConfig
from oteapi.plugins import load_strategies
from oteapi_asmod.strategies.parse import AtomisticStructureParseStrategy
from ontoflow.engine_old import OntoFlowDMEngine


ts = Triplestore(backend="stardog", base_iri="http://localhost:5820", database="ontoflow")
engine = OntoFlowDMEngine(triplestore = ts, cost_file = r"C:\Users\alexc\Desktop\Universita\Ricerca\OpenModel\OntoFlow\examples\datamodel_generation\cost_definitions.yaml", mco_interface = "")
