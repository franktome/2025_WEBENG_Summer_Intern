import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np

class QNetwork(nn.Module):
    def __init__(self, state_dim, action_dim):
        super().__init__()
        self.layers = nn.Sequential(
            nn.Linear(state_dim, 128),
            nn.ReLU(),
            nn.Linear(128, 128),
            nn.ReLU(),
            nn.Linear(128, action_dim)
        )
    def forward(self, x):
        return self.layers(x)

class DQNAgent:
    def __init__(self, state_dim, action_dim, device):
        self.device = device
        self.q_net = QNetwork(state_dim, action_dim).to(device)
        self.target_net = QNetwork(state_dim, action_dim).to(device)
        self.target_net.load_state_dict(self.q_net.state_dict())
        self.optimizer = optim.Adam(self.q_net.parameters(), lr=1e-3)
        self.gamma = 0.99

    def update(self, batch, replay_buffer, batch_size):
        states, actions, rewards, next_states, dones = batch
        states = torch.FloatTensor(states).to(self.device)
        actions = torch.LongTensor(actions).unsqueeze(1).to(self.device)
        rewards = torch.FloatTensor(rewards).to(self.device)
        next_states = torch.FloatTensor(next_states).to(self.device)
        dones = torch.FloatTensor(dones).to(self.device)

        q_values = self.q_net(states).gather(1, actions).squeeze()
        with torch.no_grad():
            max_next_q = self.target_net(next_states).max(1)[0]
            target = rewards + self.gamma * max_next_q * (1 - dones)

        loss = (q_values - target).pow(2).mean()
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()
        return loss.item()

    # 일정 주기마다 target_net를 q_net로 동기화  -> Q learning 학습을 안정화.
    def sync_target(self):
        self.target_net.load_state_dict(self.q_net.state_dict())

    def act(self, state, epsilon):
        if np.random.rand() < epsilon:
            return np.random.randint(0, 5)
        state = torch.FloatTensor(state).unsqueeze(0).to(self.device)
        with torch.no_grad():
            q = self.q_net(state)
        return q.argmax().item()
