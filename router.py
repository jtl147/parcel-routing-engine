from dataclasses import dataclass, field
from datetime import datetime, timedelta, time
from typing import List, Tuple, Optional
from hash_table import ChainingHashTable
from distances import AddressIndex, DistanceMatrix

HUB_ADDR = "4001 South 700 East"

@dataclass
class Truck:
    id: int
    speed_mph: float = 18.0
    capacity: int = 16
    start_time: timedelta = timedelta(hours=8)
    current_addr: str = HUB_ADDR
    clock: timedelta = timedelta(hours=8)
    miles: float = 0.0
    load: List[int] = field(default_factory=list)

def travel_time(miles: float, mph: float) -> timedelta:
    return timedelta(hours=miles / mph) if mph > 0 else timedelta(0)

def _would_miss_deadline(current_clock: timedelta, travel_hours: float, deadline: Optional[time]) -> bool:
    """Return True if arriving after the package's deadline."""
    if deadline is None:
        return False
    base = datetime(2000, 1, 1)
    arrival_dt = base + current_clock + timedelta(hours=travel_hours)
    deadline_dt = datetime.combine(base.date(), deadline)
    return arrival_dt > deadline_dt

def _nearest_next(
    current_addr: str,
    current_clock: timedelta,
    remaining_pkg_ids: List[int],
    packages: ChainingHashTable,
    index: AddressIndex,
    matrix: DistanceMatrix,
) -> Tuple[Optional[int], float]:
    """Return (next_package_id, distance) with shortest feasible distance from current_addr."""
    best_pid: Optional[int] = None
    best_dist: float = float("inf")
    for pid in remaining_pkg_ids:
        pkg = packages.search(pid)
        if not pkg:
            continue
        d = matrix.distance_between_addresses(current_addr, pkg.street, index)
        travel_hours = d / 18.0
        if _would_miss_deadline(current_clock, travel_hours, pkg.deadline_time):
            continue
        if d < best_dist:
            best_dist = d
            best_pid = pid
    return best_pid, (0.0 if best_pid is None else best_dist)


def route_truck(
    truck: Truck,
    pkg_ids: List[int],
    packages: ChainingHashTable,
    index: AddressIndex,
    matrix: DistanceMatrix,
) -> None:
    """
    Greedy nearest-neighbor loop:
    - Start at HUB
    - Repeatedly choose the nearest next package address among remaining
    - Move truck, advance time, mark package delivered
    - Return to HUB when done
    """
    truck.load = pkg_ids[: truck.capacity]
    truck.clock = truck.start_time
    truck.current_addr = HUB_ADDR

    for pid in truck.load:
        pkg = packages.search(pid)
        if pkg:
            pkg.truck_id = truck.id
            pkg.departure_time = truck.clock
            pkg.status = "En route"

    remaining = truck.load.copy()

    while remaining:
        next_pid, dist = _nearest_next(truck.current_addr, truck.clock, remaining, packages, index, matrix)
        if next_pid is None:
            break
        truck.miles += dist
        truck.clock += travel_time(dist, truck.speed_mph)
        pkg = packages.search(next_pid)
        if pkg:
            truck.current_addr = pkg.street
            pkg.delivery_time = truck.clock
            pkg.status = "Delivered"
        remaining.remove(next_pid)

    if truck.current_addr != HUB_ADDR:
        back = matrix.distance_between_addresses(truck.current_addr, HUB_ADDR, index)
        truck.miles += back
        truck.clock += travel_time(back, truck.speed_mph)
        truck.current_addr = HUB_ADDR
