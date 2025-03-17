import flags
import YRC.core.algorithm as algo_factory
import YRC.core.configs.utils as config_utils
import YRC.core.environment as env_factory
import YRC.core.policy as policy_factory
from YRC.core import Evaluator
from YRC.policies import *

if __name__ == "__main__":
    args = flags.make()
    args.eval_mode = True
    config = config_utils.load(args.config, flags=args)
    env_name = args.environment.common.env_name
    envs = env_factory.make(config)
    policy = policy_factory.make(config, envs["train"])
    if config.general.algorithm != "always" and not config.coord_policy.baseline:
        policy.load_model(os.path.join(config.experiment_dir, config.file_name))
    evaluator = Evaluator(config.evaluation, env_name, args.general.seed)

    evaluator.eval(policy, envs, ["test"])
