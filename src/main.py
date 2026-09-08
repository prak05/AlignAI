import json
# Import json module to read our input data file
import random
# Import random module for our heuristic algorithms

def load_data(file_path):
# Define a function to read and parse the json file
    with open(file_path, 'r') as file:
    # Open the specified file in read mode
        return json.load(file)
        # Parse and return the json content as a python dictionary

def get_predecessors(data):
# Define a function to find the predecessors (dependencies) for each activity
    preds = {int(act): [] for act in data['activities']}
    # Create an empty list of predecessors for every activity
    for u, v_list in data['successors'].items():
    # Loop through each activity and its successors
        for v in v_list:
        # Loop through each successor
            preds[v].append(int(u))
            # Add the current activity 'u' as a predecessor for 'v'
    return preds
    # Return the dictionary of predecessors

def serial_sgs(priority_list, data, preds):
# Define a function to generate a schedule using Serial Schedule Generation Scheme
    n = len(data['activities'])
    # Get the total number of activities
    start_times = {i: 0 for i in data['activities']}
    # Initialize start times for all activities to 0
    finish_times = {i: 0 for i in data['activities']}
    # Initialize finish times for all activities to 0
    resource_usage = {}
    # Dictionary to track resource usage over time
    
    scheduled = []
    # List to keep track of successfully scheduled activities
    eligible = [0]
    # Start with the dummy start activity (usually 0)
    
    while len(scheduled) < n:
    # Loop until all activities are scheduled
        best_act = -1
        # Variable to store the best eligible activity to schedule next
        for act in priority_list:
        # Iterate through the provided priority list
            if act in eligible:
            # Check if the activity is currently eligible to be scheduled
                best_act = act
                # If so, pick this activity and break the loop
                break
                # Stop searching once we find the highest priority eligible activity
        
        act = best_act
        # Set the current activity to schedule
        
        earliest_start = 0
        # Initialize the earliest possible start time
        for p in preds[act]:
        # Loop through all predecessors of the current activity
            earliest_start = max(earliest_start, finish_times[p])
            # The activity can only start after all its predecessors have finished
        
        dur = data['durations'][str(act)]
        # Get the duration of the current activity
        dem = data['demands'][str(act)]
        # Get the resource demands of the current activity
        
        t = earliest_start
        # Start checking for resource availability from the earliest start time
        while True:
        # Loop to find the first time slot with enough resources
            valid = True
            # Assume the current time slot 't' is valid
            for step in range(t, t + dur):
            # Check every time step during the activity's execution
                usage = resource_usage.get(step, [0, 0])
                # Get the current resource usage at this time step
                if usage[0] + dem[0] > data['capacities'][0] or usage[1] + dem[1] > data['capacities'][1]:
                # Check if adding this activity exceeds the maximum capacity of any resource
                    valid = False
                    # If it exceeds, this time slot is invalid
                    break
                    # Stop checking this time slot
            
            if valid:
            # If the time slot has enough resources for the entire duration
                break
                # We found our start time, break the while loop
            t += 1
            # Otherwise, try the next time step
            
        start_times[act] = t
        # Assign the found valid start time to the activity
        finish_times[act] = t + dur
        # Calculate and assign the finish time
        
        for step in range(t, t + dur):
        # Update the resource usage tracker for the duration of the activity
            usage = resource_usage.get(step, [0, 0])
            # Get the current usage
            resource_usage[step] = [usage[0] + dem[0], usage[1] + dem[1]]
            # Add the activity's demand to the current usage
            
        scheduled.append(act)
        # Mark the activity as scheduled
        eligible.remove(act)
        # Remove it from the eligible list
        
        for succ in data['successors'][str(act)]:
        # Check all successors of the newly scheduled activity
            if all(p in scheduled for p in preds[succ]):
            # If all predecessors of a successor are now scheduled
                if succ not in eligible and succ not in scheduled:
                # And it's not already in eligible or scheduled lists
                    eligible.append(succ)
                    # Add the successor to the eligible list
                    
    return max(finish_times.values())
    # Return the maximum finish time, which is the total project duration (makespan)

def tabu_search(data, preds, iterations=10):
# Define a minimal Tabu Search algorithm
    activities = data['activities'][:]
    # Copy the list of activities
    best_priority = activities[:]
    # Initialize the best priority list
    best_makespan = serial_sgs(best_priority, data, preds)
    # Calculate the makespan of the initial priority list
    
    for _ in range(iterations):
    # Run the search for a set number of iterations
        candidate = best_priority[:]
        # Create a candidate solution by copying the best one
        idx1, idx2 = random.sample(range(1, len(activities)-1), 2)
        # Randomly select two indices to swap (excluding dummy start/end)
        candidate[idx1], candidate[idx2] = candidate[idx2], candidate[idx1]
        # Swap the activities at those indices to create a new neighbor solution
        
        makespan = serial_sgs(candidate, data, preds)
        # Calculate the makespan of this new candidate solution
        if makespan < best_makespan:
        # If this candidate is better than our best so far
            best_makespan = makespan
            # Update the best makespan
            best_priority = candidate[:]
            # Update the best priority list
            
    return best_makespan, best_priority
    # Return the best found makespan and its corresponding priority list

def pso(data, preds, particles=5, iterations=5):
# Define a minimal Particle Swarm Optimization algorithm
    activities = data['activities'][:]
    # Copy the list of activities
    swarm = [random.sample(activities[1:-1], len(activities)-2) for _ in range(particles)]
    # Initialize a swarm of random priority lists (excluding start/end dummies)
    swarm = [[activities[0]] + p + [activities[-1]] for p in swarm]
    # Add the dummy start and end back to each particle's priority list
    
    best_makespan = float('inf')
    # Initialize global best makespan to infinity
    best_priority = None
    # Initialize global best priority list
    
    for _ in range(iterations):
    # Loop over the specified number of iterations
        for particle in swarm:
        # Evaluate each particle in the swarm
            makespan = serial_sgs(particle, data, preds)
            # Calculate makespan for the current particle
            if makespan < best_makespan:
            # Check if this particle found a new global best
                best_makespan = makespan
                # Update global best makespan
                best_priority = particle[:]
                # Update global best priority list
                
        for i in range(particles):
        # Update particles (simplified: just randomizing slightly towards best)
            if random.random() < 0.5:
            # With 50% probability
                swarm[i] = best_priority[:]
                # Move the particle exactly to the global best position
                idx1, idx2 = random.sample(range(1, len(activities)-1), 2)
                # Pick two random indices
                swarm[i][idx1], swarm[i][idx2] = swarm[i][idx2], swarm[i][idx1]
                # Introduce a small mutation (swap) to explore nearby areas
                
    return best_makespan, best_priority
    # Return the overall best makespan and priority list found by the swarm

def solve_project(file_path):
# Main function to solve the scheduling problem
    data = load_data(file_path)
    # Load the JSON data
    preds = get_predecessors(data)
    # Calculate the predecessors for all activities
    
    num_activities = len(data['activities'])
    # Get the total number of activities to act as a simple feature
    
    print("Project Data Loaded.")
    # Print a status message
    if num_activities < 20:
    # A simple meta-controller logic based on problem size (feature)
        print("Selecting Tabu Search (TS) for small project...")
        # Choose TS for smaller projects
        makespan, order = tabu_search(data, preds)
        # Run Tabu Search
    else:
    # If the project is larger
        print("Selecting Particle Swarm Optimization (PSO) for large project...")
        # Choose PSO which explores better in larger spaces
        makespan, order = pso(data, preds)
        # Run Particle Swarm Optimization
        
    print(f"Best Makespan Found: {makespan}")
    # Print the final best duration
    print(f"Priority Order: {order}")
    # Print the order used to achieve it

if __name__ == "__main__":
# Standard Python entry point check
    solve_project("data/gemini-code-1788886167629.json")
    # Run the solver on our provided input file
