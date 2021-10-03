import random
import threading
import json
import time

prefix = "%"  # command prefix
tickbooster = 1.0  # TPS booster

datapath = "data/"  # data file path


def dataload(file):  # 0loads data files
    return json.load(open(datapath + file))


class colors:  # printing colors
    HEADER = '\033[95m'
    INFO2 = '\033[94m'
    INFO = '\033[96m'
    SUCCESS = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


prices = dataload("prices.json")  # item prices
mines = dataload("mines.json")  # mining chances

pticks = dataload("ticks.json")  # ticks (based on pickaxe level)
biomes = dataload("biomes.json")  # biome list

errmsg = "Invalid command"  # error during parsing
costmsg = "You don't have enough money (upgraded till max)"  # money ran out
upmsg = "Your %s level is %s, type is %s"
notintmsg = "Value should be an integer"
mineupmsg = "Upgraded mine to level %s"
newbiomemsg = "Biome switched to %s"
shouldexit = False  # should main thread exit
ticks = 1  # TPS

UP_P_MULIPLIER = 210  # upgrading pickaxe costs UP_P_MULTIPLIER * level


def colorprint(msg, esc="", color=""):  # prints with a color
    print(color + msg + colors.ENDC + esc)


def progressbar(num, cap, partitions=20):  # progressbar ####--
    dashes = round(num / (cap / partitions))
    for i in range(partitions):
        if i < dashes:
            print("#", end="")
        else:
            print("-", end="")
    print(" (" + str(num) + "/" + str(cap) + ")")


def getrank(level):
    if level >= 200:
        return "netherite"
    elif level >= 150:
        return "diamond"
    elif level >= 100:
        return "gold"
    elif level >= 50:
        return "iron"
    elif level >= 25:
        return "stone"
    elif level >= 0:
        return "wooden"

    return "impossible"


def getpticks(rank):
    return pticks[rank]


class CommandParser():
    def get(self, prompt=">"):
        """returns a parsed command [command, args, args...]"""
        cmd = input(prompt)
        parsed = self.parse(cmd)
        if len(parsed) == 1:
            return parsed[0]
        else:
            return parsed

    def parse(self, data: str):
        """parses a command"""
        if data.strip() == "":
            return "???"

        data = data.strip(prefix)
        return data.split(" ")


class IdleMiner:
    def __init__(self):
        self.cmdparse = CommandParser()
        self.money = 0  # money
        self.shards = 0  # shards for pets
        self.rc = 0  # rebirth coins
        self.huntchance = 10  # chance of pet
        self.fishchance = 0  # chance of fish
        self.biome = "plains"  # current biome
        self.biomeid = 0  # current biome index in biome list
        self.basebpsize = 50  # base backpck size
        self.bpsizebooster = 1.0  # backpack size booster
        self.sellbooster = 1.0  # booster for sell prices
        self.minelevel = 1  # current mine level in biome
        self.blocksmined = 0  # blocks mined in this mine level
        self.inventory = {  # IdleMiner's inventory
            "dirt": 0,
            "wood": 0,
            "stone": 0,
            "coal": 0,
            "iron": 0,
            "diorite": 0,
            "andesite": 0,
        }
        self.tools = {  # tool levels
            "p": 0
        }

    def get(self, prefix):
        self.execute(self.cmdparse.get(prefix))

    def sell(self):
        for item in list(self.inventory.keys()):
            if self.inventory[item] > 0:
                money = round(self.inventory[item] *
                              prices[item] * self.sellbooster)
                colorprint(item, ": " + "$" + f"{money:,}" +
                           " (x" + f"{self.inventory[item]:,}" + ")", colors.BOLD)
                self.money += money
                self.inventory[item] = 0

    def up(self, tool, amount):
        match tool:
            case "p" | "pickaxe":  # rebirth = level >= 200
                global ticks
                for i in range(amount):
                    price = self.tools["p"] * UP_P_MULIPLIER
                    if price <= self.money:
                        self.tools["p"] += 1
                        self.money -= price
                    else:
                        colorprint(costmsg, color=colors.WARNING)
                        break

                ticks = getpticks(getrank(self.tools["p"]))
                print(upmsg %
                      ("pickaxe", self.tools["p"], getrank(self.tools["p"])))
            case "s" | "shovel":  # rebirth = level >= 200
                pass
            case "a" | "axe":  # rebirth = level >= 200
                pass
            case "w" | "sword":  # w = weapon
                pass
            case "d" | "shield":  # d = defense
                pass
            case "e" | "enchanting-table":
                pass
            case "b" | "boots":
                pass
            case "l" | "leggings":
                pass
            case "c" | "chestplate":
                pass
            case "h" | "helmet":
                pass
            case "t" | "tnt":
                pass
            case _:
                colorprint(errmsg + " (in IdleMiner.up)", color=colors.WARNING)

    def miningtick(self):
        num = random.randint(1, 100)
        for i in mines[self.biome][self.minelevel].keys():
            if num > 100 - mines[self.biome][self.minelevel][i]:
                self.inventory[i] += 1
                self.blocksmined += 1

    def update(self):
        if self.blocksmined > 2000 * self.minelevel:
            self.minelevel += 1
            self.blocksmined = 0
            if mines[self.biome][self.minelevel] == "nextlevel":
                self.biomeid += 1
                self.biome = biomes[self.biomeid]
                self.minelevel = 1

                print(newbiomemsg % self.biome)
            else:
                print(mineupmsg % self.minelevel)

    def execute(self, cmd):
        match cmd:
            case "sell" | "s":
                self.sell()
            case "mine":
                pass
            case "level":
                pass
            case["upgrade" | "up" | "u", tool, amount]:
                try:
                    int(amount)
                except:
                    colorprint(notintmsg, color=colors.FAIL)
                else:
                    self.up(tool, int(amount))
            case "fish" | "f":
                pass
            case "hunt" | "h":
                pass
            case "profile" | "p":
                print("money: $" + f"{self.money:,}")
                print("backpack:", self.inventory)
                print("tools:", self.tools)
                print("mine level:", self.minelevel)
                print("blocks until next level:", end=" ")
                progressbar(self.blocksmined, self.minelevel * 2000)
            case "quiz":
                pass
            case "exit":
                global shouldexit
                shouldexit = True
            case "cheat":  # for easy testing, should be disabled later
                self.money += 5000000
                self.blocksmined += 2000
            case _:
                colorprint(errmsg + " (in IdleMiner.execute)",
                           color=colors.WARNING)


if __name__ == "__main__":
    steve = IdleMiner()

    def repeatedget():
        while not shouldexit:
            steve.get(">")

    inputthread = threading.Thread(target=repeatedget)
    inputthread.daemon = True
    inputthread.start()

    # background tasks(miningtick(), and update())
    # also exits if needed
    while True:
        if shouldexit:
            exit(0)

        else:
            time.sleep(1 / ticks)
            steve.miningtick()
            steve.update()
