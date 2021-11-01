"""idleminer statistics"""


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
        "leaves": 0,
        "glow-berry": 0
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

    def printstats(self, colors: bool, console):
        """prints these stats"""

        if colors:
            console.print("[magenta]Blocks mined[/magenta]:", self.tblksmined,
                          "(" + str(self.blksmined) + ")")

            console.print("[magenta]Total money earned[/magenta]:",
                          self.tmoneyearned)
            console.print("[magenta]Total lapis earned[/magenta]:",
                          self.tlapisearned)
            console.print("[magenta]Pets caught[/magenta]:", self.petscaught)
            console.print(
                "[magenta]Total rc earned[/magenta]:", self.trcearned)
            console.print(
                "[magenta]Total mine upgrades[/magenta]:", self.tmineup)
            console.print(
                "[magenta]Total biome upgrades[/magenta]:", self.tbiomeup)
            console.print("[magenta]Total questions answered[/magenta]:", self.tqanswered,
                          "(" + str(self.tqcorrect) + " [green]correct[/green])")
            console.print("[magenta]Total fish xp[/magenta]:", self.tfishxp)
            console.print("[magenta]Total fish caught[/magenta]:", self.tfish,
                          "(" + str(self.ttreasure) + " [green]treasure[/green])")
        else:
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
