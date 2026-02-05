import pygame
from settings import *

class PhysObj(pygame.sprite.Sprite):
    def __init__(self, groups, x, y):
        super().__init__(groups)
        
        self.frame_index = 0
        self.animation_speed = 0.15
        self.animations = {}
        
        self.direction = pygame.math.Vector2()
        self.velocity_y = 0
        self.on_ground = False
        
        self.status = 'idle'
        self.facing_right = True
        
        self.image = pygame.Surface((32, 32))
        self.rect = self.image.get_rect(midbottom=(x, y))

        self.just_hit_wall = False
        self.just_jumped = False
        self.is_falling = False

    def apply_gravity(self, dt):
        self.velocity_y += GRAVITY * dt
        self.rect.y += self.velocity_y * dt
        self.is_falling = self.velocity_y > 0

    def check_platform_collisions(self, platforms):
        self.just_hit_wall = False
        hits = pygame.sprite.spritecollide(self, platforms, False)
        for hit in hits:
            if self.velocity_y > 0:
                self.rect.bottom = hit.rect.top
                self.velocity_y = 0
                self.on_ground = True
            elif self.velocity_y < 0:
                self.rect.top = hit.rect.bottom
                self.velocity_y = 0
            else: 
                self.just_hit_wall = True

    def check_horizontal_collisions(self, platforms):
        hits = pygame.sprite.spritecollide(self, platforms, False)
        for hit in hits:
            if self.direction.x > 0:
                self.rect.right = hit.rect.left
            elif self.direction.x < 0:
                self.rect.left = hit.rect.right

    def animate(self):
        if self.status not in self.animations or not self.animations[self.status]:
            return
            
        animation = self.animations[self.status]
        
        self.frame_index += self.animation_speed
        if self.frame_index >= len(animation):
            self.frame_index = 0
        
        self.image = animation[int(self.frame_index)]
        self.mask = pygame.mask.from_surface(self.image)
        
        if hasattr(self, 'invincible') and self.invincible:
            if int(pygame.time.get_ticks() / 100) % 2 == 0:
                self.image.set_alpha(100)
            else:
                self.image.set_alpha(255)
        else:
            self.image.set_alpha(255)

    def check_state(self):
        pass

    def update(self, dt):
        pass
