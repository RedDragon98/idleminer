"""IdleMiner: story mode"""
import idleminer
import eventsys


def main():
    """runs the story mode program"""
    alex = idleminer.IdleMiner()

    eventsys.call("open", alex)

    # TODO


if __name__ == "__main__":
    main()
