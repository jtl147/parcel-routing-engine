# Author: Jedi Lee
# Student ID: 012594297

from hash_table import ChainingHashTable
import csv
from dataclasses import dataclass
from typing import Optional

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
    departure_time: Optional[str] = None
    delivery_time: Optional[str] = None
    truck_id: Optional[int] = None

# ----- Data store -----
packages = ChainingHashTable(init_capacity=64)

# ----- Loaders -----
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
            )
            packages.insert(pkg.id, pkg)

# ----- Main -----
def main():
    load_packages_csv("data/packageCSV.csv")

    a = packages.search(1)
    b = packages.search(2)
    print("Loaded packages:", 1 if a else None, 2 if b else None)

if __name__ == "__main__":
    main()
