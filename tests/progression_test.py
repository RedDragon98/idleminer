"""tests for progression"""
import idleminer

steve = idleminer.IdleMiner()


class TestProgression:
    """tests upgrades"""

    @staticmethod
    def test_mineup():
        """tests mine upgrades"""
        steve.blocksmined = 2000
        steve.update()
        assert steve.blocksmined == 0
        assert steve.minelevel == 1

    @staticmethod
    def test_fishup():
        """tests fish level upgrades"""
        steve.fishxp = 4
        steve.update()
        assert steve.fishxp == 0
        assert steve.fishlevel == 2

    @staticmethod
    def test_battleup():
        """tests battle level upgrades"""
        steve.battlexp = 5
        steve.update()
        assert steve.battlexp == 0
        assert steve.battlelevel == 1

    @staticmethod
    def test_biomeup():
        """tests biome upgrades"""
        steve.minelevel = 4
        steve.blocksmined = 10000
        steve.update()
        assert steve.biome == "forest"
        assert steve.minelevel == 0
