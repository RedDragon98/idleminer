"An idle game based on Minecraft"

import json
import random
import threading
import time
from enum import Enum
import sys
import os
import yaml

PREFIX = "%"  # command prefix
TICKBOOSTER = 1.0  # TPS booster
LANGUAGE: str = yaml.safe_load(open("lang.yml"))

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
mults: dict = dataload("multipliers.json")
biomes: list = dataload("biomes.json")  # biome list
quizes: dict = dataload("quiz.json")  # list of quiz questions
farms: list = dataload("farms.json")  # things you can grow in your farm
crops: dict = dataload("crops.json")  # crops and their sources
mobs: dict = dataload("mobs.json")  # list of mobs

shouldexit = False
TICKS = 1

langdata: dict = dataload("lang/" + LANGUAGE + ".json")


class Lang:
    """defines the text messages"""
    ERRMSG: None
    COSTMSG: None
    UPMSG: None
    NOTINTMSG = None
    MINEUPMSG = None
    CATCHFISHMSG = None
    CATCHTREASUREMSG = None
    CATCHPETMSG = None
    NOCATCHPETMSG = None
    FISHINGUPMSG = None
    CORRECTANSWERMSG = None
    WRONGANSWERMSG = None
    INCOMPATDATAMSG = None
    COOLDOWNMSG = None
    UPBIOMEMSG = None
    GROWMSG = None
    HELPMSG = None
    MOBHITMSG = None
    MOBHURTMSG = None
    WINMSG = None
    DEADMSG = None

    def __init__(self, langpack: dict):
        for key in langpack.keys():
            setattr(self, key, langpack[key])


lang = Lang(langdata)

UP_P_MULTIPLIER = 210  # upgrading pickaxe costs UP_P_MULTIPLIER * level
UP_S_MULTIPLIER = 100
UP_H_MULTIPLIER = 50

PROFILE_V = "0.0.5"  # profile version
COMPAT_V = [
    "0.0.5"
]  # compatible profile versions


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


def getrank(level) -> str:
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


def getmult(tool, rank) -> str:
    """gets pickaxe multiplier based on rank"""
    return mults[tool][rank]


def intcheck(integer: str) -> bool:
    """checks if a argument is an integer, prints a error message if it is not"""
    try:
        int(integer)
    except ValueError:
        colorprint(lang.NOTINTMSG, color=Colors.FAIL)
        return False

    return True


class CommandParser():
    """parses input"""

    def get(self, prompt=">"):
        """gets input and returns a parsed version"""
        command = input(prompt)
        parsed = self.parse(command)
        if len(parsed) == 1:
            return parsed[0]

        return parsed

    @staticmethod
    def parse(data: str):
        """parses a string"""
        if data.strip() == "":
            return "???"

        data = data.strip(PREFIX)
        return data.split(" ")


class Stats:
    """manages IdleMiner stats"""

    tblksmined = 0  # total blocks mined
    blksmined = {
        "dirt": 0,
        "gravel": 0,
        "wood": 0,
        "stone": 0,
        "coal": 0,
        "iron": 0,
        "diorite": 0,
        "andesite": 0,
    }  # blocks mined(per type)

    petscaught = 0  # total pets caught
    tmoneyearned = 0  # total money earned
    tlapisearned = 0  # total lapis earned
    trcearned = 0  # total rc earned
    tmineup = 0  # total mine upgrades
    tbiomeup = 0  # total biome upgrades
    tfishxp = 0  # total fishxp
    tqanswered = 0  # total questions answered
    tqcorrect = 0  # total answers correct
    tfish = 0  # total fish caught
    ttreasure = 0  # total treasure caught

    def printstats(self):
        """prints these stats"""

        print("Blocks mined:", self.tblksmined,
              "(" + str(self.blksmined) + ")")

        print("Total money earned:", self.tmoneyearned)
        print("Total lapis earned:", self.tlapisearned)
        print("Pets caught:", self.petscaught)
        print("Total rc earned:", self.trcearned)
        print("Total mine upgrades:", self.tmineup)
        print("Total biome upgrades:", self.tbiomeup)
        print("Total questions answered:", self.tqanswered,
              "(" + str(self.tqcorrect) + " correct)")
        print("Total fish xp:", self.tfishxp)
        print("Total fish caught:", self.tfish,
              "(" + str(self.ttreasure) + " treasure)")

    def load(self, obj: dict):
        """load stats from dict"""
        self.tblksmined = obj["tblksmined"]
        self.blksmined = obj["blksmined"]
        self.petscaught = obj["petscaught"]
        self.tmoneyearned = obj["tmoneyearned"]
        self.tlapisearned = obj["tlapisearned"]
        self.trcearned = obj["trcearned"]
        self.tmineup = obj["tmineup"]
        self.tbiomeup = obj["tbiomeup"]
        self.tfishxp = obj["tfishxp"]
        self.tqanswered = obj["tqanswered"]
        self.tqcorrect = obj["tqcorrect"]
        self.tfish = obj["tfish"]
        self.ttreasure = obj["ttreasure"]

    def save(self):
        """saves stats to a dictionary"""
        obj = {}
        obj["tblksmined"] = self.tblksmined
        obj["blksmined"] = self.blksmined
        obj["petscaught"] = self.petscaught
        obj["tmoneyearned"] = self.tmoneyearned
        obj["tlapisearned"] = self.tlapisearned
        obj["trcearned"] = self.trcearned
        obj["tmineup"] = self.tmineup
        obj["tbiomeup"] = self.tbiomeup
        obj["tfishxp"] = self.tfishxp
        obj["tqanswered"] = self.tqanswered
        obj["tqcorrect"] = self.tqcorrect
        obj["tfish"] = self.tfish
        obj["ttreasure"] = self.ttreasure

        return obj


class IdleMiner:
    """Idle Miner class"""

    def __init__(self):
        self.cmdparse = CommandParser()

        self.money = 0  # money
        self.lapis = 0  # lapis for pets and other things
        self.rebirthcoins = 0  # rebirth coins

        self.biome = "plains"  # current biome
        self.biomeid = 0  # current biome index in biome list

        self.basebpsize = 50  # base inventory size
        self.bpsizebooster = 1.0  # inventory size booster

        self.sellbooster = 1.0  # booster for sell prices

        self.blocksmined = 0  # blocks mined in this mine level

        self.quizcooldown = 1

        self.pets = []
        self.huntcooldown = 1
        self.huntchance = 10  # chance of pet

        self.inventory = {
            "dirt": 0,
            "gravel": 0,
            "wood": 0,
            "stone": 0,
            "coal": 0,
            "iron": 0,
            "diorite": 0,
            "andesite": 0,
        }  # IdleMiner's inventory

        self.fishcooldown = 1  # cooldowns
        self.fishxp = 0
        self.fishlevel = 1
        self.tools = {
            "p": 0,
            "s": 0,
            "h": 0,
        }

        self.blockspertick = {
            "p": getmult("p", getrank(self.tools["p"])),
            "s": getmult("s", getrank(self.tools["s"]))
        }

        self.minelevel = 0

        self.farmgrowth = (1200 - self.tools["h"] * 5)
        self.produce = {
            "wheat": 0,
            "wheat-seed": 10,
            "rose": 0
        }
        self.farmlevel = 0

        self.battlelevel = 0
        self.battlexp = 0

        self.stats = Stats()

    def load(self, file):
        """loads a profile"""
        profile = json.load(open(file, encoding="UTF-8"))
        if (not "DATA_V" in profile) or (not profile["DATA_V"] in COMPAT_V):
            colorprint(lang.INCOMPATDATAMSG, color=Colors.FAIL)
            return

        self.money = profile["money"]
        self.lapis = profile["lapis"]
        self.rebirthcoins = profile["rebirthcoins"]

        self.biomeid = profile["biomeid"]
        self.biome = biomes[self.biomeid]
        self.minelevel = profile["minelevel"]
        self.blocksmined = profile["blocksmined"]
        self.inventory = profile["inventory"]
        self.fishxp = profile["fishxp"]
        self.fishlevel = profile["fishlevel"]
        self.huntchance = profile["huntchance"]
        self.tools = profile["tools"]
        self.pets = profile["pets"]
        self.produce = profile["produce"]
        self.farmlevel = profile["farmlevel"]

        self.stats = Stats()
        self.stats.load(profile["stats"])

        self.blockspertick["s"] = getmult("s", getrank(self.tools["s"]))
        self.blockspertick["p"] = getmult("p", getrank(self.tools["p"]))

    def save(self, file):
        """saves a profile"""

        profile = {
            "DATA_V": PROFILE_V,
            "money": self.money,
            "lapis": self.lapis,
            "rebirthcoins": self.rebirthcoins,
            "biomeid": self.biomeid,
            "minelevel": self.minelevel,
            "blocksmined": self.blocksmined,
            "inventory": self.inventory,
            "fishxp": self.fishxp,
            "fishlevel": self.fishlevel,
            "huntchance": self.huntchance,
            "tools": self.tools,
            "pets": self.pets,
            "produce": self.produce,
            "farmlevel": self.farmlevel,
            "stats": self.stats.save()
        }

        json.dump(profile, open(file, "w", encoding="UTF-8"))

    def get(self):
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
                self.stats.tmoneyearned += money

    def _individualup(self, tool, toolname, amount, multiplier):
        for _ in range(amount):
            price = self.tools[tool] * multiplier
            if price <= self.money:
                self.tools[tool] += 1
                self.money -= price
            else:
                colorprint(lang.COSTMSG, color=Colors.FAIL)
                break

        self.blockspertick[tool] = getmult(tool, getrank(self.tools[tool]))
        print(lang.UPMSG %
              (toolname, self.tools[tool], getrank(self.tools[tool])))

    def upgrade(self, tool, amount):
        """upgrades tool"""
        match tool:
            case "p" | "pickaxe":  # rebirth = level >= 200
                self._individualup("p", "pickaxe", amount, UP_P_MULTIPLIER)
            case "s" | "shovel":  # rebirth = level >= 200
                self._individualup("s", "shovel", amount, UP_S_MULTIPLIER)
            case "a" | "axe":  # rebirth = level >= 200
                pass
            case "h" | "hoe":  # rebirth = level >= 200
                self._individualup("h", "hoe", amount, UP_H_MULTIPLIER)
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
                colorprint(lang.ERRMSG + " (in IdleMiner.up)",
                           color=Colors.FAIL)

    def miningtick(self):
        """adds resources to inventory"""
        num = random.randint(1, 100)
        for tool in ["p", "s"]:
            chances = mines[self.biome][self.minelevel][tool]
            for i in chances.keys():
                if num > 100 - chances[i]:
                    tomine = self.blockspertick[tool]
                    self.inventory[i] += tomine
                    self.blocksmined += tomine

                    self.stats.tblksmined += tomine
                    self.stats.blksmined[i] += tomine

    def update(self):
        """update fishing and mining levels"""
        if self.blocksmined > 2000 * (self.minelevel + 1):
            self.minelevel += 1
            self.stats.tmineup += 1
            self.blocksmined = 0
            print(lang.MINEUPMSG % self.minelevel)

            try:
                mines[self.biome][self.minelevel]
            except IndexError:
                self.biomeid += 1
                self.biome = biomes[self.biomeid]
                self.minelevel = 0
                self.blocksmined = 0

                print(lang.UPBIOMEMSG % self.biome)

        if self.fishxp / self.fishlevel >= 4:
            self.fishlevel += 1
            self.fishxp = 0
            print(lang.FISHINGUPMSG % self.fishlevel)
        self.huntcooldown -= 1
        self.quizcooldown -= 1
        self.fishcooldown -= 1
        self.farmgrowth -= 1

    def profile(self):
        """prints profile"""
        print("money: $" + f"{self.money:,}")
        print("lapis:", self.lapis)
        print("inventory:", self.inventory)
        print("tools:", self.tools)
        print("produce:", self.produce)
        print("mine level:", self.minelevel, end=" ")
        progressbar(self.blocksmined, (self.minelevel + 1) * 2000)
        print("fishing level:", self.fishlevel, end=" ")
        progressbar(self.fishxp, self.fishlevel * 4)

    def hunt(self):
        """hunts"""
        if self.huntcooldown < 1:
            self.huntcooldown = 300
            self.huntchance = random.randint(0, 100)
            if self.huntchance < 10:
                pet = random.choice(self.pets[0:(25-(self.huntchance * 2))])
                print(pet)

                self.stats.petscaught += 1
            else:
                lapis = random.randint(1, 10)
                self.lapis += lapis
                print('You didn\'t get a pet :( You now have',
                      self.lapis, 'lapis.')

                self.stats.tlapisearned += lapis
        else:
            print(lang.COOLDOWNMSG % (self.huntcooldown, "hunting"))

    def _quiz(self, difficulty):
        """internal function for quizzes; returns whether the answer is correct"""
        question = random.choice(quizes[difficulty])

        print(question["question"] + "?")
        index = 0
        for i in question["choices"]:
            print(str(index) + ": " + i)
            index += 1

        answer = input("answer: ")

        if not intcheck(answer):
            return False

        if int(answer) == question["answer"]:
            self.stats.tqcorrect += 1
            self.stats.tqanswered += 1
            return True

        self.stats.tqanswered += 1
        return False

    def quiz(self, difficulty):
        """asks a quiz question"""
        if self.quizcooldown < 1:
            self.quizcooldown = 300

            if self._quiz(difficulty):
                print(lang.CORRECTANSWERMSG)

                self.money += 3000
            else:
                print(lang.WRONGANSWERMSG)
        else:
            print(lang.COOLDOWNMSG % (self.quizcooldown, "getting quizzed"))

    def farm(self):
        """farms"""
        if self.farmgrowth < 1:
            self.farmgrowth = (1200 - self.tools["h"] * 5)
            grown = []
            for crop in farms[self.farmlevel].keys():
                if random.randint(0, 100) <= farms[self.farmlevel][crop]:
                    grown.append(crop)

            for crop in grown:
                amount = self.produce[crops[crop]["from"]]
                self.produce[crops[crop]["from"]] = 0
                for product in crops[crop]["produces"]:
                    self.produce[product] += amount

            print(lang.GROWMSG, str(grown).strip("[] ").replace("'", ""))
        else:
            print(lang.COOLDOWNMSG % (self.farmgrowth, "farming"))

    def fish(self):
        """fishes"""
        if self.fishcooldown < 1:
            self.fishcooldown = 300
            if random.randint(1, 100 - self.fishlevel) == 1:
                print(lang.CATCHTREASUREMSG)

                self.money += 5000
                self.fishxp += 10

                self.stats.tfishxp += 10
                self.stats.ttreasure += 1
            else:
                print(lang.CATCHFISHMSG)
                self.fishxp += 1

                self.stats.tfishxp += 1
                self.stats.tfish += 1
        else:
            print(lang.COOLDOWNMSG % (self.fishcooldown, "fishing"))

    def battle(self):
        """battle a horde of mobs"""

        horde = random.choice(
            list(mobs.keys())[0:self.battlelevel + 1 * 3])

        mobhp = mobs[horde]["hp"]
        mobdmg = mobs[horde]["dmg"]\

        stevehp = self.battlelevel + 1 * 10

        print("Fighting:", horde, "with hp:", mobhp,
              "and damage:", str(mobdmg) + ".", "You have", stevehp)
        cont = input("Do you want to continue(y/N)?")

        if cont == "y":
            while stevehp > 0 and mobhp > 0:
                if mobhp > 100 and self._quiz("really"):
                    mobhp -= 10
                    print(lang.MOBHITMSG % (10, mobhp))
                elif mobhp > 50 and self._quiz("hard"):
                    mobhp -= 4
                    print(lang.MOBHITMSG % (4, mobhp))
                elif mobhp > 20 and self._quiz("medium"):
                    mobhp -= 2
                    print(lang.MOBHITMSG % (2, mobhp))
                elif self._quiz("easy"):
                    mobhp -= 1
                    print(lang.MOBHITMSG % (1, mobhp))
                else:
                    stevehp -= mobdmg
                    print(lang.MOBHURTMSG % (mobdmg, stevehp))

            if stevehp == 0:
                print(lang.DEADMSG)

            else:
                self.battlexp += 1
                print(lang.WINMSG % 1)

    def execute(self, cmd):
        """executes command"""
        match cmd:
            case "sell" | "s":
                self.sell()
            case["upgrade" | "up" | "u", tool, amount]:
                if intcheck(amount):
                    self.upgrade(tool, int(amount))
            case "fish" | "f":
                self.fish()
            case "hunt" | "h":
                self.hunt()
            case "profile" | "p":
                self.profile()
                print("--------")
                self.stats.printstats()
            case["quiz" | "q", difficulty]:
                self.quiz(difficulty)
            case "farm" | "fm":
                self.farm()
            case "battle" | "b":
                self.battle()
            case "exit" | "quit":
                self.save("profile.json")

                global shouldexit
                shouldexit = True
            case "help":
                print(lang.HELPMSG)
            case "cheat":
                self.money += 10000000
                self.blocksmined += 2000
                self.farmgrowth = 0
                self.huntcooldown = 0
                self.fishcooldown = 0
                self.quizcooldown = 0
            case ":(":
                print("Oof.")
            case _:
                colorprint(lang.ERRMSG + " (in IdleMiner.execute)",
                           color=Colors.FAIL)


if __name__ == "__main__":
    try:
        print(lang.HELPMSG)
        steve = IdleMiner()

        if os.path.exists("profile.json"):
            steve.load("profile.json")

        def repeatedget():
            """repeatedly gets input"""
            while not shouldexit:
                steve.get()

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

    except (KeyboardInterrupt, SystemExit, EOFError):
        # doesn't seem to hide the error message, but still saves
        steve.save("profile.json")
        sys.exit(0)
