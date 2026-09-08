"""
Bee Colony Optimization (BCO) for the Resource-Constrained Project Scheduling
Problem (RCPSP).
-------------------------------------------------------------------------------------
Follows the Artificial Bee Colony (ABC) structure most commonly used for RCPSP
in the scheduling literature (as in the base paper's BCO baseline), adapted to
the activity-list + serial SGS encoding shared with the SA/GA/PSO/Tabu modules
in this project, so all algorithms can be benchmarked on the same instances.

Bee roles:
    - Employed bees: each tied to one "food source" (a solution). They search
      its neighborhood and keep the better of old/new.
    - Onlooker bees: pick a food source probabilistically, weighted by fitness
      (better solutions get chosen -- and thus refined -- more often).
    - Scout bees: if a food source hasn't improved for `limit` trials, it's
      abandoned and replaced with a fresh random solution.

Requires: rcpsp_simulated_annealing.py in the same directory
          (reuses RCPSPInstance, serial_sgs, random_topological_order, swap_neighbor)
"""

import random
from rcpsp_simulated_annealing import (
    RCPSPInstance,
    serial_sgs,
    random_topological_order,
    swap_neighbor,
)


# ---------------------------------------------------------------------------
# Food source representation
# ---------------------------------------------------------------------------

class FoodSource:
    """
    One candidate solution ('food source') the colony is exploiting.
    activity_list: the precedence-feasible order (the solution itself)
    cost: makespan of the decoded schedule (lower = better)
    trials: how many consecutive rounds this source has gone without improving
            (used by scouts to decide when to abandon it)
    """
    def __init__(self, activity_list, cost):
        self.activity_list = activity_list
        self.cost = cost
        self.trials = 0

    def fitness(self):
        # Standard ABC fitness transform: turns "lower cost is better" into
        # "higher fitness is better", used for onlooker selection probabilities.
        if self.cost >= 0:
            return 1.0 / (1.0 + self.cost)
        return 1.0 + abs(self.cost)


# ---------------------------------------------------------------------------
# Core BCO / ABC loop
# ---------------------------------------------------------------------------

def bee_colony_optimization(
    instance: RCPSPInstance,
    colony_size=40,
    limit=25,
    max_iterations=200,
    seed=None,
    verbose=False,
):
    """
    colony_size: total number of food sources (employed bees == colony_size,
                 onlooker bees == colony_size, by ABC convention)
    limit:       trials without improvement before a scout abandons a source
    max_iterations: number of employed+onlooker+scout cycles to run

    Returns dict with best_activity_list, best_makespan, and history
    (list of best_makespan per iteration, for plotting convergence
    alongside the SA/GA/PSO/Tabu curves).
    """
    if seed is not None:
        random.seed(seed)

    # --- initialize food sources ---
    sources = []
    for _ in range(colony_size):
        al = random_topological_order(instance)
        _, _, cost = serial_sgs(instance, al)
        sources.append(FoodSource(al, cost))

    best = min(sources, key=lambda s: s.cost)
    best_list, best_cost = best.activity_list[:], best.cost

    history = []

    for iteration in range(max_iterations):

        # ---------------- Employed bee phase ----------------
        # Each source is exploited once: generate a neighbor, keep it only
        # if it's better (greedy selection).
        for i, source in enumerate(sources):
            candidate_list = swap_neighbor(instance, source.activity_list)
            _, _, candidate_cost = serial_sgs(instance, candidate_list)

            if candidate_cost < source.cost:
                sources[i] = FoodSource(candidate_list, candidate_cost)
            else:
                source.trials += 1

        # ---------------- Onlooker bee phase ----------------
        # Onlookers pick sources probabilistically by fitness (roulette wheel),
        # so better sources get exploited more -- this is what focuses search.
        total_fitness = sum(s.fitness() for s in sources)
        probs = [s.fitness() / total_fitness for s in sources]

        onlookers_assigned = 0
        i = 0
        while onlookers_assigned < colony_size:
            if random.random() < probs[i]:
                source = sources[i]
                candidate_list = swap_neighbor(instance, source.activity_list)
                _, _, candidate_cost = serial_sgs(instance, candidate_list)

                if candidate_cost < source.cost:
                    sources[i] = FoodSource(candidate_list, candidate_cost)
                else:
                    source.trials += 1

                onlookers_assigned += 1
            i = (i + 1) % colony_size

        # ---------------- Scout bee phase ----------------
        # Any source stuck without improvement for `limit` trials gets
        # replaced with a brand-new random solution (escapes local optima).
        for i, source in enumerate(sources):
            if source.trials >= limit:
                al = random_topological_order(instance)
                _, _, cost = serial_sgs(instance, al)
                sources[i] = FoodSource(al, cost)

        # ---------------- Track global best ----------------
        iter_best = min(sources, key=lambda s: s.cost)
        if iter_best.cost < best_cost:
            best_list, best_cost = iter_best.activity_list[:], iter_best.cost

        history.append(best_cost)
        if verbose:
            print(f"Iteration {iteration+1:4d}  best_makespan={best_cost}")

    return {
        "best_activity_list": best_list,
        "best_makespan": best_cost,
        "history": history,
    }


# ---------------------------------------------------------------------------
# Example usage (same toy instance as the SA module, for direct comparison)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
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
    capacities = [3]

    instance = RCPSPInstance(activities, durations, successors, demands, capacities)

    result = bee_colony_optimization(
        instance,
        colony_size=20,
        limit=10,
        max_iterations=50,
        seed=42,
        verbose=True,
    )

    print("\nBest activity list:", result["best_activity_list"])
    print("Best makespan:", result["best_makespan"])
