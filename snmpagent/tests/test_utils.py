import unittest

import tempfile
from snmpagent import utils


class TestUtils(unittest.TestCase):
    def test_setup_log(self):
        utils.setup_log(tempfile.gettempdir() + "/logfile.log",
                        level="debug")
