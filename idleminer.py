import json
import random
import threading
import time

prefix = "%"  # command prefix
tickbooster = 1.0  # TPS booster

datapath = "data/"  # data file path


def dataload(file):  # loads data files
    return json.load(open(datapath + file))


class colors:  # printing colors
    HEADER = '\033[95m'
    BLUE = '\033[94m'
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
mineupmsg = "Upgraded mine to %s"
catchfishmsg = "You caught a fish. +1 fishing xp"
catchtreasuremsg = "You caught treasure. +10 fishing xp"
catchpetmsg = "You caught a pet"
nocatchpetmsg = "You didn't catch a pet :(. Better luck next time!"
fishingupmsg = "Your fishing level was upgraded to %s"
shouldexit = False
ticks = 1

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
        cmd = input(prompt)
        parsed = self.parse(cmd)
        if len(parsed) == 1:
            return parsed[0]
        else:
            return parsed

    def parse(self, data: str):
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
        self.basebpsize = 50  # base inventory size
        self.bpsizebooster = 1.0  # inventory size booster
        self.sellbooster = 1.0  # booster for sell prices
        self.minelevel = 1  # current mine level in biome
        self.blocksmined = 0  # blocks mined in this mine level
        self.inventory = {
            "dirt": 0,
            "wood": 0,
            "stone": 0,
            "coal": 0,
            "iron": 0,
            "diorite": 0,
        }  # IdleMiner's inventory
        self.fishxp = 0
        self.fishlevel = 1
        self.tools = {
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
                        colorprint(costmsg, color=colors.FAIL)
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
                colorprint(errmsg + " (in IdleMiner.up)", color=colors.FAIL)

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
            print(mineupmsg % self.minelevel)
        if self.fishxp / self.fishlevel >= 4:
            self.fishlevel += 1
            self.fishxp = 0
            print(fishingupmsg % self.fishlevel)

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
                if random.randint(1, 100 - self.fishlevel) == 1:
                    print(catchtreasuremsg)  # TODO: unfinished
                    self.money += 5000
                else:
                    print(catchfishmsg)
                    self.fishxp += 1
            case "hunt" | "h":
                if random.randint(1, self.huntchance) == 1:
                    print(catchpetmsg)  # TODO: unfinished
                else:
                    print(nocatchpetmsg)
                    self.shards += random.randint(1, 10)
                    print('You now have', self.shards, 'shards.')
            case "profile" | "p":
                print("money: $" + f"{self.money:,}")
                print("shards:", self.shards)
                print("inventory:", self.inventory)
                print("tools:", self.tools)
                print("mine level:", self.minelevel)
                print("blocks until next level:", str(
                    self.blocksmined) + "/" + str(self.minelevel * 2000))
                print("fishing level:", self.fishlevel, end=" ")
                progressbar(self.fishxp, self.fishlevel * 4)
            case "quiz" | "q":
                pass
            case "exit":
                global shouldexit
                shouldexit = True
            case "cheat":
                self.money += 9**999
                self.blocksmined += 2000
            case _:
                colorprint(errmsg + " (in IdleMiner.execute)",
                           color=colors.FAIL)


if __name__ == "__main__":
    steve = IdleMiner()

    def repeatedget():
        while not shouldexit:
            steve.get(">")

    cmd = threading.Thread(target=repeatedget)
    cmd.daemon = True
    cmd.start()

    # background tasks
    while True:
        time.sleep(1 / ticks)
        steve.miningtick()
        steve.update()

        if shouldexit:
            exit(0)
