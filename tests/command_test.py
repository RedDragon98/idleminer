"""Tests for steve.get"""
import idleminer  # run in parent directory, so tests should still work

steve = idleminer.IdleMiner()


class TestCommand:
    """tests for commands"""
    @staticmethod
    def test_f():
        """tests f"""
        steve.execute("cheat")
        steve.execute("f")
        assert steve.fishxp == 1

    @staticmethod
    def test_h():
        """tests h"""
        # TODO

    @staticmethod
    def test_cheat():
        """tests cheat"""
        steve.money = 0
        steve.execute("cheat")
        assert steve.money == 10000000

    @staticmethod
    def test_s():
        """tests s"""
        steve.money = 0
        steve.miningtick()
        steve.execute("s")
        assert steve.money > 0
