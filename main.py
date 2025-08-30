from hash_table import ChainingHashTable
import csv
from dataclasses import dataclass
from typing import Optional
from distances import AddressIndex, DistanceMatrix
from router import Truck, route_truck
from datetime import timedelta, datetime, time
from simulator import simulate_day, print_summary



# ----- Models -----
@dataclass
class Package:
    id: int
    street: str
    city: str
    state: str
    zip: str
    deadline: str
    weight: str
    notes: str
    status: str = "At the hub"
    deadline_time: Optional[time] = None
    departure_time: Optional[timedelta] = None
    delivery_time: Optional[timedelta] = None
    truck_id: Optional[int] = None


# ----- Data store -----
packages = ChainingHashTable(init_capacity=64)

# ----- Loaders -----
def _parse_deadline(s: str) -> Optional[time]:
    s = (s or "").strip()
    if not s or s.upper() == "EOD":
        return None
    return datetime.strptime(s, "%I:%M %p").time()

def load_packages_csv(path: str) -> None:
    """Load packageCSV.csv and insert Package into hash table."""
    with open(path, newline="") as f:
        reader = csv.reader(f)
        next(reader)
        for row in reader:
            pkg = Package(
                id=int(row[0]),
                street=row[1],
                city=row[2],
                state=row[3],
                zip=row[4],
                deadline=row[5],
                weight=row[6],
                notes=row[7],
                deadline_time=_parse_deadline(row[5]),
            )
            packages.insert(pkg.id, pkg)

# ----- Reset Package Status -----
def reset_package_statuses():
    for pid, pkg in packages.items():
        pkg.status = "At the hub"
        pkg.departure_time = None
        pkg.delivery_time = None
        pkg.truck_id = None

# ----- Main -----
def main():
    load_packages_csv("data/packageCSV.csv")

    index = load_address_index("data/addressCSV.csv")
    matrix = load_distance_matrix("data/distanceCSV.csv")

    print("Loaded packages:", packages.search(1) is not None, packages.search(2) is not None)

    hub_addr = "4001 South 700 East"
    sample_pkg = packages.search(1)
    if sample_pkg:
        d = matrix.distance_between_addresses(hub_addr, sample_pkg.street, index)
        print(f"Distance HUB -> Package 1 address: {d:.1f} miles")

    loads = {
        1: [1, 2, 3, 4, 5, 6, 7, 8],
        2: [9, 10, 11, 12, 13, 14, 15, 16],
        3: [17, 18, 19, 20, 21, 22, 23, 24],
    }

    holds = {
    }

    reset_package_statuses()
    result = simulate_day(packages, index, matrix, loads, holds)
    print_summary(result)

    for pid in [1, 2, 3]:
        p = packages.search(pid)
        if p:
            print(f"Pkg {pid} delivered at {p.delivery_time}")


def load_address_index(path: str) -> AddressIndex:
    idx = AddressIndex()
    idx.load(path)
    return idx

def load_distance_matrix(path: str) -> DistanceMatrix:
    dm = DistanceMatrix()
    dm.load(path)
    return dm


if __name__ == "__main__":
    main()
