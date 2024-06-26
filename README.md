# OntoFlow
*An enhanced workflow designer and builder for the [OpenModel](https://github.com/H2020-OpenModel/) project*

## Architecture
---
<p align="center">
<img src="docs/images/OntoFlowHighLevel.jpg" alt="OIP High Level Architecture" width="600">
</p>

In the high-level overview of the OIP, OntoFlow is the first key component to come into play and, through its two submodules OntoFlowKB and OntoFlowDM, is responsible for storing and managing the semantic representation of the elements of interest for the individual use cases and for using decision-making and MCO techniques to choose the most suitable workflow among the possible ones.

<p align="center">
<img src="docs/images/OntoFlowArchitecture.jpg" alt="OntoFlow High Level Architecture" width="300">
</p>

**OntoFlowKB** is a triplestore-based component that stores and manages workflow-related ontological concepts and application specific ones. It also enables querying capabilities with respect to the execution of queries. The current implementation relies on the Stardog technology.

**OntoFlowDM**  is the decision-making engine for the OntoFlow architecture. Its main task consists in suggesting the best ontological route that can obtain the desired target and, at the same time, optimize the interested criteria. It:
1. Retrives all the semantic data contained in the triplestore.
2. Runs the search algorithm to navigate the ontologies and find all the possible routes producing the targeted output.
3.	Finds the best route according to predefined criteria.

The output of OntoFlow is the ontological description of a workflow that describes, as a set of concepts and relationships between them, the final process by which the output can be derived from the available ontology. This description, being ontologically defined, contains no information either about the actual data to be used or about how to perform the various functions.

## How to install
---
OntoFlow can be installed as a Python package inside your own environment. Since there is no deployment on the PyPi platform, you have too directly install it from this repository

```
pip install .
```

or add it as dependency

```
git+https://github.com/H2020-OpenModel/OntoFlow@<commit code>
```

or install it with pip

```
pip install git+https://github.com/H2020-OpenModel/OntoFlow
```

To install a given release, commit or branch, you can addit to the end of the URL preceeded by an "@"-sign. For example: `pip install git+https://github.com/H2020-OpenModel/OntoFlow@<commit code>`.


## Tests
---
To test the proper functioning of OntoFlow, there are a number of tests that can be performed. You need to install all the proper dependencies

```
pip install '.[tests]'
```

Tests can be found in the test folder. To run them, you can use the following command

```
python -m unittest tests/*.py
```

By default the triplestore url is set to the http://localhost:3030 endpoint for local testing. If you want to change it, you can set the `TRIPLESTORE_URL` environment variable to the desired endpoint.

```
TRIPLESTORE_URL=<triplestore url> python -m unittest tests/*.py
```



## Examples
---
OntoFlow comes with some examples to test its functionality and see how it works. To be able to use them install its complete version

```
pip install '.[examples]'
```

By default the triplestore url is set to the http://localhost:3030 endpoint for local testing. If you want to change it, you can set the `TRIPLESTORE_URL` environment variable to the desired endpoint.

Examples can be found in the `examples` folder. For the moment, please, refer only to the [ss3](https://github.com/H2020-OpenModel/OntoFlow/blob/main/examples/ss3_example/test.py) and the [openmodel_example](https://github.com/H2020-OpenModel/OntoFlow/blob/main/examples/openmodel_example/test.py) examples.
