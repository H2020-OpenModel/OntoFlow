# Setup OntoFlow v2.0.0

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
- Run the container: `docker run -i --rm -p 3030:3030 -v ./databases:/fuseki/databases -t fuseki --update --loc databases/ds /openmodel`

#### Commands for Fedora/Red Hat Linux
```
curl https://repo1.maven.org/maven2/org/apache/jena/jena-fuseki-docker/5.0.0/jena-fuseki-docker-5.0.0.zip -o jena-fuseki-docker-5.0.0.zip
7z x jena-fuseki-docker-5.0.0.zip
cd jena-fuseki-docker-5.0.0
mkdir -p databases/ds
chmod 757 databases/ds
podman run -i --rm -p 3030:3030 -v ./databases:/fuseki/databases -t fuseki --update --loc databases/ds /openmodel
```

### Setup of the Python Environment
- Create and use a Python Virtual Environment: `python -m venv path/to/venv`
- Activate the newly created VE: `.\venv\Scripts\activate`
- Download [OntoFlow v2.0.0](https://github.com/H2020-OpenModel/OntoFlow/tree/v2.0.0) and extract it. 

  This can be done manually, using Git (`git clone git@github.com:H2020-OpenModel/OntoFlow.git --branch v2.0.0`), or it could be installed as a Python package, but it is difficult to retrieve the examples: `pip install https://github.com/H2020-OpenModel/OntoFlow/archive/refs/tags/v2.0.0.tar.gz`.
- Enter the OntoFlow directory
- Install the package using pip: `pip install .`
- Download the (ontology)[https://raw.githubusercontent.com/EMMC-ASBL/MoDSInterface/dev-add-mcdm-algorithm-type/ontology.mods.yml] used by the MoDS MCO
- Install it using pico: `pico install ontology.mods.yml`

#### Commands for Fedora/Red Hat Linux
```
python -m venv venv
source venv/bin/activate
git clone git@github.com:H2020-OpenModel/OntoFlow.git --branch v2.0.0
# pip install https://github.com/H2020-OpenModel/OntoFlow/archive/refs/tags/v2.0.0.tar.gz
cd OntoFlow-2.0.0
pip install .
curl https://raw.githubusercontent.com/EMMC-ASBL/MoDSInterface/dev-add-mcdm-algorithm-type/ontology.mods.yml -o ontology.mods.yml
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

### N.B. At the moment only the openmodel_example works properly, a new version of OntoFlow will be releasesd when the SS3 example is ready. Meanwhile, for testing purposes only, the most updated branch is *test/ss3-run `git clone git@github.com:H2020-OpenModel/OntoFlow.git --branch test/ss3-run`


## OntoFlow in Action
This section will how to set up a script to use OntoFlow properly. Similar example can be found in the examples folder.

```python
# Import all the necessary dependencies
import os
from ontoflow.engine import OntoFlowEngine
from tripper import Triplestore

# Create an istance of Triplestore which will connect to your local Fuseki instance
__triplestore_url = os.getenv("TRIPLESTORE_URL", "http://localhost:3030")
ts = Triplestore(
    backend="fuseki", triplestore_url=__triplestore_url, database="openmodel"
)

# Clean the triplestore
ts.remove_database(
    backend="fuseki", triplestore_url=__triplestore_url, database="openmodel"
)

# Add your ontology to the triplestore
ONTOLOGY_PATH = "path/to/your/ontology.ttl"
ts.parse(ONTOLOGY_PATH, "turtle")

# Bind optional namespaces to the triplestore
ts.bind("webp", "http://webprotege.stanford.edu/")

# Initialize the engine
engine = OntoFlowEngine(triplestore=ts)

# Define the KPAs
kpis = [
    {"name": "Accuracy", "weight": 3, "maximise": True},
    {"name": "SimulationTime", "weight": 1, "maximise": False},
    {"name": "OpenSource", "weight": 5, "maximise": False},
]

# Execute the search
bestRoute = engine.getBestRoute(
    ROOT, kpis, MCO, str(Path(os.path.abspath(__file__)).parent)
)

# Export the results
bestRoute.export(os.path.join(Path(os.path.abspath(__file__)).parent, "best"))
bestRoute.visualize(output=os.path.join(Path(os.path.abspath(__file__)).parent, "best"))
```

This script executes the engine on a custom ontology and save the results as **json**, **yaml**, and **png** files.