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
import urllib
from subprocess import CalledProcessError, check_call, check_output

from ops.charm import CharmBase
from ops.framework import StoredState
from ops.main import main
from ops.model import ActiveStatus, MaintenanceStatus, BlockedStatus

logger = logging.getLogger(__name__)

NGINX_CONF_FILE_PATH = "/etc/nginx/sites-available/default"
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


class MachineCharmCharm(CharmBase):
    """Charm the service."""

    _stored = StoredState()

    def __init__(self, *args):
        super().__init__(*args)
        self.framework.observe(self.on.install, self._on_install)
        self.framework.observe(self.on.config_changed, self._on_config_changed)
        self.framework.observe(self.on.start, self._on_start)
        self.framework.observe(self.on.fortune_action, self._on_fortune_action)
        self.framework.observe(self.on.fetch_file_action,
                               self._on_fetch_file_action)
        self._stored.set_default(things=[])

    def _on_install(self, _):
        logger.info("Installing Nginx package")
        self.unit.status = MaintenanceStatus("Installing Nginx")
        self._install_apt_packages(["nginx"])

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
        logger.info("Nginx port: %s", self.config["port"])
        with open(NGINX_CONF_FILE_PATH, "w") as f:
            f.write(NGINX_CONF.format(port=self.config["port"]))
        check_call(["systemctl", "reload", "nginx"])

    def _on_start(self, _):
        logger.info("Starting Nginx service")
        check_call(["systemctl", "start", "nginx"])
        self.unit.status = ActiveStatus("Unit is ready")
        self.app.status = ActiveStatus("Application is ready")

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

    def _on_fetch_file_action(self, event):
        url = event.params["url"]
        try:
            output_file = "/usr/share/nginx/html/test.html"
            urllib.request.urlretrieve(url, output_file)
            event.set_results({"result": "Download succeded"})
        except Exception:
            event.set_results({"result": "Download failed"})

    def _install_apt_packages(self, packages: list):
        """Simple wrapper around 'apt-get install -y"""
        try:
            logger.debug("updating apt cache")
            check_output(["apt-get", "update"])
            logger.debug("installing apt packages: %s", ", ".join(packages))
            check_output(["apt-get", "install", "-y"] + packages)
        except CalledProcessError as e:
            logger.error("failed to install packages: %s", ", ".join(packages))
            logger.debug("apt error: %s", e.output)
            self.unit.status = BlockedStatus("Failed to install packages")


if __name__ == "__main__":
    main(MachineCharmCharm)
