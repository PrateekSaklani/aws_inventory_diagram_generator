"""
Kubernetes Workload Collector for EKS Clusters

Connects to EKS clusters using local kubeconfig and collects:
- Namespaces
- Deployments
- Pods (mapped to nodes)
- Services
"""

from typing import Dict, Any, List, Optional, Tuple

from kubernetes import client, config
from kubernetes.client.rest import ApiException

from utils.logger import get_logger

logger = get_logger(__name__)


class K8sCollector:
    """Collects Kubernetes workload information from EKS clusters using local kubeconfig."""

    def __init__(self, region: str = None):
        self.region = region

    def _get_context_for_cluster(self, cluster_name: str) -> Optional[str]:
        """Find kubeconfig context matching the cluster name."""
        try:
            contexts, _ = config.list_kube_config_contexts()
            for ctx in contexts:
                ctx_name = ctx.get('name', '')
                if cluster_name in ctx_name:
                    return ctx_name
            return None
        except Exception as e:
            logger.warning(f"Failed to list kubeconfig contexts: {e}")
            return None

    def _create_k8s_client(self, cluster_info: Dict[str, Any]) -> Optional[Tuple[client.CoreV1Api, client.AppsV1Api]]:
        """Create Kubernetes API client using local kubeconfig."""
        cluster_name = cluster_info.get("cluster_name", "")

        context_name = self._get_context_for_cluster(cluster_name)
        if not context_name:
            logger.error(f"No kubeconfig context found for cluster {cluster_name}")
            return None

        logger.info(f"Using kubeconfig context: {context_name}")

        try:
            config.load_kube_config(context=context_name)
            return client.CoreV1Api(), client.AppsV1Api()
        except Exception as e:
            logger.error(f"Failed to create K8s client: {e}")
            return None

    def collect_cluster_workloads(self, cluster_info: Dict[str, Any]) -> Dict[str, Any]:
        """Collect all workloads from an EKS cluster."""
        cluster_name = cluster_info.get("cluster_name", "unknown")
        logger.info(f"Collecting workloads from EKS cluster: {cluster_name}")

        result = {
            "cluster_name": cluster_name,
            "namespaces": [],
            "deployments": [],
            "pods": [],
            "services": [],
            "pods_by_node": {},
            "error": None
        }

        try:
            clients = self._create_k8s_client(cluster_info)
            if not clients:
                result["error"] = "Failed to create Kubernetes client"
                return result

            core_api, apps_api = clients

            # Get namespaces
            try:
                ns_list = core_api.list_namespace()
                result["namespaces"] = [
                    {
                        "name": ns.metadata.name,
                        "status": ns.status.phase,
                        "labels": ns.metadata.labels or {}
                    }
                    for ns in ns_list.items
                ]
                logger.info(f"  Found {len(result['namespaces'])} namespaces")
            except ApiException as e:
                logger.warning(f"Failed to list namespaces: {e.reason}")

            # Get deployments
            try:
                deploy_list = apps_api.list_deployment_for_all_namespaces()
                result["deployments"] = [
                    {
                        "name": d.metadata.name,
                        "namespace": d.metadata.namespace,
                        "replicas": d.spec.replicas or 0,
                        "ready_replicas": d.status.ready_replicas or 0,
                        "available_replicas": d.status.available_replicas or 0,
                        "labels": d.metadata.labels or {},
                        "selector": d.spec.selector.match_labels or {} if d.spec.selector else {}
                    }
                    for d in deploy_list.items
                ]
                logger.info(f"  Found {len(result['deployments'])} deployments")
            except ApiException as e:
                logger.warning(f"Failed to list deployments: {e.reason}")

            # Get pods with node assignment
            try:
                pod_list = core_api.list_pod_for_all_namespaces()
                pods_by_node = {}

                for pod in pod_list.items:
                    pod_info = {
                        "name": pod.metadata.name,
                        "namespace": pod.metadata.namespace,
                        "node_name": pod.spec.node_name,
                        "status": pod.status.phase,
                        "pod_ip": pod.status.pod_ip,
                        "host_ip": pod.status.host_ip,
                        "labels": pod.metadata.labels or {},
                        "containers": [
                            {
                                "name": c.name,
                                "image": c.image.split("/")[-1] if c.image else "unknown",
                                "image_full": c.image
                            }
                            for c in pod.spec.containers
                        ]
                    }
                    result["pods"].append(pod_info)

                    # Group by node
                    node_name = pod.spec.node_name or "unscheduled"
                    pods_by_node.setdefault(node_name, []).append(pod_info)

                result["pods_by_node"] = pods_by_node
                logger.info(f"  Found {len(result['pods'])} pods across {len(pods_by_node)} nodes")
            except ApiException as e:
                logger.warning(f"Failed to list pods: {e.reason}")

            # Get services
            try:
                svc_list = core_api.list_service_for_all_namespaces()
                result["services"] = [
                    {
                        "name": svc.metadata.name,
                        "namespace": svc.metadata.namespace,
                        "type": svc.spec.type,
                        "cluster_ip": svc.spec.cluster_ip,
                        "external_ip": svc.status.load_balancer.ingress[0].hostname
                            if svc.status.load_balancer and svc.status.load_balancer.ingress
                            else None,
                        "ports": [
                            {"port": p.port, "target_port": str(p.target_port), "protocol": p.protocol}
                            for p in (svc.spec.ports or [])
                        ],
                        "selector": svc.spec.selector or {}
                    }
                    for svc in svc_list.items
                ]
                logger.info(f"  Found {len(result['services'])} services")
            except ApiException as e:
                logger.warning(f"Failed to list services: {e.reason}")

        except Exception as e:
            logger.error(f"Error collecting workloads from {cluster_name}: {e}")
            result["error"] = str(e)

        return result

    def collect_all_clusters(self, eks_clusters: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """Collect workloads from all EKS clusters."""
        all_workloads = {}

        for cluster in eks_clusters:
            cluster_name = cluster.get("cluster_name", "unknown")
            workloads = self.collect_cluster_workloads(cluster)
            all_workloads[cluster_name] = workloads

        return all_workloads
