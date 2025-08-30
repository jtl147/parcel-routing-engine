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
    Simulate a day with up to 3 trucks, 2 drivers active at a time.

    loads: {truck_id: [pkg_ids]}
    hold_at_hub_until: optional per-truck release times

    Returns:
        {
          "trucks": {1: truck1, 2: truck2, 3: truck3},
          "total_miles": float
        }
    """
    t1 = Truck(id=1, start_time=HUB_START)
    t2 = Truck(id=2, start_time=HUB_START)
    t3 = Truck(id=3, start_time=HUB_START)

    trucks = {1: t1, 2: t2, 3: t3}

    if hold_at_hub_until:
        for tid, ts in hold_at_hub_until.items():
            if tid in trucks:
                trucks[tid].start_time = ts
                trucks[tid].clock = ts

    if 1 in loads and loads[1]:
        route_truck(t1, loads[1], packages, index, matrix)

    if 2 in loads and loads[2]:
        route_truck(t2, loads[2], packages, index, matrix)

    if 3 in loads and loads[3]:
        driver_free_time = min(t1.clock, t2.clock)
        if t3.start_time < driver_free_time:
            t3.start_time = driver_free_time
            t3.clock = driver_free_time
        route_truck(t3, loads[3], packages, index, matrix)

    total_miles = sum(tr.miles for tr in trucks.values())

    return {"trucks": trucks, "total_miles": total_miles}


def print_summary(sim_result: Dict) -> None:
    trucks = sim_result["trucks"]
    total = sim_result["total_miles"]
    for tid, tr in trucks.items():
        print(f"Truck {tid}: miles={tr.miles:.1f}, finished at {tr.clock}")
    print(f"TOTAL MILES: {total:.1f}")
