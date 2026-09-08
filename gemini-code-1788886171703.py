import json
from rcpsp_simulated_annealing import RCPSPInstance

def load_project_instance(filepath: str) -> RCPSPInstance:
    with open(filepath, "r") as f:
        data = json.load(f)
    
    return RCPSPInstance(
        activities=data["activities"],
        durations={int(k): v for k, v in data["durations"].items()},
        successors={int(k): v for k, v in data["successors"].items()},
        demands={int(k): v for k, v in data["demands"].items()},
        capacities=data["capacities"]
    )