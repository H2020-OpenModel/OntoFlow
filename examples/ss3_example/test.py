import os
from OpenModel.PyBackTrip.pybacktrip.backends.fuseki import FusekiStrategy

# podman run -i --rm -p 3030:3030 -v databases:/fuseki/databases -t fuseki --update --loc databases/openmodel /openmodel

TRIPLESTORE_HOST = "localhost"
TRIPLESTORE_PORT = 3030
DATABASE = "openmodel"
GRAPH = "graph://main"
PATH = os.path.abspath("openmodel_example.ttl")

triplestore: FusekiStrategy = FusekiStrategy(
    base_iri="http://webprotege.stanford.edu/",
    triplestore_url=f"http://{TRIPLESTORE_HOST}:{TRIPLESTORE_PORT}",
    database="openmodel",
)

triplestore.parse(location=PATH)
