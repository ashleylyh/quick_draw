import random
import json
from typing import Optional, Dict, List

from config import PER_ROUND, NUM_ROUNDS

# Load classes from JSON
with open("classes.json", "r") as f:
    classes_data = json.load(f)
    CLASSES = classes_data["CLASSES"]

# Simple mode pools (from original sketch-original.js)
POOL_TEXT = """
eyeglasses	bus	crab	camera	lollipop	ice_cream
eyeglasses	bus	crab	map	lollipop	ice_cream
eyeglasses	car	crab	camera	lollipop	ice_cream
eyeglasses	car	crab	map	lollipop	ice_cream
eyeglasses	bus	crab	camera	donut	hot_air_balloon
eyeglasses	bus	crab	map	donut	hot_air_balloon
eyeglasses	car	crab	camera	donut	hot_air_balloon
eyeglasses	car	crab	map	donut	hot_air_balloon
eyeglasses	bus	calculator	octopus	lollipop	ice_cream
eyeglasses	car	calculator	octopus	lollipop	ice_cream
eyeglasses	bus	calculator	octopus	donut	hot_air_balloon
eyeglasses	car	calculator	octopus	donut	hot_air_balloon
eyeglasses	bus	clock	camera	lollipop	helicopter
eyeglasses	bus	clock	map	lollipop	helicopter
eyeglasses	car	clock	camera	lollipop	helicopter
eyeglasses	car	clock	map	lollipop	helicopter
eyeglasses	envelope	crab	ambulance	lollipop	ice_cream
eyeglasses	envelope	crab	ambulance	donut	hot_air_balloon
eyeglasses	envelope	clock	octopus	lollipop	police_car
eyeglasses	envelope	clock	ambulance	lollipop	helicopter
eyeglasses	strawberry	crab	camera	lollipop	police_car
eyeglasses	strawberry	crab	map	lollipop	police_car
eyeglasses	strawberry	calculator	octopus	lollipop	police_car
eyeglasses	strawberry	calculator	ambulance	lollipop	helicopter
tree	bus	camel	camera	donut	helicopter
tree	bus	camel	map	donut	helicopter
tree	car	camel	camera	donut	helicopter
tree	car	camel	map	donut	helicopter	
umbrella	bus	camel	camera	donut	helicopter
umbrella	bus	camel	map	donut	helicopter
umbrella	car	camel	camera	donut	helicopter
umbrella	car	camel	map	donut	helicopter
tree	bus	crab	camera	bicycle	ice_cream
tree	bus	crab	camera	see_saw	ice_cream
tree	bus	crab	map	bicycle	ice_cream
tree	bus	crab	map	see_saw	ice_cream
tree	car	crab	camera	bicycle	ice_cream
tree	car	crab	camera	see_saw	ice_cream
tree	car	crab	map	bicycle	ice_cream
tree	car	crab	map	see_saw	ice_cream
umbrella	bus	crab	camera	bicycle	ice_cream
umbrella	bus	crab	camera	see_saw	ice_cream
umbrella	bus	crab	map	bicycle	ice_cream
umbrella	bus	crab	map	see_saw	ice_cream
umbrella	car	crab	camera	bicycle	ice_cream
umbrella	car	crab	camera	see_saw	ice_cream
umbrella	car	crab	map	bicycle	ice_cream
umbrella	car	crab	map	see_saw	ice_cream
tree	bus	calculator	octopus	bicycle	ice_cream
tree	bus	calculator	octopus	see_saw	ice_cream
tree	car	calculator	octopus	bicycle	ice_cream
tree	car	calculator	octopus	see_saw	ice_cream
umbrella	bus	calculator	octopus	bicycle	ice_cream
umbrella	bus	calculator	octopus	see_saw	ice_cream
umbrella	car	calculator	octopus	bicycle	ice_cream
umbrella	car	calculator	octopus	see_saw	ice_cream
tree	bus	clock	camera	bicycle	helicopter
tree	bus	clock	camera	see_saw	helicopter
tree	bus	clock	map	bicycle	helicopter
tree	bus	clock	map	see_saw	helicopter
tree	car	clock	camera	bicycle	helicopter
tree	car	clock	camera	see_saw	helicopter
tree	car	clock	map	bicycle	helicopter
tree	car	clock	map	see_saw	helicopter
umbrella	bus	clock	camera	bicycle	helicopter
umbrella	bus	clock	camera	see_saw	helicopter
umbrella	bus	clock	map	bicycle	helicopter
umbrella	bus	clock	map	see_saw	helicopter
umbrella	car	clock	camera	bicycle	helicopter
umbrella	car	clock	camera	see_saw	helicopter
umbrella	car	clock	map	bicycle	helicopter
umbrella	car	clock	map	see_saw	helicopter
tree	envelope	camel	octopus	donut	police_car
umbrella	envelope	camel	octopus	donut	police_car
tree	envelope	camel	ambulance	donut	helicopter
umbrella	envelope	camel	ambulance	donut	helicopter
tree	envelope	crab	ambulance	bicycle	ice_cream
tree	envelope	crab	ambulance	see_saw	ice_cream
umbrella	envelope	crab	ambulance	bicycle	ice_cream
umbrella	envelope	crab	ambulance	see_saw	ice_cream
tree	envelope	clock	octopus	bicycle	police_car
tree	envelope	clock	octopus	see_saw	police_car
umbrella	envelope	clock	octopus	bicycle	police_car
umbrella	envelope	clock	octopus	see_saw	police_car
tree	envelope	clock	ambulance	bicycle	helicopter
tree	envelope	clock	ambulance	see_saw	helicopter
umbrella	envelope	clock	ambulance	bicycle	helicopter
umbrella	envelope	clock	ambulance	see_saw	helicopter
tree	strawberry	crab	camera	bicycle	police_car
tree	strawberry	crab	camera	see_saw	police_car
tree	strawberry	crab	map	bicycle	police_car
tree	strawberry	crab	map	see_saw	police_car
umbrella	strawberry	crab	camera	bicycle	police_car
umbrella	strawberry	crab	camera	see_saw	police_car
umbrella	strawberry	crab	map	bicycle	police_car
umbrella	strawberry	crab	map	see_saw	police_car
tree	strawberry	calculator	octopus	bicycle	police_car
tree	strawberry	calculator	octopus	see_saw	police_car
umbrella	strawberry	calculator	octopus	bicycle	police_car
umbrella	strawberry	calculator	octopus	see_saw	police_car
tree	strawberry	calculator	ambulance	bicycle	helicopter
tree	strawberry	calculator	ambulance	see_saw	helicopter
umbrella	strawberry	calculator	ambulance	bicycle	helicopter
umbrella	strawberry	calculator	ambulance	see_saw	helicopter
spider	bus	camel	camera	lollipop	ice_cream
spider	bus	camel	map	lollipop	ice_cream
spider	car	camel	camera	lollipop	ice_cream
spider	car	camel	map	lollipop	ice_cream
spider	bus	camel	camera	donut	hot_air_balloon
spider	bus	camel	map	donut	hot_air_balloon
spider	car	camel	camera	donut	hot_air_balloon
spider	car	camel	map	donut	hot_air_balloon
spider	bus	clock	camera	bicycle	hot_air_balloon
spider	bus	clock	camera	see_saw	hot_air_balloon
spider	bus	clock	map	bicycle	hot_air_balloon
spider	bus	clock	map	see_saw	hot_air_balloon
spider	car	clock	camera	bicycle	hot_air_balloon
spider	car	clock	camera	see_saw	hot_air_balloon
spider	car	clock	map	bicycle	hot_air_balloon
spider	car	clock	map	see_saw	hot_air_balloon
spider	envelope	camel	ambulance	lollipop	ice_cream
spider	envelope	camel	ambulance	donut	hot_air_balloon
spider	envelope	clock	ambulance	bicycle	hot_air_balloon
spider	envelope	clock	ambulance	see_saw	hot_air_balloon
spider	strawberry	camel	camera	lollipop	police_car
spider	strawberry	camel	map	lollipop	police_car
spider	strawberry	calculator	ambulance	bicycle	hot_air_balloon
spider	strawberry	calculator	ambulance	see_saw	hot_air_balloon
""".strip()



# Hard mode rounds (from original sketch-original.js)
HARD_ROUNDS = [
    ['fish','eyeglasses','camel','see_saw','bicycle','shark'],
    ['palm_tree','hot_air_balloon','lollipop','mushroom','umbrella','penguin','tree'],
    ['spider','octopus','hedgehog','campfire','crab','helicopter'],
    ['ambulance','police_car','car','truck','bus'],
    ['radio','map','envelope','camera','calculator','laptop'],
    ['clock','donut','wheel','ice_cream','apple','strawberry'],
]


def sample_unique(arr, k, rng: Optional[random.Random] = None):
    rng = rng or random
    pool = arr.copy()
    out = []
    for _ in range(k):
        if not pool:
            break
        j = rng.randint(0, len(pool) - 1)
        out.append(pool.pop(j))
    return out

def parse_pools(pool_text, classes, per_round):
    pools = []
    for line in pool_text.split('\n'):
        if line.strip():
            row = [item.strip() for item in line.split('\t')]
            row = [c for c in row if c in classes]
            if len(row) >= min(per_round, 2):
                pools.append(row)
    return pools

POOLS = parse_pools(POOL_TEXT, CLASSES, PER_ROUND)


def _stable_dedupe(seq):
    # preserves order like JS arrays
    return list(dict.fromkeys(seq))

def _choice(seq, rng: random.Random):
    return seq[rng.randint(0, len(seq) - 1)]

# def _backfill_to_per_round(choices, prompt, rng: random.Random):
#     """
#     Ensure exactly PER_ROUND unique options, always including prompt.
#     Backfills from CLASSES if needed.
#     """
#     want = PER_ROUND
#     chosen = _stable_dedupe(list(choices))
#     if prompt not in chosen:
#         chosen.append(prompt)

#     # If oversized, keep prompt and sample others
#     if len(chosen) > want:
#         others = [c for c in chosen if c != prompt]
#         take = want - 1
#         picked_others = others if len(others) <= take else rng.sample(others, take)
#         out = picked_others + [prompt]
#         rng.shuffle(out)
#         return out

#     # If undersized, backfill from CLASSES
#     need = want - len(chosen)
#     if need > 0:
#         exclude = set(chosen)
#         pool = [c for c in CLASSES if c not in exclude]
#         extra = sample_unique(pool, min(need, len(pool)), rng=rng)
#         chosen += extra

#     rng.shuffle(chosen)
#     return chosen

def build_rounds(difficulty: str, *, seed: Optional[int] = None) -> Dict[str, List[List[str]]]:
    """
    Build rounds & prompts. Different every call by default.
    Pass a seed to reproduce (e.g., for debugging or replay).
    """
    rng = random.Random(seed) if seed is not None else random.Random()  # fresh per-game RNG

    if difficulty == 'hard':
        base = [row for row in HARD_ROUNDS if all(c in CLASSES for c in row)]
        # Ensure number of rounds aligns with NUM_ROUNDS
        if len(base) >= NUM_ROUNDS:
            base = rng.sample(base, NUM_ROUNDS)
        else:
            # If fewer templates than needed, cycle them
            base = [base[i % len(base)] for i in range(NUM_ROUNDS)]

        rounds, prompts = [], []
        for row in base:
            picked = sample_unique(row, min(PER_ROUND, len(row)), rng=rng)
            prompt = _choice(picked, rng)
            choices = list(picked)                       # CHANGED: no backfill
            if prompt not in choices:                    # (defensive; normally already included)
                choices.append(prompt)
            rng.shuffle(choices)                         # CHANGED: just shuffle
            rounds.append(choices)
            prompts.append(prompt)
        return {"rounds": rounds, "prompts": prompts}

    # easy/default
    if not POOLS:
        rounds, prompts = [], []
        for _ in range(NUM_ROUNDS):
            picked = sample_unique(CLASSES, min(PER_ROUND, len(CLASSES)), rng=rng)
            prompt = _choice(picked if picked else CLASSES, rng)
            choices = list(picked)                       # CHANGED: no backfill
            if prompt not in choices:                    # (defensive; normally already included)
                choices.append(prompt)
            rng.shuffle(choices)                         # CHANGED: just shuffle
            rounds.append(choices)
            prompts.append(prompt)
        return {"rounds": rounds, "prompts": prompts}

    # POOLS present → choose one base row, like the JS
    base_row = _choice(POOLS, rng)
    pool_set = _stable_dedupe([c for c in base_row if c in CLASSES])

    shuffled = pool_set[:]  # prompts should be distinct first, then cycle
    rng.shuffle(shuffled)
    unique_count = min(NUM_ROUNDS, len(shuffled))

    prompts = []
    for i in range(NUM_ROUNDS):
        if i < unique_count:
            prompts.append(shuffled[i])
        else:
            prompts.append(pool_set[i % len(pool_set)])  # cycle

    rounds = []
    for prompt in prompts:
        others = [x for x in pool_set if x != prompt]
        need = max(0, min(PER_ROUND - 1, len(others)))
        sampled = sample_unique(others, need, rng=rng)
        choices = sampled + [prompt]
        rng.shuffle(choices)
        rounds.append(choices)

    return {"rounds": rounds, "prompts": prompts}