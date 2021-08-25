#!/usr/bin/env python3
# Copyright 2021 Ubuntu
# See LICENSE file for licensing details.
#
# Learn more at: https://juju.is/docs/sdk

"""Charm the service.

Refer to the following post for a quick-start guide that will help you
develop a new k8s charm using the Operator Framework:

    https://discourse.charmhub.io/t/4208
"""

import logging

from ops.charm import CharmBase
from ops.framework import StoredState
from ops.main import main
from ops.model import ActiveStatus

logger = logging.getLogger(__name__)

NGINX_CONF = """
server {{
    listen       {port};
    listen  [::]:{port};
    server_name  localhost;

    location / {{
        root   /usr/share/nginx/html;
        index  index.html index.htm;
    }}

    error_page   500 502 503 504  /50x.html;
    location = /50x.html {{
        root   /usr/share/nginx/html;
    }}
}}
"""


class K8SCharmCharm(CharmBase):
    """Charm the service."""

    _stored = StoredState()

    def __init__(self, *args):
        super().__init__(*args)
        self.framework.observe(
            self.on.nginx_pebble_ready, self._on_nginx_pebble_ready)
        self.framework.observe(self.on.config_changed, self._on_config_changed)
        self.framework.observe(self.on.fortune_action, self._on_fortune_action)
        self._stored.set_default(things=[])

    def _on_nginx_pebble_ready(self, event):
        """Define and start a workload using the Pebble API.

        You'll need to specify the right entrypoint and environment
        configuration for your specific workload. Tip: you can see the
        standard entrypoint of an existing container using docker inspect

        Learn more about Pebble layers at https://github.com/canonical/pebble
        """
        # Get a reference the container attribute on the PebbleReadyEvent
        container = event.workload
        # Define an initial Pebble layer configuration
        pebble_layer = {
            "summary": "nginx layer",
            "description": "pebble config layer for nginx",
            "services": {
                "nginx": {
                    "override": "replace",
                    "summary": "nginx",
                    "command": "nginx-debug -g 'daemon off;'",
                    "startup": "enabled",
                    "environment": {"thing": self.model.config["thing"]},
                }
            },
        }
        # Add intial Pebble config layer using the Pebble API
        container.add_layer("nginx", pebble_layer, combine=True)
        # Autostart any services that were defined with startup: enabled
        container.autostart()
        self._push_nginx_config(container)
        # Learn more about statuses in the SDK docs:
        # https://juju.is/docs/sdk/constructs#heading--statuses
        self.unit.status = ActiveStatus()

    def _on_config_changed(self, _):
        """Just an example to show how to deal with changed configuration.

        If you don't need to handle config, you can remove this method,
        the hook created in __init__.py for it, the corresponding test,
        and the config.py file.

        Learn more about config at https://juju.is/docs/sdk/config
        """
        current = self.config["thing"]
        if current not in self._stored.things:
            logger.debug("found a new thing: %r", current)
            self._stored.things.append(current)
        logger.info(">>>>>> %s\n", self.config["my-config-option"])
        container = self.unit.get_container("nginx")
        if "nginx" in container.get_services():
            self._push_nginx_config(container)
            logger.info("Stopping Nginx")
            container.stop("nginx")
            logger.info("Starting Nginx")
            container.start("nginx")

    def _on_fortune_action(self, event):
        """Just an example to show how to receive actions.

        If you don't need to handle actions, you can remove this method,
        the hook created in __init__.py for it, the corresponding test,
        and the actions.py file.

        Learn more about actions at https://juju.is/docs/sdk/actions
        """
        fail = event.params["fail"]
        if fail:
            event.fail(fail)
        else:
            event.set_results({
                "fortune": ("A bug in the code is worth two "
                            "in the documentation.")})

    def _push_nginx_config(self, container):
        logger.info("Nginx port >>> %s", self.config["port"])
        conf = NGINX_CONF.format(port=self.config["port"])
        logger.info("Pushing the Nginx config")
        container.push("/etc/nginx/conf.d/default.conf", conf)


if __name__ == "__main__":
    main(K8SCharmCharm)
