"""
Simulated Annealing for the Resource-Constrained Project Scheduling Problem (RCPSP)
-------------------------------------------------------------------------------------
Consistent with the base paper's (Mitsou & Koulinas) SA baseline, extended here to
match the project's structure (activity list representation + serial SGS decode).

Encoding:
    A candidate solution is an "activity list" (a permutation of activity IDs that
    respects precedence, i.e. a valid topological order). This is decoded into a
    schedule using the Serial Schedule Generation Scheme (SGS), which respects both
    precedence and resource constraints.

Neighborhood move:
    Swap two adjacent-feasible activities in the activity list (a swap is only
    accepted as a candidate if it doesn't break precedence feasibility).

Objective:
    Minimize project makespan (completion time of the last activity).
"""

import math
import random
from copy import deepcopy


# ---------------------------------------------------------------------------
# Problem definition helpers
# ---------------------------------------------------------------------------

class RCPSPInstance:
    """
    activities: list of activity ids, e.g. [0, 1, 2, ..., n-1]
                0 is typically a dummy start, n-1 a dummy end (duration 0).
    durations:  dict {activity_id: duration}
    successors: dict {activity_id: [list of successor ids]}   (precedence)
    demands:    dict {activity_id: [resource_1_demand, resource_2_demand, ...]}
    capacities: list of resource capacities, e.g. [R1_cap, R2_cap, ...]
    """
    def __init__(self, activities, durations, successors, demands, capacities):
        self.activities = activities
        self.durations = durations
        self.successors = successors
        self.demands = demands
        self.capacities = capacities
        self.predecessors = {a: [] for a in activities}
        for a, succs in successors.items():
            for s in succs:
                self.predecessors[s].append(a)


# ---------------------------------------------------------------------------
# Serial Schedule Generation Scheme (decodes activity list -> schedule)
# ---------------------------------------------------------------------------

def serial_sgs(instance: RCPSPInstance, activity_list):
    """
    Decode a precedence-feasible activity list into start/finish times using
    the serial SGS, respecting renewable resource capacities.
    Returns (start_times, finish_times, makespan).
    """
    start = {}
    finish = {}
    # resource_usage[t] = list of resource usage at time t (extended lazily)
    resource_usage = []

    def usage_at(t, r_idx):
        if t < len(resource_usage):
            return resource_usage[t][r_idx]
        return 0

    def add_usage(t, demands):
        while len(resource_usage) <= t:
            resource_usage.append([0] * len(instance.capacities))
        for r_idx, d in enumerate(demands):
            resource_usage[t][r_idx] += d

    for act in activity_list:
        dur = instance.durations[act]
        preds = instance.predecessors[act]
        earliest = max([finish[p] for p in preds], default=0)

        demands = instance.demands.get(act, [0] * len(instance.capacities))

        # find first feasible start time >= earliest respecting resource caps
        t = earliest
        while True:
            feasible = True
            for tau in range(t, t + dur):
                for r_idx, cap in enumerate(instance.capacities):
                    if usage_at(tau, r_idx) + demands[r_idx] > cap:
                        feasible = False
                        break
                if not feasible:
                    break
            if feasible:
                break
            t += 1

        start[act] = t
        finish[act] = t + dur
        if dur > 0:
            for tau in range(t, t + dur):
                add_usage(tau, demands)

    makespan = max(finish.values())
    return start, finish, makespan


# ---------------------------------------------------------------------------
# Activity list utilities
# ---------------------------------------------------------------------------

def random_topological_order(instance: RCPSPInstance):
    """Generate a random precedence-feasible activity list."""
    remaining = set(instance.activities)
    indegree = {a: len(instance.predecessors[a]) for a in instance.activities}
    ready = [a for a in remaining if indegree[a] == 0]
    order = []
    while ready:
        random.shuffle(ready)
        a = ready.pop()
        order.append(a)
        remaining.remove(a)
        for s in instance.successors.get(a, []):
            indegree[s] -= 1
            if indegree[s] == 0:
                ready.append(s)
    return order


def swap_neighbor(instance: RCPSPInstance, activity_list):
    """
    Produce a neighbor by swapping two positions i, i+1 in the list,
    only if doing so keeps the list precedence-feasible.
    """
    new_list = activity_list[:]
    n = len(new_list)
    attempts = 0
    while attempts < n * 2:
        i = random.randint(0, n - 2)
        a, b = new_list[i], new_list[i + 1]
        # swap is feasible only if 'a' is not a required predecessor of 'b'
        if b not in instance.successors.get(a, []):
            new_list[i], new_list[i + 1] = b, a
            return new_list
        attempts += 1
    return new_list  # fallback: no swap found, return unchanged copy


# ---------------------------------------------------------------------------
# Simulated Annealing core
# ---------------------------------------------------------------------------

def simulated_annealing(
    instance: RCPSPInstance,
    initial_temp=1000.0,
    final_temp=1.0,
    cooling_rate=0.95,
    iterations_per_temp=50,
    max_no_improve=200,
    seed=None,
    verbose=False,
):
    """
    Standard SA loop:
      - geometric cooling: T = T * cooling_rate
      - Metropolis acceptance criterion for worse solutions
      - early stop if no improvement for `max_no_improve` outer iterations

    Returns dict with best_solution (activity list), best_makespan,
    and history (list of (temperature, best_makespan_so_far)) for plotting.
    """
    if seed is not None:
        random.seed(seed)

    current = random_topological_order(instance)
    _, _, current_cost = serial_sgs(instance, current)

    best = current[:]
    best_cost = current_cost

    temp = initial_temp
    history = []
    no_improve_counter = 0

    while temp > final_temp and no_improve_counter < max_no_improve:
        improved_this_temp = False

        for _ in range(iterations_per_temp):
            candidate = swap_neighbor(instance, current)
            _, _, candidate_cost = serial_sgs(instance, candidate)

            delta = candidate_cost - current_cost

            if delta < 0:
                # improvement: always accept
                current, current_cost = candidate, candidate_cost
                if current_cost < best_cost:
                    best, best_cost = current[:], current_cost
                    improved_this_temp = True
            else:
                # worse solution: accept with Metropolis probability
                if delta == 0:
                    accept_prob = 0.5
                else:
                    accept_prob = math.exp(-delta / max(temp, 1e-9))
                if random.random() < accept_prob:
                    current, current_cost = candidate, candidate_cost

        history.append((temp, best_cost))
        if verbose:
            print(f"T={temp:8.2f}  best_makespan={best_cost}")

        temp *= cooling_rate
        no_improve_counter = 0 if improved_this_temp else no_improve_counter + 1

    return {
        "best_activity_list": best,
        "best_makespan": best_cost,
        "history": history,
    }


# ---------------------------------------------------------------------------
# Example usage (small illustrative instance — replace with your PSPLIB data)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # Toy 6-activity instance: 0 = start, 5 = end (dummy, duration 0)
    activities = [0, 1, 2, 3, 4, 5]
    durations = {0: 0, 1: 4, 2: 2, 3: 3, 4: 5, 5: 0}
    successors = {
        0: [1, 2],
        1: [3],
        2: [3, 4],
        3: [5],
        4: [5],
        5: [],
    }
    demands = {
        0: [0], 1: [2], 2: [1], 3: [2], 4: [1], 5: [0],
    }
    capacities = [3]  # single renewable resource, capacity 3

    instance = RCPSPInstance(activities, durations, successors, demands, capacities)

    result = simulated_annealing(
        instance,
        initial_temp=500,
        final_temp=1,
        cooling_rate=0.9,
        iterations_per_temp=30,
        max_no_improve=15,
        seed=42,
        verbose=True,
    )

    print("\nBest activity list:", result["best_activity_list"])
    print("Best makespan:", result["best_makespan"])
