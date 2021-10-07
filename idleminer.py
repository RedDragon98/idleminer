"An idle game based on Minecraft"

import json
import random
import threading
import time
from enum import Enum
import sys
import os

PREFIX = "%"  # command prefix
TICKBOOSTER = 1.0  # TPS booster

DATAPATH = "data/"  # data file path


def dataload(file):
    """loads a data file"""
    return json.load(open(DATAPATH + file, encoding="UTF-8"))


class Colors(Enum):
    """printing colors"""
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

# mining multiplier (based on pickaxe level)
mults = dataload("multipliers.json")
biomes = dataload("biomes.json")  # biome list
quizes = dataload("quiz.json")  # list of quiz questions

shouldexit = False
TICKS = 1

ERRMSG = "Invalid command"  # error during parsing
COSTMSG = "You don't have enough money (upgraded till max)"  # money ran out
UPMSG = "Your %s level is %s, type is %s"
NOTINTMSG = "Value should be an integer"
MINEUPMSG = "Upgraded mine to %s"
CATCHFISHMSG = "You caught a fish. +1 fishing xp"
CATCHTREASUREMSG = "You caught treasure. +10 fishing xp"
CATCHPETMSG = "You caught a pet"
NOCATCHPETMSG = "You didn't catch a pet :(. Better luck next time!"
FISHINGUPMSG = "Your fishing level was upgraded to %s"
CORRECTANSWERMSG = "Correct! +$2000"
WRONGANSWERMSG = "Wrong! Better luck next time"

HELPMSG = """
s/sell: sells any resources in the inventory
p/profile: prints stats about the IdleMiner
f/fish: fishes for treasure
h/hunt: catches pets
u/upgrade tool amount: upgrades a tool by amount (eg. u p 1)
q/quiz difficulty: gives you a quiz (eg. q easy)
exit: exits the game
help: prints this menu again
The available tool is pickaxe (more are coming)
"""

UP_P_MULTIPLIER = 210  # upgrading pickaxe costs UP_P_MULTIPLIER * level
UP_S_MULTIPLIER = 100


def colorprint(msg, esc="", color=""):
    """prints text with a color"""
    print(color.value + msg + Colors.ENDC.value + esc)


def progressbar(num, cap, partitions=20):
    """progressbar ####--"""
    dashes = round(num / (cap / partitions))
    for i in range(partitions):
        if i < dashes:
            print("#", end="")
        else:
            print("-", end="")
    print(" (" + str(num) + "/" + str(cap) + ")")


def getrank(level):
    """gets rank of a tool"""

    rank = "impossible"
    if level >= 200:
        rank = "netherite"
    elif level >= 150:
        rank = "diamond"
    elif level >= 100:
        rank = "gold"
    elif level >= 50:
        rank = "iron"
    elif level >= 25:
        rank = "stone"
    elif level >= 0:
        rank = "wooden"

    return rank


def getmult(tool, rank):
    """gets pickaxe multiplier base on rank"""
    return mults[tool][rank]


class CommandParser():
    """parses input"""

    def get(self, prompt=">"):
        """gets input and returns a parsed version"""
        command = input(prompt)
        parsed = self.parse(command)
        if len(parsed) == 1:
            return parsed[0]

        return parsed

    def parse(self, data: str):
        """parses a string"""
        if data.strip() == "":
            return "???"

        data = data.strip(PREFIX)
        return data.split(" ")


class IdleMiner:
    """Idle Miner class"""

    def __init__(self):
        self.cmdparse = CommandParser()
        self.money = 0  # money
        self.shards = 0  # shards for pets
        self.rc = 0  # rebirth coins
        self.huntchance = 10  # chance of pet
        self.biome = "plains"  # current biome
        self.biomeid = 0  # current biome index in biome list
        self.basebpsize = 50  # base inventory size
        self.bpsizebooster = 1.0  # inventory size booster
        self.sellbooster = 1.0  # booster for sell prices
        self.arealevels = {
            "mine": 0,
            "dig": 0,
        }  # current level for different areas in biome
        self.blocksmined = 0  # blocks mined in this mine level
        self.inventory = {
            "dirt": 0,
            "gravel": 0,
            "wood": 0,
            "stone": 0,
            "coal": 0,
            "iron": 0,
            "diorite": 0,
        }  # IdleMiner's inventory
        self.fishxp = 0
        self.fishlevel = 1
        self.tools = {
            "p": 0,
            "s": 0,
        }

        self.blockspertick = {
            "p": getmult("p", getrank(self.tools["p"])),
            "s": getmult("s", getrank(self.tools["s"]))
        }

        self.minelevel = 0

    def load(self, file):
        """loads a profile"""
        profile = json.load(open(file))
        self.money = profile["money"]
        self.shards = profile["shards"]
        self.rc = profile["rc"]
        self.biomeid = profile["biomeid"]
        self.biome = biomes[self.biomeid]
        self.minelevel = profile["minelevel"]
        self.blocksmined = profile["blocksmined"]
        self.inventory = profile["inventory"]
        self.fishxp = profile["fishxp"]
        self.fishlevel = profile["fishlevel"]
        self.huntchance = profile["huntchance"]
        self.tools = profile["tools"]

        self.blockspertick["s"] = getmult("s", getrank(self.tools["s"]))
        self.blockspertick["p"] = getmult("p", getrank(self.tools["p"]))

    def save(self, file):
        """saves a profile"""
        profile = {
            "money": self.money,
            "shards": self.shards,
            "rc": self.rc,
            "biomeid": self.biomeid,
            "minelevel": self.minelevel,
            "blocksmined": self.blocksmined,
            "inventory": self.inventory,
            "fishxp": self.fishxp,
            "fishlevel": self.fishlevel,
            "huntchance": self.huntchance,
            "tools": self.tools
        }
        json.dump(profile, open(file, "w", encoding="UTF-8"))

    def get(self, PREFIX):
        """gets and executes command"""
        self.execute(self.cmdparse.get(PREFIX))

    def sell(self):
        """sells inventory"""
        for item in list(self.inventory.keys()):
            if self.inventory[item] > 0:
                money = round(self.inventory[item] *

                              prices[item] * self.sellbooster)
                colorprint(item, ": " + "$" + f"{money:,}" +
                           " (x" + f"{self.inventory[item]:,}" + ")", Colors.BOLD)
                self.money += money
                self.inventory[item] = 0

    def _individualup(self, tool, toolname, amount, multiplier):
        for i in range(amount):
            price = self.tools[tool] * multiplier
            if price <= self.money:
                self.tools[tool] += 1
                self.money -= price
            else:
                colorprint(COSTMSG, color=Colors.FAIL)
                break

        self.blockspertick[tool] = getmult(tool, getrank(self.tools[tool]))
        print(UPMSG %
              (toolname, self.tools[tool], getrank(self.tools[tool])))

    def up(self, tool, amount):
        """upgrades tool"""
        match tool:
            case "p" | "pickaxe":  # rebirth = level >= 200
                self._individualup("p", "pickaxe", amount, UP_P_MULTIPLIER)
            case "s" | "shovel":  # rebirth = level >= 200
                self._individualup("s", "shovel", amount, UP_S_MULTIPLIER)
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
                colorprint(ERRMSG + " (in IdleMiner.up)", color=Colors.FAIL)

    def miningtick(self):
        """adds resources to inventory"""
        num = random.randint(1, 100)
        for tool in self.tools.keys():
            chances = mines[self.biome][self.minelevel][tool]
            for i in chances.keys():
                if num > 100 - chances[i]:
                    tomine = self.blockspertick[tool]
                    self.inventory[i] += tomine
                    self.blocksmined += tomine

    def update(self):
        """update fishing and mining levels"""
        if self.blocksmined > 2000 * (self.minelevel + 1):
            self.minelevel += 1
            self.blocksmined = 0
            print(MINEUPMSG % self.minelevel)
        if self.fishxp / self.fishlevel >= 4:
            self.fishlevel += 1
            self.fishxp = 0
            print(FISHINGUPMSG % self.fishlevel)

    def execute(self, cmd):
        """executes command"""
        match cmd:
            case "sell" | "s":
                self.sell()
            case["upgrade" | "up" | "u", tool, amount]:
                try:
                    int(amount)
                except ValueError:
                    colorprint(NOTINTMSG, color=Colors.FAIL)
                else:
                    self.up(tool, int(amount))
            case "fish" | "f":
                if random.randint(1, 100 - self.fishlevel) == 1:
                    print(CATCHTREASUREMSG)
                    self.money += 5000
                else:
                    print(CATCHFISHMSG)
                    self.fishxp += 1
            case "hunt" | "h":
                if random.randint(1, self.huntchance) == 1:
                    print(CATCHPETMSG)
                else:
                    print(NOCATCHPETMSG)
                    self.shards += random.randint(1, 10)
                    print('You now have', self.shards, 'shards.')
            case "profile" | "p":
                print("money: $" + f"{self.money:,}")
                print("shards:", self.shards)
                print("inventory:", self.inventory)
                print("tools:", self.tools)
                print("mine level:", self.minelevel, end=" ")
                progressbar(self.blocksmined, (self.minelevel + 1) * 2000)
                print("fishing level:", self.fishlevel, end=" ")
                progressbar(self.fishxp, self.fishlevel * 4)
            case["quiz" | "q", difficulty]:
                question = random.choice(quizes[difficulty])
                print(question["question"] + "?")
                index = 0
                for i in question["choices"]:
                    print(str(index) + ": " + i)
                    index += 1
                answer = input("answer: ")
                try:
                    int(answer)
                except ValueError:
                    colorprint(NOTINTMSG, color=Colors.FAIL)

                if int(answer) == question["answer"]:
                    print(CORRECTANSWERMSG)
                    self.money += 3000
                else:
                    print(WRONGANSWERMSG)

            case "exit":
                self.save("profile.json")

                global shouldexit
                shouldexit = True
            case "help":
                print(HELPMSG)
            case "cheat":
                self.money += 9**999
                self.blocksmined += 2000
            case _:
                colorprint(ERRMSG + " (in IdleMiner.execute)",
                           color=Colors.FAIL)


if __name__ == "__main__":
    print(HELPMSG)
    steve = IdleMiner()

    if os.path.exists("profile.json"):
        steve.load("profile.json")

    def repeatedget():
        """repeatedly gets input"""
        while not shouldexit:
            steve.get(">")

    inputthread = threading.Thread(target=repeatedget)
    inputthread.daemon = True
    inputthread.start()

    # background tasks
    SLEEPTIME = 1 / TICKS
    while True:
        time.sleep(SLEEPTIME)
        steve.miningtick()
        steve.update()

        if shouldexit:
            sys.exit(0)
