import os
import sys
import gymnasium as gym
import numpy as np
import torch
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import SubprocVecEnv, VecFrameStack, VecNormalize
from stable_baselines3.common.callbacks import CheckpointCallback, EvalCallback, BaseCallback, StopTrainingOnNoModelImprovement
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.utils import set_random_seed
from gymnasium.wrappers import TimeLimit
from typing import Callable

# Corrected by Shoko on 2026-02-05

# Add source directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from rl.env import GetMyWeedEnv

MODELS_DIR = "models/PPO"
LOG_DIR = "logs"
TIMESTEPS = int(1e9) # 1 Milliard de pas pour un entraînement légendaire
N_ENVS = 12

class SyncObsRmsCallback(BaseCallback):
    """
    Synchronizes normalization statistics between training and evaluation environments.
    Essential for consistent performance evaluation.
    """
    def __init__(self, eval_env, eval_freq, verbose=0):
        super().__init__(verbose)
        self.eval_env = eval_env
        self.eval_freq = eval_freq

    def _on_step(self) -> bool:
        if self.eval_freq > 0 and self.n_calls % self.eval_freq == 0:
            if hasattr(self.training_env, 'obs_rms') and hasattr(self.eval_env, 'obs_rms'):
                self.eval_env.obs_rms.mean = self.training_env.obs_rms.mean.copy()
                self.eval_env.obs_rms.var = self.training_env.obs_rms.var.copy()
                self.eval_env.obs_rms.count = self.training_env.obs_rms.count
        return True

def linear_schedule(initial_value: float) -> Callable[[float], float]:
    """
    Linear learning rate schedule.
    :param initial_value: Initial learning rate.
    :return: schedule function.
    """
    def func(progress_remaining: float) -> float:
        return progress_remaining * initial_value
    return func

def make_env(rank, seed=0):
    """
    Utility function for multiprocessed env.
    """
    def _init():
        os.environ["SDL_VIDEODRIVER"] = "dummy"
        os.environ['SDL_AUDIODRIVER'] = 'dummy'
        env = GetMyWeedEnv()
        env = Monitor(env)
        env.reset(seed=seed + rank)
        return env
    set_random_seed(seed)
    return _init

def train():
    if not os.path.exists(MODELS_DIR): os.makedirs(MODELS_DIR)
    if not os.path.exists(LOG_DIR): os.makedirs(LOG_DIR)

    # 1. Environment Setup
    # parallel environments for faster data collection
    env = SubprocVecEnv([make_env(i) for i in range(N_ENVS)])
    
    # Normalization of obs is good, but norm_reward=True can squash our custom penalties
    env = VecNormalize(env, norm_obs=True, norm_reward=False, clip_obs=10.0, gamma=0.99)
    env = VecFrameStack(env, n_stack=4)

    # 2. Evaluation Environment Setup
    # Separate process for evaluation to avoid training interference
    def make_eval_env():
        os.environ["SDL_VIDEODRIVER"] = "dummy"
        os.environ['SDL_AUDIODRIVER'] = 'dummy'
        env = GetMyWeedEnv()
        env = Monitor(env)
        return TimeLimit(env, max_episode_steps=3000)

    eval_env = SubprocVecEnv([make_eval_env]) 
    # Important: norm_reward=False for evaluation to see real metrics
    eval_env = VecNormalize(eval_env, norm_obs=True, norm_reward=False, clip_obs=10.0, training=False)
    eval_env = VecFrameStack(eval_env, n_stack=4)

    # 3. Hardware Check
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Target Device: {device}")

    # 4. Network Architecture
    # 256x256 is sufficient for this complexity. 
    policy_kwargs = dict(
        net_arch=dict(pi=[256, 256], vf=[256, 256]),
        activation_fn=torch.nn.Tanh
    )
    
    model_path = f"{MODELS_DIR}/weed_bot_final.zip"
    stats_path = f"{MODELS_DIR}/vec_normalize.pkl"
    model = None

    # 5. Model Loading / Initialization
    if os.path.exists(model_path):
        print(f"Loading existing model: {model_path}")
        try:
            custom_objects = {
                "learning_rate": linear_schedule(2.5e-4),
                "clip_range": linear_schedule(0.1)
            }
            model = PPO.load(model_path, env=env, device=device, custom_objects=custom_objects)
            
            if os.path.exists(stats_path):
                print("Loading normalization stats...")
                # We need to load stats into the unwrapped environment
                env = VecNormalize.load(stats_path, env.venv)
                # Re-wrap with FrameStack
                env = VecFrameStack(env, n_stack=4)
        except Exception as e:
            print(f"Load failed ({e}). Starting fresh.")
            model = None

    if model is None:
        model = PPO(
            "MlpPolicy", 
            env, 
            verbose=1, 
            tensorboard_log=LOG_DIR, 
            policy_kwargs=policy_kwargs,
            device=device,
            
            # Optimized Hyperparameters for Stability
            n_steps=2048,               # 2048 * 12 envs = 24k steps per update
            batch_size=1024,            # Larger batch for smoother gradients
            learning_rate=linear_schedule(2.5e-4), # Decaying LR
            gamma=0.99,
            gae_lambda=0.95,
            clip_range=0.1,             # Conservative clipping to prevent policy collapse
            ent_coef=0.005,              # Calme l'exploration pour stabiliser le bot
            vf_coef=0.5,
            max_grad_norm=0.5,
        )

    # 6. Callbacks
    stop_callback = StopTrainingOnNoModelImprovement(
        max_no_improvement_evals=50, 
        min_evals=20, 
        verbose=1
    )

    eval_freq_steps = max(1, 100000 // N_ENVS)
    
    sync_callback = SyncObsRmsCallback(eval_env, eval_freq=eval_freq_steps)

    eval_callback = EvalCallback(
        eval_env, 
        best_model_save_path=MODELS_DIR,
        log_path=LOG_DIR, 
        eval_freq=eval_freq_steps, 
        n_eval_episodes=10, 
        deterministic=True, 
        render=False,
        callback_after_eval=stop_callback
    )

    checkpoint_callback = CheckpointCallback(
        save_freq=50000,
        save_path=MODELS_DIR,
        name_prefix="weed_bot_checkpoint"
    )

    print("--- Starting Training Session ---")
    
    try:
        model.learn(
            total_timesteps=TIMESTEPS, 
            callback=[sync_callback, checkpoint_callback, eval_callback],
            progress_bar=True,
            reset_num_timesteps=False
        )
    except KeyboardInterrupt:
        print("\nTraining interrupted. Saving current state...")
    
    # 7. Save & Exit
    model.save(f"{MODELS_DIR}/weed_bot_final")
    env.save(stats_path)
    print(f"Model and stats saved to {MODELS_DIR}")
    
    env.close()
    eval_env.close()

if __name__ == "__main__":
    train()