# Author: Jedi Lee
# Student ID: 012594297

import csv
from typing import Dict, List

class AddressIndex:
    """
    Maps human-readable street addresses <-> numeric node IDs used by the distance matrix.

    Why:
      - The WGUPS distance table is organized by row/column indices.
      - We normalize and store each address once, then look up node IDs in O(1).

    Process/Flow:
      - load(): read addressCSV, build two maps:
          addr_to_node: "410 S State St" -> 9
          node_to_addr: 9 -> "410 S State St"
      - node_for(): get ID for an address
      - address_for(): get address for an ID
    """
    def __init__(self) -> None:
        self.addr_to_node: Dict[str, int] = {}
        self.node_to_addr: List[str] = []

    @staticmethod
    def _normalize(addr: str) -> str:
        # Normalization for consistent keys
        return addr.strip()

    def load(self, path: str) -> None:
        # Parse CSV rows and populate both maps. Non-numeric row[0] are headers and are skipped.
        rows = list(csv.reader(open(path, newline="")))
        for row in rows:
            try:
                node = int(row[0])
            except ValueError:
                continue
            addr = self._normalize(row[2])
            while len(self.node_to_addr) <= node:
                self.node_to_addr.append("")
            self.node_to_addr[node] = addr
            self.addr_to_node[addr] = node

    def node_for(self, address: str) -> int:
        # Translate an address to its node index for matrix lookups
        return self.addr_to_node[self._normalize(address)]

    def address_for(self, node: int) -> str:
        # Translate a node index back to its canonical address string
        return self.node_to_addr[node]


class DistanceMatrix:
    """
    Stores a fully symmetric miles matrix.

    Why:
      - WGUPS CSV provides one direction; we mirror to make lookups O(1) for any (i, j).

    Process/Flow:
      - load(): build a square matrix of floats, copy lower triangle to upper
      - get(): return miles by node IDs
      - distance_between_addresses(): convenience wrapper using AddressIndex
    """
    def __init__(self) -> None:
        self._miles: List[List[float]] = []

    def load(self, path: str) -> None:
        rows = list(csv.reader(open(path, newline="")))
        n = len(rows)
        self._miles = [[0.0 for _ in range(n)] for _ in range(n)]

        # Fill whatever the CSV has
        for i in range(n):
            for j in range(len(rows[i])):
                cell = rows[i][j].strip()
                if cell:
                    self._miles[i][j] = float(cell)

        # Mirror to ensure symmetry and zero diagonal
        for i in range(n):
            for j in range(n):
                if i == j:
                    self._miles[i][j] = 0.0
                elif self._miles[i][j] == 0.0 and self._miles[j][i] != 0.0:
                    self._miles[i][j] = self._miles[j][i]

    def get(self, i: int, j: int) -> float:
        return self._miles[i][j]

    def distance_between_addresses(self, a: str, b: str, index: AddressIndex) -> float:
        # Convert both addresses to nodes, then fetch miles in O(1)
        return self.get(index.node_for(a), index.node_for(b))
