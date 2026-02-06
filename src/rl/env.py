import gymnasium as gym
from gymnasium import spaces
import numpy as np
import pygame
from states.game_state import GameState
from settings import *
import os

# Corrected by Shoko on 2026-02-05
class GetMyWeedEnv(gym.Env):
    def __init__(self, brain_stack=None):
        super(GetMyWeedEnv, self).__init__()
        
        if not pygame.display.get_init():
            pygame.display.init()
        if not pygame.font.get_init():
            pygame.font.init()
        
        if not pygame.mixer.get_init():
            os.environ['SDL_AUDIODRIVER'] = 'dummy'

        # Actions: 0=Nothing, 1=Jump, 2=FastFall
        self.action_space = spaces.Discrete(3)
        
        # Observation: 16 floats (Added shield status for v3)
        self.observation_space = spaces.Box(
            low=-np.inf, 
            high=np.inf, 
            shape=(16,), 
            dtype=np.float32
        )

        self.game = None
        self.brain = brain_stack
        self.last_x = 0
        self.last_action = 0
        self.stagnation_counter = 0
        self.last_milestone = 0
        self.frames_on_ground = 0
        self.last_reward = 0 
        self.last_reward_reason = "" 

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        
        if self.game is None:
            self.game = GameState(self.brain)
        else:
            self.game.hard_reset()
            
        self.game.player.ai_mode = True
        self.last_x = self.game.player.rect.x
        self.max_dist_this_episode = self.game.player.rect.x
        self.last_action = 0
        self.stagnation_counter = 0
        self.last_milestone = 0
        self.frames_on_ground = 0
        return self._get_obs(), {}

    def step(self, action):
        self.game.player.current_ai_action = action
        
        # On scan AVANT de bouger
        scan = self.game.scan_surroundings()
        p = self.game.player
        was_on_ground = p.on_ground 
        # CRITIQUE : Capturer le temps au sol AVANT l'update pour valider le Bunny Hop
        ground_time_prev = self.frames_on_ground
        
        dt = 1.0/60.0
        self.game.update(dt, [])
        
        # Gestion du compteur de sol
        if p.on_ground:
            self.frames_on_ground += 1
        else:
            self.frames_on_ground = 0
        
        # --- REWARD ENGINEERING ---
        reward = 0.0
        reason = "INIT"
        
        # 1. Survival & Efficiency Cost (Adaptive Clock)
        stagnation_penalty_mult = 1.0 + (self.stagnation_counter / 60.0)
        reward -= 0.01 * stagnation_penalty_mult

        # 2. Action Smoothing (Désactivé pour supprimer le bruit visuel)
        self.last_action = action

        # 3. Physics Logic & Energy Cost (SIGNAL PUR)
        if action == 1: # On veut sauter
            reward -= 5.0 # Taxe de base augmentée (était -1.0)
            if was_on_ground:
                # On ne considère une plateforme comme un danger QUE si elle est plus haute ou s'il y a un trou
                is_real_platform_danger = scan['next_platform_x_dist'] < 150 and scan['next_platform_y_delta'] < -0.05
                
                real_danger_dist = min(scan['next_trash_dist'], scan['next_enemy_dist'])
                gap_is_far = scan['next_gap_dist'] > 200 # Un peu plus tolérant
                
                # Le saut n'est "LÉGITIME" que si danger proche ou plateforme haute ou trou imminent
                if real_danger_dist > 250 and gap_is_far and not is_real_platform_danger:
                    if ground_time_prev < 40: # Un peu plus permissif que 60 pour ne pas brider le gameplay
                        reward -= 150.0 # PUNITION ENCORE PLUS ATOMIQUE
                        reason = "BUNNY_HOP_NUCLEAR"
                    else:
                        reward -= 40.0 # Doublé la punition
                        reason = "USELESS_JUMP"
                else:
                    # Même si c'est un safe jump, on veut qu'il reste au sol le plus possible
                    reward -= 2.0 
                    reason = "SAFE_JUMP"
        
        # --- LE SIGNAL MAÎTRE ---
        if p.on_ground:
            reward += 5.0 # SUPER CAROTTE
            reward += 0.2 # BONUS V3: Chaque frame au sol est une victoire
            if action == 0:
                reason = "PURE_RUNNING"
            else:
                reason = "STABLE_GROUND"
        else:
            # En l'air, on récompense le fait de plonger pour revenir au sol vite
            if action == 2:
                reward += 0.5
                reason = "FAST_DESCEND"

        # C. Interdictions Physiques (Sévères)
        if action == 1 and not was_on_ground:
            reward -= 20.0 # ON TUE LE JITTER EN L'AIR
            reason = "AIR_JUMP_FAIL"
        if action == 2 and p.on_ground:
            reward -= 1.0 
            reason = "GROUND_FALL_FAIL"

        # 4. Momentum & Progress
        current_x = p.rect.x
        if current_x > self.max_dist_this_episode:
            self.max_dist_this_episode = current_x
            self.stagnation_counter = 0
            if current_x > self.last_milestone + 5000:
                reward += 1000.0 
                self.last_milestone = current_x
                reason = "CHECKPOINT!"
        else:
            self.stagnation_counter += 1
            if self.stagnation_counter > 30:
                reward -= 0.1
                reason = "STAGNATION"
        
        # 5. Major Objectives
        if p.just_collected_weed:      
            reward += 50.0
            reason = "COLLECT_WEED"
        
        # 6. Penalties
        if p.just_took_damage:        
            reward -= 200.0 
            reason = "DAMAGE_TAKEN"
        
        # 7. Termination
        terminated = False
        if p.hp <= 0 or p.rect.top > DEATH_Y or self.game.death_triggered:
            terminated = True
            reward -= 1000.0 
            reason = "DEATH"
        
        self.last_reward = reward
        self.last_reward_reason = reason
        self.last_action = action # Mis à jour à la fin
            
        if p.rect.top > DEATH_Y:
            terminated = True
            
        # Truncate if stuck
        truncated = False
        if self.stagnation_counter > 600:
            truncated = True
            reward -= 10.0
            
        obs = self._get_obs()
        return obs, reward, terminated, truncated, {}

    def _get_obs(self):
        scan = self.game.scan_surroundings()
        p = self.game.player
        
        obs = np.array([
            p.rect.centery / SCREEN_HEIGHT,
            p.velocity_y / 1000.0,
            scan['next_gap_dist'] / 500.0,
            scan['next_enemy_dist'] / 500.0,
            scan['next_enemy_type'],
            1.0 if p.on_ground else 0.0,
            p.speed / 500.0,
            scan['next_platform_y_delta'],
            scan['enemy_y_delta'], 
            scan['next_platform_x_dist'] / 500.0,
            scan['next_platform_width'] / 500.0,
            scan['gap_size'] / 300.0,
            scan['next_weed_dist'] / 500.0,
            scan['next_trash_dist'] / 500.0,
            self.last_action / 2.0,
            1.0 if p.has_shield else 0.0 # NOUVEAU V3: Etat du bouclier
        ], dtype=np.float32)
        
        return np.clip(obs, -5.0, 5.0)

    def render(self):
        pass
