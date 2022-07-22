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


def printlist(msg: list[str], end=str):
    """prints list"""
    index = 0
    for i in msg:
        index += 1
        if index == len(msg):
            print(i, end="")
        else:
            print(i, end=" ")

    print(end=end)


LANGUAGE: str = configload("lang.yml")
COLORS: bool = configload("colors.yml")
DIFFICULTY: str = configload("difficulty.yml")


idleprint = lambda *msg, style=None, end="\n": printlist(msg, end)

if COLORS:
    idleprint = c.print

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
pets: list = dataload("pets.json")
tools: list = dataload("tools.json")
enchants: dict = dataload("enchants.json")
shop: dict = dataload("shop.json")
armor: dict = dataload("armor.json")

shouldexit: bool = False
lastminelevel: bool = False


TICKS = 1

langdata: dict = dataload("lang/" + LANGUAGE + ".json")

lang.load(langdata)

HELPMSG = lang.HELPMSG
if COLORS:
    HELPMSG = lang.HELPMSGC

PROFILE_V: str = "0.0.11"  # profile version
COMPAT_V: list[str] = [
    "0.0.11"
]  # compatible profile versions

pbooster: int = 0


def progressbar(num: int, cap: int, partitions=20):
    """progressbar ####--"""

    dashes = round(num / (cap / partitions))
    for i in range(partitions):
        if i < dashes:
            idleprint("#", end="")
        else:
            idleprint("-", end="")
    idleprint(" (" + str(num) + "/" + str(cap) + ")")


def getrank(level: int) -> str:
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


def getmult(tool: str, rank: str) -> str:
    """gets multiplier based on rank"""
    return mults[tool][rank]


def intcheck(integer: str) -> bool:
    """checks if a argument is an integer, prints a error message if it is not"""
    try:
        int(integer)
    except ValueError:
        idleprint(lang.NOTINTMSG, style="red")
        return False

    return True


class CommandParser():
    """parses input"""

    def get(self, prompt: str = ">"):
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

        self.adminmode = False

        self.fishcooldown = 1  # cooldowns
        self.fishxp = 0
        self.fishlevel = 1
        self.tools = resources.Resources()

        self.equippedHelmet = "leather"
        self.equippedChestplate = "leather"
        self.equippedLeggings = "leather"
        self.equippedBoots = "leather"
        self.armorBonus = 0

        self.allHelmet = ["Leather"]
        self.allChestplate = ["Leather"]
        self.allLeggings = ["Leather"]
        self.allBoots = ["Leather"]

        self.blockspertick = {
            "p": getmult("p", getrank(self.tools.get("p"))),
            "s": getmult("s", getrank(self.tools.get("s"))),
            "a": getmult("a", getrank(self.tools.get("a")))
        }

        self.minelevel = 0

        self.farmgrowth = (1200 - self.tools.get("h") * 5)
        self.produce = resources.Resources()
        self.produce.set("wheat-seed", 10)

        self.farmlevel = 0

        self.battlelevel = 0
        self.battlexp = 0

        self.stats = Stats()

    def load(self, filename: str):
        """loads a profile"""
        with open(filename, encoding="utf-8") as jsonfile:
            try:
                profile = json.load(jsonfile)
            except json.JSONDecodeError:
                idleprint(lang.BADPROFILEMSG, style="red")
                return

        if (not "DATA_V" in profile) or (not profile["DATA_V"] in COMPAT_V):
            idleprint(lang.INCOMPATDATAMSG, style="red")
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
        self.tools = resources.load(profile["tools"])
        self.pets = profile["pets"]
        self.produce = resources.load(profile["produce"])
        self.farmlevel = profile["farmlevel"]
        self.battlelevel = profile["battlelevel"]
        self.battlexp = profile["battlexp"]
        self.adminmode = profile["adminmode"]
        self.equippedHelmet = profile["helmet"]
        self.equippedChestplate = profile["chestplate"]
        self.equippedLeggings = profile["leggings"]
        self.equippedBoots = profile["boots"]

        self.stats = Stats()
        self.stats.load(profile["stats"])

        self.blockspertick["s"] = getmult("s", getrank(self.tools.get("s")))
        self.blockspertick["p"] = getmult("p", getrank(self.tools.get("p")))

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
            "tools": self.tools.save(),
            "pets": self.pets,
            "produce": self.produce.save(),
            "farmlevel": self.farmlevel,
            "stats": self.stats.save(),
            "battlelevel": self.battlelevel,
            "battlexp": self.battlexp,
            "itemselected": self.itemselected,
            "adminmode": self.adminmode
        }

        with open(file, "w", encoding="utf-8") as jsonfile:
            json.dump(profile, jsonfile)

    def get(self):
        """gets and executes command"""
        self.execute(self.cmdparse.get(PREFIX))

    def _sell(self, itemstosell: resources.Resources):
        """internal function to sell from a dictionary"""
        for item in list(itemstosell.list()):
            if itemstosell.get(item) > 0:
                money = round(itemstosell.get(item) *
                              prices[item] * self.sellbooster)
                idleprint(item + ": " + "$" + f"{money:,}" +
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

    def _individualup(self, tool: str, toolname: str, amount: int, multiplier: int):
        for _ in range(amount):  # stop iterating in this function
            price = self.tools.get(tool) * multiplier
            if price <= self.money:
                self.tools.modify(tool, 1)
                self.money -= price
            else:
                idleprint(lang.COSTMSG, style="red")
                break

        self.blockspertick[tool] = getmult(tool, getrank(self.tools.get(tool)))
        idleprint(lang.UPMSG %
                  (toolname, self.tools.get(tool), getrank(self.tools.get(tool))))

    def upgrade(self, tool: str, amount: int):
        """upgrades tool"""
        index = 0
        toolid = 0
        for _toolid in tools.keys():
            if tool in (_toolid, tools[_toolid]["name"]):
                toolid = _toolid
                break

            index += 1

        if toolid != 0:
            self._individualup(
                toolid, tools[toolid]["name"], amount, tools[toolid]["multiplier"])

            return

        # if nothing matches
        idleprint(lang.ERRMSG + " (in IdleMiner.up)", style="red")

    def miningtick(self):
        """adds resources to inventory"""
        num = random.randint(1, 100)
        for tool in ["p", "s", "a"]:  # some tools doesn't get ticks
            chances = mines[self.biome][self.minelevel][tool]
            for i in chances.keys():
                if num > 100 - chances[i]:
                    tomine = self.blockspertick[tool] + pbooster
                    self.inventory.modify(i, tomine)
                    self.blocksmined += tomine

                    self.stats.tblksmined += tomine
                    self.stats.blksmined.modify(i, tomine)

    def update(self):
        """update fishing and mining levels"""
        global lastminelevel
        toprint = []

        if self.blocksmined >= 4000 * (self.minelevel + 1) and not lastminelevel:
            try:
                mines[self.biome][self.minelevel + 1]
            except IndexError:
                if self.biomeid + 1 >= len(mines):
                    pass  # no more biome upgrades
                else:
                    self.biomeid += 1

                    self.biome = biomes[self.biomeid]
                    self.minelevel = 0
                    self.blocksmined = 0

                    toprint.append(lang.UPBIOMEMSG % self.biome)

                lastminelevel = True
            else:
                self.minelevel += 1
                self.stats.tmineup += 1
                self.blocksmined = 0
                toprint.append(lang.MINEUPMSG % self.minelevel)

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
        idleprint("money:", style="blue", end=" ")
        idleprint(f"{self.money:,}")
        idleprint("lapis:", style="blue", end=" ")
        idleprint(self.lapis)
        idleprint("inventory:", style="blue", end=" ")
        idleprint(self.inventory.save())
        idleprint("tools:", style="blue", end=" ")
        idleprint(self.tools.save())
        idleprint("produce:", style="blue", end=" ")
        idleprint(self.produce.save())
        if lastminelevel:
            idleprint(lang.LASTMINELEVELMSG)
        else:
            idleprint("mine level:", style="blue", end=" ")
            idleprint(self.minelevel, end=" ")
            progressbar(self.blocksmined, (self.minelevel + 1) * 4000)
        idleprint("fishing level:", style="blue", end=" ")
        idleprint(self.fishlevel, end=" ")
        progressbar(self.fishxp, self.fishlevel * 4)
        idleprint("battle level:", style="blue", end=" ")
        idleprint(self.battlelevel, end="")
        progressbar(self.battlexp, (self.battlelevel + 1) * 5)

    def hunt(self):
        """hunts"""
        if self.huntcooldown < 1:
            self.huntcooldown = 300
            self.huntchance = random.randint(0, 100)
            if self.huntchance < 10:
                pet = random.choice(pets[0:(25-(self.huntchance * 2))])
                idleprint(pet)

                self.stats.petscaught += 1
            else:
                lapis = random.randint(1, 10)
                self.lapis += lapis
                idleprint('You didn\'t get a pet :( You now have',
                          self.lapis, 'lapis.')

                self.stats.tlapisearned += lapis
        else:
            idleprint(lang.COOLDOWNMSG % (self.huntcooldown, "hunting"))

    def enchant(self):
        """enchants random tool with random enchant"""
        tier = chr(random.choice([1]) + 96)
        enchant = random.choice(list(enchants[tier].keys()))
        enchantjson = enchants[tier][enchant]
        if input(enchant + "is available, would you like to use it").lower().startswith("y"):
            if self.lapis >= enchantjson["lapis"]:
                tool = input("What tool would you like to enchant? " +
                             str(enchantjson["tools"]) + " are valid tools: ")
                if tool in enchantjson["tools"]:
                    for effect in enchantjson["effects"].keys():
                        if effect == "speed":
                            global pbooster
                            # TODO other tools than p
                            pbooster += enchantjson["effects"]["speed"]

                    self.lapis -= enchantjson["lapis"]
                else:
                    print(lang.INVALIDTOOLMSG)
            else:
                print(lang.NOLAPISMSG)

    def _quiz(self, difficulty: str):
        """internal function for quizzes; returns whether the answer is correct"""
        if not difficulty in quizes:
            print(lang.BADDIFFICULTYMSG)
            return False

        question = random.choice(quizes[difficulty])

        idleprint(question["question"] + "?")
        index = 0
        for i in question["choices"]:
            idleprint(str(index) + ": " + i)
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

    def quiz(self, difficulty: str):
        """asks a quiz question"""
        if self.quizcooldown < 1:
            self.quizcooldown = 300

            if self._quiz(difficulty):
                idleprint(lang.CORRECTANSWERMSG)

                self.money += 3000
            else:
                idleprint(lang.WRONGANSWERMSG)
        else:
            idleprint(lang.COOLDOWNMSG %
                      (self.quizcooldown, "getting quizzed"))

    def shop(self, item: str):
        if item in list(shop):
            if self.money >= shop[item]:
                self.money -= shop[item]
                checkout = item.split("_")
                try:
                    checkout[1] += " " + checkout[2]
                except: pass
                if checkout[len(checkout) - 1] != "boots":
                    print("You spent", shop[item], "coins on an", checkout[0], checkout[1])
                else:
                    print("You spent", shop[item], "coins on a pair of", checkout[0], checkout[1])
                boughtItem = ""
                for i in range(len(checkout) - 1):
                    boughtItem += checkout[i].capitalize()
                if checkout[len(checkout) - 1] == "helmet": #d3banana oof section
                    self.equippedHelmet = checkout[0]
                    self.allHelmet.append(boughtItem)
                    if (len(checkout) == 3):
                        self.equippedHelmet += checkout[1]
                elif checkout[len(checkout) - 1] == "chestplate":
                    self.equippedChestplate = checkout[0]
                    self.allChestplate.append(boughtItem)
                    if (len(checkout) == 3):
                        self.equippedChestplate += checkout[1]
                elif checkout[len(checkout) - 1] == "leggings":
                    self.equippedLeggings = checkout[0]
                    self.allLeggings.append(boughtItem)
                    if (len(checkout) == 3):
                        self.equippedLeggings += checkout[1]
                elif checkout[len(checkout) - 1] == "boots":
                    self.equippedBoots = checkout[0]
                    self.allBoots.append(boughtItem)
                    if (len(checkout) == 3):
                        self.equippedBoots += checkout[1]
            else:
                print("You don't have enough money!")
            self.armorBonus = 0
            for i in range(4):
                self.currentArmor = [self.equippedHelmet, self.equippedChestplate, self.equippedLeggings, self.equippedBoots][i]
                self.armorType = ["helmet", "chestplate", "leggings", "boots"][i]
                self.armorBonus += armor[self.currentArmor][self.armorType]["health"]
        elif item in ["catalog", "catalogue", "c"]:
            for i in range(len(shop)):
                print(list(shop)[i], ":" + str(shop[list(shop)[i]]) + "coins")
        else:
            print("This is not an item in the shop!")
        
    def wardrobe(self):
        print("Current Set:\n")
        print("Helmet:", self.equippedHelmet.capitalize())
        print("Chestplate:", self.equippedChestplate.capitalize())
        print("Leggings:", self.equippedLeggings.capitalize())
        print("Boots:", self.equippedBoots.capitalize(), "\n")

        print("All Armor Owned:\n")
        print("Helmet:", self.allHelmet)
        print("Chestplate:", self.allChestplate)
        print("Leggings:", self.allLeggings)
        print("Boots:", self.allBoots)

    def equip(self, type, piece: str):
        type = type.capitalize()
        if piece == "helmet" and type in self.allHelmet:
            self.equippedHelmet = type
        elif piece == "chestplate" and type in self.allBoots:
            self.equippedChestplate = type
        elif piece == "leggings" and type in self.allLeggings:
            self.equippedLeggings = type
        elif piece == "boots" and type in self.allBoots:
            self.equippedBoots = type
        elif type in list(armor):
            print("You don't have this armor!")
        else:
            print("This armor doesn't exist!")

    def farm(self):
        """farms"""
        if self.farmgrowth < 1:
            self.farmgrowth = (1200 - self.tools.get("h") * 5)
            grown = []
            for crop in farms[self.farmlevel].keys():
                if random.randint(0, 100) <= farms[self.farmlevel][crop]:
                    grown.append(crop)

            for crop in grown:
                amount = self.produce.get(crops[crop]["from"])
                self.produce.zero(crops[crop]["from"])
                for product in crops[crop]["produces"]:
                    self.produce.modify(
                        product, amount * getmult("h", getrank(self.tools.get("h"))))

            idleprint(lang.GROWMSG, str(grown).strip("[] ").replace("'", ""))
        else:
            idleprint(lang.COOLDOWNMSG % (self.farmgrowth, "farming"))

    def fish(self):
        """fishes"""
        if self.fishcooldown < 1:
            self.fishcooldown = 300
            if random.randint(1, 100 - self.fishlevel) == 1:
                idleprint(lang.CATCHTREASUREMSG)

                self.money += 5000
                self.fishxp += 10

                self.stats.tfishxp += 10
                self.stats.ttreasure += 1
            else:
                idleprint(lang.CATCHFISHMSG)
                self.fishxp += 1

                self.produce.modify("fish", 1)

                self.stats.tfishxp += 1
                self.stats.tfish += 1
        else:
            idleprint(lang.COOLDOWNMSG % (self.fishcooldown, "fishing"))

    def battle(self):
        """battle a horde of mobs"""
        difficulty = DIFFICULTY
        DIFFICULTIES = ["easy", "medium", "hard", "really"]
        DAMAGES = [1, 2, 4, 10]
        damage = 1

        horde = random.choice(
            list(mobs.keys())[0:(self.battlelevel + 1) * 3])

        mobhp = mobs[horde]["hp"]
        mobdmg = DAMAGES[DIFFICULTIES.index(DIFFICULTY)]

        stevehp = ((self.battlelevel + 1) * 10) + self.armorBonus

        idleprint("Fighting:", horde, "with hp:", mobhp,
                  "and damage:", str(mobdmg) + ".", "You have", stevehp, "hp")
        cont = input("Do you want to continue(y/N)?")

        if cont == "n":
            return

        while stevehp > 0 and mobhp > 0:
            # if mobhp >= 100:
            #     difficulty = "really"
            #     damage = 10
            # elif mobhp >= 50:
            #     difficulty = "hard"
            #     damage = 4
            # elif mobhp >= 20:
            #     difficulty = "medium"
            #     damage = 2
            if self._quiz(difficulty):
                dmgdone = damage * \
                    getmult("w", getrank(self.tools.get("w")))
                mobhp -= dmgdone
                idleprint(lang.MOBHITMSG % (dmgdone, mobhp))
            else:
                stevehp -= mobdmg
                idleprint(lang.MOBHURTMSG % (mobdmg, stevehp))

            eat = input(lang.WOULDLIKETOEATMSG % stevehp)
            if eat:
                food = self._takefood()
                if food:
                    idleprint(lang.ATEMSG % food)
                    stevehp += 1
                else:
                    idleprint(lang.NOFOODMSG)

        if stevehp == 0:
            idleprint(lang.DEADMSG)

        else:
            self.battlexp += mobs[horde]["xp"]
            idleprint(lang.WINMSG % 1)

    def execute(self, cmd: list[str]):
        """executes command"""
        match cmd:
            # normal commands
            case "s" | "sell":
                self.sell()
            case "sp" | "sell-produce":
                self.sell(True)
            case["upgrade" | "up" | "u", tool, amount]:
                if intcheck(amount):
                    self.upgrade(tool, int(amount))
            case "fish" | "f":
                self.fish()
            case "hunt" | "h":
                self.hunt()
            case "shop", item:
                self.shop(item)
            case "profile" | "p":
                self.profile()
                idleprint("--------")
                self.stats.printstats(idleprint, COLORS)
            case "wardrobe" | "w":
                self.wardrobe()
            case "equip", type, piece:
                self.equip(type, piece)
            case["quiz" | "q", difficulty]:
                self.quiz(difficulty)
            case "farm" | "fm":
                self.farm()
            case "battle" | "b":
                self.battle()
            case "enchant" | "e":
                self.enchant()
            case "exit" | "quit":
                self.save("profile.json")
                global shouldexit
                shouldexit = True
            case "help":
                idleprint(HELPMSG)

            # hacking section
            case "cheat":
                if self.adminmode:
                    self.money += 10000000000000000
                    self.blocksmined += 2000
                    self.farmgrowth = 0
                    self.huntcooldown = 0
                    self.fishcooldown = 0
                    self.quizcooldown = 0
                else:
                    idleprint(
                        lang.ERRMSG + " (in IdleMiner.execute)", style="red")
            case "a\\b\\c\\d\\e\\f\\..\\z\\now\\I\\know\\my\\a\\b\\c's\\now\\will\\you\\sing\\with\\me":
                self.adminmode = True
                idleprint(lang.ABCHACKS)

            # easter egg section
            case ":(":
                idleprint("Oof", style="red")
            case ":)":
                idleprint("Yay", style="green")
            case "whoasked":
                idleprint("I did", style="blue italics")

            # default
            case _:
                idleprint(lang.ERRMSG + " (in IdleMiner.execute)",
                          style="red")


def main():
    """runs idleminer input thread and event loop"""
    queue = []
    try:
        idleprint(HELPMSG)
        steve = IdleMiner()

        if os.path.exists("profile.json"):
            steve.load("profile.json")

        def repeatedget():
            """repeatedly gets input"""

            while not shouldexit:
                nonlocal queue

                steve.get()
                for i in queue:
                    idleprint(i)

                queue = []

        inputthread = threading.Thread(target=repeatedget)
        inputthread.daemon = True
        inputthread.start()

        # background tasks
        while True:
            time.sleep(1 / TICKS)
            steve.miningtick()
            queue.extend(steve.update())

            if shouldexit:
                sys.exit(0)

    except (KeyboardInterrupt, SystemExit, EOFError):
        # doesn't seem to hide the error message, but still saves
        steve.save("profile.json")
        sys.exit(0)


if __name__ == "__main__":
    main()
