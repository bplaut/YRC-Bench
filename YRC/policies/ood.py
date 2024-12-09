import os
import numpy as np
from copy import deepcopy as dc

import torch
import logging
from torch.distributions.categorical import Categorical
from YRC.core import Policy
from pyod.models import deep_svdd
from joblib import dump, load
from YRC.core.configs.global_configs import get_global_variable


class OODPolicy(Policy):
    def __init__(self, config, env):
        self.args = config.coord_policy
        self.agent = env.weak_agent
        self.params = {"threshold": 0.0, "explore_temp": 1.0}
        self.clf = None
        self.clf_name = None
        self.device = get_global_variable("device")
        self.feature_type = config.coord_policy.feature_type

    def gather_rollouts(self, env, num_rollouts):
        assert num_rollouts % env.num_envs == 0
        observations = []
        for i in range(num_rollouts // env.num_envs):
            observations.extend(self._rollout_once(env))
        if self.feature_type in ["hidden_obs", "hidden_dist", "obs_dist"]:
            feature_tensors = [[], []]
            for i, tensor in enumerate(observations):
                feature_tensors[i % 2].append(tensor)
            observations = [torch.cat(tensors, dim=0) for tensors in feature_tensors]
        elif self.feature_type == "obs_hidden_dist":
            feature_tensors = [[], [], []]
            for i, tensor in enumerate(observations):
                feature_tensors[i % 3].append(tensor)
            observations = [torch.cat(tensors, dim=0) for tensors in feature_tensors]

        else:
            observations = torch.stack(observations)
        return observations

    def _rollout_once(self, env):
        def sample_action(logit):
            """Samples an action using a categorical distribution with exploration temperature."""
            dist = Categorical(logits=logit / self.params["explore_temp"])
            return dist.sample().cpu().numpy()

        def get_features(obs, feature_type):
            """Retrieves features based on the specified feature type."""
            feature_map = {
                "obs": lambda obs: obs["env_obs"],
                "hidden": lambda obs: obs["weak_features"],
                "hidden_obs": lambda obs: [obs["env_obs"], obs["weak_features"]],
                "dist": lambda obs: obs["weak_logit"],
                "hidden_dist": lambda obs: [obs["weak_features"], obs["weak_logit"]],
                "obs_dist": lambda obs: [obs["env_obs"], obs["weak_logit"]],
                "obs_hidden_dist": lambda obs: [obs["env_obs"], obs["weak_features"], obs["weak_logit"]],
            }
            return feature_map[feature_type](obs)

        def maybe_convert_to_tensor(features):
            """Converts features to tensors if they are not already tensors."""
            if isinstance(features, list):  # Handle lists of features (e.g., for concatenation)
                return [self.to_tensor(f) if not torch.is_tensor(f) else f for f in features]
            return self.to_tensor(features) if not torch.is_tensor(features) else features

        agent = self.agent
        agent.eval()
        obs = env.reset()
        has_done = np.array([False] * env.num_envs)
        observations = []

        while not has_done.all():
            logit = agent.forward(obs["env_obs"])

            if get_global_variable("benchmark") == "cliport":
                # todo: fix faeture type for cliport
                obs_features = obs["env_obs"]['img']
                if np.random.rand() < 0.005:  # Randomly sample for memory efficiency
                    observations.extend(obs_features)
            else:
                for i in range(env.num_envs):
                    if not has_done[i]:
                        obs_features = get_features(obs, self.feature_type)
                        if np.random.rand() < 0.005:  # Randomly sample for memory efficiency
                            obs_features = maybe_convert_to_tensor(obs_features)
                            observations.extend(obs_features)

            action = sample_action(logit)
            obs, reward, done, info = env.step(action)
            has_done |= done

        return observations

    def update_params(self, params):
        self.params = dc(params)

    def act(self, obs, greedy=False):
        if get_global_variable("benchmark") == "cliport":
            score = self.clf.decision_function(obs["env_obs"]['img'])
        else:
            if self.feature_type in ["obs", "hidden", "dist"]:
                key = {
                    "obs": "env_obs",
                    "hidden": "weak_features",
                    "dist": "weak_logit"
                }[self.feature_type]
                observation = self.to_tensor(obs[key])
            elif self.feature_type in ["hidden_obs", "hidden_dist", "obs_dist"]:
                keys = {
                    "hidden_obs": ["env_obs", "weak_features"],
                    "hidden_dist": ["weak_features", "weak_logit"],
                    "obs_dist": ["env_obs", "weak_logit"]
                }[self.feature_type]
                observation = [self.to_tensor(obs[key]) for key in keys]
            elif self.feature_type == "obs_hidden_dist":
                keys = {
                    "obs_hidden_dist": ["env_obs", "weak_features", "weak_logit"]
                }[self.feature_type]
                observation = [self.to_tensor(obs[key]) for key in keys]
            score = self.clf.decision_function(observation)

        action = 1 - (score < self.clf.threshold_).astype(int)
        if 0 not in action and 1 not in action:
            print("No action is selected as OOD")
        return action

    def initialize_ood_detector(self, args, env):
        if self.args.method == "DeepSVDD":
            dummy_obs = env.reset()
            feature_type_to_shapes = {
                "obs": lambda dummy_obs: (dummy_obs['env_obs']['img'] if get_global_variable("benchmark") == "cliport" else dummy_obs['env_obs']).shape,
                "hidden": lambda dummy_obs: dummy_obs['weak_features'].shape,
                "hidden_obs": lambda dummy_obs: (
                    (dummy_obs['env_obs']['img'] if get_global_variable("benchmark") == "cliport" else dummy_obs['env_obs']).shape + dummy_obs['weak_features'].shape[1:]
                ),
                "dist": lambda dummy_obs: dummy_obs['weak_logit'].shape,
                "hidden_dist": lambda dummy_obs: (
                    dummy_obs['weak_features'].shape + dummy_obs['weak_logit'].shape[1:]
                ),
                "obs_dist": lambda dummy_obs: (
                    (dummy_obs['env_obs']['img'] if get_global_variable("benchmark") == "cliport" else dummy_obs['env_obs']).shape + dummy_obs['weak_logit'].shape[1:]
                ),
                "obs_hidden_dist": lambda dummy_obs: (
                    (dummy_obs['env_obs']['img'] if get_global_variable("benchmark") == "cliport" else dummy_obs['env_obs']).shape + dummy_obs['weak_features'].shape[1:] + dummy_obs['weak_logit'].shape[1:]
                )
            }

            dummy_obs_shape = feature_type_to_shapes[self.feature_type](dummy_obs)

            if get_global_variable("benchmark") == "cliport":
                dummy_obs = dummy_obs.unsqueeze(0).permute(0, 3, 1, 2)

            self.clf_name = 'DeepSVDD'
            self.clf = deep_svdd.DeepSVDD(
                            n_features=args.feature_size,
                            use_ae=args.use_ae,
                            contamination=args.contamination,
                            epochs=args.epoch,
                            batch_size=args.batch_size,
                            input_shape=dummy_obs_shape,
                            feature_type=self.feature_type
                        )
            self.clf.model_.to(self.device)
        else:
            raise ValueError(f"Unknown OOD detector type: {args.ood_detector}")

    def save_model(self, name, save_dir):
        save_path = os.path.join(save_dir, f"{name}.joblib")
        state_dict = {
            'clf': self.clf,
            'class_name': self.__class__.__name__,
            'config': {
                'contamination': self.clf.contamination,
            },
            'clf_name': self.clf_name,
        }
        if type(self.clf) == deep_svdd.DeepSVDD:
            state_dict['config']['use_ae'] = self.clf.use_ae
        dump(state_dict, save_path)
        logging.info(f"Saved model to {save_path}")

    def load_model(self, load_dir):
        state_dict = load(f"{load_dir}")
        self.clf = state_dict['clf']
        return self


    def to_tensor(self, data):
        """Converts input to a torch tensor if it's not already."""
        if not torch.is_tensor(data):
            return torch.from_numpy(data).float().to(self.device)
        return data