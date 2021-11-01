"An idle game based on Minecraft"

import json
import random
import threading
import time
import sys
import os
import yaml
import rich

import lang
from stats import Stats
import resources

c = rich.get_console()

PREFIX = "%"  # command prefix
TICKBOOSTER = 1.0  # TPS booster


def configload(file):
    """loads a config file"""
    return yaml.safe_load(open("config/" + file, encoding="UTF-8"))


LANGUAGE: str = configload("lang.yml")
COLORS: bool = configload("colors.yml")

DATAPATH = "data/"  # data file path


def dataload(file):
    """loads a data file"""
    return json.load(open(DATAPATH + file, encoding="UTF-8"))


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

lang.load(langdata)

HELPMSG = lang.HELPMSG
if COLORS:
    HELPMSG = lang.HELPMSGC

UP_P_MULTIPLIER = 210  # upgrading pickaxe costs UP_P_MULTIPLIER * level
UP_S_MULTIPLIER = 100
UP_H_MULTIPLIER = 50
UP_A_MULTIPLIER = 120

PROFILE_V = "0.0.8"  # profile version
COMPAT_V = [
    "0.0.8"
]  # compatible profile versions


def progressbar(num, cap, partitions=20):
    """progressbar ####--"""
    out = print
    if COLORS:
        out = c.print

    dashes = round(num / (cap / partitions))
    for i in range(partitions):
        if i < dashes:
            out("#", end="")
        else:
            out("-", end="")
    out(" (" + str(num) + "/" + str(cap) + ")")


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
    """gets multiplier based on rank"""
    return mults[tool][rank]


def intcheck(integer: str) -> bool:
    """checks if a argument is an integer, prints a error message if it is not"""
    try:
        int(integer)
    except ValueError:
        c.print(lang.NOTINTMSG, style="red")
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

        self.inventory = resources.Resources()  # IdleMiner's inventory

        self.fishcooldown = 1  # cooldowns
        self.fishxp = 0
        self.fishlevel = 1
        self.tools = {
            "p": 0,
            "s": 0,
            "h": 0,
            "a": 0,
        }

        self.blockspertick = {
            "p": getmult("p", getrank(self.tools["p"])),
            "s": getmult("s", getrank(self.tools["s"])),
            "a": getmult("a", getrank(self.tools["a"]))
        }

        self.minelevel = 0

        self.farmgrowth = (1200 - self.tools["h"] * 5)
        self.produce = resources.Resources()
        self.produce.set("wheat-seed", 10)

        self.farmlevel = 0

        self.battlelevel = 0
        self.battlexp = 0

        self.stats = Stats()

    def load(self, file):
        """loads a profile"""
        profile = json.load(open(file, encoding="UTF-8"))
        if (not "DATA_V" in profile) or (not profile["DATA_V"] in COMPAT_V):
            c.print(lang.INCOMPATDATAMSG, style="red")
            return

        self.money = profile["money"]
        self.lapis = profile["lapis"]
        self.rebirthcoins = profile["rebirthcoins"]

        self.biomeid = profile["biomeid"]
        self.biome = biomes[self.biomeid]
        self.minelevel = profile["minelevel"]
        self.blocksmined = profile["blocksmined"]
        self.inventory = resources.load(profile["inventory"])
        self.fishxp = profile["fishxp"]
        self.fishlevel = profile["fishlevel"]
        self.huntchance = profile["huntchance"]
        self.tools = profile["tools"]
        self.pets = profile["pets"]
        self.produce = resources.load(profile["produce"])
        self.farmlevel = profile["farmlevel"]
        self.battlelevel = profile["battlelevel"]
        self.battlexp = profile["battlexp"]

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
            "inventory": self.inventory.save(),
            "fishxp": self.fishxp,
            "fishlevel": self.fishlevel,
            "huntchance": self.huntchance,
            "tools": self.tools,
            "pets": self.pets,
            "produce": self.produce.save(),
            "farmlevel": self.farmlevel,
            "stats": self.stats.save(),
            "battlelevel": self.battlelevel,
            "battlexp": self.battlexp,
        }

        json.dump(profile, open(file, "w", encoding="UTF-8"))

    def get(self):
        """gets and executes command"""
        self.execute(self.cmdparse.get(PREFIX))

    def _sell(self, itemstosell: resources.Resources):
        """internal function to sell from a dictionary"""
        for item in list(itemstosell.list()):
            if itemstosell.get(item) > 0:
                money = round(itemstosell.get(item) *
                              prices[item] * self.sellbooster)
                print(item + ": " + "$" + f"{money:,}" +
                      " (x" + f"{itemstosell.get(item):,}" + ")")
                self.money += money
                itemstosell.zero(item)
                self.stats.tmoneyearned += money

        return itemstosell

    def sell(self, sproduce=False):
        """sells inventory"""
        if sproduce:
            self.produce = self._sell(self.produce)
        else:
            self.inventory = self._sell(self.inventory)

    def _individualup(self, tool, toolname, amount, multiplier):
        for _ in range(amount):
            price = self.tools[tool] * multiplier
            if price <= self.money:
                self.tools[tool] += 1
                self.money -= price
            else:
                c.print(lang.COSTMSG, style="red")
                break

        self.blockspertick[tool] = getmult(tool, getrank(self.tools[tool]))
        c.print(lang.UPMSG %
                (toolname, self.tools[tool], getrank(self.tools[tool])))

    def upgrade(self, tool, amount):
        """upgrades tool"""
        match tool:
            case "p" | "pickaxe":  # rebirth = level >= 200
                self._individualup("p", "pickaxe", amount, UP_P_MULTIPLIER)
            case "s" | "shovel":  # rebirth = level >= 200
                self._individualup("s", "shovel", amount, UP_S_MULTIPLIER)
            case "a" | "axe":  # rebirth = level >= 200
                self._individualup("a", "axe", amount, UP_A_MULTIPLIER)
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
                c.print(lang.ERRMSG + " (in IdleMiner.up)",
                        style="red")

    def miningtick(self):
        """adds resources to inventory"""
        num = random.randint(1, 100)
        for tool in ["p", "s", "a"]:  # hoe doesn't get ticks
            chances = mines[self.biome][self.minelevel][tool]
            for i in chances.keys():
                if num > 100 - chances[i]:
                    tomine = self.blockspertick[tool]
                    self.inventory.modify(i, tomine)
                    self.blocksmined += tomine

                    self.stats.tblksmined += tomine
                    self.stats.blksmined.modify(i, tomine)

    def update(self):
        """update fishing and mining levels"""
        toprint = []

        if self.blocksmined >= 2000 * (self.minelevel + 1):
            self.minelevel += 1
            self.stats.tmineup += 1
            self.blocksmined = 0
            toprint.append(lang.MINEUPMSG % self.minelevel)

            try:
                mines[self.biome][self.minelevel]
            except IndexError:
                self.biomeid += 1
                self.biome = biomes[self.biomeid]
                self.minelevel = 0
                self.blocksmined = 0

                toprint.append(lang.UPBIOMEMSG % self.biome)

        if self.fishxp / self.fishlevel >= 4:
            self.fishlevel += 1
            self.fishxp = 0
            toprint.append(lang.FISHINGUPMSG % self.fishlevel)
        if self.battlexp / (self.battlelevel + 1) >= 5:
            self.battlelevel += 1
            self.battlexp = 0
            toprint.append(lang.BATTLEUPMSG % self.battlelevel)

        self.huntcooldown -= 1
        self.quizcooldown -= 1
        self.fishcooldown -= 1
        self.farmgrowth -= 1

        return toprint

    def profile(self):
        """prints profile"""
        if COLORS:
            c.print("[blue]money[/blue]:", f"{self.money:,}")
            c.print("[blue]lapis[/blue]:", self.lapis)
            c.print("[blue]inventory[/blue]:", self.inventory.save())
            c.print("[blue]tools[/blue]:", self.tools)
            c.print("[blue]produce[/blue]:", self.produce.save())
            c.print("[blue]mine level[/blue]:", self.minelevel, end=" ")
            progressbar(self.blocksmined, (self.minelevel + 1) * 2000)
            c.print("[blue]fishing level[/blue]:", self.fishlevel, end=" ")
            progressbar(self.fishxp, self.fishlevel * 4)
            c.print("[blue]battle level[/blue]:", self.battlelevel, end=" ")
            progressbar(self.battlexp, (self.battlelevel + 1) * 5)
        else:
            print("money:", f"{self.money:,}")
            print("lapis:", self.lapis)
            print("inventory:", self.inventory.save())
            print("tools:", self.tools)
            print("produce:", self.produce.save())
            print("mine level:", self.minelevel, end=" ")
            progressbar(self.blocksmined, (self.minelevel + 1) * 2000)
            print("fishing level:", self.fishlevel, end=" ")
            progressbar(self.fishxp, self.fishlevel * 4)
            print("battle level:", self.battlelevel, end=" ")
            progressbar(self.battlexp, (self.battlelevel + 1) * 5)

    def hunt(self):
        """hunts"""
        if self.huntcooldown < 1:
            self.huntcooldown = 300
            self.huntchance = random.randint(0, 100)
            if self.huntchance < 10:
                print(self.pets)
                pet = random.choice(self.pets[0:(25-(self.huntchance * 2))])
                c.print(pet)

                self.stats.petscaught += 1
            else:
                lapis = random.randint(1, 10)
                self.lapis += lapis
                c.print('You didn\'t get a pet :( You now have',
                        self.lapis, 'lapis.')

                self.stats.tlapisearned += lapis
        else:
            c.print(lang.COOLDOWNMSG % (self.huntcooldown, "hunting"))

    def _quiz(self, difficulty):
        """internal function for quizzes; returns whether the answer is correct"""
        question = random.choice(quizes[difficulty])

        if COLORS:
            c.print(question["question"] + "?")
        else:
            print(question["question"] + "?")
        index = 0
        for i in question["choices"]:
            if COLORS:
                c.print(str(index) + ": " + i)
            else:
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

    def _takefood(self):
        """internal function to take food from produce"""
        for i in self.produce.list():
            if self.produce.get(i) > 0:
                self.produce.modify(i, -1)
                return i

        return None

    def quiz(self, difficulty):
        """asks a quiz question"""
        if self.quizcooldown < 1:
            self.quizcooldown = 300

            if self._quiz(difficulty):
                c.print(lang.CORRECTANSWERMSG)

                self.money += 3000
            else:
                c.print(lang.WRONGANSWERMSG)
        else:
            c.print(lang.COOLDOWNMSG % (self.quizcooldown, "getting quizzed"))

    def farm(self):
        """farms"""
        if self.farmgrowth < 1:
            self.farmgrowth = (1200 - self.tools["h"] * 5)
            grown = []
            for crop in farms[self.farmlevel].keys():
                if random.randint(0, 100) <= farms[self.farmlevel][crop]:
                    grown.append(crop)

            for crop in grown:
                amount = self.produce.get(crops[crop]["from"])
                self.produce.zero(crops[crop]["from"])
                for product in crops[crop]["produces"]:
                    self.produce.modify(product, amount)

            c.print(lang.GROWMSG, str(grown).strip("[] ").replace("'", ""))
        else:
            c.print(lang.COOLDOWNMSG % (self.farmgrowth, "farming"))

    def fish(self):
        """fishes"""
        if self.fishcooldown < 1:
            self.fishcooldown = 300
            if random.randint(1, 100 - self.fishlevel) == 1:
                c.print(lang.CATCHTREASUREMSG)

                self.money += 5000
                self.fishxp += 10

                self.stats.tfishxp += 10
                self.stats.ttreasure += 1
            else:
                c.print(lang.CATCHFISHMSG)
                self.fishxp += 1

                self.produce.modify("fish", 1)

                self.stats.tfishxp += 1
                self.stats.tfish += 1
        else:
            c.print(lang.COOLDOWNMSG % (self.fishcooldown, "fishing"))

    def battle(self):
        """battle a horde of mobs"""

        horde = random.choice(
            list(mobs.keys())[0:(self.battlelevel + 1) * 3])

        mobhp = mobs[horde]["hp"]
        mobdmg = mobs[horde]["dmg"]

        stevehp = (self.battlelevel + 1) * 10

        c.print("Fighting:", horde, "with hp:", mobhp,
                "and damage:", str(mobdmg) + ".", "You have", stevehp, "hp")
        cont = input("Do you want to continue(y/N)?")

        if cont == "y":
            while stevehp > 0 and mobhp > 0:
                difficulty = "easy"
                damage = 1
                if mobhp >= 100:
                    difficulty = "really"
                    damage = 10
                elif mobhp >= 50:
                    difficulty = "hard"
                    damage = 4
                elif mobhp >= 20:
                    difficulty = "medium"
                    damage = 2

                if self._quiz(difficulty):
                    mobhp -= damage
                    print(lang.MOBHITMSG % (damage, mobhp))
                else:
                    stevehp -= mobdmg
                    c.print(lang.MOBHURTMSG % (mobdmg, stevehp))

                eat = input(lang.WOULDLIKETOEATMSG % stevehp)
                if eat:
                    food = self._takefood()
                    if food:
                        print(lang.ATEMSG % food)
                        stevehp += 1
                    else:
                        c.print(lang.NOFOODMSG)

            if stevehp == 0:
                c.print(lang.DEADMSG)

            else:
                self.battlexp += mobs[horde]["xp"]
                c.print(lang.WINMSG % 1)

    def execute(self, cmd):
        """executes command"""
        match cmd:
            case "s":
                self.sell()
            case "sp":
                self.sell(True)
            case["upgrade" | "up" | "u", tool, amount]:
                if intcheck(amount):
                    self.upgrade(tool, int(amount))
            case "fish" | "f":
                self.fish()
            case "hunt" | "h":
                self.hunt()
            case "profile" | "p":
                self.profile()
                c.print("--------")
                self.stats.printstats(COLORS, c)
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
                c.print(HELPMSG)
            case "cheat":
                self.money += 10000000
                self.blocksmined += 2000
                self.farmgrowth = 0
                self.huntcooldown = 0
                self.fishcooldown = 0
                self.quizcooldown = 0
            # easter eggs?
            case ":(":
                c.print("Oof", style="red")
            case ":)":
                c.print("Yay", style="green")
            case _:
                c.print(lang.ERRMSG + " (in IdleMiner.execute)",
                        style="red")


if __name__ == "__main__":
    queue = []
    try:
        c.print(HELPMSG)
        steve = IdleMiner()

        if os.path.exists("profile.json"):
            steve.load("profile.json")

        def repeatedget():
            """repeatedly gets input"""
            global queue

            while not shouldexit:
                steve.get()
                for i in queue:
                    print(i)

                queue = []

        inputthread = threading.Thread(target=repeatedget)
        inputthread.daemon = True
        inputthread.start()

        # background tasks
        SLEEPTIME = 1 / TICKS
        while True:
            time.sleep(SLEEPTIME)
            steve.miningtick()
            queue.extend(steve.update())

            if shouldexit:
                sys.exit(0)

    except (KeyboardInterrupt, SystemExit, EOFError):
        # doesn't seem to hide the error message, but still saves
        steve.save("profile.json")
        sys.exit(0)
