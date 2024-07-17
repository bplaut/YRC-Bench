import os
import random

from YRC.core.utils import set_global_seeds


class EnvRegistry():
    def __init__(self):
        self.all_cfgs = {}
        self.cfgs = None

    def register(self, benchmark, cfgs):
        self.all_cfgs[benchmark] = cfgs

    def set_cfgs(self, name):
        self.cfgs = self.all_cfgs[name]

    def setup_cfgs(self, args):
        if args.benchmark == 'procgen':
            self.cfgs.weak_model_file = args.weak_model_file
            self.cfgs.strong_model_file = args.strong_model_file
            self.cfgs.benchmark = args.benchmark
            self.cfgs.help_policy_type = args.help_policy_type

            self.cfgs.val_env_name = self.cfgs.val_env_name if self.cfgs.val_env_name else self.cfgs.env_name
            self.cfgs.start_level_val = random.randint(0, 9999)
            set_global_seeds(self.cfgs.seed)
            if self.cfgs.start_level == self.cfgs.start_level_val:
                raise ValueError("Seeds for training and validation envs are equal.")
            
            policy_attrs = self.cfgs.load_subclass_attributes(args.param_name)
            for attr, value in policy_attrs.items():
                setattr(self.cfgs.policy, attr, value)
            
            self.cfgs.weak_model_file = os.path.join("YRC", "checkpoints", "procgen", self.cfgs.env_name, self.cfgs.weak_model_file)
            self.cfgs.strong_model_file = os.path.join("YRC", "checkpoints", "procgen", self.cfgs.env_name, self.cfgs.strong_model_file)

            self.cfgs.distribution_mode = args.distribution_mode
        elif args.benchmark == 'cliport':
            self.cfgs.weak_model_file = args.weak_model_file
            self.cfgs.benchmark = args.benchmark
            self.cfgs.help_policy_type = args.help_policy_type
            self.cfgs.model_path = f"{self.cfgs.results_path}/{self.cfgs.model_task}-{self.cfgs.agent}-n{self.cfgs.n_demos}-train/checkpoints"
            self.cfgs.results_path = f"{self.cfgs.results_path}/{self.cfgs.task}-{self.cfgs.agent}-n{self.cfgs.n_demos}-train/checkpoints"
        return self.cfgs


# make global env registry
env_registry = EnvRegistry()
