"""Implements mappings between entities.

Units are currently handled with pint.Quantity.  The benefit of this
compared to explicit unit conversions, is that units will be handled
transparently by mapping functions, without any need to specify units
of input and output parameters.

Shapes are automatically handled by expressing non-scalar quantities
with numpy.

"""
from __future__ import annotations

from enum import Enum

import dlite
import yaml
from pint import Quantity
from tripper import DM, EMMO,  FNO, MAP, RDF, RDFS
from tripper.mappings import MappingStep, Value, mapping_routes as tripper_mapping_routes


class MappingError(Exception):
    """Base class for mapping errors."""

class InsufficientMappingError(MappingError):
    """There are properties or dimensions that are not mapped."""

class MissingRelationError(MappingError):
    """There are missing relations in RDF triples."""



class StepType(Enum):
    """Type of mapping step when going from the output to the inputs."""
    UNSPECIFIED = 0
    MAPSTO = 1
    INV_MAPSTO = -1
    INSTANCEOF = 2
    INV_INSTANCEOF = -2
    SUBCLASSOF = 3
    INV_SUBCLASSOF = -3
    FUNCTION = 4


class OntoFlowEngineMappingStep(MappingStep):

    
    def adjust_cost(self, predicate_dict, costs):
        
        total_cost = 0
        for cost_definition_key in predicate_dict.keys():
            cost_definition = predicate_dict[cost_definition_key]
            if self.output_iri in cost_definition:
                # find the cost_defintion
                cost_el = next(iter({key: value for key, value in costs.items() if value.get('namespace') == cost_definition_key}.values()))
                if isinstance(cost_el.get("cost"), float):
                    #unique cost
                    total_cost =  total_cost + float(cost_el.get("cost"))
                else:
                    #value-dependent cost
                    total_cost =  total_cost + float(cost_el.get("cost")[cost_definition[self.output_iri]])

        self.cost = self.cost + total_cost

        for input in self.input_routes:
           list(input.values())[0].adjust_cost(predicate_dict, costs)


    def _to_yaml(self, routeno: int, next_iri: str, next_steptype: StepType) -> list:

        hasOutput = EMMO.EMMO_c4bace1d_4db0_4cd3_87e9_18122bae2840

        inputs, idx = self.get_inputs(routeno)
        execution_flow = []
        current_ctx = []
        for _, input in inputs.items():
            if isinstance(input, OntoFlowEngineValue):
                collection_label = input.output_iri.split("#")[1].lower()
                input_entry = {}
                input_entry["workflow"] = "execflow.pipeline"
                input_entry["inputs"] = {}
                input_entry["inputs"]["pipeline"] = "file://random/path/pipeline_for_{}.yaml".format(collection_label)  # Generate random reference
                input_entry["inputs"]["run_pipleline"] = "get_{}".format(collection_label)  # Generate random pipeline name

                ctx_element = {}
                ctx_element["label"] = collection_label

                execution_flow.append(input_entry)
                current_ctx.append(ctx_element)
                
            elif isinstance(input, OntoFlowEngineMappingStep):
                execution_flow = input._to_yaml(  # pylint: disable=protected-access
                    routeno=idx,
                    next_iri=self.output_iri,
                    next_steptype=self.steptype,
                )
                
            else:
                raise TypeError("input should be Value or MappingStep")
       
        if next_iri:
            if next_steptype.name == StepType.FUNCTION.name and self.triplestore:
                model_iri = self.triplestore.value(
                    predicate=hasOutput,  # Assuming EMMO
                    object=next_iri,
                    default="function",
                    any=True,
                )
                if model_iri:
                    label = self.triplestore.value(
                        subject=model_iri,
                        predicate=RDFS.label,
                        default=self._iri(model_iri),
                        any=True,
                    )
                function_entry = {}
                function_entry["calcjob"] = "openmodel.{}".format(label)
                function_entry["inputs"] = {}
                n = 1
                for input in current_ctx:
                    function_entry["inputs"]["input{}".format(n)] = "{{ get_dlite_istance_by_label(\"{}\") }}".format(input["label"])    
                    n = n + 1
                function_entry["postprocess"] = ["{{ ctx.current.outputs[\"output_data\"] | to_ctx(\"{}_output\") }}".format(label)]

                execution_flow.append(function_entry)

        else:
            # Final step
            collection_label = input.output_iri.split("#")[1].lower()
            input_entry = {}
            input_entry["workflow"] = "execflow.pipeline"
            input_entry["inputs"] = {}
            input_entry["inputs"]["pipeline"] = "file://random/path/pipeline_for_{}_output.yaml".format(collection_label)  # Generate random reference
            input_entry["inputs"]["run_pipleline"] = "get_{}_output".format(collection_label)  # Generate random pipeline name

            execution_flow.append(input_entry)

        return execution_flow
    

    def get_workflow_yaml(self, routeno: int) -> str:
        workflow_yaml = {}
        workflow_yaml["steps"] = self._to_yaml(routeno, "", StepType.UNSPECIFIED)
    
        return yaml.dump(workflow_yaml)



class OntoFlowEngineValue(Value):

    def adjust_cost(self, predicate_dict, costs):
         
        total_cost = 0
        for cost_definition_key in predicate_dict.keys():
            cost_definition = predicate_dict[cost_definition_key]
            if self.output_iri in cost_definition:
                # find the cost_defintion
                print({key: value for key, value in costs.items() if value.get('namespace') == cost_definition_key})
                cost_el = next(iter({key: value for key, value in costs.items() if value.get('namespace') == cost_definition_key}.values()))
                if isinstance(cost_el.get("cost"), float):
                    #unique cost
                    total_cost =  total_cost + float(cost_el.get("cost"))
                else:
                    #value-dependent cost
                    total_cost =  total_cost + float(cost_el.get("cost")[cost_definition[self.output_iri]])

        self.cost = self.cost + total_cost



class OntoFlowDMEngine():

    def __init__(self, triplestore, cost_file, mco_interface):
        self.triplestore = triplestore

        # Parse YAML
        cost_file = cost_file
        yaml_parsed = None
        with open(cost_file, "r") as file:
            try:
                yaml_parsed = yaml.safe_load(file)["function_costs"]["predicate"]
                print(yaml_parsed)
            except yaml.YAMLError as exc:
                print(exc)

        self.__validate_yaml(yaml_parsed)

        # MCO
        self.mco_interface = mco_interface


    def __validate_yaml(self, content):

        costs = {}
        for predicate in content:
            predicate_keys = list(predicate.keys())
            predicate_name = predicate_keys[0]

            if "namespace" not in predicate_keys:
                raise Exception("Namespace not defined")
            
            if (predicate["self-contained"] and "cost" not in predicate_keys) or (not predicate["self-contained"] and "values" not in predicate_keys) :
                raise Exception("Cost value not present")
            
            predicate_data = {}
            predicate_data["namespace"] = predicate["namespace"]

            if predicate["self-contained"]:
                predicate_data["cost"] = float(predicate["cost"])
            else:
                specific_costs = {}
                for value in predicate["values"]:
                    specific_costs[value["value"]] = value["cost"]

                predicate_data["cost"] = specific_costs

            costs[predicate_name] = predicate_data

        costs["value"] = {"cost": 0.0}

        print(costs)

        
        # Navigation predicate are mandatory, check if all of them exists
        if "mapsTo" not in costs or "instanceOf" not in costs or "subClassOf" not in costs or "function" not in costs or "label" not in costs:
            raise Exception("Navigation predicate are mandatory: mapsTo, instanceOf, subClassOf, function, label")
        
        self.costs = costs

    def instance_routes(self, meta, instances, allow_incomplete=False,
                        quantity=Quantity, **kwargs):
        """Find all mapping routes for populating an instance of `meta`.

        Arguments:
            meta: Metadata for the instance we will create.
            instances: sequence of instances that the new intance will be
                populated from.
            self.triplestore: self.triplestore containing the mappings.
            allow_incomplete: Whether to allow not populating all properties
                of the returned instance.
            quantity: Class implementing quantities with units.  Defaults to
                pint.Quantity.
            kwargs: Keyword arguments passed to mapping_route().

        Returns:
            A dict mapping property names to a MappingStep instance.
        """
        # if isinstance(meta, str):
        #     meta = dlite.get_instance(meta)
        # if isinstance(instances, dlite.Instance):
        #     instances = [instances]

        # # These lines populated sources starting from dlite instances with raw data
        # # OntoFlow works on the ontological plan, so we don't want to have raw data but just references
        # # Here we can substitute dlite istances with a datamodels reader
        # sources = {}
        # for inst in instances:
        #     props = {p.name: p for p in inst.meta['properties']}
        #     for k, v in inst.properties.items():
        #         uri = f'{inst.meta.uri}#{k}'
        #         uri_references = list(self.triplestore.objects(uri, "http://example.com/demo-ontology#hasReference"))
        #         sources[uri] = uri_references[0] if uri_references else None
        #         # sources[uri] = quantity(v, props[k].unit)

        default_function_costs = []
        default_function_costs.append(("mapsTo", self.costs["mapsTo"]["cost"]))
        default_function_costs.append(("function", self.costs["function"]["cost"]))
        default_function_costs.append(("instanceOf", self.costs["instanceOf"]["cost"]))
        default_function_costs.append(("instanceOf", self.costs["instanceOf"]["cost"]))
        default_function_costs.append(("value", 0.0))
        
        filtered_cost = {k: v for k, v in self.costs.items() if k not in ["mapsTo","instanceOf","subClassOf","function","label", "value"]}
        custom_costs = {}
        for key in filtered_cost.keys():
            entry = filtered_cost[key]
            custom_costs[entry["namespace"]] = {s: o for s, o in self.triplestore.subject_objects(entry["namespace"])}

        # routes = {}

        routes = tripper_mapping_routes(meta, instances, triplestore=self.triplestore, mappingstep_class=OntoFlowEngineMappingStep, value_class=OntoFlowEngineValue, default_costs=default_function_costs, **kwargs)
        routes.adjust_cost(custom_costs, self.costs)

        # for prop in meta['properties']:
        #     target = f'{meta.uri}#{prop.name}'
        #     try:
        #         # route = self.mapping_route(target, sources, triplestore=self.triplestore, **kwargs)
                
        #     # except MissingRelationError:
        #     except Exception:
        #         if allow_incomplete:
        #             continue
        #         raise
        #     if not allow_incomplete and not route.number_of_routes():
        #         raise InsufficientMappingError(f'no mappings for {target}')
        #     routes[prop.name] = route

        return routes


    def getmappingroute(self, outputs, instances, **kwargs):
       
        
        result_dict = {}
        if isinstance(outputs, list):
            for output in outputs:
                routes = self.instance_routes(
                    meta=output,
                    instances=instances
                )

                result_dict[output] = routes

        elif isinstance(outputs, str):
            routes = self.instance_routes(
                    meta=outputs,
                    instances=instances
                )

            result_dict[outputs] = routes
        else:
            raise Exception("Output format not recognized")

        # # best_routes = routes
        # best_routes = {}
        # for k,v in routes.items():
        #     best_routes[k] = self.mco_interface.get_best_route(v)["root"]

        # return best_routes

        return result_dict