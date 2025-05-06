import json
import os

BDFS = {
    "linear": "a*x+b",
    "quadratic": "a*x**2 + b*x + c",
    "cubic": "a*x**3 + b*x**2 + c*x + d",
    "quartic": "a*x**4 + b*x**3 + c*x**2 + d*x + e",
    "sym_hump": "",
    "left_hump": "",
    "right_hump": "",
    "exp_hump": "a*(x-b) / (1 + c**(x-d))",
}

ALPHABET = ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j"]

class ODKProcess:
    def __init__(
        self,
        name,
        type,
        constant_bool: bool,
        constant: float,
        function_var: str,
        function_bdf: str,
        function_bdf_parameters: list,
        scalars_bool: bool,
        scalar_constants_bool: bool,
        scalar_constants: set,
        scalar_vars: set,
        **kwargs,
    ):
        function_var = "A" if function_var == "age" else function_var
        
        if constant_bool:
            bdf = constant
            bdf_inputs = {}
        else:
            print("BDF", name,type, function_bdf)
            func_str = BDFS.get(function_bdf).replace("x", function_var.upper())
            bdf = f"max(0, {func_str})"
            bdf_inputs = dict(zip(ALPHABET, function_bdf_parameters))
        
        base_func = f"{type}_rate"
        base_inputs = {f"{type}_rate": f"{name}.bdfs.{type}_rate"}
        
        self.bdfs = {
            f"{type}_rate": {
                "type": "age_structured" if function_var == "A" else "single",
                "function": bdf,
                "inputs": bdf_inputs
            }
        }

        rate_func = "1"
        rate_inputs = {}
        
        if scalars_bool:
            for entry in scalar_vars:
                id, bdf, parameters = entry.values()
                rate_func = f"{rate_func}*{id}_scalar"
                rate_inputs |= {f"{id}_scalar": f"{name}.bdfs.{type}_{id}_scalar"}
                print(id, bdf, parameters)
                self.bdfs |= {
                    f"{type}_{id}_scalar": {
                        "function": f"max(0, min(1, {BDFS.get(bdf).replace('x', id.upper())}))",
                        "inputs": dict(zip(ALPHABET, parameters)),
                    }
                }

        if scalar_constants_bool:
            for entry in scalar_constants:
                scalar, value = entry.values()
                rate_func = f"{rate_func}*{scalar}"
                rate_inputs |= {scalar: value}    
                print(rate_func, rate_inputs)   

        self.processes = {
            type: {
                "rates": {
                    f"{type}_rate": {
                        "function": f"{rate_func}*{base_func}" ,
                        "inputs": base_inputs | rate_inputs,
                    }
                },
                "variables": {"var": {"function": f"{type}_rate"}},
            }
        }

        self.processes = {}

        if type == "reproduction":
            self.processes = {
                "reproduction": {
                    "rates": {
                        "reproduction_rate": {
                            "function": f"total_egg * {rate_func}",
                            "inputs": rate_inputs
                        }
                    },
                    "variables": {"var": {"function": f"{type}_rate"}},
                    "functions": {
                        "total_egg": {
                            "type": "age_structured_integral",
                            "integrand": "reproduction_rate * number",
                            "age_structured_inputs": {"reproduction_rate": f"{name}.bdfs.reproduction_rate", "number": f"{name}.n"}
                        }
                    },
                    # TODO: THIS IS BAD. ALSO NEED TO FIX THAT n is EXPOSED - IT SHOULDN'T BE
                }
            }
        elif type == "mortality":
            self.processes = {
                "mortality": {
                    "rates": {
                        "mortality_rate": {
                            "type": "age_structured",
                            "function": f"{rate_func}*{base_func}*number",
                            "inputs": base_inputs | rate_inputs,
                            "age_structured_inputs": {"number": f"{name}.n"},
                        }
                    },
                    "variables": {
                        "var": {
                            "type": "age_structured",
                            "function": f"-{type}_rate",
                            "age_structured_inputs": [f"{type}_rate"],
                        }
                    },
                }
            }

class Insect:
    def __init__(
        self,
        org_name,
        dynamics,
        mortality = {},
        repro = {},
        diapause = {"bool": False}
    ):
        pop_data = {
            "name": org_name,
            "sub_populations": {},
            "stage_structure": {},
        }
        
        substages = list(dynamics.keys())
        
        for stage in substages:
            pop_data["sub_populations"][stage] = {
                "variable": "n",
                "bdfs": {},
                "processes": {},
                "dynamics": {},
            }
        
        # Process dynamics
        for name, data in dynamics.items():
            assert name in substages
            inherit = data.pop("inherit")
            inherit_from = data.pop("inherit_from")

            pbdm_data = pop_data["sub_populations"][name]

            if not inherit:
                process_source = data
                process_name = name
            else:
                process_source = dynamics[inherit_from]
                process_name = f"{org_name}.{inherit_from}"
            process = ODKProcess(name=process_name, type="development", **process_source)
            Del = process_source["Del"]
            variance = process_source["variance"]
            pbdm_data["age_structure"] = {}
            pbdm_data["age_structure"]["k"] = 3 #math.floor(Del**2/variance)
            pbdm_data["age_structure"]["variable"] = "A"
            pbdm_data["Del"] = Del 
            #pbdm_data["processes"].update(process.processes)
            if not inherit:
                pbdm_data["bdfs"].update(process.bdfs)

            pbdm_data["dynamics"].update(
                numbers = {
                    "type": "distributed_delay",
                    "rate": {
                        "function": "dev_rate * k/Del",
                        "inputs": {"dev_rate": f"{process_name}.bdfs.development_rate"}
                    }
                }
            )

        # Process mortality
        print(mortality)
        if mortality:
            for name, data in mortality.items():
                assert name in substages
                inherit = data.pop("inherit")
                inherit_from = data.pop("inherit_from")

                pbdm_data = pop_data["sub_populations"][name]

                if not inherit:
                    process = ODKProcess(name=name, type="mortality", **data)
                    pbdm_data["bdfs"].update(process.bdfs)
                    pbdm_data["processes"].update(process.processes)
                else:
                    process = ODKProcess(name=f"{org_name}.{inherit_from}", type="mortality",  **mortality[inherit_from])
                    pbdm_data["processes"].update(process.processes)

        # Process reproduction
        if repro:
            adult_name = substages[-1]
            pbdm_data = pop_data["sub_populations"][adult_name]
            process = ODKProcess(name=adult_name, type="reproduction", **repro)
            pbdm_data["bdfs"].update(process.bdfs)
            pbdm_data["processes"].update(process.processes)
            first_stage = substages[0]
            pbdm_data["processes"]["reproduction"].update(variable_connections = {"n": f"{org_name}.{first_stage}.n_1"})

        pop_data["stage_structure"].update(
            egg = {
                "next_stage": {
                    "larva": {
                        "target_variable": "n_1"
                    }
                }
            },
            larva = {
                "next_stage": {
                    "pupa": {
                        "target_variable": "n_1"
                    }
                }
            },
            pupa = {
                "next_stage": {
                    "adult": {
                        "target_variable": "n_1"
                    }
                }
            },

        ) 

        # Process diapause
        add_diapause = diapause.pop("bool")
        if add_diapause:
            prev_stage = diapause.get("prev_stage")
            next_stage = diapause.get("next_stage")
            entry_rate = diapause.get("entry_function_bdf")
            entry_var = diapause.get("entry_function_var")
            entry_params = diapause.get("entry_function_bdf_parameters")
            exit_rate = diapause.get("exit_function_bdf")
            exit_var = diapause.get("exit_function_var")
            exit_params = diapause.get("exit_function_bdf_parameters")
            pop_data["sub_populations"].update(
                diapause = {
                    "variable": "n",
                    "bdfs": {
                        "entry": {
                            "function": BDFS.get(entry_rate).replace("x", entry_var.upper()),
                            "inputs": dict(zip(ALPHABET, entry_params))
                        },
                        "exit": {
                            "function": BDFS.get(exit_rate).replace("x", exit_var.upper()),
                            "inputs": dict(zip(ALPHABET, exit_params))
                        }
                    },
                    "dynamics": {
                        "numbers": {
                            "type": "population_variable",
                        }
                    }
                }
            )
            split_stage = next(iter(pop_data["stage_structure"][prev_stage]["next_stage"].keys()))
            pop_data["stage_structure"][prev_stage]["next_stage"] = {
                split_stage: {
                    "rate": "1 - diap_entry_rate",
                    "inputs": {"diap_entry_rate": f"{org_name}.diapause.bdfs.entry"},
                    "target_variable": "n_1",
                },
                "diapause": {
                    "rate": "diap_entry_rate",
                    "inputs": {"diap_entry_rate": f"{org_name}.diapause.bdfs.entry"},
                    "target_variable": "n",
                }
            }
            pop_data["stage_structure"]["diapause"] = {
                "next_stage": {
                    next_stage: {
                        "rate": "diap_exit_rate",
                        "inputs": {"diap_exit_rate": f"diapause.bdfs.exit"},
                        "target_variable": "n_1",
                    }
                }
            }

        self.data = pop_data

    def to_json(self, dir, file_name):
        FILE_DIR = os.path.join(dir, file_name)
        with open(FILE_DIR, "w") as f:
            json.dump(self.data, f)