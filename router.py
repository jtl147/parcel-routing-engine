# Author: Jedi Lee
# Student ID: 012594297

from dataclasses import dataclass, field
from datetime import datetime, timedelta, time
from typing import List, Tuple, Optional
from hash_table import ChainingHashTable
from distances import AddressIndex, DistanceMatrix

HUB_ADDR = "4001 South 700 East"

@dataclass
class Truck:
    """
    A minimal truck state used by the greedy router.
      - id:             1..3
      - speed_mph:      18 mph
      - capacity:       16 packages max
      - start_time:     when the truck is allowed to leave (supports holding at hub)
      - current_addr:   where the truck is right now (starts at HUB)
      - clock:          simulated time-of-day
      - miles:          miles accrued so far
      - load:           package IDs loaded for this run
    """
    id: int
    speed_mph: float = 18.0
    capacity: int = 16
    start_time: timedelta = timedelta(hours=8)
    current_addr: str = HUB_ADDR
    clock: timedelta = timedelta(hours=8)
    miles: float = 0.0
    load: List[int] = field(default_factory=list)

def travel_time(miles: float, mph: float) -> timedelta:
    # Convert miles and mph to travel duration
    return timedelta(hours=miles / mph) if mph > 0 else timedelta(0)

def _would_miss_deadline(current_clock: timedelta, travel_hours: float, deadline: Optional[time]) -> bool:
    """
    Helper: determine if arrival would be later than a package's deadline.
    We anchor both to the same base date for comparison.
    """
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
    URGENCY = timedelta(minutes=15)
    urgent_pick = None
    urgent_dist = float("inf")
    best_on_pid, best_on_dist = None, float("inf")
    best_any_pid, best_any_dist = None, float("inf")

    for pid in remaining_pkg_ids:
        pkg = packages.search(pid)
        if not pkg:
            continue
        if current_clock < getattr(pkg, "available_time", timedelta(0)):
            continue

        addr = pkg.street
        corr_time = getattr(pkg, "correction_time", None)
        corr_street = getattr(pkg, "corrected_street", None)
        if corr_time is not None and corr_street and current_clock >= corr_time:
            addr = corr_street

        d = matrix.distance_between_addresses(current_addr, addr, index)
        travel_hours = d / 18.0

        if d < best_any_dist:
            best_any_pid, best_any_dist = pid, d

        if not _would_miss_deadline(current_clock, travel_hours, pkg.deadline_time):
            if d < best_on_dist:
                best_on_pid, best_on_dist = pid, d
            if pkg.deadline_time is not None:
                base = datetime(2000, 1, 1)
                arrival_dt = base + current_clock + timedelta(hours=travel_hours)
                deadline_dt = datetime.combine(base.date(), pkg.deadline_time)
                slack = deadline_dt - arrival_dt
                if slack <= URGENCY and d < urgent_dist:
                    urgent_pick, urgent_dist = pid, d

    if urgent_pick is not None:
        return urgent_pick, urgent_dist
    if best_on_pid is not None:
        return best_on_pid, best_on_dist
    if best_any_pid is not None:
        return best_any_pid, best_any_dist
    return None, 0.0


def route_truck(
    truck: Truck,
    pkg_ids: List[int],
    packages: ChainingHashTable,
    index: AddressIndex,
    matrix: DistanceMatrix,
) -> None:
    """
    Greedy nearest-neighbor loop:
      1) Initialize truck state (start at HUB at start_time).
      2) Mark any already-available packages as 'En route' with departure_time.
      3) While remaining packages:
            - pick nearest feasible next stop
            - advance miles & time; mark package delivered
      4) Return to HUB and finish.

    This respects: capacity, delayed availability, address correction time, and deadlines.
    """
    # Load packages and set the clock to start_time
    truck.load = pkg_ids[: truck.capacity]
    truck.clock = truck.start_time
    truck.current_addr = HUB_ADDR

    # Tag initial 'En route' for any packages immediately available at departure
    for pid in truck.load:
        pkg = packages.search(pid)
        if pkg:
            pkg.truck_id = truck.id

    remaining = truck.load.copy()

    # Main routing loop
    while remaining:
        next_pid, dist = _nearest_next(truck.current_addr, truck.clock, remaining, packages, index, matrix)

        # If we identified a next package that is just now becoming available, mark its depart time
        pkg = packages.search(next_pid)
        if pkg and pkg.departure_time is None and truck.clock >= getattr(pkg, "available_time", timedelta(0)):
            pkg.departure_time = truck.clock
            pkg.status = "En route"

        # No feasible next stop — break to avoid infinite loop
        if next_pid is None:
            # find next availability or correction time in the future
            next_events = []
            for pid in remaining:
                pkg = packages.search(pid)
                if not pkg:
                    continue
                avail = getattr(pkg, "available_time", None)
                if avail is not None and avail > truck.clock:
                    next_events.append(avail)
                corr_t = getattr(pkg, "correction_time", None)
                if corr_t is not None and corr_t > truck.clock:
                    next_events.append(corr_t)
            if next_events:
                truck.clock = min(next_events)
                continue
            else:
                break
        # Travel to next stop
        truck.miles += dist
        truck.clock += travel_time(dist, truck.speed_mph)

        # Deliver and stamp delivery time and final address
        pkg = packages.search(next_pid)
        if pkg:
            addr = pkg.street
            corr_time = getattr(pkg, "correction_time", None)
            corr_street = getattr(pkg, "corrected_street", None)
            if corr_time is not None and corr_street and truck.clock >= corr_time:
                addr = corr_street
            truck.current_addr = addr
            pkg.delivery_time = truck.clock
            pkg.status = "Delivered"
        remaining.remove(next_pid)

    # Return to hub after finishing last stop
    if truck.current_addr != HUB_ADDR:
        back = matrix.distance_between_addresses(truck.current_addr, HUB_ADDR, index)
        truck.miles += back
        truck.clock += travel_time(back, truck.speed_mph)
        truck.current_addr = HUB_ADDR
