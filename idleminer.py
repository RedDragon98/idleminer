import random
import threading
import json
import time

prefix = "%"  # prefix that commands should start with
tickbooster = 1.0  # multiplies TPS

datapath = "data/"  # path to find the data files


def dataload(file):  # function to load data
    return json.load(open(datapath + file))


class colors:  # colors to print with
    HEADER = '\033[95m'
    INFO2 = '\033[94m'
    INFO = '\033[96m'
    SUCCESS = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


prices = dataload("prices.json")  # data file for item prices
mines = dataload("mines.json")  # data file for mine chances

pticks = dataload("ticks.json")  # data file for ticks(based on pickaxe level)
biomes = dataload("biomes.json")

errmsg = "Invalid command"  # when we hit a error during command parsing
# when you run out of money while upgrading
costmsg = "You don't have enough money (upgraded till max)"
upmsg = "Your %s level is %s, type is %s"  # shown after upgraading
# error message if value isn't an integer
notintmsg = "Value should be an integer"
mineupmsg = "Upgraded mine to level %s"  # shown after upgrading mine
newbiomemsg = "Biome switched to %s"  # shown after biome switches
shouldexit = False  # should main thread exit
ticks = 1  # TPS

UP_P_MULIPLIER = 200  # upgrading pickaxe costs UP_P_MULTIPLIER * level


def colorprint(msg, esc="", color=""):  # prints with a color from the colors class
    print(color + msg + colors.ENDC + esc)


def progressbar(num, cap, partitions=20):  # prints a progressbar
    dashes = round(num / (cap / partitions))
    for i in range(partitions):
        if i < dashes:
            print("#", end="")
        else:
            print("-", end="")
    print(" (" + str(num) + "/" + str(cap) + ")")


def getrank(level):  # gets rank of pickaxe
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


def getpticks(rank):  # returns number of ticks based on pickaxe rank
    return pticks[rank]


class CommandParser():  # class to parse commands
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


class IdleMiner:  # class for the IdleMiner
    def __init__(self):
        self.cmdparse = CommandParser()  # initialize a command parser
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

    def get(self, prefix):  # get a command and call self.execute()
        self.execute(self.cmdparse.get(prefix))

    def sell(self):  # sell the inventory
        for item in list(self.inventory.keys()):
            if self.inventory[item] > 0:
                money = round(self.inventory[item] *
                              prices[item] * self.sellbooster)
                colorprint(item, ": " + "$" + f"{money:,}" +
                           " (x" + f"{self.inventory[item]:,}" + ")", colors.BOLD)
                self.money += money
                self.inventory[item] = 0

    def up(self, tool, amount):  # upgrades
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

    def miningtick(self):  # mine resources and add to the inventory
        num = random.randint(1, 100)
        for i in mines[self.biome][self.minelevel].keys():
            if num > 100 - mines[self.biome][self.minelevel][i]:
                self.inventory[i] += 1
                self.blocksmined += 1

    def update(self):  # check for mine or biome upgrades
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

    def execute(self, cmd):  # execute a command
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
            case "exit":  # exit game
                global shouldexit
                shouldexit = True
            case "cheat":  # for easy testing, should be disabled later
                self.money += 5000000
                self.blocksmined += 2000
            case _:
                colorprint(errmsg + " (in IdleMiner.execute)",
                           color=colors.WARNING)


if __name__ == "__main__":
    steve = IdleMiner()  # make a idle miner

    def repeatedget():  # get commands in a while true loop, target of the input thread
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
