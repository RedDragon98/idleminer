"""implments resource class"""


class Resources:  # TODO
    """manages different resource collections(like inventory)"""

    def __init__(self):
        pass

    def modify(self, resource: str, amount: int):
        """adds or removes resources"""

    def save(self) -> dict:
        """returns dict representation"""


def load(resdict: dict) -> Resources:
    """load from dict representation"""
