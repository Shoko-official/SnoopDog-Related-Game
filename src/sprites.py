import pygame
import math
import random

from settings import *
from entity import PhysObj
from asset_loader import asset_loader, play_sfx
from assets_registry import ASSETS

# Petit helper pour pas réecrire la ligne 50 fois
def get_mask(surface):
    return pygame.mask.from_surface(surface)

class Player(PhysObj):
    def __init__(self, groups):
        super().__init__(groups, 100, FLOOR_Y - 50)
        
        # RL Integration
        self.ai_mode = False
        self.current_ai_action = 0 # 0 = Run | 1 = Jump | 2 = Fast Fall

        # Rewards
        self.just_jumped = False
        self.just_fast_fell = False
        self.just_landed = False
        self.just_hit_enemy = False
        self.just_dodged_enemy = False
        self.just_collected_weed = False
        self.just_used_shield = False
        self.just_used_magnet = False
        self.just_took_damage = False
        self.just_died = False
        self.just_reached_max_withdrawal = False
        self.just_reached_min_withdrawal = False
        self.just_reached_max_speed = False
        self.just_reached_min_speed = False
        self.just_reached_max_combo = False
        self.just_reached_min_combo = False
        self.just_reached_max_hp = False
        self.just_reached_min_hp = False

        # Chargement des assets
        self.load_all()
        
        # Hitbox un peu plus petite que le sprite pour être sympa
        self.hitbox_w = 50
        self.hitbox_h = 100
        self.rect = pygame.Rect(0, 0, self.hitbox_w, self.hitbox_h)
        self.rect.midbottom = (100, FLOOR_Y)
        
        # Physique
        self.acceleration = 2000
        self.deacceleration = 2600
        self.is_jumping = False
        self.speed = PLAYER_SPEED
        self.velocity_y = 0 
        self.visual_offset_x = -39
        self.visual_offset_y = -10 

        # Etats du joueur
        self.withdrawal = 0
        self.max_withdrawal = MAX_WITHDRAWAL
        self.weed_count = 0
        self.hp = 3
        self.max_hp = 3
        
        # Timers et flags
        self.invincible = False
        self.invincibility_timer = 0
        self.invincibility_duration = 60 # Frames
        self.is_hurt = False
        self.hurt_timer = 0
        self.just_healed = False
        self.just_damaged = False
        self.slowed = False
        self.slow_timer = 0
        self.slow_duration = 300
        
        # PowerUps & Bonus
        self.speed_boost = 0
        self.combo_counter = 0 
        self.magnet_active = False
        self.magnet_timer = 0
        self.has_shield = False      
        self.shield_timer = 0
        
        # Cheats / Debug
        self.god_mode = False 
        self.global_speed_mult = 1.0 
        
        # Stats pour les succès/quêtes
        self.shield_activations = 0
        self.magnet_activations = 0

    def load_all(self):
        # On charge le skin actif via le loader
        self.animations, fps_ratio = asset_loader.load_player(PLAYER_SCALE)
        self.animation_speed = fps_ratio
    
    def inputs(self):
        # Bloque les contrôles si mort ou KO
        if self.hp <= 0 or self.withdrawal >= self.max_withdrawal:
            self.direction.x = 0
            return
            
        self.direction.x = 1 # Avance tout le temps
        self.facing_right = True
        
        if self.ai_mode:
            if self.current_ai_action == 1: # Jump
                if self.on_ground:
                    self.jump()
                    self.just_jumped = True # Reward 
            elif self.current_ai_action == 2: # Fast Fall
                if not self.on_ground:
                    self.velocity_y = max(self.velocity_y, FAST_FALL_FORCE)
                    self.just_fast_fell = True # Reward
            return
        keys = pygame.key.get_pressed()
        
        if self.god_mode:
            # Mode dev : vol libre
            if keys[pygame.K_RIGHT]: self.speed += 10
            if keys[pygame.K_LEFT]:  self.speed = max(0, self.speed - 10)
            if keys[pygame.K_UP]:    
                self.rect.y -= 10
                self.velocity_y = 0
            if keys[pygame.K_DOWN]:  
                self.rect.y += 10
                self.velocity_y = 0
        else:
            # Saut standard
            if (keys[pygame.K_SPACE] or keys[pygame.K_UP]):
                if self.on_ground: self.jump()
                    
        # Fast fall : descente rapide en l'air
        if keys[pygame.K_DOWN] and not self.on_ground:
            self.velocity_y = max(self.velocity_y, FAST_FALL_FORCE)
            
    def check_state(self):
        # Machine à états basique pour l'animation
        if self.hp <= 0 or self.withdrawal >= self.max_withdrawal or self.rect.top > DEATH_Y:
            self.status = 'dead'
        elif self.is_hurt:
            self.status = 'hurt'
        elif not self.on_ground:
             self.status = 'jump'
        elif self.direction.x != 0:
            # Marche si défoncé, sinon courir
            if self.withdrawal > self.max_withdrawal * 0.5:
                self.status = 'walk'
            else:
                self.status = 'run'
        else:
            self.status = 'idle'
    
    def apply_withdrawal(self):
        if self.god_mode: return
        
        # Augmente le manque petit à petit
        if self.withdrawal >= self.max_withdrawal:
             if not hasattr(self, '_last_at_max_withdrawal') or not self._last_at_max_withdrawal:
                 self.just_reached_max_withdrawal = True
             self._last_at_max_withdrawal = True
        else:
             self._last_at_max_withdrawal = False
             
        # Ralentit le joueur si trop en manque
        ratio = self.withdrawal / self.max_withdrawal
        factor = 1.0
        if ratio > 0.5:
             factor = 1.0 - ((ratio - 0.5) * 0.8)

        slow = 0.5 if self.slowed else 1.0
        new_speed = (PLAYER_SPEED + self.speed_boost) * factor * slow * self.global_speed_mult
        
        # Reward speed thresholds
        if new_speed >= (PLAYER_SPEED + MAX_SPEED_BOOST) * 0.95:
             if not hasattr(self, '_last_at_max_speed') or not self._last_at_max_speed:
                 self.just_reached_max_speed = True
             self._last_at_max_speed = True
        else:
             self._last_at_max_speed = False
             
        if new_speed <= PLAYER_SPEED * 0.3:
             if not hasattr(self, '_last_at_min_speed') or not self._last_at_min_speed:
                 self.just_reached_min_speed = True
             self._last_at_min_speed = True
        else:
             self._last_at_min_speed = False

        self.speed = new_speed
    
    def apply_slow(self):
        self.slowed = True
        self.slow_timer = self.slow_duration
        self.combo_counter = 0 # Cassé le combo dommage
    
    def take_damage(self, amount):
        if self.god_mode: return False 
        
        if not self.invincible:
            self.hp -= 1
            self.is_hurt = True
            self.hurt_timer = 20 
            self.invincible = True
            self.invincibility_timer = self.invincibility_duration
            self.just_damaged = True
            
            # Reset des bonus
            self.combo_counter = 0
            self.speed_boost = 0
            
            if self.hp <= 0:
                self.hp = 0
                return True # Mort trigger
            if self.hp == 1: self.just_reached_min_hp = True
            play_sfx("hurt", 0.6)
        return False

    def jump(self):
        self.velocity_y = JUMP_FORCE
        self.is_jumping = True
        self.on_ground = False
        self.rect.y -= 5 # Décolle du sol direct
        play_sfx("jump", 0.4)

    def bounce(self):
        # Rebond sur ennemi (Mario style)
        self.velocity_y = BOUNCE_FORCE
        self.is_jumping = True
        self.on_ground = False
        self.combo_counter += 1
        if self.combo_counter >= 5: self.just_reached_max_combo = True
        play_sfx("jump", 0.3)

    def apply_gravity(self, dt):
        if self.god_mode:
             self.velocity_y = 0
             return
             
        self.velocity_y += GRAVITY * dt
        self.rect.y += self.velocity_y * dt

    def check_collisions(self, platforms, trash_list, dt):
        # Mouvement horizontal
        self.rect.x += self.direction.x * self.speed * dt
        if self.rect.left < 0: self.rect.left = 0

        # Collisions obstacles (poubelles...)
        for trash in trash_list:
            if self.rect.colliderect(trash.rect):
                if self.has_shield:
                    trash.kill() # BOUM
                    continue
                
                # Si on tape par le côté -> Ralentissement
                if self.rect.bottom > trash.rect.top + 20: 
                    if not self.slowed:
                        play_sfx("trash_fall", 0.5)
                    self.apply_slow()

        # Collisions plateformes (PhysObj)
        self.check_horizontal_collisions(platforms)
        
        # Gravité
        self.apply_gravity(dt)
        self.on_ground = False 
        self.check_platform_collisions(platforms)
        
        # Atterrissage sur poubelles (pour sauter dessus)
        if self.velocity_y > 0:
            hits = pygame.sprite.spritecollide(self, trash_list, False)
            for hit in hits:
                if self.rect.bottom <= hit.rect.bottom: 
                    self.rect.bottom = hit.rect.top
                    self.velocity_y = 0
                    self.on_ground = True

    def activate_powerup(self, p_type):
        if p_type == "magnet":
            self.magnet_active = True
            self.magnet_timer = 1200 # ~20 sec
            self.magnet_activations += 1
        elif p_type == "shield":
            self.has_shield = True
            self.shield_timer = 1200 
            self.shield_activations += 1
    
    def update_powerups(self, dt, weed_group):
        # MAGNET : Attire la weed vers le joueur
        if self.magnet_active:
            self.magnet_timer -= 60 * dt
            if self.magnet_timer <= 0:
                self.magnet_active = False
            
            for weed in weed_group:
                pc = pygame.math.Vector2(self.rect.center)
                wc = pygame.math.Vector2(weed.rect.center)
                vec = pc - wc
                
                if 0 < vec.length() < 400: # Rayon d'action
                    vec.normalize_ip()
                    weed.rect.x += vec.x * 600 * dt
                    weed.rect.y += vec.y * 600 * dt
        
        # SHIELD : Timer simple
        if self.has_shield:
            self.shield_timer -= 60 * dt
            if self.shield_timer <= 0:
                self.has_shield = False

    def update(self, dt, platforms=None, trash_obstacles=None, weed_group=None, powerups_group=None, mobs_group=None, *args):
        # Update général appelé chaque frame
        self.reset_reward_flags()
        if self.hp <= 0 or self.withdrawal >= self.max_withdrawal or self.rect.top > DEATH_Y:
            self.check_state()
            self.animate()
            return # Rip

        # Accélération progressive
        self.speed_boost = min(self.speed_boost + SPEED_INCREMENT_RATE * dt, MAX_SPEED_BOOST)
        self.apply_withdrawal()
        
        # Gestion des timers
        for timer_attr in ['invincibility_timer', 'hurt_timer', 'slow_timer']:
            val = getattr(self, timer_attr)
            if val > 0:
                setattr(self, timer_attr, val - 60 * dt)
                
        # Remise à zéro des flags
        if self.invincibility_timer <= 0: self.invincible = False
        if self.hurt_timer <= 0: self.is_hurt = False
        if self.slow_timer <= 0: self.slowed = False
        
        self.inputs()
        self.check_state()
        self.animate()
        
    def check_death(self):
        if self.god_mode: return None
        if self.hp <= 0: return "WASTED"
        if self.withdrawal >= self.max_withdrawal: return "OVERDOSE"
        if self.rect.top > DEATH_Y: return "WASTED" # Tombé dans le vide
        return None

    def animate(self):
        if self.status not in self.animations: return
            
        anim = self.animations[self.status]
        
        if self.status == 'jump':
            # Animation spéciale pour le saut (basée sur la vitesse verticale)
            total = len(anim)
            if self.velocity_y < 0: # Montée
                param = max(0, min(1, abs(self.velocity_y) / abs(JUMP_FORCE)))
                idx = int((1.0 - param) * (total / 2))
                self.frame_index = min(idx, (total // 2) - 1)
            else: # Descente
                self.frame_index = 7
                if self.frame_index >= total: self.frame_index = total - 1
            
            self.frame_index = max(0, min(self.frame_index, total - 1))
        else:
            # Animation boucle classique
            spd = 0.5 if self.status == 'walk' else 1.0
            self.frame_index += self.animation_speed * spd
            
            if self.frame_index >= len(anim):
                if self.status == 'dead':
                    self.frame_index = len(anim) - 1 # Bloque sur la dernière frame
                else:
                    self.frame_index = 0
        
        # indicateurs de retrait et combinaison minimum
        if self.withdrawal <= 5: 
            if not hasattr(self, '_last_at_min_withdrawal') or not self._last_at_min_withdrawal:
                self.just_reached_min_withdrawal = True
            self._last_at_min_withdrawal = True
        else:
            self._last_at_min_withdrawal = False
            
        if self.combo_counter == 0 and hasattr(self, '_old_combo') and self._old_combo > 0:
            self.just_reached_min_combo = True
        self._old_combo = self.combo_counter
                    
        self.image = anim[int(self.frame_index)].copy()
        self.mask = get_mask(self.image)
        
        # Clignotement invincibilité
        if self.invincible:
            alpha = 100 if int(pygame.time.get_ticks() / 100) % 2 == 0 else 255
            self.image.set_alpha(alpha)
        else:
             self.image.set_alpha(255)
        
        # Effet bleu du bouclier
        if self.has_shield:
            blue = self.image.copy()
            blue.fill((0, 100, 255), special_flags=pygame.BLEND_RGB_MULT)
            self.image.blit(blue, (0, 0), special_flags=pygame.BLEND_ADD)
            
            # Ça clignote quand ça va piger
            if self.shield_timer < 180:
                if int(pygame.time.get_ticks() / 150) % 2 == 0:
                    self.image.set_alpha(150)
                else:
                    self.image.set_alpha(255)

    def reset_reward_flags(self):
        """Reset des flags de récompense pour la nouvelle frame."""
        self.just_jumped = False
        self.just_fast_fell = False
        self.just_landed = False
        self.just_hit_enemy = False
        self.just_dodged_enemy = False
        self.just_collected_weed = False
        self.just_used_shield = False
        self.just_used_magnet = False
        self.just_took_damage = False
        self.just_died = False
        self.just_reached_max_withdrawal = False
        self.just_reached_min_withdrawal = False
        self.just_reached_max_speed = False
        self.just_reached_min_speed = False
        self.just_reached_max_combo = False
        self.just_reached_min_combo = False
        self.just_reached_max_hp = False
        self.just_reached_min_hp = False

class PowerUp(pygame.sprite.Sprite):
    def __init__(self, x, y, type_name):
        super().__init__()
        self.type = type_name
        self.image = asset_loader.fetch_img(ASSETS["items"][type_name], alpha=True)
        self.mask = get_mask(self.image)
        self.rect = self.image.get_rect(midbottom=(x, y - 60)) 
        
        self.offset_y = 0
        self.bob_angle = random.uniform(0, 6.28)
        self.bob_speed = 3.0

    def update(self, dt, *args):
        # Petit flottement sympa
        self.bob_angle += self.bob_speed * dt
        self.offset_y = math.sin(self.bob_angle) * 15

class Obstacle(pygame.sprite.Sprite):
    def __init__(self, x, y, w, h, biome="street"):
        self._layer = 0 # Background
        super().__init__()
        self.visual_offset_y = 0
        hitbox_off = 0
        
        # Ajustement selon biome
        if biome in ["park", "foret", "rooftop"]:
            if h < 100:
                 hitbox_off = 80 if biome != "rooftop" else 40
            else:
                 self.visual_offset_y = -75 if biome != "rooftop" else -15        
        
        # Choix texture
        key = f"ground_{biome}"
        if key not in ASSETS["environment"]: key = "ground"
            
        try:
            raw = asset_loader.fetch_img(ASSETS["environment"][key], alpha=True)
        except:
            raw = asset_loader.fetch_img(ASSETS["environment"]["ground"], alpha=True)

        # Tiling de la texture pour remplir w
        iw, ih = raw.get_size()
        self.image = pygame.Surface((w, h), pygame.SRCALPHA)
        self.mask = get_mask(self.image)
        
        tile_w = int(iw * (h / ih))
        tile = pygame.transform.scale(raw, (tile_w, h))
        
        cx = 0
        while cx < w:
            self.image.blit(tile, (cx, 0))
            cx += tile_w
            
        self.rect = self.image.get_rect(topleft=(x, y - hitbox_off))

class Weed(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.visual_offset_y = 0
        
        # Choix du sprite selon le thème du perso
        from progression import progression
        active = progression.state.get("active_skin_set", "default")
        
        c_map = ASSETS.get("collectible_map", {})
        # 1. Check direct (si c'est un set)
        key = c_map.get(active)
        
        # 2. Si pas trouvé, c'est peut-être un item isolé -> on cherche son set parent
        if not key:
            key = "weed" # default
            for s_name, s_cfg in ASSETS.get("boutique_sets", {}).items():
                if active == s_name or active in s_cfg.get("variants", []):
                    key = c_map.get(s_name, "weed")
                    break
        
        # Charge l'image
        try:
            path = ASSETS["items"].get(key, ASSETS["items"]["weed"])
            self.image = asset_loader.fetch_img(path, alpha=True)
        except:
            self.image = asset_loader.fetch_img(ASSETS["items"]["weed"], alpha=True)
            
        # Un peu de resize pour que ce soit homogène
        if self.image.get_width() > 48:
             self.image = pygame.transform.scale(self.image, (40, 40))
        elif self.image.get_width() < 20: 
             self.image = pygame.transform.scale(self.image, (32, 32))
             
        self.mask = get_mask(self.image)
        self.rect = self.image.get_rect(midbottom=(x, y - 50))

class Prop(pygame.sprite.Sprite):
    def __init__(self, x, y, image):
        self._layer = -1 # Background lointain
        super().__init__()
        self.visual_offset_y = 0
        self.image = image
        self.rect = self.image.get_rect(midbottom=(x, y))

class TrashObstacle(pygame.sprite.Sprite):
    def __init__(self, x, y, image):
        self._layer = -1
        super().__init__()
        self.image = image
        self.mask = get_mask(self.image)
        
        box = self.image.get_bounding_rect()
        
        # Hitbox fine (50%) pour pas bloquer bêtement
        self.rect = pygame.Rect(0, 0, int(box.width * 0.5), box.height)
        self.rect.midbottom = (x, y)
        self.rect.x += 10 # Petit tweak position
        self.visual_offset_y = 0

class Police(PhysObj):
    def __init__(self, groups, player):
        # Spawn derrière le joueur
        super().__init__(groups, player.rect.centerx - 200, FLOOR_Y)
        self.player = player
        self.anims = asset_loader.load_police(PLAYER_SCALE)
        self.status = 'run'
        self.idx = 0
        self.image = self.anims[self.status][0]
        self.rect = pygame.Rect(0, 0, 60, 120) 
        self.rect.midbottom = (player.rect.centerx - 200, FLOOR_Y)
        
        self.speed = PLAYER_SPEED * 0.8
        self.on_ground = True
        self.velocity_y = 0
        self.anim_speed = 0.2
        self.visual_offset_x = 0 
        self.visual_offset_y = -10
        self.facing_right = True

    def check_state(self):
        # L'attaque doit se finir avant de changer
        if self.status == 'attack' and self.idx < 2.9: return
        
        if not self.on_ground: self.status = 'jump'
        elif self.speed > 50: self.status = 'run'
        else: self.status = 'idle'
            
    def animate(self):
        if self.status not in self.anims: return
            
        if self.status == 'attack' and self.idx >= 2.8:
            self.idx = 2.8 # Bloque frame d'attaque
            return

        frames = self.anims[self.status]
        self.idx += self.anim_speed
        if self.idx >= len(frames): self.idx = 0
            
        self.image = frames[int(self.idx)]
        self.mask = get_mask(self.image)
        self.image.set_alpha(255)

    def update(self, dt, platforms=None, trash_list=None, *args):
        if not platforms: 
            self.animate()
            return
        
        # IA basique : suit le player mais pas trop près
        # Vitesse de base sans les pénalités du joueur (slow/addiction) pour que le policier rattrape
        wanted = PLAYER_SPEED * self.player.global_speed_mult
        dist = self.player.rect.centerx - self.rect.centerx
        
        if dist > 600:   wanted *= 1.2 # Rattrape
        elif dist < 150: wanted *= 0.8 # Freine
        
        # Lissage de la vitesse
        self.speed += (wanted - self.speed) * 0.1
        
        self.apply_gravity(dt)
        self.rect.x += self.speed * dt
        self.on_ground = False
        self.check_platform_collisions(platforms)
        
        self.check_state()
        self.animate()

class Bird(PhysObj):
    def __init__(self, groups, x, y, dir_x=-1):
        super().__init__(groups, x, y)
        self.anims = {
            'walk': asset_loader.get_anim('bird', 'walk', 1.5),
            'idle': asset_loader.get_anim('bird', 'idle', 1.5)
        }
        self.image = self.anims['walk'][0]
        self.mask = get_mask(self.image)
        self.rect = self.image.get_rect(center=(x, y))
        self.status = 'walk'
        self.direction.x = dir_x
        self.facing_right = dir_x > 0
        self.speed = random.randint(150, 250)
        self.visual_offset_y = 0

    def update(self, dt, *args):
        self.rect.x += self.direction.x * self.speed * dt
        # Anim simple
        frames = self.anims[self.status]
        self.image = frames[int(pygame.time.get_ticks() / 100) % len(frames)]
        self.mask = get_mask(self.image)

# Classe générique pour les mobs terrestres (Loup / Ours)
class GroundMob(PhysObj):
    def __init__(self, groups, x, y, key, scale, speed_range, size, dir_x=-1):
        super().__init__(groups, x, y)
        self.anims = {
            'run': asset_loader.get_anim(key, 'run', scale),
            'idle': asset_loader.get_anim(key, 'idle', scale)
        }
        self.status = 'run'
        self.image = self.anims['run'][0]
        self.mask = get_mask(self.image)
        self.rect = pygame.Rect(0, 0, size[0], size[1])
        self.rect.midbottom = (x, y)
        self.direction.x = dir_x
        self.facing_right = dir_x > 0
        self.speed = random.randint(*speed_range)
        self.visual_offset_y = 0

    def update(self, dt, platforms=None, *args):
        self.apply_gravity(dt)
        self.rect.x += self.direction.x * self.speed * dt
        self.on_ground = False
        if platforms: self.check_platform_collisions(platforms)
        
        # Anim loop
        frames = self.anims[self.status]
        self.image = frames[int(pygame.time.get_ticks() / 100) % len(frames)]
        self.mask = get_mask(self.image)

class Rat(GroundMob):
    def __init__(self, groups, x, y, dir_x=-1):
        # Init manuel car Rat utilise 'walk' et pas 'run'
        PhysObj.__init__(self, groups, x, y)
        self.anims = {
            'walk': asset_loader.get_anim('rat', 'walk', 1.5),
            'idle': asset_loader.get_anim('rat', 'idle', 1.5)
        }
        self.image = self.anims['walk'][0]
        self.mask = get_mask(self.image)
        self.rect = pygame.Rect(0, 0, 40, 30)
        self.rect.midbottom = (x, y)
        self.status = 'walk'
        self.direction.x = dir_x
        self.facing_right = dir_x > 0
        self.speed = random.randint(50, 120)
        self.visual_offset_y = -10 
        self.velocity_y = 0

class DeadRat(pygame.sprite.Sprite):
    def __init__(self, x, y, groups, play_anim=False, facing_right=True):
        super().__init__(groups)
        self.visual_offset_y = 0
        self.frames = asset_loader.get_anim('rat', 'death', 1.5)
        self.idx = 0
        self.anim_speed = 0.2
        self.playing = play_anim
        
        if self.frames:
            self.image = self.frames[0] if self.playing else self.frames[-1]
        else:
            # Fallback moche mais fonctionnel
            img = asset_loader.fetch_img(ASSETS["rat"]["idle"]["p"])
            self.image = pygame.transform.rotate(pygame.transform.scale(img, (48, 48)), -90)
            self.playing = False
        
        if not facing_right:
            self.image = pygame.transform.flip(self.image, True, False)
            
        self.rect = self.image.get_rect(midbottom=(x, y))
        
    def update(self, dt, *args):
        if self.playing and self.frames:
            self.idx += self.anim_speed
            if self.idx >= len(self.frames):
                self.idx = len(self.frames) - 1
                self.playing = False
            self.image = self.frames[int(self.idx)]

class Drone(PhysObj):
    def __init__(self, groups, x, y, player):
        super().__init__(groups, x, y)
        self.player = player
        
        # Plusieurs types de drones pour la variété
        dtype = random.choice(["1", "2", "3", "4", "5", "6"])
        self.anims = asset_loader.load_drone(dtype, scale=2)
        
        self.status = 'idle'
        if self.status not in self.anims:
             self.status = list(self.anims.keys())[0]
             
        self.idx = 0
        self.anim_speed = 0.15
        self.image = self.anims[self.status][0]
        self.mask = get_mask(self.image)
        self.rect = self.image.get_rect(center=(x, y))
        self.visual_offset_y = 0
        
        # IA de suivi
        self.target_y_off = -180 
        self.wobble = 0
        self.vel_x = 0.12 
        self.vel_y = 0.08 
        self.retreating = False 
    
    def update(self, dt, *args):
        self.wobble += dt * 4
        
        if self.retreating:
             self.rect.y -= 10
             self.rect.x += 5
             if self.rect.bottom < -100: self.kill()
             self._play_anim()
             return

        # Cible le haut de la tête du joueur
        tx = self.player.rect.centerx + 50 
        ty = self.player.rect.centery + self.target_y_off + math.sin(self.wobble) * 40

        dx = abs(self.rect.centerx - self.player.rect.centerx)
        if dx < 150:
             ty += 150 # Plonge vers le joueur
             self.vel_x = 0.15 
        else:
             self.vel_x = 0.12

        # Lissage mouvement
        self.rect.centerx += (tx - self.rect.centerx) * self.vel_x
        self.rect.centery += (ty - self.rect.centery) * self.vel_y
        
        # Change anim si ça bouge vite (ou pas)
        if abs(tx - self.rect.centerx) > 2:
             if 'walk' in self.anims: self.status = 'walk'
        else:
             if 'idle' in self.anims: self.status = 'idle'

        self._play_anim()
        
    def _play_anim(self):
        # Petite méthode interne pour pas dupliquer
        frames = self.anims.get(self.status)
        if not frames: return
            
        self.idx += self.anim_speed
        if self.idx >= len(frames): self.idx = 0
        self.image = frames[int(self.idx)]
        self.mask = get_mask(self.image)



class Wolf(GroundMob):
    def __init__(self, groups, x, y, dir_x=-1):
        super().__init__(groups, x, y, 'loup', 2.0, (200, 300), (80, 100), dir_x)

class Bear(GroundMob):
    def __init__(self, groups, x, y, dir_x=-1):
        super().__init__(groups, x, y, 'ours', 2.5, (100, 180), (100, 150), dir_x)
