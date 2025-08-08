import torch
from envs.central_env import CentralEnv
from agents.dqn import DQNAgent
from agents.replay_buffer import ReplayBuffer
import time
import matplotlib.pyplot as plt
import numpy as np

env = CentralEnv()
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
agent = DQNAgent(state_dim=4, action_dim=5, device=device)
buffer = ReplayBuffer(10000)

epsilon = 1.0
epsilon_min = 0.05
epsilon_decay = 0.995
batch_size = 32
target_update = 50
steps = 0
losses = []

for episode in range(1000):
    state, _ = env.reset()
    done = False
    total_reward = 0
    while not done:
        action = agent.act(state, epsilon)
        next_state, reward, done, trunc, _ = env.step(action)
        print(f"[Step {steps}] State: {state}, Action: {action}, Reward: {reward}, Next State: {next_state}")

        buffer.push(state, action, reward, next_state, done)
        state = next_state
        total_reward += reward
        time.sleep(5)

        if len(buffer) > batch_size:
            batch = buffer.sample(batch_size)
            loss = agent.update(batch, buffer, batch_size)
            losses.append(loss)
            if steps % target_update == 0:
                agent.sync_target()
            if steps % 10 == 0:
                print(f"[step {steps}] Loss: {loss:.4f}")
            with open("loss_log.txt", "a") as f:
                f.write(f"{steps},{loss}\n")
        steps += 1
    epsilon = max(epsilon_min, epsilon * epsilon_decay)
    print(f"Episode {episode}, Reward: {total_reward}")


plt.plot(losses)
plt.xlabel("Training Steps")
plt.ylabel("Loss")
plt.title("DQN Loss Over Time")
plt.show()