import argparse
import subprocess
import concurrent.futures
import os

def run_command(args):
    env, seed = args
    # Replace this with your actual command
    if 'coinrun' not in env and 'maze' not in env:
        raise ValueError(f"Invalid environment: {env}")
    overall_env = 'coinrun' if 'coinrun' in env else 'maze'
    cmd = f"python eval.py -c configs/procgen_threshold.yaml -n {overall_env}_qc_neg -en {env} -sim YRC/checkpoints/procgen/{overall_env}/sim_weak/model_40009728.pth -weak YRC/checkpoints/procgen/{overall_env}/weak/model_80019456.pth -strong YRC/checkpoints/procgen/{overall_env}/strong/model_200015872.pth -cp_metric margin -f_n best_val_true.ckpt -query_cost 0 -seed {seed}"
    print(f"Running command for seed {seed}...")
    return subprocess.run(cmd, shell=True, capture_output=True)

def main():
    parser = argparse.ArgumentParser(description="Run commands with varying seeds in parallel")
    parser.add_argument("environment", type=str, help="Environment name")
    parser.add_argument("start_seed", type=int, help="Starting seed (inclusive)")
    parser.add_argument("end_seed", type=int, help="Ending seed (exclusive)")
    parser.add_argument("--workers", type=int, default=os.cpu_count() // 2, 
                       help="Number of parallel workers (default: number of CPU cores)")
    
    args = parser.parse_args()
    
    tasks = [(args.environment, seed) for seed in range(args.start_seed, args.end_seed)]
    print(f"Running {len(tasks)} tasks with {args.workers} workers")
    with concurrent.futures.ProcessPoolExecutor(max_workers=args.workers) as executor:
        results = list(executor.map(run_command, tasks))
    
    print(f"Completed {len(tasks)} tasks")

if __name__ == "__main__":
    main()
