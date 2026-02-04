import pygame
import math
import random

from settings import *
from entity import PhysObj
from asset_loader import asset_loader 
from assets_registry import ASSETS

def get_mask(surface):
    return pygame.mask.from_surface(surface)


class Player(PhysObj):
    def __init__(self, groups):
        self._layer = 2
        super().__init__(groups, 100, FLOOR_Y - 50)
        self.load_all()
        
        self.hitbox_w = 50
        self.hitbox_h = 100
        self.rect = pygame.Rect(0, 0, self.hitbox_w, self.hitbox_h)
        self.rect.midbottom = (100, FLOOR_Y)
        
        self.acceleration = 2000
        self.deacceleration = 2600
        self.is_jumping = False
        self.speed = PLAYER_SPEED
        
        self.withdrawal = 0
        self.max_withdrawal = MAX_WITHDRAWAL
        self.weed_count = 0
        
        self.invincible = False
        self.invincibility_timer = 0
        self.invincibility_duration = 60
        
        self.is_hurt = False
        self.hurt_timer = 0
        
        self.just_healed = False
        self.just_damaged = False
        self.hp = 3
        self.max_hp = 3
        
        self.visual_offset_x = -39
        self.visual_offset_y = -10 
        
        self.slowed = False
        self.slow_timer = 0
        self.slow_duration = 300
        
        self.speed_boost = 0
        self.velocity_y = 0 
        
        self.combo_counter = 0 
        
        self.magnet_active = False
        self.magnet_timer = 0
        self.has_shield = False      
        self.shield_timer = 0
        
        self.god_mode = False 
        self.global_speed_mult = 1.0 

    def load_all(self):
        self.animations = asset_loader.load_player(PLAYER_SCALE)
    
    def inputs(self):
        if self.hp <= 0 or self.withdrawal >= self.max_withdrawal:
            self.direction.x = 0
            return
            
        self.direction.x = 1
        self.facing_right = True
        
        keys = pygame.key.get_pressed()
        if self.god_mode:
            if keys[pygame.K_RIGHT]:
                self.speed += 10
            if keys[pygame.K_LEFT]:
                self.speed = max(0, self.speed - 10)
            
            if keys[pygame.K_UP]:
                self.rect.y -= 10
                self.velocity_y = 0
            if keys[pygame.K_DOWN]:
                self.rect.y += 10
                self.velocity_y = 0
        else:
            if (keys[pygame.K_SPACE] or keys[pygame.K_UP]):
                if self.on_ground:
                    self.jump()

    def check_state(self):
        if self.hp <= 0 or self.withdrawal >= self.max_withdrawal or self.rect.top > DEATH_Y:
            self.status = 'dead'
        elif self.is_hurt:
            self.status = 'hurt'
        elif not self.on_ground:
             self.status = 'jump'
        elif self.direction.x != 0:
            if self.withdrawal > self.max_withdrawal * 0.5:
                self.status = 'walk'
            else:
                self.status = 'run'
        else:
            self.status = 'idle'
    
    def apply_withdrawal(self):
        if self.god_mode: return
        self.withdrawal = min(self.withdrawal + WITHDRAWAL_RATE, self.max_withdrawal)
        withdrawal_ratio = self.withdrawal / self.max_withdrawal
        withdrawal_factor = 1.0
        
        if withdrawal_ratio > 0.5:
             withdrawal_factor = 1.0 - ((withdrawal_ratio - 0.5) * 0.8)

        slow_factor = 0.5 if self.slowed else 1.0
        self.speed = (PLAYER_SPEED + self.speed_boost) * withdrawal_factor * slow_factor * self.global_speed_mult
    
    def apply_slow(self):
        self.slowed = True
        self.slow_timer = self.slow_duration
        self.combo_counter = 0 
    
    def take_damage(self, amount):
        if self.god_mode: return False 
        
        if not self.invincible:
            self.hp -= 1
            self.is_hurt = True
            self.hurt_timer = 20 
            self.invincible = True
            self.invincibility_timer = self.invincibility_duration
            self.just_damaged = True
            self.combo_counter = 0
            self.speed_boost = 0
            if self.hp <= 0:
                self.hp = 0
                return True
        return False

    def jump(self):
        self.velocity_y = JUMP_FORCE
        self.is_jumping = True
        self.on_ground = False
        self.rect.y -= 5 

    def bounce(self):
        self.velocity_y = BOUNCE_FORCE
        self.is_jumping = True
        self.on_ground = False
        self.combo_counter += 1

    def apply_gravity(self, dt):
        if self.god_mode:
             self.velocity_y = 0
             return
             
        self.velocity_y += GRAVITY * dt
        self.rect.y += self.velocity_y * dt

    def check_collisions(self, platforms, trash_obstacles, dt):
        self.rect.x += self.direction.x * self.speed * dt
        if self.rect.left < 0:
            self.rect.left = 0

        for trash in trash_obstacles:
            if self.rect.colliderect(trash.rect):
                if self.has_shield:
                    trash.kill() 
                    continue
                if self.rect.bottom > trash.rect.top + 20: 
                    self.apply_slow()
                    self.rect.right = trash.rect.left

        self.check_horizontal_collisions(platforms)
        self.apply_gravity(dt)
        self.on_ground = False 
        self.check_platform_collisions(platforms)
        
        if self.velocity_y > 0:
            hits = pygame.sprite.spritecollide(self, trash_obstacles, False)
            for hit in hits:
                if self.rect.bottom <= hit.rect.bottom: 
                    self.rect.bottom = hit.rect.top
                    self.velocity_y = 0
                    self.on_ground = True

    def activate_powerup(self, p_type):
        if p_type == "magnet":
            self.magnet_active = True
            self.magnet_timer = 1200 
        elif p_type == "shield":
            self.has_shield = True
            self.shield_timer = 1200 
    
    def update_powerups(self, dt, weed_group):
        if self.magnet_active:
            self.magnet_timer -= 60 * dt
            if self.magnet_timer <= 0:
                self.magnet_active = False
            
            for weed in weed_group:
                player_center = pygame.math.Vector2(self.rect.center)
                weed_center = pygame.math.Vector2(weed.rect.center)
                dist_v = player_center - weed_center
                
                if 0 < dist_v.length() < 400: 
                    dist_v.normalize_ip()
                    weed.rect.x += dist_v.x * 600 * dt
                    weed.rect.y += dist_v.y * 600 * dt
        
        if self.has_shield:
            self.shield_timer -= 60 * dt
            if self.shield_timer <= 0:
                self.has_shield = False

    def update(self, dt, platforms=None, trash_obstacles=None, weed_group=None, powerups_group=None, mobs_group=None, *args):
        if self.hp <= 0 or self.withdrawal >= self.max_withdrawal or self.rect.top > DEATH_Y:
            self.check_state()
            self.animate()
            return

        self.speed_boost = min(self.speed_boost + SPEED_INCREMENT_RATE * dt, MAX_SPEED_BOOST)
        self.apply_withdrawal()
        
        if self.invincibility_timer > 0:
            self.invincibility_timer -= 1 * 60 * dt
            if self.invincibility_timer <= 0:
                self.invincible = False
        
        if self.hurt_timer > 0:
            self.hurt_timer -= 1 * 60 * dt
            if self.hurt_timer <= 0:
                self.is_hurt = False
        
        if self.slow_timer > 0:
            self.slow_timer -= 1 * 60 * dt
            if self.slow_timer <= 0:
                self.slowed = False
        
        self.inputs()
        self.check_state()
        self.animate()
        
    def check_death(self):
        if self.god_mode: return None
        if self.hp <= 0: return "WASTED"
        if self.withdrawal >= self.max_withdrawal: return "OVERDOSE"
        if self.rect.top > DEATH_Y: return "WASTED" 
        return None

    def animate(self):
        if self.status not in self.animations:
            return 
            
        animation = self.animations[self.status]
        
        if self.status == 'jump':
            total_frames = len(animation)
            if self.velocity_y < 0:
                norm = max(0, min(1, abs(self.velocity_y) / abs(JUMP_FORCE)))
                idx = int((1.0 - norm) * (total_frames / 2))
                self.frame_index = min(idx, (total_frames // 2) - 1)
            else:
                self.frame_index = 7
                if self.frame_index >= total_frames:
                    self.frame_index = total_frames - 1
            self.frame_index = max(0, min(self.frame_index, total_frames - 1))
        else:
            speed_mult = 0.5 if self.status == 'walk' else 1.0
            self.frame_index += self.animation_speed * speed_mult
            if self.frame_index >= len(animation):
                if self.status == 'dead':
                    self.frame_index = len(animation) - 1
                else:
                    self.frame_index = 0
        image = animation[int(self.frame_index)]
        self.image = image.copy() 
        self.mask = get_mask(self.image)
        
        if self.invincible:
            alpha = 100 if int(pygame.time.get_ticks() / 100) % 2 == 0 else 255
            self.image.set_alpha(alpha)
        else:
             self.image.set_alpha(255)
        
        if self.has_shield:
            blue_mask = self.image.copy()
            blue_mask.fill((0, 100, 255), special_flags=pygame.BLEND_RGB_MULT)
            self.image.blit(blue_mask, (0, 0), special_flags=pygame.BLEND_ADD)
            
            if self.shield_timer < 180:
                if int(pygame.time.get_ticks() / 150) % 2 == 0:
                    self.image.set_alpha(150)
                else:
                    self.image.set_alpha(255)

class PowerUp(pygame.sprite.Sprite):
    def __init__(self, x, y, type_name):
        super().__init__()
        self.type = type_name
        self.image = asset_loader.fetch_img(ASSETS["items"][type_name], alpha=True)
        self.mask = get_mask(self.image)
        self.rect = self.image.get_rect(midbottom=(x, y - 60)) 
        self.visual_offset_y = 0
        self.float_offset = random.uniform(0, math.pi * 2)
        self.float_speed = 3.0

    def update(self, dt, *args):
        self.float_offset += self.float_speed * dt
        self.visual_offset_y = math.sin(self.float_offset) * 15

class Obstacle(pygame.sprite.Sprite):
    def __init__(self, x, y, w, h, biome="street"):
        self._layer = 0
        super().__init__()
        hitbox_offset = 0
        self.visual_offset_y = 0
        
        if biome == "park" or biome == "foret":
            if h < 100:
                 hitbox_offset = 80 
            else:
                 self.visual_offset_y = -75        
        asset_key = f"ground_{biome}"
        if asset_key not in ASSETS["environment"]:
            asset_key = "ground"
            
        try:
            path = ASSETS["environment"][asset_key]
            original_image = asset_loader.fetch_img(path, alpha=True)
        except:
            original_image = asset_loader.fetch_img(ASSETS["environment"]["ground"], alpha=True)

        img_w, img_h = original_image.get_size()
        self.image = pygame.Surface((w, h), pygame.SRCALPHA)
        self.mask = get_mask(self.image)
        tile_w = int(img_w * (h / img_h))
        tile_image = pygame.transform.scale(original_image, (tile_w, h))
        curr_x = 0
        while curr_x < w:
            self.image.blit(tile_image, (curr_x, 0))
            curr_x += tile_w
        self.rect = self.image.get_rect(topleft=(x, y - hitbox_offset))

class Weed(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.visual_offset_y = 0
        self.image = asset_loader.fetch_img(ASSETS["items"]["weed"], alpha=True)
        self.mask = get_mask(self.image)
        self.rect = self.image.get_rect(midbottom=(x, y - 50))

class Prop(pygame.sprite.Sprite):
    def __init__(self, x, y, image):
        self._layer = -1
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
        
        trim_rect = self.image.get_bounding_rect()
        self.rect = pygame.Rect(0, 0, trim_rect.width, trim_rect.height)
        self.rect.midbottom = (x, y)
        self.visual_offset_y = 0

class Police(PhysObj):
    def __init__(self, groups, player):
        super().__init__(groups, player.rect.centerx - 200, FLOOR_Y)
        self.player = player
        self.animations = asset_loader.load_police(PLAYER_SCALE)
        self.status = 'run'
        self.frame_index = 0
        self.image = self.animations[self.status][self.frame_index]
        self.rect = pygame.Rect(0, 0, 60, 120) 
        self.rect.midbottom = (player.rect.centerx - 200, FLOOR_Y)
        
        self.speed = PLAYER_SPEED * 0.8
        self.on_ground = True
        self.velocity_y = 0
        self.animation_speed = 0.2
        self.visual_offset_x = 0 
        self.visual_offset_y = -10
        self.facing_right = True

    def check_state(self):
        if self.status == 'attack' and self.frame_index < 2.9:
            return

        if not self.on_ground: self.status = 'jump'
        elif self.speed > 50: self.status = 'run'
        else: self.status = 'idle'
            
    def animate(self):
        if self.status not in self.animations or not self.animations[self.status]:
            return
            
        if self.status == 'attack' and self.frame_index >= 2.8:
            self.frame_index = 2.8
            return

        animation = self.animations[self.status]
        self.frame_index += self.animation_speed
        if self.frame_index >= len(animation):
            self.frame_index = 0
            
        self.image = animation[int(self.frame_index)]
        self.mask = get_mask(self.image)
        self.image.set_alpha(255)

    def update(self, dt, platforms=None, trash_obstacles=None, *args):
        if platforms is None: 
            self.animate()
            return

        target_speed = self.player.speed
        dist_to_player = self.player.rect.centerx - self.rect.centerx
        
        if dist_to_player > 600:
             target_speed *= 1.2
        elif dist_to_player < 150:
             target_speed *= 0.8
        
        self.speed += (target_speed - self.speed) * 0.1
        self.apply_gravity(dt)
        self.rect.x += self.speed * dt
        self.on_ground = False
        self.check_platform_collisions(platforms)
        
        for trash in trash_obstacles:
            if self.rect.colliderect(trash.rect):
                self.speed = 0 
        
        self.check_state()
        self.animate()

class Bird(PhysObj):
    def __init__(self, groups, x, y, dir_x=-1):
        super().__init__(groups, x, y)
        self.animations = {
            'walk': asset_loader.get_anim('bird', 'walk', 1.5),
            'idle': asset_loader.get_anim('bird', 'idle', 1.5)
        }
        self.image = self.animations['walk'][0]
        self.mask = get_mask(self.image)
        self.rect = self.image.get_rect(center=(x, y))
        self.status = 'walk'
        self.direction.x = dir_x
        self.speed = random.randint(150, 250)
        self.visual_offset_y = 0

    def update(self, dt, *args):
        self.rect.x += self.direction.x * self.speed * dt
        self.animate()
        
    def animate(self):
        animation = self.animations[self.status]
        self.image = animation[int(pygame.time.get_ticks() / 100) % len(animation)]
        self.mask = get_mask(self.image)


class Rat(PhysObj):
    def __init__(self, groups, x, y, dir_x=-1):
        super().__init__(groups, x, y)
        self.animations = {
            'walk': asset_loader.get_anim('rat', 'walk', 1.5),
            'idle': asset_loader.get_anim('rat', 'idle', 1.5)
        }
        self.image = self.animations['walk'][0]
        self.mask = get_mask(self.image)
        self.rect = pygame.Rect(0, 0, 40, 30)
        self.rect.midbottom = (x, y)
        self.status = 'walk'
        self.direction.x = dir_x
        self.speed = random.randint(50, 120)
        self.visual_offset_y = -10 
        self.velocity_y = 0

    def update(self, dt, platforms=None, *args):
        self.apply_gravity(dt)
        self.rect.x += self.direction.x * self.speed * dt
        self.on_ground = False
        if platforms:
            self.check_platform_collisions(platforms)
        self.animate()
        
    def animate(self):
        animation = self.animations[self.status]
        self.image = animation[int(pygame.time.get_ticks() / 100) % len(animation)]
        self.mask = get_mask(self.image)


class DeadRat(pygame.sprite.Sprite):
    def __init__(self, x, y, groups, play_anim=False, facing_right=True):
        super().__init__(groups)
        self.visual_offset_y = 0
        self.frames = asset_loader.get_anim('rat', 'death', 1.5)
        
        self.frame_index = 0
        self.animation_speed = 0.2
        self.playing = play_anim
        
        if self.frames:
            self.image = self.frames[0] if self.playing else self.frames[-1]
        else:
            img = asset_loader.fetch_img(ASSETS["rat"]["idle"]["p"])
            img = pygame.transform.scale(img, (48, 48))
            # Angle de -90 pour mettre le rat sur le dos sans être à l'envers
            self.image = pygame.transform.rotate(img, -90)
            self.playing = False
            
        self.rect = self.image.get_rect(midbottom=(x, y))
        
    def update(self, dt, *args):
        if self.playing and self.frames:
            self.frame_index += self.animation_speed
            if self.frame_index >= len(self.frames):
                self.frame_index = len(self.frames) - 1
                self.playing = False
            
            self.image = self.frames[int(self.frame_index)]

class Drone(PhysObj):
    def __init__(self, groups, x, y, player):
        super().__init__(groups, x, y)
        self.player = player
        self.drone_type = random.choice(["1", "2", "3", "4", "5", "6"])
        self.animations = asset_loader.load_drone(self.drone_type, scale=2)
        
        self.status = 'idle'
        if self.status not in self.animations:
             self.status = list(self.animations.keys())[0]
             
        self.frame_index = 0
        self.animation_speed = 0.15
        self.image = self.animations[self.status][self.frame_index]
        self.mask = get_mask(self.image)
        self.rect = self.image.get_rect(center=(x, y))
        self.hitbox_rect = self.rect.inflate(-20, -20)
        
        self.visual_offset_y = 0
        self.target_offset_y = -180 
        self.wobble = 0
        self.speed_x = 0.12 
        self.speed_y = 0.08 
        
        self.attack_cooldown = 0
        self.can_attack = True
        self.retreating = False 
    
    def update(self, dt, *args):
        self.wobble += dt * 4
        if self.retreating:
             self.rect.y -= 10
             self.rect.x += 5
             if self.rect.bottom < -100:
                  self.kill()
             self.animate()
             return

        target_x = self.player.rect.centerx + 50 
        target_y = self.player.rect.centery + self.target_offset_y + math.sin(self.wobble) * 40

        dist_x = abs(self.rect.centerx - self.player.rect.centerx)
        if dist_x < 150:
             target_y += 150
             self.speed_x = 0.15 
        else:
             self.speed_x = 0.12

        self.rect.centerx += (target_x - self.rect.centerx) * self.speed_x
        self.rect.centery += (target_y - self.rect.centery) * self.speed_y
        
        if abs(target_x - self.rect.centerx) > 2:
             if 'walk' in self.animations: self.status = 'walk'
        else:
             if 'idle' in self.animations: self.status = 'idle'

        self.animate()
        
        if self.attack_cooldown > 0:
            self.attack_cooldown -= dt
            alpha = 100 if int(pygame.time.get_ticks() / 50) % 2 == 0 else 255
            self.image.set_alpha(alpha)
            return 
        
        if pygame.sprite.collide_mask(self, self.player):
            self.attack_cooldown = 2.0 
            if self.player.god_mode:
                 self.speed_x = -0.5 
                 self.rect.x += 20 
                 return

            if not self.player.invincible and not self.player.has_shield:
                self.player.take_damage(1)
                self.retreating = True
                return       
            elif self.player.has_shield:
                self.speed_x = -0.5

class Wolf(PhysObj):
    def __init__(self, groups, x, y, dir_x=-1):
        super().__init__(groups, x, y)
        self.animations = {
            'run': asset_loader.get_anim('loup', 'run', 2.0),
            'idle': asset_loader.get_anim('loup', 'idle', 2.0)
        }
        self.status = 'run'
        self.image = self.animations['run'][0]
        self.mask = get_mask(self.image)
        self.rect = pygame.Rect(0, 0, 80, 100)
        self.rect.midbottom = (x, y)
        self.direction.x = dir_x
        self.speed = random.randint(200, 300)
        self.visual_offset_y = 0

    def update(self, dt, platforms=None, *args):
        self.apply_gravity(dt)
        self.rect.x += self.direction.x * self.speed * dt
        self.on_ground = False
        if platforms: self.check_platform_collisions(platforms)
        self.animate()
        
    def animate(self):
        animation = self.animations[self.status]
        self.image = animation[int(pygame.time.get_ticks() / 100) % len(animation)]
        self.mask = get_mask(self.image)

class Bear(PhysObj):
    def __init__(self, groups, x, y, dir_x=-1):
        super().__init__(groups, x, y)
        self.animations = {
            'run': asset_loader.get_anim('ours', 'run', 2.5),
            'idle': asset_loader.get_anim('ours', 'idle', 2.5),
             'dead': asset_loader.get_anim('ours', 'death', 2.5)
        }
        self.status = 'run'
        self.image = self.animations['run'][0]
        self.mask = get_mask(self.image)
        self.rect = pygame.Rect(0, 0, 100, 150)
        self.rect.midbottom = (x, y)
        self.direction.x = dir_x
        self.speed = random.randint(100, 180)
        self.visual_offset_y = 0

    def update(self, dt, platforms=None, *args):
        self.apply_gravity(dt)
        self.rect.x += self.direction.x * self.speed * dt
        self.on_ground = False
        if platforms: self.check_platform_collisions(platforms)
        self.animate()

    def animate(self):
        animation = self.animations[self.status]
        self.image = animation[int(pygame.time.get_ticks() / 100) % len(animation)]
        self.mask = get_mask(self.image)