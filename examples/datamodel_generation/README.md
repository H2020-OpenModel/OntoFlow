# DataModel Generation
This examples showcases a concrete application of OntoFlow regarding the automatic generation of datamodels starting from information already present in the platform.

In particular, the scenario involves two different datamodels: ASEAtoms and CalcResult. ASEAtoms contains information about the atoms in a molecule, their element, position and symbols, while CalcResult contains information about the calculated properties of a molecule, such as its energy and maximum force. The scenario also assume the existence of two different instances of these models that constitutes the input data for the example. On the other hand, the Molecule datamodel, which has the fields formula, energy and maxforce, represents the final output and the schema of the final instance that we want to generate.

## How to run
Install OntoFlow according to the instruction contained into the [Main Page](../../README.md).

Execute the code

```
python formula_generation.py
```