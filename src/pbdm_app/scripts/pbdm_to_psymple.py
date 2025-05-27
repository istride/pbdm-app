from pbdm.functional_population.functional_population import FunctionalPopulation
from psymple.build import System, HIERARCHY_SEPARATOR
from pbdm.climate import ClimateHandler
import json, os

BASE_DIR = os.path.dirname(os.path.abspath(''))
FILES_DIR = os.path.join(BASE_DIR, "pbdm-flask-app", "flask-app", "files")

class SetEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, set):
            return list(obj)
        return json.JSONEncoder.default(self, obj)

wx_file = os.path.join(FILES_DIR, "sample_weather.csv")

class pbdmRunner:
    def __init__(self, pbdm_data):
        pop = FunctionalPopulation(**pbdm_data)
        pop.compile_system_connections()
        X = pop.generate_ported_object()
        data = X.to_data()
        psymple_dir = os.path .join(FILES_DIR, "psymple_data.json")
        with open(psymple_dir, "w") as f:
            json.dump(data, f, cls=SetEncoder)
        self.system = System(X)
        self._insert_system_parameters()
        self.system.compile()
        

    def _insert_system_parameters(self):
        C = ClimateHandler(wx_file, 14, 2, 2007)
        S = self.system
        S.add_system_parameter("TMIN", lambda T: C.climate(T, "TMIN"))
        S.add_system_parameter("TMAX", lambda T: C.climate(T, "TMAX"))
        S.add_system_parameter("RH", lambda T: C.climate(T, "RH"))
        S.add_system_parameter("DAY_LENGTH", "11")
        S.add_system_parameter("SOLAR_RAD", lambda T: C.climate(T, "SOL"))
        S.add_system_parameter("TEMP", "(TMAX + TMIN)/2", signature=("TMIN", "TMAX"))

    def generate_input_parameters(self):
        return self.system._check_required_parameters()

    def generate_initial_conditions(self):
        vars = {var.name: var.initial_value for var in self.system.variables.values() if HIERARCHY_SEPARATOR not in var.name and (not var.name.startswith("dummy"))}

        return vars


pbdm_file = os.path.join(FILES_DIR, "pbdm_data.json")

with open(pbdm_file) as f:
    pbdm_data = json.load(f)

X = pbdmRunner(pbdm_data)

print(X.generate_input_parameters())
print(X.generate_initial_conditions())

