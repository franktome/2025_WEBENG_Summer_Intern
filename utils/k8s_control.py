from kubernetes import client, config

# kubeconfig 경로 명시적으로 지정 (Windows 경로)
config.load_kube_config(config_file="C:/Users/webeng/.kube/config")

apps_v1 = client.AppsV1Api()

def scale_deployment(replica_count, target_node=None):
    if target_node:
        body = {
            "spec": {
                "replicas": replica_count,
                "template": {
                    "spec": {
                        "nodeSelector": {
                            "kubernetes.io/hostname": target_node
                        }
                    }
                }
            }
        }
    else:
        body = {"spec": {"replicas": replica_count}}

    apps_v1.patch_namespaced_deployment(
        name="productpage",           # ← nginx deployment 이름
        namespace="bookinfo",   # ← 네임스페이스 변경
        body=body
    )
    if target_node==None:
        print(f"[ACTION] Deployment scaled to {replica_count} by scheduler")
    else:
        print(f"[ACTION] Deployment scaled to {replica_count} on {target_node}")
