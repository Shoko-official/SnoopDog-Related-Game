import os
import sys
import pygame
import numpy as np
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv, VecFrameStack, VecNormalize

# On rajoute le dossier src au path pour les imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from rl.env import GetMyWeedEnv
from settings import SCREEN_WIDTH, SCREEN_HEIGHT, FPS, TITLE
from state_machine import StateStack

def watch_bot():
    # 1. Dossiers des modèles
    model_path = "models/PPO/best_model.zip"
    stats_path = "models/PPO/vec_normalize.pkl"

    import time
    while not os.path.exists(model_path):
        print(f"\rAttente du premier modèle ({model_path})...", end="")
        time.sleep(5)
    print("\nModèle trouvé ! Lancement de la preview...")

    # 2. On prépare Pygame pour la fenêtre
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption(f"{TITLE} - AI WATCHER")
    clock = pygame.time.Clock()

    # 3. On recrée l'environnement RL
    def make_env():
        # Mode vidéo normal pour voir le bot
        os.environ["SDL_VIDEODRIVER"] = "windows" # On force la fenêtre
        env = GetMyWeedEnv()
        return env

    venv = DummyVecEnv([make_env])
    
    # On remet les stats de normalisation pour que le bot comprenne ses observations
    if os.path.exists(stats_path):
        print("Chargement des stats de normalisation...")
        venv = VecNormalize.load(stats_path, venv)
        venv.training = False # On ne touche plus aux stats
        venv.norm_reward = False
    else:
        print("Attention : Pas de stats de normalisation, le bot va galérer.")
        venv = VecNormalize(venv, norm_obs=True, norm_reward=False)

    # FrameStack (le bot a été entraîné avec 4 frames de mémoire)
    venv = VecFrameStack(venv, n_stack=4)

    # 4. Chargement initial
    print(f"Chargement du modèle : {model_path}")
    model = PPO.load(model_path, env=venv, device='cpu')
    last_reload_time = pygame.time.get_ticks()
    reload_interval = 30000 # 30 secondes

    # 5. La boucle de jeu
    obs = venv.reset()
    running = True
    game_env = venv.venv.venv.envs[0]
    
    print("--- MODE AUTO-RELOAD ACTIF (30s) ---")
    
    action_names = ["COURIR", "SAUTER", "PLONGER"]
    last_action = 0

    while running:
        current_time = pygame.time.get_ticks()
        
        # Auto-reload du cerveau
        if current_time - last_reload_time > reload_interval:
            if os.path.exists(model_path):
                print(f"[{pygame.time.get_ticks()}] Rechargement du cerveau tout frais...")
                try:
                    model = PPO.load(model_path, env=venv, device='cpu')
                    # On recharge aussi les stats si possible
                    if os.path.exists(stats_path):
                        venv = VecNormalize.load(stats_path, venv.venv)
                        venv.training = False
                        venv.norm_reward = False
                        venv = VecFrameStack(venv, n_stack=4)
                    last_reload_time = current_time
                except:
                    print("Echec du reload (le fichier est peut-être en train d'être écrit), on réessayera...")
        
        dt = clock.tick(FPS) / 1000.0
        # ... (reste de la gestion d'events)
        
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False

        # L'IA décide quoi faire
        # On passe deterministic=False pour voir si le bot est plus "vivant"
        action, _ = model.predict(obs, deterministic=False)
        last_action = action[0]
        
        # On exécute l'action
        obs, rewards, dones, infos = venv.step(action)
        
        # On dessine le résultat à l'écran
        game_env.game.draw(screen)
        
        # Overlay de debug
        f = pygame.font.SysFont("arial", 20, bold=True)
        txt_status = f.render("MODE IA : ACTIF", True, (0, 255, 0))
        txt_action = f.render(f"ACTION : {action_names[last_action]}", True, (255, 255, 0))
        
        # COULEUR REWARD : Rouge si négatif, Vert si positif
        rew_color = (255, 100, 100) if game_env.last_reward < 0 else (100, 255, 100)
        txt_reward = f.render(f"REWARD : {game_env.last_reward:.2f}", True, rew_color)
        txt_reason = f.render(f"MOTIF : {game_env.last_reward_reason}", True, rew_color)
        
        txt_ground = f.render(f"STAB. SOL : {game_env.frames_on_ground} fr", True, (100, 200, 255))
        
        screen.blit(txt_status, (20, 20))
        screen.blit(txt_action, (20, 45))
        screen.blit(txt_reward, (20, 70))
        screen.blit(txt_reason, (20, 95))
        screen.blit(txt_ground, (20, 120))
        
        pygame.display.flip()

        if dones[0]:
            print("--- MORT DU BOT ---")
            print(f"Score final : {game_env.game.score}")
            
    pygame.quit()

            
    pygame.quit()

if __name__ == "__main__":
    watch_bot()
