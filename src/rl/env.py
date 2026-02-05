import gymnasium as gym
from gymnasium import spaces
import numpy as np
import pygame
from states.game_state import GameState
from settings import *
import os

class GetMyWeedEnv(gym.Env):
    def __init__(self, brain_stack=None):
        super(GetMyWeedEnv, self).__init__()
        
        # On initialise pygame au strict minimum (affichage + polices)
        if not pygame.display.get_init():
            pygame.display.init()
        if not pygame.font.get_init():
            pygame.font.init()
        
        # On dégage le son pour pas ralentir les workers
        if not pygame.mixer.get_init():
            os.environ['SDL_AUDIODRIVER'] = 'dummy'

        # 3 actions de base : gauche/rien, saut, chute rapide
        self.action_space = spaces.Discrete(3)
        
        # 12 valeurs d'entrée pour l'IA (normalisées plus tard par VecNormalize)
        self.observation_space = spaces.Box(
            low=-np.inf, 
            high=np.inf, 
            shape=(12,), 
            dtype=np.float32
        )

        self.game = None
        self.brain = brain_stack
        self.last_x = 0

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        
        # On évite de recréer l'objet à chaque fois pour gagner du temps
        if self.game is None:
            self.game = GameState(self.brain)
        else:
            self.game.hard_reset()
            
        self.game.player.ai_mode = True
        self.last_x = self.game.player.rect.x
        return self._get_obs(), {}

    def step(self, action):
        # On envoie l'action au joueur et on update la physique
        self.game.player.current_ai_action = action
        self.game.update(1.0/60.0, [])
        
        # On calcule les points (reward)
        reward = 0.0
        p = self.game.player
        
        # Récompense pour l'avance (0.01 pt par pixel vers la droite)
        progress = p.rect.x - self.last_x
        self.last_x = p.rect.x
        if progress > 0:
            reward += progress * 0.01

        # Bonus pour les bons trucs
        if p.just_collected_weed:          reward += 5.0 # L'objectif n°1
        if p.just_hit_enemy:          reward += 2.0
        if p.just_dodged_enemy:       reward += 1.0
        if p.just_fast_fell:          reward += 0.1
        if p.just_used_shield:        reward += 0.5
        if p.just_used_magnet:        reward += 0.5
        if p.just_reached_max_combo:  reward += 3.0
        if p.just_reached_min_withdrawal: reward += 2.0
        if p.just_reached_max_speed:  reward += 0.5
        if p.just_reached_max_hp:     reward += 1.0

        # Malus (les erreurs)
        if p.just_took_damage:        reward -= 5.0
        if p.just_died:               reward -= 50.0 # Grosse claque s'il meurt
        if p.just_reached_max_withdrawal: reward -= 5.0
        if p.just_reached_min_speed:  reward -= 0.5
        if p.just_reached_min_hp:     reward -= 2.0
        if p.just_reached_min_combo:  reward -= 0.5
            
        terminated = False
        if p.hp <= 0 or p.rect.top > DEATH_Y:
            terminated = True
            
        # Tomber dans un trou c'est la mort instantanée
        if p.rect.top > DEATH_Y:
            reward -= 20.0 
            
        obs = self._get_obs()
        return obs, reward, terminated, False, {}

    def _get_obs(self):
        # On récupère le scan des environs (plateformes, trous, mobs)
        scan = self.game.scan_surroundings()
        p = self.game.player
        
        # On construit le vecteur de 12 observations
        obs = np.array([
            p.rect.centery,
            p.velocity_y,
            scan['next_gap_dist'],
            scan['next_enemy_dist'],
            scan['next_enemy_type'],
            1.0 if p.on_ground else 0.0,
            p.speed,
            scan['next_platform_y_delta'],
            scan['enemy_y_delta'], 
            scan['next_platform_x_dist'],
            scan['next_platform_width'],
            scan['gap_size']
        ], dtype=np.float32)
        return obs

    def render(self):
        pass # Pas de rendu ici, c'est pour l'entraînement