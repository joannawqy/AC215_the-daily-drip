"""
A Pulumi project to deploy a GKE cluster and the 'the-daily-drip' application.
This is a DEMONSTRATION file showing how infrastructure code looks.
"""

import pulumi
from pulumi_gcp import container
from pulumi_kubernetes import Provider, apps, core, meta
import pulumi_kubernetes as k8s

# --- Configuration ---
# In a real setup, we would read these from pulumi config
project = "ac215-480602"
region = "us-central1"
zone = "us-central1-a"
app_name = "daily-drip"
repo_name = "the-daily-drip-app"

# --- 1. Infrastructure: GKE Cluster ---
# Create a GKE cluster
cluster_name = f"{app_name}-cluster"

# Note: In a real/production environment, you would configure node pools,
# VPC networking, and authorized networks here.
cluster = container.Cluster(cluster_name,
    initial_node_count=1,
    min_master_version="latest",
    node_version="latest",
    location=zone,
    node_config=container.ClusterNodeConfigArgs(
        machine_type="e2-medium", # Cost-effective for demo
        oauth_scopes=[
            "https://www.googleapis.com/auth/compute",
            "https://www.googleapis.com/auth/devstorage.read_only",
            "https://www.googleapis.com/auth/logging.write",
            "https://www.googleapis.com/auth/monitoring"
        ],
    ),
)

# Export the Cluster Name
pulumi.export("cluster_name", cluster.name)

# --- 2. Kubernetes Provider Setup ---
# We need to create a Kubernetes provider instance that uses the credentials
# from the newly created GKE cluster.
k8s_info = pulumi.Output.all(cluster.name, cluster.endpoint, cluster.master_auth)
k8s_config = k8s_info.apply(
    lambda info: """apiVersion: v1
clusters:
- cluster:
    certificate-authority-data: {0}
    server: https://{1}
  name: {2}
contexts:
- context:
    cluster: {2}
    user: {2}
  name: {2}
current-context: {2}
kind: Config
preferences: {{}}
users:
- name: {2}
  user:
    auth-provider:
      config:
        cmd-args: config config-helper --format=json
        cmd-path: gcloud
        expiry-key: '{{.credential.token_expiry}}'
        token-key: '{{.credential.access_token}}'
      name: gcp
""".format(info[2]['cluster_ca_certificate'], info[1], info[0]))

# Create the Provider
k8s_provider = Provider("gke_drip_provider", kubeconfig=k8s_config)

# --- 3. Application Deployment ---

# Read the Docker Image Tag from Pulumi Config (passed from CI/CD)
# Default to 'latest' if not provided
config = pulumi.Config()
image_tag = config.get("image_tag") or "latest"
full_image_name = f"gcr.io/{project}/{repo_name}:{image_tag}"

# Create the Namespace (Optional, but good practice)
ns = core.v1.Namespace("app-ns",
    metadata=meta.v1.ObjectMetaArgs(name="daily-drip-ns"),
    opts=pulumi.ResourceOptions(provider=k8s_provider)
)

# Deployment
app_labels = {"app": app_name}
deployment = apps.v1.Deployment("app-deployment",
    metadata=meta.v1.ObjectMetaArgs(
        name="daily-drip-deployment",
        namespace=ns.metadata.name,
    ),
    spec=apps.v1.DeploymentSpecArgs(
        replicas=1,
        selector=meta.v1.LabelSelectorArgs(match_labels=app_labels),
        template=core.v1.PodTemplateSpecArgs(
            metadata=meta.v1.ObjectMetaArgs(labels=app_labels),
            spec=core.v1.PodSpecArgs(
                containers=[core.v1.ContainerArgs(
                    name="daily-drip",
                    image=full_image_name,
                    resources=core.v1.ResourceRequirementsArgs(
                        requests={"cpu": "500m", "memory": "2Gi"}, # Adjusted for e2-medium
                        limits={"cpu": "1000m", "memory": "4Gi"}
                    ),
                    env=[
                        core.v1.EnvVarArgs(name="PORT", value="8000"),
                        # Example of secrets:
                        # In production, you would Create a Secret resource in Pulumi
                        # using config.require_secret("openai_key")
                        core.v1.EnvVarArgs(
                            name="OPENAI_API_KEY",
                            value_from=core.v1.EnvVarSourceArgs(
                                secret_key_ref=core.v1.SecretKeySelectorArgs(
                                    name="openai-api-key", # Assumes this secret exists or created elsewhere
                                    key="key"
                                )
                            )
                        )
                    ],
                )]
            ),
        ),
    ),
    opts=pulumi.ResourceOptions(provider=k8s_provider)
)

# Service
service = core.v1.Service("app-service",
    metadata=meta.v1.ObjectMetaArgs(
        name="daily-drip-service",
        namespace=ns.metadata.name,
    ),
    spec=core.v1.ServiceSpecArgs(
        selector=app_labels,
        ports=[core.v1.ServicePortArgs(
            port=80,
            target_port=8000,
            protocol="TCP"
        )],
        type="LoadBalancer"
    ),
    opts=pulumi.ResourceOptions(provider=k8s_provider)
)

# Export the Service External IP
pulumi.export("service_ip", service.status.load_balancer.ingress[0].ip)
