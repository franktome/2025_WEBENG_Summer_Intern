import gymnasium as gym
import numpy as np
from envs.prometheus_client import get_cluster_metrics
from utils.k8s_control import scale_deployment

# train_central.py에서 이 환경을 사용해 한 개의 중앙 RL agent를 학습시킴
# 이 agent는 전체 클러스터의 상태를 보고 전역 scale 결정을 내린다.

class CentralEnv(gym.Env):
    max_replicas = 100
    min_replicas = 0

    def __init__(self):
        super().__init__()
        self.action_space = gym.spaces.Discrete(8)  # 0~4 pods 추가
        self.observation_space = gym.spaces.Box(0, np.inf, shape=(3,), dtype=np.float32)
        self.current_replicas = 1
        self.current_step = 0
        self.max_steps = 30
        self.prev_req = 0

        # 보상함수 관련 설정
        self.target_u = 0.6
        self.alpha = 3.0
        self.beta = 0.05
        self.eps = 0.05  # 데드존 폭

    def step(self, action):
        action_map = [0, 0, 0, 0, 1, 2, 3, 4]  # pod를 늘리는 것과 pod를 늘리지 않는 것의 비율이 50:50이 되도록 함.
        action = action_map[int(action)]

        if action > 0:
            self.current_replicas += action
            self.current_replicas = min(self.max_replicas, self.current_replicas)
            scale_deployment(self.current_replicas)

        cpu, req, pods = get_cluster_metrics()
        req_delta = req - self.prev_req
        self.prev_req = req
        obs = np.array([cpu, req_delta, pods], dtype=np.float32)

        # 보상함수 파트
        u = float(cpu)  # cpu가 vCPU 기준이면 0~1 범위가 되도록 스케일 확인
        err = abs(u - self.target_u) - self.eps
        err = err if err > 0 else 0.0  # 데드존 적용
        reward = -(self.alpha * (err ** 2)) - (self.beta * self.current_replicas)
        reward = float(np.clip(reward, -10.0, 10.0))

        self.current_step += 1
        done = self.current_step >= self.max_steps
        return obs, reward, done, False, {}

    def reset(self, seed=None, options=None):
        self.current_step = 0
        cpu, req, pods = get_cluster_metrics()
        self.prev_req = req
        req_delta = 0.0
        return np.array([cpu, req_delta, pods], dtype=np.float32), {}
