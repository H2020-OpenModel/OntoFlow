# Setup OntoFlow v2.1.0

### Install software required for running OntoFlow
The OS needs the following softwares:
- Python 3 - https://www.python.org/
- Git - https://git-scm.com/
- Docker - https://www.docker.com/products/docker-desktop/
- Graphviz (for dot) - https://graphviz.org/
- 7zip (for extracting compressed files, not always needed) - https://www.7-zip.org/

#### Commands for Fedora/Red Hat Linux
For other Linux distros should be similar
- Python 3 (should be already installed)
```
sudo dnf install python3
```
- Git
```
sudo dnf install git
```
- Docker
```
sudo dnf install dnf-plugins-core
sudo dnf config-manager --add-repo https://download.docker.com/linux/fedora/docker-ce.repo
sudo dnf install docker-ce docker-ce-cli containerd.io
sudo systemctl start docker
```
- Graphviz
```
sudo dnf install graphviz
```
- 7zip
```
sudo dnf install p7zip
```

### Setup the Jena Fuseki container
- Download [Jena Fuseki for Docker](https://repo1.maven.org/maven2/org/apache/jena/jena-fuseki-docker/5.0.0/jena-fuseki-docker-5.0.0.zip)
- Unpack and open it
- Build the Fuseki image: `docker compose build --build-arg JENA_VERSION=5.0.0`
- Create a folder for the databases, inside of it create one for the specific dataset (e.g. databases/ds)
- Make sure the dataset folder is writable by everyone
- Run the container passing the dataset as a volume: `docker run -i --rm -p 3030:3030 -v ./databases:/fuseki/databases -t fuseki --update --loc databases/ds /openmodel`
- In alternative, mostly for test purposes, run the container saving data temporarily in memory: `docker run -i --rm -p 3030:3030 -t fuseki --update --mem /openmodel`
#### Commands for Fedora/Red Hat Linux
```
curl https://repo1.maven.org/maven2/org/apache/jena/jena-fuseki-docker/5.0.0/jena-fuseki-docker-5.0.0.zip -o jena-fuseki-docker-5.0.0.zip
7z x jena-fuseki-docker-5.0.0.zip
cd jena-fuseki-docker-5.0.0
mkdir -p databases/ds
chmod 757 databases/ds
docker run -i --rm -p 3030:3030 -v ./databases:/fuseki/databases -t fuseki --update --loc databases/ds /openmodel
# docker run -i --rm -p 3030:3030 -t fuseki --update --mem /openmodel
```

### Setup of the Python Environment
- Create and use a Python Virtual Environment: `python -m venv path/to/venv`
- Activate the newly created VE: `.\venv\Scripts\activate`
- Download [OntoFlow v2.1.0](https://github.com/H2020-OpenModel/OntoFlow/tree/v2.1.0) and extract it. 

  This can be done manually, using Git (`git clone git@github.com:H2020-OpenModel/OntoFlow.git --branch v2.1.0`), or it could be installed as a Python package, but it is difficult to retrieve the examples: `pip install https://github.com/H2020-OpenModel/OntoFlow/archive/refs/tags/v2.1.0.tar.gz`.
- Enter the OntoFlow directory
- Install the package using pip: `pip install .`
- Download the (ontology)[https://raw.githubusercontent.com/EMMC-ASBL/MoDSInterface/main/ontology.mods.yml] used by the MoDS MCO
- Install it using pico: `pico install ontology.mods.yml`

#### Commands for Fedora/Red Hat Linux
```
python -m venv venv
source venv/bin/activate
git clone git@github.com:H2020-OpenModel/OntoFlow.git --branch v2.1.0
# pip install https://github.com/H2020-OpenModel/OntoFlow/archive/refs/tags/v2.1.0.tar.gz
cd OntoFlow-2.1.0
pip install .
curl https://raw.githubusercontent.com/EMMC-ASBL/MoDSInterface/main/ontology.mods.yml -o ontology.mods.yml
pico install ontology.mods.yml
```

### Run the example *openmodel_example*
- Open the directory *openmodel_example* inside of *examples*
- Check that the Fuseki container is up and running and the Python environment with OntoFLow installed is currently selected
- Run the example: `python test.py`

#### Commands for Fedora/Red Hat Linux
```
cd examples/openmodel_example
python test.py
```

## OntoFlow in Action
This section will how to set up a script to use OntoFlow properly. Similar example can be found in the examples folder.

```python
# Import all the necessary dependencies
import os
from pathlib import Path

import sys

from ontoflow.engine import OntoFlowEngine
from ontoflow.node import Node

from tripper import Triplestore

# Initialize the knowledge base
ONTOLOGIES = ["paths/to/ontologies.ttl"]
TARGET = "target_iri"
MCO = "mods"

__triplestore_url = os.getenv("TRIPLESTORE_URL", "http://localhost:3030")
ts = Triplestore(
    backend="fuseki", triplestore_url=__triplestore_url, database="openmodel"
)

ts.remove_database(
    backend="fuseki", triplestore_url=__triplestore_url, database="openmodel"
)

for ontology in ONTOLOGIES:
    ts.parse(os.path.join(Path(os.path.abspath(__file__)).parent, ontology), "turtle")


ts.bind("emmo", "https://w3id.org/emmo#")
ts.bind("ss3", "http://open-model.eu/ontologies/ss3#")

# Initialize the engine
engine = OntoFlowEngine(triplestore=ts)

KPAS = [
    {"name": "Accuracy", "weight": 3, "maximise": True},
    {"name": "SimulationTime", "weight": 2, "maximise": False},
    {"name": "OpenSource", "weight": 1, "maximise": True},
]

FOLDER = str(Path(os.path.abspath(__file__)).parent)

# Get the routes ordered according to the MCO ranking
routes = engine.getRoutes(TARGET, KPAS, MCO, FOLDER)

filtered: list["Node"] = Node.filterIncompleteRoutes(routes)

for i, route in enumerate(filtered):
    route.visualize(f"filtered_{i}", "png")
```

This script executes the engine on a custom ontology and save the results as **json**, **yaml**, and **png** files.