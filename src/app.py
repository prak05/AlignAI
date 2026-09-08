from flask import Flask, jsonify, request
import json
import os
from main import load_data, get_predecessors, tabu_search, pso

app = Flask(__name__, static_url_path='', static_folder='static')

class SchedulerState:
    def __init__(self):
        self.generator = None
        self.last_state = None
        
    def reset(self, filepath):
        project_data = load_data(filepath)
        preds = get_predecessors(project_data)
        num_activities = len(project_data['activities'])
        
        if num_activities < 20:
            makespan, priority_list = tabu_search(project_data, preds)
            algo = "Tabu Search (TS)"
        else:
            makespan, priority_list = pso(project_data, preds)
            algo = "Particle Swarm Optimization (PSO)"

        self.generator = self.serial_sgs_stepper(priority_list, project_data, preds, algo)
        self.last_state = next(self.generator)
        
    def step(self):
        if not self.generator:
            return {"error": "Not initialized"}
        try:
            self.last_state = next(self.generator)
            return self.last_state
        except StopIteration:
            self.last_state['done'] = True
            return self.last_state

    def serial_sgs_stepper(self, priority_list, data, preds, algo):
        n = len(data['activities'])
        start_times = {i: 0 for i in data['activities']}
        finish_times = {i: 0 for i in data['activities']}
        resource_usage = {}
        scheduled = []
        eligible = [0]
        
        yield {
            "status": "Initialized",
            "explanation": f"Loaded project with {n} activities. Since activities {'<' if n < 20 else '>='} 20, the meta-controller chose {algo}. Priority list found: {priority_list}. Starting with Dummy Activity 0.",
            "scheduled": scheduled,
            "eligible": eligible,
            "start_times": start_times,
            "finish_times": finish_times,
            "capacities": data['capacities'],
            "done": False,
            "activities": data['activities'],
            "durations": data['durations']
        }
        
        while len(scheduled) < n:
            best_act = -1
            for act in priority_list:
                if act in eligible:
                    best_act = act
                    break
            act = best_act
            
            earliest_start = 0
            for p in preds[act]:
                earliest_start = max(earliest_start, finish_times[p])
                
            dur = data['durations'][str(act)]
            dem = data['demands'][str(act)]
            
            t = earliest_start
            while True:
                valid = True
                for step in range(t, t + dur):
                    usage = resource_usage.get(step, [0, 0])
                    if usage[0] + dem[0] > data['capacities'][0] or usage[1] + dem[1] > data['capacities'][1]:
                        valid = False
                        break
                if valid:
                    break
                t += 1
                
            start_times[act] = t
            finish_times[act] = t + dur
            
            for step in range(t, t + dur):
                usage = resource_usage.get(step, [0, 0])
                resource_usage[step] = [usage[0] + dem[0], usage[1] + dem[1]]
                
            scheduled.append(act)
            eligible.remove(act)
            
            new_eligible = []
            for succ in data['successors'][str(act)]:
                if all(p in scheduled for p in preds[succ]):
                    if succ not in eligible and succ not in scheduled:
                        eligible.append(succ)
                        new_eligible.append(succ)
            
            explanation = (
                f"Selected Activity {act} because it has the highest priority among eligible tasks. "
                f"It needs resources {dem} and takes {dur} units of time. "
                f"It was scheduled from time {t} to {t+dur}. "
            )
            if new_eligible:
                explanation += f"This made activities {new_eligible} newly eligible."
            
            yield {
                "status": f"Scheduled Activity {act}",
                "explanation": explanation,
                "scheduled": scheduled.copy(),
                "eligible": eligible.copy(),
                "start_times": start_times.copy(),
                "finish_times": finish_times.copy(),
                "capacities": data['capacities'],
                "done": False,
                "activities": data['activities'],
                "durations": data['durations']
            }

# Get the absolute path to the root directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

scheduler = SchedulerState()
# Initialize with default on startup
scheduler.reset(os.path.join(BASE_DIR, "data", "ts_test.json"))

@app.route('/')
def index():
    return app.send_static_file('index.html')

@app.route('/reset', methods=['POST'])
def reset():
    req_data = request.get_json(silent=True) or {}
    filename = req_data.get('filename', 'ts_test.json')
    filepath = os.path.join(BASE_DIR, "data", filename)
    
    if not os.path.exists(filepath):
        return jsonify({"error": "File not found"}), 404
        
    scheduler.reset(filepath)
    return jsonify(scheduler.last_state)

@app.route('/step', methods=['POST'])
def step():
    return jsonify(scheduler.step())

if __name__ == '__main__':
    app.run(debug=True, port=5000)
