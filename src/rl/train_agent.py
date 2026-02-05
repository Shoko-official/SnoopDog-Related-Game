import os
import gymnasium as gym
import numpy as np
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import SubprocVecEnv, VecFrameStack, VecNormalize
from stable_baselines3.common.callbacks import CheckpointCallback, EvalCallback
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.utils import set_random_seed

import sys
# On ajoute le dossier src au path pour que les imports fonctionnent depuis la racine
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# On importe les trucs du projet
from rl.env import GetMyWeedEnv

# Dossiers et config
MODELS_DIR = "models/PPO"
LOG_DIR = "logs"
TIMESTEPS = int(1e12) # Autant dire l'infini
N_ENVS = 12 # Pour le Ryzen 9 (16 threads), 12 c'est le sweet spot

def make_env(rank, seed=0):
    def _init():
        # Mode sans fenêtre pour les bots
        os.environ["SDL_VIDEODRIVER"] = "dummy"
        env = GetMyWeedEnv()
        env = Monitor(env)
        env.reset(seed=seed + rank)
        return env
    set_random_seed(seed)
    return _init

def train():
    # Création des dossiers si besoin
    if not os.path.exists(MODELS_DIR): os.makedirs(MODELS_DIR)
    if not os.path.exists(LOG_DIR): os.makedirs(LOG_DIR)

    # Setup des 12 envs en parallèle
    print(f"Lancement de {N_ENVS} environnements...")
    env = SubprocVecEnv([make_env(i) for i in range(N_ENVS)])
    env = VecFrameStack(env, n_stack=4)
    env = VecNormalize(env, norm_obs=True, norm_reward=True, clip_obs=100.)

    # Env d'éval (un seul suffit)
    from gymnasium.wrappers import TimeLimit
    def make_eval_env():
        os.environ["SDL_VIDEODRIVER"] = "dummy"
        env = GetMyWeedEnv()
        env = Monitor(env)
        # On limite à 3000 steps pour pas que l'éval bloque si le bot est trop fort
        return TimeLimit(env, max_episode_steps=3000)

    eval_env = SubprocVecEnv([make_eval_env]) 
    eval_env = VecFrameStack(eval_env, n_stack=4)
    # On fige les stats de norm pour les tests
    eval_env = VecNormalize(eval_env, norm_obs=True, norm_reward=False, clip_obs=100., training=False)

    # Check si on a la CG
    import torch
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Utilisation de : {device}")
    if device == "cpu":
        print("ATTENTION: Pas de CUDA trouvé, ça va ramer sévère.")

    # Params du cerveau (MlpPolicy classique)
    policy_kwargs = dict(net_arch=dict(pi=[256, 256], vf=[256, 256]))
    
    # On check si on peut reprendre un entraînement existant
    model_path = f"{MODELS_DIR}/weed_bot_final.zip"
    if os.path.exists(model_path):
        print(f"Reprise du bot : {model_path}")
        model = PPO.load(model_path, env=env, device=device)
        model.learning_rate = 1e-4 # Plus lent = plus stable
        model.ent_coef = 0.02      # Pour garder un peu de curiosité
    else:
        model = PPO(
            "MlpPolicy", 
            env, 
            verbose=1, 
            tensorboard_log=LOG_DIR, 
            policy_kwargs=policy_kwargs,
            device=device,
            n_steps=2048,
            batch_size=128,
            learning_rate=1e-4, 
            gamma=0.99,
            gae_lambda=0.95,
            ent_coef=0.02,
        )

    # Callback pour arrêter si on stagne trop
    from stable_baselines3.common.callbacks import StopTrainingOnNoModelImprovement
    stop_callback = StopTrainingOnNoModelImprovement(
        max_no_improvement_evals=20, 
        min_evals=10, 
        verbose=1
    )

    # Fréquence d'éval (~150k steps)
    e_freq = max(1, 150000 // N_ENVS)

    eval_callback = EvalCallback(
        eval_env, 
        best_model_save_path=MODELS_DIR,
        log_path=LOG_DIR, 
        eval_freq=e_freq, 
        n_eval_episodes=3, # 3 parties de test c'est suffisant
        deterministic=True, 
        render=False,
        callback_after_eval=stop_callback
    )

    checkpoint_callback = CheckpointCallback(
        save_freq=50000,
        save_path=MODELS_DIR,
        name_prefix="weed_bot_v2"
    )

    print("C'est parti !")
    
    if os.path.exists(model_path):
        model.set_env(env)
    
    try:
        model.learn(
            total_timesteps=TIMESTEPS, 
            callback=[checkpoint_callback, eval_callback],
            progress_bar=True,
            reset_num_timesteps=False
        )
    except KeyboardInterrupt:
        print("Entraînement coupé, on sauvegarde...")
    
    # On sauvegarde tout à la fin
    model.save(f"{MODELS_DIR}/weed_bot_final")
    env.save(f"{MODELS_DIR}/vec_normalize.pkl")
    print(f"Fini ! Sauvegardé dans {MODELS_DIR}")

if __name__ == "__main__":
    train()
