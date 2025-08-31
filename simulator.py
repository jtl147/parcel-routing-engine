# Author: Jedi Lee
# Student ID: 012594297

from datetime import timedelta
from typing import Dict, List

from hash_table import ChainingHashTable
from router import Truck, route_truck
from distances import AddressIndex, DistanceMatrix

HUB_START = timedelta(hours=8)

def simulate_day(
    packages: ChainingHashTable,
    index: AddressIndex,
    matrix: DistanceMatrix,
    loads: Dict[int, List[int]],
    hold_at_hub_until: Dict[int, timedelta] | None = None,
) -> Dict:
    """
    Orchestrates up to 3 trucks with 2 drivers active at a time.

    Inputs:
      - loads:             {truck_id: [package_ids]} (manual staging that satisfies constraints)
      - hold_at_hub_until: optional per-truck 'start gates'

    Flow:
      1) Create 3 Truck objects (clock=start_time by default 8:00).
      2) Apply any per-truck hold overrides (start_time/clock).
      3) Route Truck 1 and Truck 2 immediately (two drivers).
      4) When a driver is free (min(t1.clock, t2.clock)), start Truck 3 if needed.
      5) Return total mileage and the truck objects for reporting.
    """
    t1 = Truck(id=1, start_time=HUB_START)
    t2 = Truck(id=2, start_time=HUB_START)
    t3 = Truck(id=3, start_time=HUB_START)

    trucks = {1: t1, 2: t2, 3: t3}

    # Optional holds
    if hold_at_hub_until:
        for tid, ts in hold_at_hub_until.items():
            if tid in trucks:
                trucks[tid].start_time = ts
                trucks[tid].clock = ts

    # Two drivers active: run 1 and 2 in parallel
    if 1 in loads and loads[1]:
        route_truck(t1, loads[1], packages, index, matrix)

    if 2 in loads and loads[2]:
        route_truck(t2, loads[2], packages, index, matrix)

    # Truck 3 waits until one driver returns
    if 3 in loads and loads[3]:
        driver_free_time = min(t1.clock, t2.clock)
        if t3.start_time < driver_free_time:
            t3.start_time = driver_free_time
            t3.clock = driver_free_time
        route_truck(t3, loads[3], packages, index, matrix)

    total_miles = sum(tr.miles for tr in trucks.values())

    return {"trucks": trucks, "total_miles": total_miles}


def print_summary(sim_result: Dict) -> None:
    """
    Console helper for Task 2 outputs: per-truck miles/finish times and grand total.
    """
    trucks = sim_result["trucks"]
    total = sim_result["total_miles"]
    for tid, tr in trucks.items():
        print(f"Truck {tid}: miles={tr.miles:.1f}, finished at {tr.clock}")
    print(f"TOTAL MILES: {total:.1f}")
