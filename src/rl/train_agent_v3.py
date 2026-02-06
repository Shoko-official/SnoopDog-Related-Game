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

# On ajoute le dossier src au path pour les imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from rl.env import GetMyWeedEnv

# --- CONFIGURATION V3 (SUPER BASE) ---
MODELS_DIR = "models/PPO_v3"
LOG_DIR = "logs_v3"
TIMESTEPS = int(1e9) 
N_ENVS = 12

class SyncObsRmsCallback(BaseCallback):
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
    def func(progress_remaining: float) -> float:
        return progress_remaining * initial_value
    return func

def make_env(rank, seed=0):
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

    # 1. Setup Env Multi-coeurs
    env = SubprocVecEnv([make_env(i) for i in range(N_ENVS)])
    env = VecNormalize(env, norm_obs=True, norm_reward=False, clip_obs=10.0, gamma=0.99)
    env = VecFrameStack(env, n_stack=4)

    # 2. Setup Env d'Eval
    def make_eval_env():
        os.environ["SDL_VIDEODRIVER"] = "dummy"
        os.environ['SDL_AUDIODRIVER'] = 'dummy'
        env = GetMyWeedEnv()
        env = Monitor(env)
        return TimeLimit(env, max_episode_steps=5000)

    eval_env = SubprocVecEnv([make_eval_env]) 
    eval_env = VecNormalize(eval_env, norm_obs=True, norm_reward=False, clip_obs=10.0, training=False)
    eval_env = VecFrameStack(eval_env, n_stack=4)

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Propulsion de l'entraînement sur : {device}")

    # --- ARCHITECTURE XXL (V3) ---
    policy_kwargs = dict(
        net_arch=dict(pi=[512, 512, 256], vf=[512, 512, 256]),
        activation_fn=torch.nn.Tanh
    )
    
    model_path = f"{MODELS_DIR}/weed_bot_v3_final.zip"
    stats_path = f"{MODELS_DIR}/vec_normalize_v3.pkl"
    model = None

    if os.path.exists(model_path):
        print(f"Chargement de la base existante : {model_path}")
        try:
            model = PPO.load(model_path, env=env, device=device)
            if os.path.exists(stats_path):
                env = VecNormalize.load(stats_path, env.venv)
                env = VecFrameStack(env, n_stack=4)
        except Exception as e:
            print(f"Echec du load ({e}), on repart de zéro.")
            model = None

    if model is None:
        model = PPO(
            "MlpPolicy", 
            env, 
            verbose=1, 
            tensorboard_log=LOG_DIR, 
            policy_kwargs=policy_kwargs,
            device=device,
            
            # --- HYPERPARAMETRES V3 (STABILITE MAX) ---
            n_steps=2048,               
            batch_size=2048,            # Plus gros batch pour des gradients "Super Base"
            learning_rate=linear_schedule(2e-4), 
            gamma=0.995,                # On voit un peu plus loin dans le futur
            gae_lambda=0.95,
            clip_range=0.15,            
            ent_coef=0.001,             # On calme l'exploration très vite pour fixer le comportement
            vf_coef=0.5,
            max_grad_norm=0.5,
        )

    eval_freq_steps = max(1, 150000 // N_ENVS)
    
    sync_callback = SyncObsRmsCallback(eval_env, eval_freq=eval_freq_steps)
    eval_callback = EvalCallback(
        eval_env, 
        best_model_save_path=MODELS_DIR,
        log_path=LOG_DIR, 
        eval_freq=eval_freq_steps, 
        n_eval_episodes=15, 
        deterministic=True,
        callback_after_eval=StopTrainingOnNoModelImprovement(50, 20)
    )

    checkpoint_callback = CheckpointCallback(
        save_freq=100000,
        save_path=MODELS_DIR,
        name_prefix="weed_bot_v3_checkpoint"
    )

    print("--- LANCEMENT DE LA SUPER BASE V3 ---")
    try:
        model.learn(
            total_timesteps=TIMESTEPS, 
            callback=[sync_callback, checkpoint_callback, eval_callback],
            progress_bar=True,
            reset_num_timesteps=False
        )
    except KeyboardInterrupt:
        print("\nInterrompu. Sauvegarde en cours...")
    
    model.save(f"{MODELS_DIR}/weed_bot_v3_final")
    env.save(stats_path)
    print(f"Sauvegardé dans {MODELS_DIR}")
    
    env.close()
    eval_env.close()

if __name__ == "__main__":
    train()
