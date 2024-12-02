import logging
import numpy as np

import torch
from torch.distributions.categorical import Categorical
import torch.nn.functional as F
import torch.optim as optim

import os

from YRC.core.policy import Policy
import YRC.models as models
from YRC.core.configs.global_configs import get_global_variable
from YRC.core.configs.utils import config_logging

class BasePolicy(Policy):
    def __init__(self, config, env):
        self.model_cls = getattr(models, config.coord_policy.model_cls)
        self.model = self.model_cls(config, env)
        self.model.to(get_global_variable("device"))
        self.optim = optim.Adam(self.model.parameters(), lr=1e-4, eps=1e-5)
        #TODO: not sure write optim.Adam messes up logging, need to reconfigure here
        config_logging(get_global_variable("log_file"))

    def train(self):
        self.model.train()

    def eval(self):
        self.model.eval()

    def predict(self, obs):
        logit = self.model(obs)
        log_prob = F.log_softmax(logit, dim=-1)
        return Categorical(logits=log_prob)

    def act(self, obs, greedy=False):
        dist = self.predict(obs)
        if greedy:
            action = dist.probs.argmax(dim=-1)
        else:
            action = dist.sample()
        return action.cpu().numpy()

    def update_params(self, grad_clip_norm=None):
        if grad_clip_norm is not None:
            torch.nn.utils.clip_grad_norm_(self.model.parameters(), grad_clip_norm)
        self.optim.step()
        self.optim.zero_grad()

    def save_model(self, name, save_dir):
        save_path = os.path.join(save_dir, f"{name}.ckpt")
        torch.save(
            {
                "model_state_dict": self.model.state_dict(),
                "optim_state_dict": self.optim.state_dict(),
            },
            save_path,
        )
        logging.info(f"Saved model to {save_path}")

    def load_model(self, load_path):
        ckpt = torch.load(load_path)
        self.model.load_state_dict(ckpt["model_state_dict"])
        self.optim.load_state_dict(ckpt["optim_state_dict"])


class AlwaysPolicy(Policy):
    def __init__(self, config, env):
        agent = config.coord_policy.agent
        assert agent in ["weak", "strong"], f"Unrecognized agent: {agent}!"
        self.choice = env.WEAK if agent == "weak" else env.STRONG

    def act(self, obs, greedy=False):
        if type(obs["env_obs"]) is dict:
            return np.ones((1,), dtype=np.int64) * self.choice
        return np.ones((obs["env_obs"].shape[0],), dtype=np.int64) * self.choice


class RandomPolicy(Policy):
    def __init__(self, config, env):
        self.prob = 0.5
        self.device = get_global_variable("device")

    def act(self, obs, greedy=False):
        if isinstance(obs['env_obs'], dict):
            action = torch.rand((1,)).to(self.device) < self.prob
        else:
            action = torch.rand((obs["env_obs"].shape[0],)).to(self.device) < self.prob
        action = action.int()
        return action.cpu().numpy()

    def update_params(self, prob):
        self.prob = prob

    def save_model(self, name, save_dir):
        save_path = os.path.join(save_dir, f"{name}.ckpt")
        torch.save({"prob": self.prob}, save_path)
        logging.info(f"Saved model to {save_path}")

    def load_model(self, load_path):
        ckpt = torch.load(load_path)
        self.prob = ckpt["prob"]
