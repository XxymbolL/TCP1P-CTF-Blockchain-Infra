import hashlib
import os

VERSION = "s"

class Challenge:
    def __init__(self, d, prefix):
        self.d = d
        self.prefix = prefix

    @classmethod
    def generate(cls, d=5):
        return cls(d, os.urandom(8).hex())

    @classmethod
    def from_string(cls, v):
        parts = v.split(".", 2)
        if len(parts) != 3 or parts[0] != VERSION:
            raise ValueError("Incorrect version")
        return cls(int(parts[1]), parts[2])

    def __str__(self):
        return f"{VERSION}.{self.d}.{self.prefix}"

    def solve(self):
        i = 0
        target = "0" * self.d
        while True:
            if hashlib.sha256(f"{self.prefix}{i}".encode()).hexdigest().startswith(target):
                return f"{VERSION}.{i}"
            i += 1


def check(challenge, s):
    parts = s.split(".", 1)
    if len(parts) != 2 or parts[0] != VERSION:
        return False
    i = int(parts[1])
    return hashlib.sha256(f"{challenge.prefix}{i}".encode()).hexdigest().startswith("0" * challenge.d)
