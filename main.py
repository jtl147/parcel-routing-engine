from hash_table import ChainingHashTable
import csv
from dataclasses import dataclass
from typing import Optional
from distances import AddressIndex, DistanceMatrix
from router import Truck, route_truck
from datetime import timedelta, datetime, time
from simulator import simulate_day, print_summary
import re



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
    available_time: timedelta = timedelta(hours=0)
    correction_time: Optional[timedelta] = None
    corrected_street: Optional[str] = None


# ----- Data store -----
packages = ChainingHashTable(init_capacity=64)

# ----- Loaders -----
def _parse_deadline(s: str) -> Optional[time]:
    s = (s or "").strip()
    if not s or s.upper() == "EOD":
        return None
    return datetime.strptime(s, "%I:%M %p").time()

_TIME_RE = re.compile(r'(\d{1,2}:\d{2})\s*([AaPp][Mm])?')

def _parse_hhmm_from_text(text: str) -> Optional[time]:
    m = _TIME_RE.search(text)
    if not m:
        return None
    hhmm, ampm = m.group(1), m.group(2)
    if ampm:
        return datetime.strptime(f"{hhmm} {ampm.upper()}", "%I:%M %p").time()
    return datetime.strptime(hhmm, "%H:%M").time()

def _infer_constraints(pkg: Package) -> None:
    note = (pkg.notes or "").strip().lower()
    if "delay" in note:
        t = _parse_hhmm_from_text(note)
        if t:
            pkg.available_time = timedelta(hours=t.hour, minutes=t.minute)
    if "wrong address" in note or "address corrected" in note or "corrected at" in note:
        t = _parse_hhmm_from_text(note)
        if t:
            pkg.correction_time = timedelta(hours=t.hour, minutes=t.minute)
            pkg.available_time = max(pkg.available_time, pkg.correction_time)
        if " to " in (pkg.notes or ""):
            try:
                pkg.corrected_street = pkg.notes.split(" to ", 1)[1].strip()
            except Exception:
                pkg.corrected_street = None

    m = re.search(r"\bto\b\s*(.+)$", pkg.notes or "", flags=re.IGNORECASE)
    if m:
        pkg.corrected_street = m.group(1).strip()

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
            _infer_constraints(pkg)
            packages.insert(pkg.id, pkg)

# ----- Reset Package Status -----
def reset_package_statuses():
    for pid, pkg in packages.items():
        pkg.status = "At the hub"
        pkg.departure_time = None
        pkg.delivery_time = None
        pkg.truck_id = None

def apply_scenario_overrides() -> None:
    """
    Encode rubric assumptions:
    - Pkgs 6,25,28,32 are not available until 9:05
    - Pkg 9 has wrong address corrected at 10:20; corrected street is 410 S State St
    """
    for pid in (6, 25, 28, 32):
        p = packages.search(pid)
        if p:
            p.available_time = timedelta(hours=9, minutes=5)

    p9 = packages.search(9)
    if p9:
        p9.correction_time = timedelta(hours=10, minutes=20)
        p9.available_time = max(p9.available_time, p9.correction_time)
        p9.corrected_street = "410 S State St"


# ----- Console Helpers -----
def parse_query_time(s: str) -> timedelta:
    s = s.strip()
    if "AM" in s.upper() or "PM" in s.upper():
        t = datetime.strptime(s.upper(), "%I:%M %p").time()
    else:
        t = datetime.strptime(s, "%H:%M").time()
    return timedelta(hours=t.hour, minutes=t.minute)

def fmt_time(td: Optional[timedelta]) -> str:
    if td is None:
        return "N/A"
    return (datetime(2000, 1, 1) + td).strftime("%I:%M %p")

def address_at_time(pkg: Package, query: timedelta) -> str:
    if pkg.correction_time is not None and pkg.corrected_street:
        if query >= pkg.correction_time:
            return pkg.corrected_street
    return pkg.street

def status_at_time(pkg: Package, query: timedelta) -> str:
    if query < pkg.available_time:
        return "DELAYED"
    if pkg.delivery_time and query >= pkg.delivery_time:
        return f"Delivered at {fmt_time(pkg.delivery_time)}"
    if pkg.departure_time and pkg.departure_time <= query:
        return "En route"
    return "At the hub"

# ----- Main -----
def main():
    load_packages_csv("data/packageCSV.csv")
    print("\nHash Table Contents:")
    packages.print_table()

    index = load_address_index("data/addressCSV.csv")
    matrix = load_distance_matrix("data/distanceCSV.csv")

    print("Loaded packages:", packages.search(1) is not None, packages.search(2) is not None)

    hub_addr = "4001 South 700 East"
    sample_pkg = packages.search(1)
    if sample_pkg:
        d = matrix.distance_between_addresses(hub_addr, sample_pkg.street, index)
        print(f"Distance HUB -> Package 1 address: {d:.1f} miles")

    loads = {
        1: [1, 29, 7, 30, 8, 34, 40, 14, 15, 16, 19, 20, 13, 37, 38, 36],
        2: [3, 18, 6, 28, 32, 33, 25, 12, 9, 22, 24, 11, 10, 5, 4, 21],
        3: [2, 17, 23, 26, 27, 31, 35, 39],
    }

    holds = {
        2: timedelta(hours=9, minutes=5),
        3: timedelta(hours=11, minutes=0),
    }

    reset_package_statuses()
    apply_scenario_overrides()

    result = simulate_day(packages, index, matrix, loads, holds)
    print_summary(result)

    for pid in [1, 2, 3]:
        p = packages.search(pid)
        if p:
            print(f"Pkg {pid} delivered at {p.delivery_time}")

    # ----- Console Menu -----
    while True:
        print("\nMenu:")
        print("1) Status of a single package at a time")
        print("2) Status of all packages at a time")
        print("3) Summary (truck miles and total)")
        print("4) Exit")
        choice = input("Choose an option (1-4): ").strip()

        if choice == "1":
            try:
                pid = int(input("Enter package ID: ").strip())
                q = parse_query_time(input("Enter time (e.g., 9:15 AM or 13:45): "))
                pkg = packages.search(pid)
                if not pkg:
                    print("Package not found.")
                    continue
                print(f"Package {pid} | Truck {pkg.truck_id if pkg.truck_id else 'N/A'}")
                print(f"Address at {fmt_time(q)}: {address_at_time(pkg, q)}")
                print(f"Status at {fmt_time(q)}: {status_at_time(pkg, q)}")

            except Exception as e:
                print("Error:", e)

        elif choice == "2":
            try:
                q = parse_query_time(input("Enter time (e.g., 9:15 AM or 13:45): "))
                for pid, pkg in sorted(packages.items(), key=lambda kv: kv[0]):
                    addr = address_at_time(pkg, q)
                    status = status_at_time(pkg, q)
                    truck = pkg.truck_id if pkg.truck_id else "N/A"
                    print(f"Package {pid} | Truck {truck} | {addr} | {status}")
            except Exception as e:
                print("Error:", e)

        elif choice == "3":
            print_summary(result)

        elif choice == "4":
            print("Goodbye.")
            break

        else:
            print("Invalid choice.")

# ----- Helpers -----
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
