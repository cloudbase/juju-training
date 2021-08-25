# Copyright 2021 Ubuntu
# See LICENSE file for licensing details.
#
# Learn more about testing at: https://juju.is/docs/sdk/testing

import unittest
from unittest.mock import Mock

from charm import K8SCharmCharm
from ops.model import ActiveStatus
from ops.testing import Harness


class TestCharm(unittest.TestCase):
    def setUp(self):
        self.harness = Harness(K8SCharmCharm)
        self.addCleanup(self.harness.cleanup)
        self.harness.begin()

    def test_config_changed(self):
        self.assertEqual(list(self.harness.charm._stored.things), [])
        self.harness.update_config({"thing": "foo"})
        self.assertEqual(list(self.harness.charm._stored.things), ["foo"])

    def test_action(self):
        # the harness doesn't (yet!) help much with actions themselves
        action_event = Mock(params={"fail": ""})
        self.harness.charm._on_fortune_action(action_event)

        self.assertTrue(action_event.set_results.called)

    def test_action_fail(self):
        action_event = Mock(params={"fail": "fail this"})
        self.harness.charm._on_fortune_action(action_event)

        self.assertEqual(action_event.fail.call_args, [("fail this",)])

    def test_nginx_pebble_ready(self):
        # Check the initial Pebble plan is empty
        initial_plan = self.harness.get_container_pebble_plan("nginx")
        self.assertEqual(initial_plan.to_yaml(), "{}\n")
        # Expected plan after Pebble ready with default config
        expected_plan = {
            "services": {
                "nginx": {
                    "override": "replace",
                    "summary": "nginx",
                    "command": "nginx-debug -g 'daemon off;'",
                    "startup": "enabled",
                    "environment": {"thing": "🎁"},
                }
            },
        }
        # Get the nginx container from the model
        container = self.harness.model.unit.get_container("nginx")
        # Emit the PebbleReadyEvent carrying the nginx container
        self.harness.charm.on.nginx_pebble_ready.emit(container)
        # Get the plan now we've run PebbleReady
        updated_plan = self.harness.get_container_pebble_plan(
            "nginx").to_dict()
        # Check we've got the plan we expected
        self.assertEqual(expected_plan, updated_plan)
        # Check the service was started
        service = self.harness.model.unit.get_container(
            "nginx").get_service("nginx")
        self.assertTrue(service.is_running())
        # Ensure we set an ActiveStatus with no message
        self.assertEqual(self.harness.model.unit.status, ActiveStatus())
