import torch
from envs.edge_env import EdgeEnv
from agents.dqn import DQNAgent
from agents.replay_buffer import ReplayBuffer

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# 1:1 매칭된 쌍 (scaling_node, placement_node)
pairs = [
    ("worker1", "worker3"),
    ("worker2", "worker4")
]

agents = []
buffers = []
envs = []

# 각 쌍에 대해 scaling agent와 placement agent를 생성
for scale_node, place_node in pairs:
    # scaling agent: neighbor_agent_name 지정
    scaling_env = EdgeEnv(scale_node, agent_type="scaling", neighbor_agent_name=place_node)
    envs.append(scaling_env)
    state_dim = 3
    action_dim = scaling_env.action_space.n
    scaling_agent = DQNAgent(state_dim, action_dim, device)
    agents.append(scaling_agent)
    buffers.append(ReplayBuffer(10000))

    # placement agent: neighbor 없음
    placement_env = EdgeEnv(place_node, agent_type="placement")
    envs.append(placement_env)
    action_dim = placement_env.action_space.n
    placement_agent = DQNAgent(state_dim, action_dim, device)
    agents.append(placement_agent)
    buffers.append(ReplayBuffer(10000))

epsilon = 1.0
epsilon_min = 0.05
epsilon_decay = 0.995
batch_size = 32
target_update = 50
steps = 0
episodes = 500

for ep in range(episodes):
    states = []
    for env in envs:
        s, _ = env.reset()
        states.append(s)

    done = [False] * len(envs)
    total_rewards = [0.0] * len(envs)

    # 에피소드 내 step 루프
    for t in range(50):
        for i, env in enumerate(envs):
            action = agents[i].act(states[i], epsilon)
            next_state, reward, done_i, trunc, _ = env.step(action)
            buffers[i].push(states[i], action, reward, next_state, done_i)
            states[i] = next_state
            total_rewards[i] += reward

            if len(buffers[i]) > batch_size:
                batch = buffers[i].sample(batch_size)
                loss = agents[i].update(batch, buffers[i], batch_size)
                if steps % target_update == 0:
                    agents[i].sync_target()
            steps += 1

    epsilon = max(epsilon_min, epsilon * epsilon_decay)

    # 에피소드 결과 출력
    for i, env in enumerate(envs):
        print(f"Episode {ep}, Agent {i} ({env.agent_type}, node={env.node_name}), Reward: {total_rewards[i]}")
