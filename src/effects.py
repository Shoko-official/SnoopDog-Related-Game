import pygame
import random
import math
from settings import HEART_SIZE, WITHDRAWAL_BAR_WIDTH, SCREEN_WIDTH, SCREEN_HEIGHT
from asset_loader import asset_loader
from assets_registry import ASSETS

class Particle(pygame.sprite.Sprite):
    def __init__(self, x, y, image, velocity, lifetime, groups, scale_decay=True):
        super().__init__(groups)
        self.original_image = image
        self.image = image.copy()
        self.rect = self.image.get_rect(center=(x, y))
        
        self.velocity = list(velocity)
        self.lifetime = lifetime
        self.age = 0
        self.scale_decay = scale_decay
        self.angle = random.uniform(0, 360)
        self.rot_speed = random.uniform(-5, 5)

    def update(self):
        self.age += 1
        if self.age >= self.lifetime:
            self.kill()
            return
        
        self.rect.x += self.velocity[0]
        self.rect.y += self.velocity[1]
        self.velocity[1] += 0.2 # Gravité légère
        
        self.angle += self.rot_speed
        life_ratio = 1 - (self.age / self.lifetime)
        alpha = int(255 * life_ratio)
        
        rotated_img = pygame.transform.rotate(self.original_image, self.angle)
        if self.scale_decay:
            scale = max(0, life_ratio)
            w = int(rotated_img.get_width() * scale)
            h = int(rotated_img.get_height() * scale)
            if w <= 0 or h <= 0:
                self.kill()
                return
            rotated_img = pygame.transform.scale(rotated_img, (w, h))

        rotated_img.set_alpha(alpha)
        self.image = rotated_img
        self.rect = self.image.get_rect(center=self.rect.center)


class ParticleEmitter:
    def __init__(self):
        self.sprites = {}
        try:
            weed_img = asset_loader.fetch_img(ASSETS["items"]["weed"])
            self.sprites["weed"] = pygame.transform.scale(weed_img, (16, 16))
            heart_img = asset_loader.fetch_img(ASSETS["items"]["heart"])
            self.sprites["heart"] = pygame.transform.scale(heart_img, (12, 12))
            
            # Shard (éclat générique) - on crée un carré blanc propre
            shard = pygame.Surface((8, 8), pygame.SRCALPHA)
            shard.fill((255, 255, 255))
            self.sprites["shard"] = shard
            
        except Exception as e:
            print(f"ERREUR : Impossible de charger les sprites de particules : {e}")

    def create_explosion(self, x, y, color, count, particles_group, sprite_key="shard"):
        base_img = self.sprites.get(sprite_key, self.sprites.get("shard"))
        if not base_img: return # Safety

        for _ in range(count):
            speed_x = random.uniform(-6, 6)
            speed_y = random.uniform(-8, -2)
            img = base_img.copy()
            if sprite_key == "shard":
                img.fill(color, special_flags=pygame.BLEND_RGBA_MULT)
            
            Particle(x, y, img, (speed_x, speed_y), random.randint(20, 40), particles_group)

    def weed_collected(self, x, y, particles_group):
        # Explosion de petites feuilles vertes
        self.create_explosion(x, y, (100, 255, 100), 10, particles_group, sprite_key="weed")
    
    def enemy_killed(self, x, y, particles_group):
        # Sang / Éclats rouges
        self.create_explosion(x, y, (255, 50, 50), 15, particles_group, sprite_key="shard")
    
    def player_hurt(self, x, y, particles_group):
        self.create_explosion(x, y, (200, 0, 0), 10, particles_group, sprite_key="shard")

    def drone_hit(self, x, y, particles_group):
        # Éclats métalliques (gris) + Étincelles (jaune)
        self.create_explosion(x, y, (150, 150, 150), 10, particles_group, sprite_key="shard")
        self.create_explosion(x, y, (255, 255, 0), 5, particles_group, sprite_key="shard")

    def heal_effect(self, x, y, particles_group):
        # Petits coeurs qui montent
        img = self.sprites.get("heart")
        if not img: return

        for _ in range(8):
            speed_x = random.uniform(-2, 2)
            speed_y = random.uniform(-5, -2)
            Particle(x, y, img, (speed_x, speed_y), 40, particles_group, scale_decay=False)


class HUD:
    def __init__(self):
        # Polices
        self.font_main = pygame.font.SysFont('Impact', 32)
        self.font_sub = pygame.font.SysFont('Arial', 20, bold=True)
        self.font_btn = pygame.font.SysFont('Arial', 32, bold=True)
        self.font_small = pygame.font.SysFont('Arial', 14)
        
    def draw_hearts(self, surface, x, y, current, maximum, size=HEART_SIZE):
        from asset_loader import asset_loader
        from assets_registry import ASSETS
        
        heart_img = asset_loader.fetch_img(ASSETS["items"]["heart"])
        heart_img = pygame.transform.scale(heart_img, (size, size))
        
        for i in range(maximum):
            px = x + i * (size + 5)
            pos = (px, y)
            if i < current:
                surface.blit(heart_img, pos)
            else:
                # coeur vide ou sombre
                dark = heart_img.copy()
                dark.fill((40, 40, 40), special_flags=pygame.BLEND_RGB_MULT)
                surface.blit(dark, pos)
    def draw_withdrawal_bar(self, surface, x, y, current, maximum, width=WITHDRAWAL_BAR_WIDTH, height=20):
        # Ratio du manque
        ratio = max(0, min(1, current / maximum))
        
        # Le fond de la barre
        bg_rect = pygame.Rect(x, y, width, height)
        pygame.draw.rect(surface, (20, 20, 20), bg_rect)
        pygame.draw.rect(surface, (150, 150, 150), bg_rect, 2)
        
        if ratio > 0:
            # Plus on est en manque, plus c'est rouge
            r = int(255 * ratio)
            g = int(255 * (1 - ratio))
            color = (r, g, 50)
            
            inner_w = int((width - 4) * ratio)
            if inner_w > 0:
                pygame.draw.rect(surface, color, (x + 2, y + 2, inner_w, height - 4))
        
        # Texte d'état à droite de la barre pour gagner de la place
        status_txt = "MANQUE!" if ratio > 0.7 else "OK"
        txt_color = (255, 50, 50) if ratio > 0.7 else (150, 255, 150)
        label = self.font_sub.render(status_txt, True, txt_color)
        surface.blit(label, (x + width + 10, y - 2))
    
    def draw_powerup_bar(self, surface, x, y, current, maximum, color, label_text):
        ratio = max(0, min(1, current / maximum))
        if ratio <= 0: return
        
        bg_rect = pygame.Rect(x, y, 150, 12)
        pygame.draw.rect(surface, (20, 20, 20), bg_rect)
        pygame.draw.rect(surface, color, (x + 2, y + 2, int(146 * ratio), 8))
        
        txt = self.font_sub.render(label_text, True, color)
        surface.blit(txt, (x, y - 22))
    
    def draw_item_count(self, surface, x, y, icon, count):
        # Affichage du compteur de weed en haut à droite
        if icon:
            scaled_icon = pygame.transform.scale(icon, (40, 40))
            surface.blit(scaled_icon, (x, y))
            
            txt = self.font_main.render(f"x {count}", True, (100, 255, 100))
            surface.blit(txt, (x + 50, y + 2))
    
    def draw_pause_menu(self, surface, show_missions=False):
        # Overlay sombre avec flou simulé
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        surface.blit(overlay, (0, 0))
        
        cx, cy = surface.get_width() // 2, surface.get_height() // 2
        
        if not show_missions:
            # Titre
            title = self.font_main.render("- PAUSE -", True, (255, 255, 255))
            surface.blit(title, title.get_rect(center=(cx, cy - 180)))
            
            # Boutons (On définit leurs rects pour la détection de clic dans GameState)
            self._draw_pause_btn(surface, (cx, cy - 60), "REPRENDRE", (100, 255, 100))
            self._draw_pause_btn(surface, (cx, cy + 10), "MISSIONS", (100, 200, 255))
            self._draw_pause_btn(surface, (cx, cy + 80), "RECOMMENCER", (255, 200, 50))
            self._draw_pause_btn(surface, (cx, cy + 150), "QUITTER LE JEU", (255, 80, 80))
            
            hint = self.font_small.render("[P] ou [ESC] pour fermer", True, (150, 150, 150))
            surface.blit(hint, hint.get_rect(center=(cx, surface.get_height() - 30)))
        else:
            # Menu missions pendant la pause
            from progression import progression
            from settings import PANEL_W, PANEL_H
            
            panel_w, panel_h = 600, 500
            px, py = cx - panel_w // 2, cy - panel_h // 2
            
            panel_rect = pygame.Rect(px, py, panel_w, panel_h)
            pygame.draw.rect(surface, (20, 20, 30), panel_rect, border_radius=20)
            pygame.draw.rect(surface, (0, 180, 255), panel_rect, width=2, border_radius=20)
            
            title = self.font_sub.render("OBJECTIFS EN COURS", True, (0, 180, 255))
            surface.blit(title, title.get_rect(centerx=cx, top=py + 20))
            
            for i, q in enumerate(progression.state["quests"]):
                qy = py + 80 + i * 120
                q_rect = pygame.Rect(px + 30, qy, panel_w - 60, 100)
                
                bar_w = 400
                bar_h = 6
                bar_rect = pygame.Rect(q_rect.left + 20, qy + 60, bar_w, bar_h)
                pygame.draw.rect(surface, (50, 50, 60), bar_rect, border_radius=3)
                
                progress = q["current"] / q["goal"]
                prog_color = (0, 255, 150) if q["completed"] else (255, 255, 255)
                pygame.draw.rect(surface, prog_color, (bar_rect.x, bar_rect.y, int(bar_w * progress), bar_h), border_radius=3)
                
                name = self.font_sub.render(q["title"], True, prog_color)
                surface.blit(name, (q_rect.left + 20, qy + 10))
                desc = self.font_small.render(q["desc"], True, (200, 200, 200))
                surface.blit(desc, (q_rect.left + 20, qy + 35))
                
                stat_txt = f"{q['current']} / {q['goal']}"
                stat_surf = self.font_small.render(stat_txt, True, (150, 150, 150))
                surface.blit(stat_surf, (bar_rect.right + 15, bar_rect.y - 6))

            hint = self.font_small.render("Appuie sur [ESC] pour revenir au menu pause", True, (150, 150, 150))
            surface.blit(hint, hint.get_rect(centerx=cx, bottom=py + panel_h - 20))

    def _draw_pause_btn(self, surface, center, text, color):
        rect = pygame.Rect(0, 0, 300, 50)
        rect.center = center
        souris = pygame.mouse.get_pos()
        hover = rect.collidepoint(souris)
        
        alpha = (0, 0, 0, 100)
        if hover: alpha = (color[0], color[1], color[2], 50)
        
        bg = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        bg.fill(alpha)
        surface.blit(bg, rect)
        
        border_color = color if hover else (150, 150, 150)
        pygame.draw.rect(surface, border_color, rect, width=2, border_radius=5)
        
        txt_color = (255, 255, 255) if hover else (200, 200, 200)
        txt = self.font_sub.render(text, True, txt_color)
        surface.blit(txt, txt.get_rect(center=rect.center))
    
    def draw_game_over(self, surface, score, status):
        # Écran de fin un peu plus "brut"
        s = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        s.fill((20, 0, 0, 220))
        surface.blit(s, (0, 0))
        
        title_str = "T'ES MORT..."
        if status == "ARRESTED": title_str = "CHOUPÉ PAR LES FLICS !"
        elif status == "OVERDOSE": title_str = "OVERDOSE..."
        
        title = self.font_main.render(title_str, True, (255, 0, 0))
        score_info = self.font_main.render(f"SCORE : {score}", True, (255, 255, 255))
        retry = self.font_sub.render("Appuie sur R pour retenter ta chance", True, (200, 200, 200))
        
        cx, cy = surface.get_width()//2, surface.get_height()//2
        surface.blit(title, title.get_rect(center=(cx, cy - 60)))
        surface.blit(score_info, score_info.get_rect(center=(cx, cy)))
        surface.blit(retry, retry.get_rect(center=(cx, cy + 60)))


class ParallaxLayer:
    def __init__(self, image, scroll_factor, height_offset=0):
        self.image = image
        self.factor = scroll_factor
        self.width = self.image.get_width()
        self.height_offset = height_offset
        
    def draw(self, surface, camera_x, screen_width):
        rel_x = (camera_x * self.factor) % self.width
        surface.blit(self.image, (-rel_x, self.height_offset))
        if rel_x < screen_width:
            surface.blit(self.image, (-rel_x + self.width, self.height_offset))

class ParallaxBackground:
    def __init__(self, layers):
        self.layers = layers
    
    def draw(self, surface, camera_x):
        sw = surface.get_width()
        for layer in self.layers:
            layer.draw(surface, camera_x, sw)