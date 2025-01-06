import logging

from kubernetes import client
from utility.data import ensure_list

from .base import KubeBase

logger = logging.getLogger(__name__)


class KubeAgent(KubeBase):
    def get_spec(self, name, command):
        type = "agent"
        labels = self._get_labels(name, type)

        if not command:
            command = []

        return client.V1Deployment(
            api_version="apps/v1",
            kind="Deployment",
            metadata=self._get_metadata_spec(labels, name),
            spec=client.V1DeploymentSpec(
                replicas=1,
                revision_history_limit=2,
                selector=client.V1LabelSelector(match_labels=self._get_selector_labels(name, type)),
                template=self._get_pod_spec(
                    name,
                    labels,
                    ["zimagi", *ensure_list(command)],
                    env={"ZIMAGI_CLI_EXEC": "True", "ZIMAGI_WORKER_EXEC": "True"},
                    restart_policy="Always",
                ),
            ),
        )

    def check(self, name):
        try:
            self.cluster.apps_api.read_namespaced_deployment(name, self.cluster.namespace)

        except client.ApiException as e:
            if e.status == 404:
                return False
            else:
                raise e
        return True

    def create(self, name, command):
        def create_agent(cluster):
            cluster.apps_api.create_namespaced_deployment(cluster.namespace, self.get_spec(name, command), pretty=False)

        return self.cluster.exec(f"create {self.type} agent", create_agent)

    def destroy(self, name):
        def destroy_agent(cluster):
            cluster.apps_api.delete_namespaced_deployment(name, cluster.namespace)

        return self.cluster.exec(f"destroy {self.type} agent", destroy_agent)
