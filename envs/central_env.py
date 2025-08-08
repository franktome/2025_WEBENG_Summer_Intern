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
        self.action_space = gym.spaces.Discrete(5)  # 0~4 pods 추가
        self.observation_space = gym.spaces.Box(0, np.inf, shape=(4,), dtype=np.float32)
        self.current_replicas = 1
        self.current_step = 0
        self.max_steps = 30
        self.prev_req = 0

    def step(self, action):

        # delta = action - 4
        # self.current_replicas += delta
        # self.current_replicas = np.clip(self.current_replicas, self.min_replicas, self.max_replicas)
        # scale_deployment(int(self.current_replicas))
        if action > 0:
            self.current_replicas += action
            self.current_replicas = min(self.max_replicas, self.current_replicas)
            scale_deployment(self.current_replicas)

        cpu, pods, req = get_cluster_metrics()
        req_delta = req - self.prev_req
        self.prev_req = req

        obs = np.array([cpu, pods, req, req_delta], dtype=np.float32)

        reward = (req_delta * 0.5) - (cpu*0.3) - (pods*0.1)
        reward = np.clip(reward, -5.0, 5.0)
        self.current_step += 1
        done = self.current_step >= self.max_steps
        return obs, reward, done, False, {}

    def reset(self, seed=None, options=None):
        self.current_step = 0
        cpu, pods, req = get_cluster_metrics()
        self.prev_req = req
        req_delta = 0.0
        return np.array([cpu, pods, req, req_delta], dtype=np.float32), {}
