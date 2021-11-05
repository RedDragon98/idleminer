"""idleminer statistics"""

import resources


class Stats:
    """manages IdleMiner stats"""

    tblksmined = 0  # total blocks mined
    blksmined = resources.Resources()  # blocks mined(per type)

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

    def printstats(self, idleprint, colors):
        """prints these stats"""

        if colors:  # TODO use new idleprint: replace color blocks with style=""
            idleprint("[magenta]Blocks mined[/magenta]:", self.tblksmined,
                      "(" + str(self.blksmined.save()) + ")")

            idleprint("[magenta]Total money earned[/magenta]:",
                      self.tmoneyearned)
            idleprint("[magenta]Total lapis earned[/magenta]:",
                      self.tlapisearned)
            idleprint("[magenta]Pets caught[/magenta]:", self.petscaught)
            idleprint(
                "[magenta]Total rc earned[/magenta]:", self.trcearned)
            idleprint(
                "[magenta]Total mine upgrades[/magenta]:", self.tmineup)
            idleprint(
                "[magenta]Total biome upgrades[/magenta]:", self.tbiomeup)
            idleprint("[magenta]Total questions answered[/magenta]:", self.tqanswered,
                      "(" + str(self.tqcorrect) + " [green]correct[/green])")
            idleprint("[magenta]Total fish xp[/magenta]:", self.tfishxp)
            idleprint("[magenta]Total fish caught[/magenta]:", self.tfish,
                      "(" + str(self.ttreasure) + " [green]treasure[/green])")
        else:
            idleprint("Blocks mined:", self.tblksmined,
                      "(" + str(self.blksmined.save()) + ")")
            idleprint("Total money earned:", self.tmoneyearned)
            idleprint("Total lapis earned:", self.tlapisearned)
            idleprint("Pets caught:", self.petscaught)
            idleprint("Total rc earned:", self.trcearned)
            idleprint("Total mine upgrades:", self.tmineup)
            idleprint("Total biome upgrades:", self.tbiomeup)
            idleprint("Total questions answered:", self.tqanswered,
                      "(" + str(self.tqcorrect) + " correct)")
            idleprint("Total fish xp:", self.tfishxp)
            idleprint("Total fish caught:", self.tfish,
                      "(" + str(self.ttreasure) + " treasure)")

    def load(self, obj: dict):
        """load stats from dict"""
        self.tblksmined = obj["tblksmined"]
        self.blksmined = resources.load(obj["blksmined"])
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
        obj["blksmined"] = self.blksmined.save()
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
