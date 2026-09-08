from flask import Flask, jsonify, request
# Flask: A lightweight web framework for Python. jsonify: Converts Python dictionaries to JSON format for web responses. request: Handles incoming HTTP requests.
import json
# json: A built-in module to read and write JSON data.
import os
# os: Operating System module used to build safe file paths regardless of whether we run on Windows, Mac, or Linux.
import sys
# sys: System-specific parameters and functions, used here to modify the Python search path so it can find our other files.

# BASE_DIR: The absolute path to the very top folder of our project. We calculate it dynamically based on where this file (__file__) is located.
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(BASE_DIR, "src"))
# sys.path.append(): We add the 'src' directory to Python's internal list of folders to search when we use the 'import' command.

from main import load_data, get_predecessors, tabu_search, pso, genetic_algorithm, priority_rule_heuristic
# Import all of our scheduling logic and the 4 algorithms from our main.py file.

app = Flask(__name__, static_url_path='', static_folder='../src/static')
# Initialize our Flask app. We tell it where to find our static files (HTML, CSS, JS) relative to this api/ folder.

class SchedulerState:
# Class: A blueprint for creating objects. Here we create an object that remembers the state of our algorithm as it steps forward.
    def __init__(self):
    # __init__: The constructor method that runs automatically when a new SchedulerState object is created.
        self.generator = None
        # generator: A special Python object that can be paused and resumed. It will hold our running algorithm.
        self.last_state = None
        # last_state: A variable to remember the most recent data sent to the frontend GUI.
        
    def reset(self, filepath):
    # reset: A method to restart the entire scheduling process with a new file.
        project_data = load_data(filepath)
        # Load the raw project data from the selected JSON file.
        preds = get_predecessors(project_data)
        # Calculate all the task dependencies (predecessors).
        num_activities = len(project_data['activities'])
        # Extract the total number of activities. This acts as our "Feature" for the Meta-Controller!
        
        # Meta-Controller: An AI or logic system that looks at the problem and decides WHICH algorithm to use!
        if num_activities < 8:
        # If it's a very simple project (less than 8 tasks)...
            makespan, priority_list = priority_rule_heuristic(project_data, preds)
            # Use Priority Rule Heuristic (fastest, simplest method).
            algo = "Priority Rule Heuristic (PRH)"
        elif num_activities < 15:
        # If it's a small project (8 to 14 tasks)...
            makespan, priority_list = tabu_search(project_data, preds)
            # Use Tabu Search (exhaustively explores small spaces).
            algo = "Tabu Search (TS)"
        elif num_activities < 20:
        # If it's a medium project (15 to 19 tasks)...
            makespan, priority_list = genetic_algorithm(project_data, preds)
            # Use Genetic Algorithm (evolves solutions for complex, tightly constrained spaces).
            algo = "Genetic Algorithm (GA)"
        else:
        # If it's a massive project (20 or more tasks)...
            makespan, priority_list = pso(project_data, preds)
            # Use Particle Swarm Optimization (excellent at finding good solutions in massive search spaces without getting stuck).
            algo = "Particle Swarm Optimization (PSO)"

        self.generator = self.serial_sgs_stepper(priority_list, project_data, preds, algo)
        # Create a new generator using the priority list found by our chosen algorithm.
        self.last_state = next(self.generator)
        # next(): Advances the generator to its first 'yield' statement (initialization step) and saves the state.
        
    def step(self):
    # step: A method to advance the algorithm by one single scheduling action.
        if not self.generator:
        # If the generator hasn't been created yet...
            return {"error": "Not initialized"}
            # Return an error.
        try:
        # try...except: A way to catch errors.
            self.last_state = next(self.generator)
            # Ask the generator for the next step.
            return self.last_state
            # Return it to the frontend.
        except StopIteration:
        # StopIteration: A built-in Python error that happens when a generator is completely finished.
            self.last_state['done'] = True
            # Mark the state as completely finished.
            return self.last_state

    def serial_sgs_stepper(self, priority_list, data, preds, algo):
    # The step-by-step version of our Schedule Generation Scheme (SGS). It uses 'yield' instead of 'return'.
        n = len(data['activities'])
        # Count activities.
        start_times = {i: 0 for i in data['activities']}
        # Reset start times.
        finish_times = {i: 0 for i in data['activities']}
        # Reset finish times.
        resource_usage = {}
        # Reset resource tracking.
        scheduled = []
        # Clear scheduled list.
        eligible = [0]
        # Set Activity 0 (Start Dummy) as the only eligible task.
        
        yield {
        # yield: Unlike 'return', yield sends data back but PAUSES the function exactly here. Next time it's called, it resumes from here!
            "status": "Initialized",
            "explanation": f"Loaded project with {n} activities. The Meta-Controller analyzed this size and chose {algo}. It generated the optimal priority order: {priority_list}. We start with the Dummy Activity 0.",
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
        # Keep looping until all tasks are scheduled.
            best_act = -1
            # Reset best act tracker.
            for act in priority_list:
            # Check the priority list in order.
                if act in eligible:
                # Find the first one that is allowed to be scheduled right now.
                    best_act = act
                    break
            act = best_act
            # We found the task to schedule!
            
            earliest_start = 0
            # Track when it can begin.
            for p in preds[act]:
            # Wait for all its predecessors to finish.
                earliest_start = max(earliest_start, finish_times[p])
                
            dur = data['durations'][str(act)]
            # Get task duration.
            dem = data['demands'][str(act)]
            # Get resource demands.
            
            t = earliest_start
            # Start checking the timeline.
            while True:
            # Infinite loop to find an open time slot.
                valid = True
                # Assume the slot is valid.
                for step in range(t, t + dur):
                # Check every moment it runs.
                    usage = resource_usage.get(step, [0, 0])
                    # See current resource usage.
                    if usage[0] + dem[0] > data['capacities'][0] or usage[1] + dem[1] > data['capacities'][1]:
                    # If we run out of resources...
                        valid = False
                        # Invalid slot.
                        break
                if valid:
                # If we made it through without breaking, it's valid!
                    break
                t += 1
                # Check the next time slot.
                
            start_times[act] = t
            # Save the start time.
            finish_times[act] = t + dur
            # Save the finish time.
            
            for step in range(t, t + dur):
            # Officially book the resources in our tracker.
                usage = resource_usage.get(step, [0, 0])
                resource_usage[step] = [usage[0] + dem[0], usage[1] + dem[1]]
                
            scheduled.append(act)
            # Move it to the scheduled list.
            eligible.remove(act)
            # Remove it from eligible.
            
            new_eligible = []
            # Keep track of newly unlocked tasks.
            for succ in data['successors'][str(act)]:
            # Check all tasks that depend on the one we just scheduled.
                if all(p in scheduled for p in preds[succ]):
                # If all of their requirements are finally met...
                    if succ not in eligible and succ not in scheduled:
                    # And they aren't already processed...
                        eligible.append(succ)
                        # Make them eligible!
                        new_eligible.append(succ)
            
            explanation = (
                f"Selected Activity {act} because it has the highest priority among eligible tasks. "
                f"It needs resources {dem} and takes {dur} units of time. "
                f"It was scheduled from time {t} to {t+dur}. "
            )
            # Build a string explaining what just happened in this step.
            if new_eligible:
                explanation += f"This successfully unlocked activities {new_eligible}!"
            
            yield {
            # yield: Pause the algorithm again and send this step's data to the GUI!
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

scheduler = SchedulerState()
# Create the global scheduler state manager.

# We initialize it safely.
try:
# Attempt to load the TS test by default.
    scheduler.reset(os.path.join(BASE_DIR, "data", "ts_test.json"))
except FileNotFoundError:
# If it fails, ignore it, it will be loaded from the web interface.
    pass

@app.route('/')
# @app.route: A Decorator. It tells Flask that whenever a user visits the root URL ('/'), run the function below it.
def index():
# The function that serves our main HTML page.
    return app.send_static_file('index.html')
    # Sends the index.html file to the user's browser.

@app.route('/reset', methods=['POST'])
# A backend endpoint (API route) that the Javascript calls to reset the schedule. It requires a POST request.
def reset():
# Function to handle reset requests.
    req_data = request.get_json(silent=True) or {}
    # Extract the JSON payload sent by the Javascript frontend (which contains the selected filename).
    filename = req_data.get('filename', 'ts_test.json')
    # Get the filename, or default to ts_test.json if none provided.
    filepath = os.path.join(BASE_DIR, "data", filename)
    # Build the full absolute path to the data file safely.
    
    if not os.path.exists(filepath):
    # Check if the file actually exists on the hard drive.
        return jsonify({"error": "File not found"}), 404
        # Return an HTTP 404 Not Found error if it doesn't.
        
    scheduler.reset(filepath)
    # Restart our state machine with the new file.
    return jsonify(scheduler.last_state)
    # Send the very first step's data back to the GUI.

@app.route('/step', methods=['POST'])
# Endpoint called when the user clicks the "Next Step" button.
def step():
# Function to handle step requests.
    return jsonify(scheduler.step())
    # Advance the generator by one step and send the new data to the GUI.

# Vercel Note: For serverless deployments, the 'app' object defined above is all it needs.
# The block below only runs if you execute this file directly (e.g., 'python api/index.py') on your own computer.
if __name__ == '__main__':
    app.run(debug=True, port=5000)
    # Starts a local development server on port 5000 with hot-reloading enabled (debug=True).
