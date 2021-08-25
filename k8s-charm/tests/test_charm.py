# Copyright 2021 Ubuntu
# See LICENSE file for licensing details.
#
# Learn more about testing at: https://juju.is/docs/sdk/testing

import unittest

from charm import K8SCharmCharm
from ops.testing import Harness


class TestCharm(unittest.TestCase):
    def setUp(self):
        self.harness = Harness(K8SCharmCharm)
        self.addCleanup(self.harness.cleanup)
        self.harness.begin()

    def test_config_changed(self):
        # TODO
        pass

    def test_fortune_action_success(self):
        # TODO
        pass

    def test_fortune_action_fail(self):
        # TODO
        pass

    def test_nginx_pebble_ready(self):
        # TODO
        pass
