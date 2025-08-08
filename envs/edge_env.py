import gymnasium as gym
import numpy as np
from envs.prometheus_client import get_node_metrics
from utils.k8s_control import scale_deployment

class EdgeEnv(gym.Env):
    """
    특정 node를 위한 개별 환경
    node_name: 어떤 worker node에 대한 환경인지 지정
    """
    def __init__(self, node_name, agent_type="scaling", neighbor_agent_name=None):
        super().__init__()
        self.node_name = node_name
        self.agent_type = agent_type  # "scaling" or "placement"
        self.neighbor_agent_name = neighbor_agent_name  # 1:1 매칭된 placement node
        self.action_space = gym.spaces.Discrete(3 if agent_type=="scaling" else 2)
        # scaling: [0=do nothing, 1=add local, 2=request neighbor]
        # placement: [0=local place, 1=neighbor]
        self.observation_space = gym.spaces.Box(0, np.inf, shape=(3,), dtype=np.float32)
        self.current_replicas = 1
        self.env_dict = None  # train_edge.py에서 할당 (다른 env 접근용)  ### 수정

        self.forward_penalty = 0.0 # 다른 placement로 전달한 횟수에 대한 패널티

    def step(self, action):
        cpu, pods, req = get_node_metrics(self.node_name)

        if self.agent_type == "scaling":
            if action == 1:
                # local pod 추가
                self.current_replicas += 1
                scale_deployment(self.current_replicas, target_node=self.node_name)

            elif action == 2:
                # Neighbor placement agent에게 요청
                if self.env_dict and self.neighbor_agent_name in self.env_dict:
                    neighbor_env = self.env_dict[self.neighbor_agent_name]
                    # TTL = 1로 요청 (placement agent가 다른 곳으로 넘길 수 있는 횟수)
                    neighbor_env.handle_request(request_source=self.node_name, ttl=1)

        else:  # placement agent
            if action == 1:
                # (자율적 배치: 기본 step 안에서는 별도 동작 없음, 요청은 handle_request로 처리)
                pass

        # 상태 업데이트
        cpu2, pods2, req2 = get_node_metrics(self.node_name)
        obs = np.array([cpu2, pods2, req2], dtype=np.float32)

        # reward 설계
        if self.agent_type == "scaling":
            reward = -(pods2 * 0.1 + max(0, req2 - pods2))
        else:
            reward = -(max(0, req2 - pods2))

        done = False
        return obs, reward, done, False, {}

    ### 수정: placement agent가 scaling agent 요청을 처리하는 함수 추가
    def handle_request(self, request_source, ttl=1):
        """
        scaling agent나 다른 placement agent로부터 요청을 받았을 때 처리.
        ttl: 다른 placement agent에게 전달할 수 있는 남은 횟수
        """
        if self.agent_type != "placement":
            return  # placement agent만 처리

        print(f"[Placement Agent] {self.node_name} received a request from {request_source} (ttl={ttl})")

        # 간단한 로직: 자신의 노드 상태를 확인
        cpu, pods, req = get_node_metrics(self.node_name)

        # 여기서는 CPU 부하가 높다고 가정할 조건을 단순화 (예: pods > 5이면 부족)
        if pods > 5 and ttl > 0:
            # 다른 placement agent를 찾아서 한 번만 전달
            # env_dict에서 다른 placement agent를 선택
            other_candidates = [
                env for env in self.env_dict.values()
                if env.agent_type == "placement" and env.node_name != self.node_name
            ]
            if other_candidates:
                # 첫 번째 다른 placement agent에게 전달
                other_candidates[0].handle_request(request_source, ttl=ttl-1)
                return

        # 로컬에 Pod 1개 추가
        self.current_replicas += 1
        scale_deployment(self.current_replicas, target_node=self.node_name)

    def reset(self, seed=None, options=None):
        cpu, pods, req = get_node_metrics(self.node_name)
        return np.array([cpu, pods, req], dtype=np.float32), {}
