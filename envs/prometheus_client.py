import requests
from utils.config import PROM_URL

def query_prometheus(promql: str):
    resp = requests.get(f"{PROM_URL}/api/v1/query", params={"query": promql})
    data = resp.json()
    return data["data"]["result"]

def get_cluster_metrics():
    """
    중앙집중형 상태 정보:
    - CPU 사용률 평균
    - 현재 전체 Pod 수
    - 최근 1분간 처리 요청 수 (istio_requests_total)
    """
    cpu = query_prometheus('avg(rate(container_cpu_usage_seconds_total{container!=""}[15s]))')
    pods = query_prometheus('count(kube_pod_info)')
    req = query_prometheus('sum(rate(istio_requests_total[1m]))')

    cpu_val = float(cpu[0]['value'][1]) if cpu else 0.0
    pods_val = float(pods[0]['value'][1]) if pods else 0.0
    req_val = float(req[0]['value'][1]) if req else 0.0
    print(cpu_val, pods_val, req_val)

    return cpu_val, pods_val, req_val

def get_node_metrics(node_name: str):
    """
    분산형 상태 정보 (특정 node 기준)
    """
    cpu = query_prometheus(
        f'avg(rate(node_cpu_seconds_total{{mode!="idle",instance=~"{node_name}.*"}}[1m]))'
    )
    pods = query_prometheus(f'count(kube_pod_info{{node="{node_name}"}})')
    req = query_prometheus(f'sum(rate(istio_requests_total[1m])) by (destination_service)')
    cpu_val = float(cpu[0]['value'][1]) if cpu else 0.0
    pods_val = float(pods[0]['value'][1]) if pods else 0.0
    req_val = float(req[0]['value'][1]) if req else 0.0
    return cpu_val, pods_val, req_val
