---
title: Home
layout: home
---

OntoFlow is an enhanced workflow designer and builder, responsible for storing and managing the semantic representation of the elements of interest for the individual use cases and for using decision-making and MCO techniques to choose the most suitable workflow among the possible ones.

Delving more into details, OntoFlow is made up of two different subcomponents: OntoFlowKB and OntoFlowDM
* OntoFlowKB is a triplestore-based component that stores and manages workflow-related ontological concepts and application specific ones. It also enables querying capabilities with respect to the execution of queries. The current implementation relies on the Stardog technology.

* OntoFlowDM is the decision-making engine for the OntoFlow architecture. Its main task consists in suggesting the best ontological route that can obtain the desired target and, at the same time, optimize the interested criteria. It:

    1. Retrives all the semantic data contained in the triplestore.
    2. Runs the search algorithm to navigate the ontologies and find all the possible routes producing the targeted output.
    3. Finds the best route according to predefined criteria.

The output of OntoFlow is the ontological description of a workflow that describes, as a set of concepts and relationships between them, the final process by which the output can be derived from the available ontology. 

---