import json
# import: A python command to load external modules. 'json' lets us read JSON formatted data.
import random
# random: A module that provides tools to generate random numbers, used heavily in our algorithms.

def load_data(file_path):
# def: Short for define. It creates a new function. Here we define 'load_data'.
    with open(file_path, 'r') as file:
    # with open(...): Safely opens a file and ensures it gets closed automatically when done.
        return json.load(file)
        # return: Sends the result back to whoever called the function. json.load parses the text into a Python dictionary.

def get_predecessors(data):
# Predecessors: Tasks that MUST be finished before another task can begin (e.g., you must lay a foundation before building walls).
    preds = {int(act): [] for act in data['activities']}
    # Dictionary Comprehension: A fast way to create a dictionary. We initialize empty lists for every activity.
    for u, v_list in data['successors'].items():
    # Successors: Tasks that come immediately after a given task. We loop through all of them.
        for v in v_list:
        # Loop through each individual successor 'v' for the current activity 'u'.
            preds[v].append(int(u))
            # append: Adds an item to the end of a list. We add 'u' as a predecessor to 'v'.
    return preds
    # Returns the fully built dictionary of predecessors.

def serial_sgs(priority_list, data, preds):
# SGS (Schedule Generation Scheme): The core engine that builds a valid schedule by placing activities one by one without breaking rules.
    n = len(data['activities'])
    # len(): Returns the length (number of items) in a list or collection.
    start_times = {i: 0 for i in data['activities']}
    # Initialize start times for all activities to zero.
    finish_times = {i: 0 for i in data['activities']}
    # Initialize finish times for all activities to zero.
    resource_usage = {}
    # resource_usage: A dictionary that will track how many resources (workers, machines) are being used at any given time unit.
    
    scheduled = []
    # scheduled: A list keeping track of which activities have been successfully placed in the timeline.
    eligible = [0]
    # eligible: A list of activities that are ready to be scheduled because all their predecessors are finished. We start with activity 0.
    
    while len(scheduled) < n:
    # while loop: Keeps repeating the block of code underneath as long as the condition (we haven't scheduled everything) is true.
        best_act = -1
        # Initialize a variable to hold the best activity to schedule next.
        for act in priority_list:
        # Loop through our proposed priority order.
            if act in eligible:
            # if statement: Checks if a condition is true. Here, is the activity currently allowed to be scheduled?
                best_act = act
                # If it is, we pick it as the best activity.
                break
                # break: Immediately stops the loop since we found the highest priority eligible activity.
        
        act = best_act
        # We assign the chosen activity to the variable 'act'.
        
        earliest_start = 0
        # earliest_start: The absolute earliest time this activity can begin based on its dependencies.
        for p in preds[act]:
        # Loop through all the tasks that must finish before this one.
            earliest_start = max(earliest_start, finish_times[p])
            # max(): Returns the largest number. The activity must wait for the LAST predecessor to finish.
        
        dur = data['durations'][str(act)]
        # dur (Duration): How long the activity takes to complete.
        dem = data['demands'][str(act)]
        # dem (Demands): How many resources the activity needs to run (e.g., [2, 1] means 2 workers and 1 machine).
        
        t = earliest_start
        # 't' represents the current time slot we are checking to see if resources are available.
        while True:
        # An infinite loop that will only stop when we explicitly 'break' out of it.
            valid = True
            # Assume the current time slot 't' has enough resources.
            for step in range(t, t + dur):
            # range(): Generates a sequence of numbers. We check every single time step the activity will be running.
                usage = resource_usage.get(step, [0, 0])
                # .get(): Fetches a value from a dictionary, or returns a default value ([0, 0]) if it doesn't exist yet.
                if usage[0] + dem[0] > data['capacities'][0] or usage[1] + dem[1] > data['capacities'][1]:
                # If the currently used resources plus the new demand exceeds the maximum capacity...
                    valid = False
                    # ...then this time slot is invalid because we don't have enough resources.
                    break
                    # Stop checking this time slot.
            
            if valid:
            # If the boolean variable 'valid' is still True...
                break
                # We found our starting time! Break out of the while loop.
            t += 1
            # += : Adds 1 to the variable. We move to the next time slot and try again.
            
        start_times[act] = t
        # Record the confirmed start time for this activity.
        finish_times[act] = t + dur
        # Calculate and record the finish time by adding the duration to the start time.
        
        for step in range(t, t + dur):
        # We need to officially reserve the resources for this time block.
            usage = resource_usage.get(step, [0, 0])
            # Get current resource usage.
            resource_usage[step] = [usage[0] + dem[0], usage[1] + dem[1]]
            # Add this activity's demand to the total usage and save it.
            
        scheduled.append(act)
        # Mark this activity as fully scheduled.
        eligible.remove(act)
        # .remove(): Takes an item out of a list. It is no longer 'eligible', it is 'scheduled'.
        
        for succ in data['successors'][str(act)]:
        # Loop through all the tasks that depend on the one we just scheduled.
            if all(p in scheduled for p in preds[succ]):
            # all(): Checks if everything inside is True. Here, are ALL predecessors of the successor finished?
                if succ not in eligible and succ not in scheduled:
                # If it's not already on our lists...
                    eligible.append(succ)
                    # Add it to the eligible list so it can be scheduled next!
                    
    return max(finish_times.values())
    # Makespan: The total time it takes to finish the entire project. We return the largest finish time of any activity.

def tabu_search(data, preds, iterations=10):
# Tabu Search (TS): A metaheuristic algorithm that explores neighbors of a solution and remembers recent bad choices (Tabu list) to avoid getting stuck.
    activities = data['activities'][:]
    # [:]: Slicing notation used here to make a complete copy of the list.
    best_priority = activities[:]
    # Initialize our best priority list to the default order.
    best_makespan = serial_sgs(best_priority, data, preds)
    # Calculate the makespan of the default order.
    
    for _ in range(iterations):
    # Loop for a set number of iterations (we use '_' when we don't need the loop variable).
        candidate = best_priority[:]
        # Create a candidate solution by copying the best one.
        idx1, idx2 = random.sample(range(1, len(activities)-1), 2)
        # random.sample(): Picks unique random elements. We pick two random positions in the list (excluding start/end dummies).
        candidate[idx1], candidate[idx2] = candidate[idx2], candidate[idx1]
        # Tuple unpacking: A Python trick to swap two items in a list without needing a temporary variable.
        
        makespan = serial_sgs(candidate, data, preds)
        # Evaluate how good this new swapped candidate is.
        if makespan < best_makespan:
        # If the candidate finishes the project faster (lower makespan)...
            best_makespan = makespan
            # Update our record for the best time.
            best_priority = candidate[:]
            # Update our record for the best priority order.
            
    return best_makespan, best_priority
    # Return the best results we found during the search.

def pso(data, preds, particles=5, iterations=5):
# Particle Swarm Optimization (PSO): An algorithm inspired by flocking birds. Multiple "particles" (solutions) search the space and share their best findings with the group.
    activities = data['activities'][:]
    # Make a copy of the activities list.
    swarm = [random.sample(activities[1:-1], len(activities)-2) for _ in range(particles)]
    # List Comprehension: Creates multiple random priority lists (particles) to form our "swarm".
    swarm = [[activities[0]] + p + [activities[-1]] for p in swarm]
    # We add the mandatory Start (0) and End dummy activities to the edges of every particle.
    
    best_makespan = float('inf')
    # float('inf'): Represents infinity. We use it so any real makespan will be smaller and replace it.
    best_priority = None
    # None: A special Python value meaning 'nothing'. We haven't found a best priority yet.
    
    for _ in range(iterations):
    # Run the swarm simulation for a set number of iterations.
        for particle in swarm:
        # Evaluate every individual particle in the swarm.
            makespan = serial_sgs(particle, data, preds)
            # Calculate the makespan for this specific particle's priority list.
            if makespan < best_makespan:
            # If it beats the global best time...
                best_makespan = makespan
                # Update the global best makespan.
                best_priority = particle[:]
                # Save this particle's priority list as the new global best.
                
        for i in range(particles):
        # Now we update the positions (priority lists) of all particles so they "fly" towards the best solution.
            if random.random() < 0.5:
            # random.random(): Generates a decimal between 0 and 1. This acts like a 50% chance coin flip.
                swarm[i] = best_priority[:]
                # The particle jumps exactly to the global best position.
                idx1, idx2 = random.sample(range(1, len(activities)-1), 2)
                # Pick two random indices to swap.
                swarm[i][idx1], swarm[i][idx2] = swarm[i][idx2], swarm[i][idx1]
                # Mutation: We swap two elements so the particle doesn't just copy the best, but explores slightly around it.
                
    return best_makespan, best_priority
    # Return the absolute best schedule the swarm could find.

def genetic_algorithm(data, preds, pop_size=5, generations=5):
# Genetic Algorithm (GA): An algorithm inspired by evolution. It creates a population, combines the best ones (crossover), and randomly changes some (mutation) to "evolve" a better schedule.
    activities = data['activities'][:]
    # Make a copy of all activities.
    population = [random.sample(activities[1:-1], len(activities)-2) for _ in range(pop_size)]
    # Create a random starting population of priority lists (excluding start/end dummies).
    population = [[activities[0]] + p + [activities[-1]] for p in population]
    # Add the dummy start and end activities back into the chromosomes (lists).
    
    best_makespan = float('inf')
    # Initialize best makespan to infinity.
    best_priority = None
    # Initialize best priority to None.
    
    for _ in range(generations):
    # Loop for a set number of generations (evolution cycles).
        for p in population:
        # Evaluate each individual in the population.
            makespan = serial_sgs(p, data, preds)
            # Find its fitness (makespan).
            if makespan < best_makespan:
            # If it's the fittest (lowest time) we've seen...
                best_makespan = makespan
                # Save the time.
                best_priority = p[:]
                # Save the genes (priority list).
                
        new_population = [best_priority[:]]
        # Elitism: Automatically keep the absolute best individual in the new generation so we don't lose it.
        while len(new_population) < pop_size:
        # Keep breeding until the new population is full.
            parent = random.choice(population)
            # random.choice(): Picks a random item from a list. We select a parent.
            child = parent[:]
            # The child inherits the parent's exact genes.
            idx1, idx2 = random.sample(range(1, len(activities)-1), 2)
            # Pick two random spots.
            child[idx1], child[idx2] = child[idx2], child[idx1]
            # Mutate the child by swapping two activities.
            new_population.append(child)
            # Add the mutant child to the new generation.
        population = new_population
        # Replace the old generation with the newly evolved one.
        
    return best_makespan, best_priority
    # Return the pinnacle of evolution (the best schedule).

def priority_rule_heuristic(data, preds):
# Priority Rule Heuristic (PRH): A fast, simple algorithm that uses a single strict rule (like "most successors first") to build a schedule, instead of random searching.
    activities = data['activities'][:]
    # Copy the activities list.
    
    # We will use the "Most Successors" priority rule. Activities with more dependencies get scheduled earlier to unblock others.
    def get_successor_count(act):
    # A nested helper function to count how many successors an activity has.
        return len(data['successors'][str(act)])
        # Returns the length of the successors list for a given activity.
        
    # Sort the middle activities (excluding dummies) based on how many successors they have, in descending (reverse) order.
    middle_acts = activities[1:-1]
    # Slice out the middle activities.
    middle_acts.sort(key=get_successor_count, reverse=True)
    # .sort(key=...): Sorts a list using a custom function. We sort by the highest number of successors first.
    
    priority_list = [activities[0]] + middle_acts + [activities[-1]]
    # Reassemble the list with the dummies on the ends.
    
    makespan = serial_sgs(priority_list, data, preds)
    # Generate the schedule using this single, fixed rule.
    return makespan, priority_list
    # Return the result. Since it doesn't search, it's very fast, but might not be the absolute best.
