import pygame
import random
from state_machine import State
from settings import *
from sprites import Player, Obstacle, Weed, Bird, Rat, DeadRat, Prop, TrashObstacle, Police, PowerUp, Drone, Wolf, Bear
from effects import ParticleEmitter, HUD, ParallaxBackground, ParallaxLayer
from asset_loader import asset_loader, play_sfx
from assets_registry import ASSETS
from states.game_over_state import GameOverState

class GameState(State):
    def check_mask_collision(self, s1, s2):
        # On check les collisions au pixel près (masques)
        if not hasattr(s1, 'mask') or not hasattr(s2, 'mask'):
            return pygame.sprite.collide_rect(s1, s2)
            
        def get_vis(s):
            # Rect pour le dessin avec offsets
            b = s.image.get_rect(midbottom=s.rect.midbottom)
            b.x += getattr(s, 'visual_offset_x', 0)
            b.y += getattr(s, 'visual_offset_y', 0)
            return b

        v1, v2 = get_vis(s1), get_vis(s2)
        if not v1.colliderect(v2): return False
        return s1.mask.overlap(s2.mask, (v2.x - v1.x, v2.y - v1.y)) is not None

    def __init__(self, brain):
        super().__init__(brain)
        # Init du HUD et des particules
        self.hud, self.emitter = HUD(), ParticleEmitter()
        self.score = 0
        self.init_audio(); self.init_graphics(); self.init_sprites()
        
        self.paused = self.show_missions = self.game_over = False
        self.render_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT)) 
        self.camera_x, self.mission_alpha = 0, 0
        self.death_triggered = False
        self.death_timer, self.slow_motion_factor = 0.0, 1.0
        self.drone_cooldown, self.current_biome, self.show_hitboxes = 0, "street", False
        self.arrest_status = None
        
        # Le dico pour les quêtes
        self.run_stats = {
            "dist": 0, "weed": 0, "rats": 0, "birds": 0,
            "drones": 0, "shield": 0, "magnet": 0, "combo": 0
        }

    def init_audio(self):
        # On lance la zik si on peut
        try:
            if not pygame.mixer.get_init(): return
            p = str(ASSET_DIR / ASSETS["audio"]["music_bg"])
            pygame.mixer.music.load(p)
            pygame.mixer.music.set_volume(MUSIC_VOLUME)
            pygame.mixer.music.play(-1)
        except: pass

    def init_graphics(self):
        # Setup des fonds qui bougent (parallax)
        specs = [
            {"k": "bg_layer1", "s": 0.05, "y": 0}, {"k": "bg_layer2", "s": 0.2, "y": -80}, 
            {"k": "bg_layer3", "s": 0.4, "y": -80}, {"k": "bg_layer4", "s": 0.6, "y": -80},
            {"k": "bg_layer5", "s": 0.8, "y": -80}
        ]
        self.bg_layers_store = {}
        for biome in ["ville", "foret"]:
            layers = []
            data = ASSETS["environment"]["backgrounds"].get(biome, {})
            for sp in specs:
                idx = sp["k"][-1]
                if idx in data:
                    img = asset_loader.fetch_img(data[idx])
                    if img:
                        w = int(img.get_width() * (SCREEN_HEIGHT / img.get_height()))
                        img = pygame.transform.scale(img, (w, SCREEN_HEIGHT))
                        layers.append(ParallaxLayer(img, sp["s"], sp["y"]))
            self.bg_layers_store[biome] = ParallaxBackground(layers)
            
        self.parallax_bg = self.bg_layers_store.get("ville", ParallaxBackground([]))
        self.next_parallax_bg, self.fade_alpha, self.fade_speed = None, 0, 180

    def init_sprites(self):
        # On prépare les groupes de sprites
        self.all_sprites = pygame.sprite.LayeredUpdates()
        self.platforms, self.weed_items, self.powerups = pygame.sprite.Group(), pygame.sprite.Group(), pygame.sprite.Group()
        self.particles, self.mobs, self.props, self.trash_obstacles = pygame.sprite.Group(), pygame.sprite.Group(), pygame.sprite.Group(), pygame.sprite.Group()
        self.current_biome, self.last_chunk_type = "street", 'flat'
        # On met un sol de départ
        g = Obstacle(-SCREEN_WIDTH, FLOOR_Y, SCREEN_WIDTH * 2, 200, biome=self.current_biome)
        self.platforms.add(g); self.all_sprites.add(g)
        self.last_gen_x = SCREEN_WIDTH
        self.player = Player(self.all_sprites)
        self.police = Police(self.all_sprites, self.player)
        self.player.invincibility_timer = 120

    def get_biome_at(self, x):
        # On change de biome tous les 400 points
        biomes = ["street", "park", "foret", "rooftop"]
        return biomes[(int(x / 100) // 400) % 4]

    def update_visuals(self):
        v_biome = self.get_biome_at(self.camera_x + SCREEN_WIDTH // 2)
        k = "ville"
        if v_biome in ["park", "foret"]: k = "foret"
        
        if k in self.bg_layers_store:
            t = self.bg_layers_store[k]
            if self.parallax_bg != t and self.next_parallax_bg != t:
                 self.next_parallax_bg, self.fade_alpha = t, 0
                 
    def update_fade(self, dt):
        if self.next_parallax_bg:
            self.fade_alpha += self.fade_speed * dt
            if self.fade_alpha >= 255:
                self.parallax_bg, self.next_parallax_bg, self.fade_alpha = self.next_parallax_bg, None, 0

    def spawn_world_chunk(self):
        self.current_biome = self.get_biome_at(self.last_gen_x)
        while self.last_gen_x < self.camera_x + SCREEN_WIDTH * 1.5:
            # Choix au pif du style de chunk
            p_type = random.choices(['flat', 'gap', 'platform'], [45, 20, 35])[0]
            if self.score < 5 and p_type == 'gap': p_type = 'flat'
            if self.last_chunk_type == 'gap' and p_type == 'gap': p_type = 'platform'
            self.last_chunk_type = p_type

            if p_type == 'gap':
                w_gap = random.randint(GAP_SIZE_MIN, GAP_SIZE_MAX)
                self.last_gen_x += w_gap
                if random.random() < 0.25:
                    Weed(self.last_gen_x - w_gap/2, FLOOR_Y - 100).add(self.all_sprites, self.weed_items)
            
            elif p_type == 'platform':
                w = random.randint(400, 800)
                g = Obstacle(self.last_gen_x, FLOOR_Y, w, 200, biome=self.current_biome)
                self.platforms.add(g); self.all_sprites.add(g)
                # Petite plateforme en l'air
                pw = random.randint(150, 300)
                px = self.last_gen_x + random.randint(50, w - pw - 50)
                py = FLOOR_Y - PLATFORM_HEIGHT
                pl = Obstacle(px, py, pw, 40, biome=self.current_biome)
                self.platforms.add(pl); self.all_sprites.add(pl)
                if random.random() < 0.4: Weed(px + pw/2, py).add(self.all_sprites, self.weed_items)
                if random.random() < 0.2: PowerUp(px + pw/2, py, random.choice(["magnet", "shield"])).add(self.all_sprites, self.powerups)
                self.spawn_decor(self.last_gen_x, w); self.last_gen_x += w
                
            else:
                w = random.randint(400, 1000)
                g = Obstacle(self.last_gen_x, FLOOR_Y, w, 200, biome=self.current_biome)
                self.platforms.add(g); self.all_sprites.add(g)
                self.spawn_decor(self.last_gen_x, w)
                if random.random() < 0.7: self.spawn_mobs_on_ground(self.last_gen_x, w)
                
                if self.camera_x > 5000 and self.player.hp > 1 and self.drone_cooldown <= 0:
                    self.drone_cooldown = 60 
                    if self.current_biome != "foret" and random.random() < 0.6:
                        Drone(self.all_sprites, self.camera_x + SCREEN_WIDTH + 100, 200, self.player).add(self.all_sprites, self.mobs)
                self.last_gen_x += w

    def spawn_decor(self, xs, width):
        # On pose les arbres/poubelles et la weed au sol
        if random.random() < 0.3: self.spawn_props(xs, width)
        for _ in range(random.randint(0, 1)):
             Weed(xs + random.randint(20, width - 20), FLOOR_Y).add(self.all_sprites, self.weed_items)
        if random.random() < 0.15: 
            PowerUp(xs + random.randint(50, width - 50), FLOOR_Y, "heart").add(self.all_sprites, self.powerups)

    def spawn_props(self, x, width):
        choice, px = random.random(), x + random.randint(50, width - 50)
        if self.current_biome in ["foret", "park"]:
            f_keys = list(ASSETS["forest_props"].keys())
            p_name = random.choice(f_keys); p_img = asset_loader.fetch_img(ASSETS["forest_props"][p_name])
            if p_name in ["log", "rock"]:
                 o = TrashObstacle(px, FLOOR_Y, p_img)
                 self.trash_obstacles.add(o); self.all_sprites.add(o)
            else: Prop(px, FLOOR_Y, p_img).add(self.all_sprites, self.props)
        elif choice < 0.5:
            t_props = ["sac_poubelle.png", "sacs_poubelle.png", "poubelle.png", "benne_rouge.png"]
            p_img = asset_loader.fetch_img(f"graphics/environment/props/items/{random.choice(t_props)}")
            t = TrashObstacle(px, FLOOR_Y, p_img)
            self.trash_obstacles.add(t); self.all_sprites.add(t)
        elif choice < 0.8:
            l_props = ["lampadaire.png", "feu_poteau.png"]
            p_img = asset_loader.fetch_img(f"graphics/environment/props/items/{random.choice(l_props)}")
            Prop(px, FLOOR_Y, p_img).add(self.all_sprites, self.props)

    def spawn_mobs_on_ground(self, xs, width):
         rx = xs + random.randint(100, width - 100)
         if self.current_biome in ["foret", "park"]:
             Wolf([self.all_sprites, self.mobs], rx, FLOOR_Y, -1) if random.random() < 0.5 else Bear([self.all_sprites, self.mobs], rx, FLOOR_Y, -1)
         else: Rat([self.all_sprites, self.mobs], rx, FLOOR_Y, -1)

    def update(self, dt: float, events: list):
        for e in events:
            if e.type == pygame.KEYDOWN:
                if (e.key == pygame.K_p or e.key == pygame.K_ESCAPE) and not self.death_triggered:
                    self.paused = not self.paused; self.show_missions = False
                    play_sfx("click")
                if e.key == pygame.K_r and (self.game_over or self.death_triggered):
                    self.brain.change(GameState(self.brain)); return
                if e.key == pygame.K_g:
                    from progression import progression
                    progression.state["credits"] += 1000; progression.commit(); play_sfx("click")
                if e.key == pygame.K_k: self.player.god_mode = not self.player.god_mode
                if e.key == pygame.K_h: self.show_hitboxes = not self.show_hitboxes
            if self.paused and e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                cx, cy, s = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2, pygame.mouse.get_pos()
                if not self.show_missions:
                    if pygame.Rect(cx-150, cy-85, 300, 50).collidepoint(s): self.paused = False
                    elif pygame.Rect(cx-150, cy-15, 300, 50).collidepoint(s): self.show_missions = True
                    elif pygame.Rect(cx-150, cy+55, 300, 50).collidepoint(s): self.brain.change(GameState(self.brain)); return
                    elif pygame.Rect(cx-150, cy+125, 300, 50).collidepoint(s):
                        from states.menu_state import MenuState
                        self.brain.change(MenuState(self.brain)); return
                    play_sfx("click")
        if self.paused: return
        actual_dt = dt * self.slow_motion_factor
        if self.drone_cooldown > 0: self.drone_cooldown -= actual_dt
        self.camera_x = max(0, self.player.rect.centerx - SCREEN_WIDTH // 2)
        self.score = max(self.score, int(self.camera_x / 100))
        # Plus on va loin, plus c'est dur
        spd = 1.0 + min(0.6, self.camera_x / 50000.0) 
        self.player.global_speed_mult = spd
        self.update_visuals(); self.update_fade(actual_dt); self.spawn_world_chunk()
        if self.death_triggered:
            s = self.run_stats
            s["dist"], s["weed"], s["combo"] = self.score, self.player.weed_count, self.player.combo_counter
            s["shield"], s["magnet"] = self.player.shield_activations, self.player.magnet_activations
            if self.brain: self.brain.change(GameOverState(self.brain, self.score, self.arrest_status, s))
            return
        self.player.check_collisions(self.platforms, self.trash_obstacles, actual_dt)
        self.player.update_powerups(actual_dt, self.weed_items); self.particles.update()
        for sprite in self.all_sprites:
            if sprite.rect.right < self.camera_x - 400 or sprite.rect.top > SCREEN_HEIGHT + 400:
                # Si c'est un mob qui dégage, c'est qu'on l'a évité proprement
                if sprite in self.mobs:
                    self.player.just_dodged_enemy = True
                sprite.kill()
        # Pop des oiseaux
        ch = 0.04 if self.get_biome_at(self.camera_x + SCREEN_WIDTH) == "foret" else 0.005
        if self.camera_x > 5000 and random.random() < ch: self.spawn_aerial_enemy()
        self.player.update(actual_dt, self.platforms, self.trash_obstacles, self.weed_items, self.powerups, self.mobs)
        self.all_sprites.update(actual_dt, self.platforms, self.trash_obstacles, self.arrest_status)
        self.weed_items.update(actual_dt); self.powerups.update(actual_dt); self.check_interactions()

    def spawn_aerial_enemy(self):
        Bird([self.all_sprites, self.mobs], self.camera_x + SCREEN_WIDTH + 100, random.randint(50, 400), -1)

    def check_interactions(self):
        # Stomp - On est super clément (juste le rectangle)
        for m in list(self.mobs):
            # On vérifie si on est en train de tomber ou si on vient d'atterrir
            ca_tombe = self.player.velocity_y > 0 or (self.player.on_ground and self.player.rect.bottom <= m.rect.centery + 35)
            if ca_tombe and self.player.rect.colliderect(m.rect):
                # Seuil de tolérance pour le stomp
                seuil = m.rect.centery + 10
                if isinstance(m, Bird): seuil = m.rect.centery + 40
                if self.player.rect.bottom < seuil: 
                    m.kill(); self.player.bounce(); self.player.just_hit_enemy = True
                    self.emitter.enemy_killed(m.rect.centerx, m.rect.centery, self.particles)
                    if isinstance(m, Rat):
                        self.run_stats["rats"] += 1
                        DeadRat(m.rect.centerx, m.rect.bottom, self.all_sprites, True, m.facing_right)
                    elif isinstance(m, Bird): self.run_stats["birds"] += 1
                    continue
            hit = self.player.rect.inflate(-10, -10).colliderect(m.rect) if isinstance(m, (Bird, Drone)) else self.check_mask_collision(self.player, m)
            if hit:
                if self.player.has_shield:
                    if isinstance(m, Rat): self.run_stats["rats"] += 1
                    elif isinstance(m, Bird): self.run_stats["birds"] += 1
                    elif isinstance(m, Drone): self.run_stats["drones"] += 1
                    m.kill(); self.score += 10; self.player.just_hit_enemy = True
                    self.emitter.enemy_killed(m.rect.centerx, m.rect.centery, self.particles); continue
                if isinstance(m, Drone):
                    if not self.player.invincible: self.player.take_damage(1)
                    self.emitter.drone_hit(self.player.rect.centerx, self.player.rect.centery, self.particles); play_sfx("hurt", 0.4)
                    if hasattr(m, 'retreating'): m.retreating = True
                else: 
                    if self.player.take_damage(1): self.trigger_death("WASTED")
                    self.player.just_took_damage = True
        c_rect = self.player.rect.inflate(60, 60)
        for w in self.weed_items:
            if c_rect.colliderect(w.rect):
                w.kill(); self.emitter.weed_collected(w.rect.centerx, w.rect.centery, self.particles)
                self.player.weed_count += 1; self.player.withdrawal = max(0, self.player.withdrawal - WEED_WITHDRAWAL_REDUCE)
                self.player.just_collected_weed = True
                self.player.just_healed = True; play_sfx("click", 0.2)
        for p in self.powerups:
            if c_rect.colliderect(p.rect):
                p.kill(); self.player.activate_powerup(p.type)
                if p.type == "shield": self.player.just_used_shield = True
                elif p.type == "magnet": self.player.just_used_magnet = True
                
                if p.type == "heart":
                    if self.player.hp < self.player.max_hp:
                        self.player.hp += 1
                        if self.player.hp == self.player.max_hp: self.player.just_reached_max_hp = True
                    
                self.emitter.heal_effect(p.rect.centerx, p.rect.centery, self.particles)
        if pygame.sprite.collide_mask(self.player, self.police) and not self.death_triggered and not self.player.god_mode:
             if self.player.has_shield:
                  self.police.rect.x -= 400; self.police.speed = 0 
                  self.emitter.create_explosion(self.player.rect.centerx, self.player.rect.centery, (100, 200, 255), 15, self.particles)
             elif not self.player.invincible: self.trigger_death("ARRESTED")
        for m in self.mobs:
            if isinstance(m, Drone):
                h_hit = [p for p in pygame.sprite.spritecollide(m, self.powerups, True, pygame.sprite.collide_mask) if p.type == "heart"]
                if h_hit:
                    m.kill(); self.emitter.create_explosion(m.rect.centerx, m.rect.centery, (255, 105, 180), 10, self.particles)
                    self.emitter.create_explosion(m.rect.centerx, m.rect.centery, (50, 50, 50), 10, self.particles)
        if self.player.just_healed: self.emitter.heal_effect(self.player.rect.centerx, self.player.rect.centery, self.particles); self.player.just_healed = False
        if self.player.just_damaged: self.emitter.player_hurt(self.player.rect.centerx, self.player.rect.centery, self.particles); self.player.just_damaged = False
        st = self.player.check_death()
        if st: self.trigger_death(st)

    def trigger_death(self, res):
        if not self.death_triggered:
            if self.player.has_shield:
                 self.player.has_shield, self.player.invincible, self.player.invincibility_timer = False, True, 60; return
            self.death_triggered, self.arrest_status = True, res
            self.player.status, self.player.frame_index, self.player.direction.x = 'dead', 0, 0
            self.player.just_died = True
            self.police.status = 'idle'
            play_sfx("arrest" if res == "ARRESTED" else "game_over", 0.8)

    def draw(self, surface):
        self.render_surface.fill((25, 25, 30))
        self.render_surface.fill((25, 25, 30))
        self.parallax_bg.draw(self.render_surface, self.camera_x)
        if self.next_parallax_bg:
            # On dessine le prochain fond sur une surface temporaire avec de l'alpha pour le fondu
            temp_bg = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT)); temp_bg.set_colorkey((0,0,0))
            self.next_parallax_bg.draw(temp_bg, self.camera_x)
            temp_bg.set_alpha(int(self.fade_alpha)); self.render_surface.blit(temp_bg, (0,0))
        for s in self.all_sprites:
            h_rect = s.rect.move(-self.camera_x, 0)
            v_rect = s.image.get_rect(midbottom=h_rect.midbottom)
            v_rect.x += getattr(s, 'visual_offset_x', 0); v_rect.y += getattr(s, 'visual_offset_y', 0)
            self.render_surface.blit(s.image, v_rect)
        for p in self.particles: self.render_surface.blit(p.image, (p.rect.x - self.camera_x, p.rect.y))
        if self.show_hitboxes:
            for s in self.all_sprites:
                if hasattr(s, 'mask'):
                    pts = s.mask.outline()
                    if pts:
                         hr = s.rect.move(-self.camera_x, 0); vr = s.image.get_rect(midbottom=hr.midbottom)
                         vr.x += getattr(s, 'visual_offset_x', 0); vr.y += getattr(s, 'visual_offset_y', 0)
                         pts_adj = [(p[0] + vr.x, p[1] + vr.y) for p in pts]
                         if len(pts_adj) > 1: pygame.draw.lines(self.render_surface, (50, 255, 50), True, pts_adj, 1)
        surface.blit(self.apply_shake(self.render_surface), (0, 0))
        # On blit tout sur la surface de rendu
        self.hud.draw_hearts(surface, HUD_X, HUD_Y, self.player.hp, self.player.max_hp)
        if not self.game_over:
            off = self.player.max_hp * (HEART_SIZE + 5) + 20
            self.hud.draw_withdrawal_bar(surface, HUD_X + off, HUD_Y + 10, self.player.withdrawal, self.player.max_withdrawal)
            from progression import progression
            k, _ = progression.get_active_collectible(); w_im = asset_loader.fetch_img(ASSETS["items"][k])
            self.hud.draw_item_count(surface, SCREEN_WIDTH - 150, HUD_Y, w_im, self.player.weed_count)
            f = pygame.font.Font(None, 40); sc_t = f.render(f"DIST: {self.score}m", True, (255, 255, 255))
            surface.blit(sc_t, (SCREEN_WIDTH // 2 - sc_t.get_width() // 2, 25))
            self.hud.draw_powerup_bar(surface, HUD_X, HUD_Y + 60, self.player.shield_timer, 1200, (100, 200, 255), "SHIELD")
            self.hud.draw_powerup_bar(surface, HUD_X + 170, HUD_Y + 60, self.player.magnet_timer, 1200, (255, 100, 100), "MAGNET")
            if self.player.combo_counter > 1:
                cf = pygame.font.Font(None, 60); ct = cf.render(f"{self.player.combo_counter}x COMBO!", True, C_GOLD)
                surface.blit(ct, (SCREEN_WIDTH // 2 - ct.get_width() // 2, 80))
        if self.paused: self.hud.draw_pause_menu(surface, self.show_missions)

    def apply_shake(self, surf):
        if self.game_over: return surf
        sx, sy = 0, 0
        if self.player.withdrawal > 40:
            i = int((self.player.withdrawal - 40) / 10) 
            sx, sy = random.randint(-i, i), random.randint(-i, i)
        if self.player.hurt_timer > 0: sx, sy = sx + random.randint(-5, 5), sy + random.randint(-5, 5)
        if sx == 0 and sy == 0: return surf
        ns = pygame.Surface(surf.get_size()); ns.blit(surf, (sx, sy))
        return ns

    def scan_surroundings(self):
        # On check où s'arrête le sol et où est la suite
        p, h_ecran = self.player, float(SCREEN_HEIGHT)
        scan = {
            'next_gap_dist': 1500, 'next_enemy_dist': 1500, 'next_enemy_type': 0, 'next_platform_y_delta': 0,
            'next_platform_x_dist': 1500, 'next_platform_width': 0, 'gap_size': 0, 'enemy_y_delta': 0
        }
        end_sol, next_p, d_min = -1, None, 9999
        pr, pb = p.rect.right, p.rect.bottom
        for plat in self.platforms:
            r = plat.rect
            if r.right < p.rect.left - 100: continue
            meme_h = abs(r.top - pb) < 50 or (p.on_ground and abs(r.top - p.rect.bottom) < 50)
            if r.left <= end_sol + 20 or (end_sol == -1 and r.left <= pr + 50):
                if meme_h: end_sol = max(end_sol, r.right)
            if r.left > pr:
                dist = r.left - pr
                if dist < d_min: d_min, next_p = dist, plat
        if end_sol != -1: scan['next_gap_dist'] = max(0, end_sol - pr)
        else: scan['next_gap_dist'] = 0
        if next_p:
            scan['next_platform_y_delta'] = (next_p.rect.top - pb) / h_ecran
            scan['next_platform_x_dist'] = max(0, next_p.rect.left - pr)
            scan['next_platform_width'] = next_p.rect.width
            if end_sol != -1: scan['gap_size'] = max(0, next_p.rect.left - end_sol)
        else: scan['next_platform_y_delta'], scan['next_platform_x_dist'], scan['next_platform_width'], scan['gap_size'] = 0, 1500, 0, 0
        m_dist, m_ref = 1500, None
        targets = list(self.mobs)
        if self.police and self.police.rect.centerx > p.rect.centerx: targets.append(self.police)
        for m in targets:
            dx = m.rect.left - pr
            if 0 < dx < m_dist: m_dist, m_ref = dx, m
        scan['next_enemy_dist'] = m_dist
        if m_ref:
            scan['next_enemy_type'] = 1.0 if isinstance(m_ref, (Bird, Drone)) else 0.5
            scan['enemy_y_delta'] = (m_ref.rect.centery - p.rect.centery) / h_ecran
        return scan

    def hard_reset(self):
        # On vide tout sans recréer les listes (gain de temps)
        for s in [self.all_sprites, self.platforms, self.weed_items, self.powerups, self.particles, self.mobs, self.props, self.trash_obstacles]:
            s.empty()
        self.score, self.camera_x, self.last_gen_x, self.drone_cooldown = 0, 0, SCREEN_WIDTH, 0
        self.death_triggered = self.game_over = self.paused = False
        sg = Obstacle(-SCREEN_WIDTH, FLOOR_Y, SCREEN_WIDTH * 2, 200, biome=self.current_biome)
        self.platforms.add(sg); self.all_sprites.add(sg)
        self.player = Player(self.all_sprites)
        self.player.ai_mode, self.player.invincibility_timer = True, 120
        self.police = Police(self.all_sprites, self.player)
