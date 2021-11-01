"""implements resource class"""


class Resources:
    """manages different resource collections(like inventory)"""

    def __init__(self):
        self.resdict = {}

    def modify(self, resource: str, amount: int):
        """adds or removes resources"""
        if resource in self.resdict:
            self.resdict[resource] += amount
        else:
            self.resdict[resource] = amount

    def get(self, resource):
        """gets amount of resources"""
        return self.resdict[resource]

    def zero(self, resource: str):
        """sets resource to zero"""
        self.resdict[resource] = 0

    def set(self, resource: str, amount: int):
        """set resource to amount"""
        self.resdict[resource] = amount

    def list(self):
        """lists resources"""
        return list(self.resdict.keys())

    def save(self) -> dict:
        """returns dict representation"""
        return self.resdict


def load(resdict: dict) -> Resources:
    """load from dict representation"""
    res = Resources()
    res.resdict = resdict

    return res
