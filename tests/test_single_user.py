import os
import sys
import unittest

# Add selfbot to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from config import Config
from database import Database, db
from modules.clock import format_time, FONT_STYLES
from modules.anti_delete import cache_message, message_cache
from modules.casino import get_emoji_result_text, EMOJI_DICE, EMOJI_SLOT

class TestSingleUserSelfBot(unittest.TestCase):

    def test_database_initialization(self):
        self.assertIsNotNone(db)
        clock = db.get_clock()
        self.assertIn("enabled", clock)
        self.assertIn("font_style", clock)

        ad = db.get_anti_delete()
        self.assertIn("enabled", ad)

        casino = db.get_casino()
        self.assertGreaterEqual(casino.get("balance", 0), 0)

    def test_clock_formatting(self):
        for style in FONT_STYLES.keys():
            formatted = format_time(style=style, show_heart=True)
            self.assertTrue(len(formatted) > 3, f"Failed for style: {style}")

    def test_casino_balance_and_records(self):
        initial_bal = db.get_casino()["balance"]
        db.record_bet(won=True, amount=500)
        self.assertEqual(db.get_casino()["balance"], initial_bal + 500)

        db.record_bet(won=False, amount=200)
        self.assertEqual(db.get_casino()["balance"], initial_bal + 300)

        dice_res = get_emoji_result_text(EMOJI_DICE, 6)
        self.assertIn("6", dice_res)

    def test_enemies_management(self):
        test_uid = 99887766
        db.add_enemy(test_uid, mode="text", value="تست ترول")
        self.assertIsNotNone(db.is_enemy(test_uid))
        self.assertEqual(db.is_enemy(test_uid)["mode"], "text")

        db.remove_enemy(test_uid)
        self.assertIsNone(db.is_enemy(test_uid))

    def test_triggers_auto_reply(self):
        db.add_trigger("قیمت", "خدمات رایگان است!")
        triggers = db.get_triggers()
        self.assertIn("قیمت", triggers)
        self.assertEqual(triggers["قیمت"], "خدمات رایگان است!")

        db.remove_trigger("قیمت")
        self.assertNotIn("قیمت", db.get_triggers())

    def test_stats_increment(self):
        initial = db.get_stats().get("commands_run", 0)
        db.increment_stat("commands_run", 5)
        self.assertEqual(db.get_stats().get("commands_run", 0), initial + 5)

if __name__ == "__main__":
    unittest.main()
