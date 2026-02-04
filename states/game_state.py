import pygame
import random


from state_machine import State
from settings import *
from sprites import Player, Obstacle, Weed, Bird, Rat, DeadRat, Prop, TrashObstacle, Police, PowerUp, Drone, Wolf, Bear
# Biomes et trucs de jeu
from effects import ParticleEmitter, HUD, ParallaxBackground, ParallaxLayer
from asset_loader import asset_loader, play_sfx
from assets_registry import ASSETS
from states.game_over_state import GameOverState


class GameState(State):
    def check_mask_collision(self, s1, s2):
        # Collision propre avec les masques
        if not hasattr(s1, 'mask') or not hasattr(s2, 'mask'):
            return pygame.sprite.collide_rect(s1, s2)
            
        def visual_rect(s):
            # Rect de dessin avec les offsets
            bx = s.image.get_rect(midbottom=s.rect.midbottom)
            bx.x += getattr(s, 'visual_offset_x', 0)
            bx.y += getattr(s, 'visual_offset_y', 0)
            return bx

        v1, v2 = visual_rect(s1), visual_rect(s2)
        if not v1.colliderect(v2): return False
        
        return s1.mask.overlap(s2.mask, (v2.x - v1.x, v2.y - v1.y)) is not None

    def __init__(self, brain):
        super().__init__(brain)
        
        self.hud = HUD()
        self.emitter = ParticleEmitter()
        
        self.score = 0
        self.init_audio()
        self.init_graphics() 
        self.init_sprites()
        
        self.paused = False
        self.show_missions = False
        self.game_over = False
        self.arrest_status = None
        
        self.render_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT)) 
        self.camera_x = 0
        self.mission_alpha = 0
 
        
        self.death_triggered = False
        self.death_timer = 0.0      
        self.slow_motion_factor = 1.0
        
        self.drone_cooldown = 0 
        self.current_biome = "street"
        self.show_hitboxes = False
        
        # Stats pour les quêtes
        self.run_stats = {
            "dist": 0, "weed": 0, "rats": 0, "birds": 0,
            "drones": 0, "shield": 0, "magnet": 0, "combo": 0
        }



    def init_audio(self):
        try:
            if not pygame.mixer.get_init(): return
            music_path = ASSETS["audio"]["music_bg"]
            full_path = str(ASSET_DIR / music_path)
            pygame.mixer.music.load(full_path)
            pygame.mixer.music.set_volume(MUSIC_VOLUME)
            pygame.mixer.music.play(-1)
        except:
             pass

    def init_graphics(self):
        layers = []
        layer_specs = [
            {"key": "bg_layer1", "scroll": 0.05, "y_off": 0}, 
            {"key": "bg_layer2", "scroll": 0.2,  "y_off": -80}, 
            {"key": "bg_layer3", "scroll": 0.4,  "y_off": -80},
            {"key": "bg_layer4", "scroll": 0.6,  "y_off": -80},
            {"key": "bg_layer5", "scroll": 0.8,  "y_off": -80}
        ]
        
        self.bg_layers_store = {}
        
        for biome_key in ["ville", "foret"]:
            layers = []
            bg_data = ASSETS["environment"]["backgrounds"].get(biome_key, {})
            
            for spec in layer_specs:
                idx = spec["key"][-1] # "1", "2"...
                if idx in bg_data:
                    path = bg_data[idx]
                    img = asset_loader.fetch_img(path, alpha=True)
                    if img:
                        h = SCREEN_HEIGHT
                        w = int(img.get_width() * (h / img.get_height()))
                        img = pygame.transform.scale(img, (w, h))
                        layers.append(ParallaxLayer(img, scroll_factor=spec["scroll"], height_offset=spec["y_off"]))
            
            self.bg_layers_store[biome_key] = ParallaxBackground(layers)

        # Default
        self.parallax_bg = self.bg_layers_store.get("ville", ParallaxBackground([]))
        self.next_parallax_bg = None
        self.fade_alpha = 0
        self.fade_speed = 180 # Boosted speed for smoother feel (~1.4s)

    def init_sprites(self):
        self.all_sprites = pygame.sprite.LayeredUpdates()
        self.platforms = pygame.sprite.Group()
        self.weed_items = pygame.sprite.Group()
        self.powerups = pygame.sprite.Group()
        self.particles = pygame.sprite.Group()
        self.mobs = pygame.sprite.Group()
        self.props = pygame.sprite.Group()
        self.trash_obstacles = pygame.sprite.Group()

        self.current_biome = "street"
        self.last_chunk_type = 'flat'

        start_ground = Obstacle(-SCREEN_WIDTH, FLOOR_Y, SCREEN_WIDTH * 2, 200, biome=self.current_biome)
        self.platforms.add(start_ground)
        self.all_sprites.add(start_ground)
        self.last_gen_x = SCREEN_WIDTH

        self.player = Player(self.all_sprites)
        self.police = Police(self.all_sprites, self.player)
        self.player.invincibility_timer = 120 # Petit buff au debut

    def get_biome_at(self, x_pos):
        score_equivalent = int(x_pos / 100)
        cycle_index = (score_equivalent // 400) % 4
        biomes = ["street", "park", "foret", "rooftop"]
        return biomes[cycle_index]

    def update_visuals(self):
        visual_biome = self.get_biome_at(self.camera_x + SCREEN_WIDTH // 2)
        
        # Switch background visuals
        bg_key = "ville"
        if visual_biome in ["park", "foret"]:
            bg_key = "foret"
        elif visual_biome == "rooftop":
             bg_key = "ville"
        
        if bg_key in self.bg_layers_store:
            target_bg = self.bg_layers_store[bg_key]
            if self.parallax_bg != target_bg and self.next_parallax_bg != target_bg:
                 self.next_parallax_bg = target_bg
                 self.fade_alpha = 0
                 
    def update_fade(self, dt):
        if self.next_parallax_bg:
            self.fade_alpha += self.fade_speed * dt
            if self.fade_alpha >= 255:
                self.parallax_bg = self.next_parallax_bg
                self.next_parallax_bg = None
                self.fade_alpha = 0

    def spawn_world_chunk(self):
        # Determine biome for GENERATION based on last_gen_x (future)
        self.current_biome = self.get_biome_at(self.last_gen_x)
        
        while self.last_gen_x < self.camera_x + SCREEN_WIDTH * 1.5:
             # ... rest of generation logic uses self.current_biome

            pattern_type = random.choices(
                ['flat', 'gap', 'platform'], 
                weights=[45, 20, 35], 
                k=1
            )[0]

            if self.score < 5 and pattern_type == 'gap': pattern_type = 'flat'
            
            if self.last_chunk_type == 'gap' and pattern_type == 'gap':
                 pattern_type = 'platform'

            self.last_chunk_type = pattern_type

            if pattern_type == 'gap':
                gap_w = random.randint(GAP_SIZE_MIN, GAP_SIZE_MAX)
                self.last_gen_x += gap_w
                if random.random() < 0.5:
                    Weed(self.last_gen_x - gap_w/2, FLOOR_Y - 100).add(self.all_sprites, self.weed_items)
            
            elif pattern_type == 'platform':
                w = random.randint(400, 800)
                ground = Obstacle(self.last_gen_x, FLOOR_Y, w, 200, biome=self.current_biome)
                self.platforms.add(ground)
                self.all_sprites.add(ground)
                
                plat_w = random.randint(150, 300)
                plat_x = self.last_gen_x + random.randint(50, w - plat_w - 50)
                plat_y = FLOOR_Y - PLATFORM_HEIGHT
                
                plat = Obstacle(plat_x, plat_y, plat_w, 40, biome=self.current_biome)
                self.platforms.add(plat)
                self.all_sprites.add(plat)
                
                Weed(plat_x + plat_w/2, plat_y).add(self.all_sprites, self.weed_items)
                
                if random.random() < 0.2:
                    p_type = random.choice(["magnet", "shield"])
                    PowerUp(plat_x + plat_w/2, plat_y, p_type).add(self.all_sprites, self.powerups)
                
                self.spawn_decor(self.last_gen_x, w)
                self.last_gen_x += w
                
            else:
                w = random.randint(400, 1000)
                ground = Obstacle(self.last_gen_x, FLOOR_Y, w, 200, biome=self.current_biome)
                self.platforms.add(ground)
                self.all_sprites.add(ground)
                self.spawn_decor(self.last_gen_x, w)
                if random.random() < 0.7:
                     self.spawn_mobs_on_ground(self.last_gen_x, w)
                
                if self.camera_x > 5000 and self.player.hp > 1 and self.drone_cooldown <= 0:
                    self.drone_cooldown = 60 
                    if self.current_biome != "foret" and random.random() < 0.60:
                        Drone(self.all_sprites, self.camera_x + SCREEN_WIDTH + 100, 200, self.player).add(self.all_sprites, self.mobs)

                self.last_gen_x += w

    def spawn_decor(self, x_start, width):
        if random.random() < 0.3:
            self.spawn_props(x_start, width)
        for _ in range(random.randint(0, 2)):
             wx = x_start + random.randint(20, width - 20)
             Weed(wx, FLOOR_Y).add(self.all_sprites, self.weed_items)

        if random.random() < 0.15: 
            hx = x_start + random.randint(50, width - 50)
            PowerUp(hx, FLOOR_Y, "heart").add(self.all_sprites, self.powerups)

    def spawn_props(self, x, width):
        choice = random.random()
        px = x + random.randint(50, width - 50)
        
        if self.current_biome in ["foret", "park"]:
            forest_keys = list(ASSETS["forest_props"].keys()) # bush, log, rock
            prop_name = random.choice(forest_keys)
            prop_path = ASSETS["forest_props"][prop_name]
            prop_img = asset_loader.fetch_img(prop_path, alpha=True)
            
            # Park : mix ville/nature ? Le user veut "foret". Donnons-lui de la foret dès le parc.
            
            if prop_name in ["log", "rock"]:
                 obs = TrashObstacle(px, FLOOR_Y, prop_img)
                 self.trash_obstacles.add(obs)
                 self.all_sprites.add(obs)
            else:
                 Prop(px, FLOOR_Y, prop_img).add(self.all_sprites, self.props)
                 
        elif choice < 0.5:
            trash_props = ["sac_poubelle.png", "sacs_poubelle.png", "poubelle.png", "benne_rouge.png"]
            prop_name = random.choice(trash_props)
            prop_path = f"graphics/environment/props/items/{prop_name}"
            prop_img = asset_loader.fetch_img(prop_path, alpha=True)
            
            trash = TrashObstacle(px, FLOOR_Y, prop_img)
            self.trash_obstacles.add(trash)
            self.all_sprites.add(trash)
            
        elif choice < 0.8:
            light_props = ["lampadaire.png", "feu_poteau.png"]
            prop_name = random.choice(light_props)
            prop_img = asset_loader.fetch_img(f"graphics/environment/props/items/{prop_name}", alpha=True)
            Prop(px, FLOOR_Y, prop_img).add(self.all_sprites, self.props)

    def spawn_mobs_on_ground(self, x_start, width):
         rx = x_start + random.randint(100, width - 100)
         
         if self.current_biome in ["foret", "park"]:
             if random.random() < 0.5:
                 Wolf([self.all_sprites, self.mobs], rx, FLOOR_Y, -1)
             else:
                 Bear([self.all_sprites, self.mobs], rx, FLOOR_Y, -1)
         else:
             Rat([self.all_sprites, self.mobs], rx, FLOOR_Y, -1)

    def update(self, dt: float, events: list):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if (event.key == pygame.K_p or event.key == pygame.K_ESCAPE) and not self.death_triggered:
                    if self.show_missions:
                        self.show_missions = False
                    else:
                        self.paused = not self.paused
                        if not self.paused: self.show_missions = False
                    play_sfx("click")
                
                if event.key == pygame.K_r and (self.game_over or self.death_triggered):
                    self.brain.change(self.__class__(self.brain))
                    return
                    
                if event.key == pygame.K_g:
                    from progression import progression
                    progression.state["credits"] += 1000
                    progression.commit()
                    play_sfx("click")
                    
                if event.key == pygame.K_k:
                    self.player.god_mode = not self.player.god_mode
                    
                if event.key == pygame.K_h:
                    self.show_hitboxes = not self.show_hitboxes

            if self.paused and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                cx, cy = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2
                souris = pygame.mouse.get_pos()
                
                if not self.show_missions:
                    # REPRENDRE
                    if pygame.Rect(cx - 150, cy - 85, 300, 50).collidepoint(souris):
                        self.paused = False
                        play_sfx("click")
                    # MISSIONS
                    elif pygame.Rect(cx - 150, cy - 15, 300, 50).collidepoint(souris):
                        self.show_missions = True
                        play_sfx("click")
                    # RECOMMENCER
                    elif pygame.Rect(cx - 150, cy + 55, 300, 50).collidepoint(souris):
                        self.brain.change(GameState(self.brain))
                        play_sfx("click")
                        return
                    # QUITTER
                    elif pygame.Rect(cx - 150, cy + 125, 300, 50).collidepoint(souris):
                        play_sfx("click")
                        from states.menu_state import MenuState
                        self.brain.change(MenuState(self.brain))
                        return
        if self.paused: 
            return

        actual_dt = dt * self.slow_motion_factor
        
        if self.drone_cooldown > 0:
            self.drone_cooldown -= actual_dt
        
        # Camera lockée au milieu
        t_cam = self.player.rect.centerx - SCREEN_WIDTH // 2
        self.camera_x = max(0, t_cam)

        self.score = max(self.score, int(self.camera_x / 100))

        # Augmentation de la difficulté auto
        diff_mult = 1.0 + min(0.6, self.camera_x / 50000.0) 
        self.player.global_speed_mult = diff_mult
        
        self.update_visuals()
        self.update_fade(actual_dt)
        self.spawn_world_chunk()

        if self.death_triggered:
            # On met à jour les stats finales avant de passer à l'écran de fin
            self.run_stats["dist"] = self.score
            self.run_stats["weed"] = self.player.weed_count
            self.run_stats["combo"] = self.player.combo_counter
            self.run_stats["shield"] = self.player.shield_activations
            self.run_stats["magnet"] = self.player.magnet_activations
            
            self.brain.change(GameOverState(self.brain, self.score, self.arrest_status, self.run_stats))
            return

        self.player.check_collisions(self.platforms, self.trash_obstacles, actual_dt)
        self.player.update_powerups(actual_dt, self.weed_items)
        self.particles.update()
        
        for sprite in self.all_sprites:
            if sprite.rect.right < self.camera_x - 400: 
                sprite.kill()
            elif sprite.rect.top > SCREEN_HEIGHT + 400: 
                sprite.kill()

        # Plus d'oiseaux dans la forêt
        chance = 0.005
        if self.get_biome_at(self.camera_x + SCREEN_WIDTH) == "foret":
            chance = 0.04
            
        if self.camera_x > 5000 and random.random() < chance: 
            self.spawn_aerial_enemy()
        
        self.player.update(actual_dt, self.platforms, self.trash_obstacles, self.weed_items, self.powerups, self.mobs)
        self.all_sprites.update(actual_dt, self.platforms, self.trash_obstacles, self.arrest_status)
        self.weed_items.update(actual_dt)
        self.powerups.update(actual_dt)
        self.check_interactions()


    def spawn_aerial_enemy(self):
        x = self.camera_x + SCREEN_WIDTH + 100
        y = random.randint(50, 400)
        Bird([self.all_sprites, self.mobs], x, y, -1)

    def check_interactions(self):
        # Stomp - Ultra clément (Rectangle seulement)
        for m in list(self.mobs):
            # On check si on tombe ou si on vient de se poser
            ca_tombe = self.player.velocity_y > 0 or (self.player.on_ground and self.player.rect.bottom <= m.rect.centery + 35)
            
            if ca_tombe and self.player.rect.colliderect(m.rect):
                # Tolerance seuil pour le stomp
                seuil = m.rect.centery + 10
                if isinstance(m, Bird): seuil = m.rect.centery + 40
                
                if self.player.rect.bottom < seuil: 
                    m.kill()
                    self.player.bounce()
                    self.emitter.enemy_killed(m.rect.centerx, m.rect.centery, self.particles)
                    if isinstance(m, Rat):
                        self.run_stats["rats"] += 1
                        DeadRat(m.rect.centerx, m.rect.bottom, self.all_sprites, play_anim=True, facing_right=m.facing_right)
                    elif isinstance(m, Bird):
                        self.run_stats["birds"] += 1
                    continue

            # Check collisions volants
            volant = isinstance(m, (Bird, Drone))
            hit = False
            
            hit = False
            if volant:
                if self.player.rect.inflate(-10, -10).colliderect(m.rect):
                    hit = True
            
            if not hit and self.check_mask_collision(self.player, m):
                hit = True

            if hit:
                if self.player.has_shield:
                    # Bouclier actif : on defonce le mob
                    if isinstance(m, Rat): self.run_stats["rats"] += 1
                    elif isinstance(m, Bird): self.run_stats["birds"] += 1
                    elif isinstance(m, Drone): self.run_stats["drones"] += 1
                    
                    m.kill()
                    self.score += 10
                    self.emitter.enemy_killed(m.rect.centerx, m.rect.centery, self.particles)
                    continue

                if isinstance(m, Drone):
                    # Le drone nous touche
                    if not self.player.invincible:
                        self.player.take_damage(1)
                        
                    self.emitter.drone_hit(self.player.rect.centerx, self.player.rect.centery, self.particles)
                    play_sfx("hurt", 0.4)
                    
                    if hasattr(m, 'retreating'):
                        m.retreating = True
                else:
                    if self.player.take_damage(1):
                        self.trigger_death("WASTED")
        
        collect_rect = self.player.rect.inflate(60, 60)
        
        for weed in self.weed_items:
            # Revert à colliderect pour le feeling, masque trop strict pour les items
            if collect_rect.colliderect(weed.rect):
                weed.kill()
                self.emitter.weed_collected(weed.rect.centerx, weed.rect.centery, self.particles)
                self.player.weed_count += 1
                self.player.withdrawal = max(0, self.player.withdrawal - WEED_WITHDRAWAL_REDUCE)
                self.player.just_healed = True
                play_sfx("click", 0.2)
            
        for p in self.powerups:
            if collect_rect.colliderect(p.rect):
                p.kill()
                self.player.activate_powerup(p.type)
                if p.type == "heart":
                     self.player.hp = min(self.player.hp + 1, self.player.max_hp)
                     self.emitter.heal_effect(p.rect.centerx, p.rect.centery, self.particles)
                else:
                     self.emitter.heal_effect(p.rect.centerx, p.rect.centery, self.particles)
        
        if pygame.sprite.collide_mask(self.player, self.police) and not self.death_triggered and not self.player.god_mode:
             if self.player.has_shield:
                  self.police.rect.x -= 400
                  self.police.speed = 0 
                  self.emitter.create_explosion(self.player.rect.centerx, self.player.rect.centery, (100, 200, 255), 15, self.particles)
             elif not self.player.invincible:
                  self.trigger_death("ARRESTED")
        
        for mob in self.mobs:
            if isinstance(mob, Drone):
                hit_hearts = [p for p in pygame.sprite.spritecollide(mob, self.powerups, True, pygame.sprite.collide_mask) if p.type == "heart"]
                if hit_hearts:
                    mob.kill()
                    self.emitter.create_explosion(mob.rect.centerx, mob.rect.centery, (255, 105, 180), 10, self.particles)
                    self.emitter.create_explosion(mob.rect.centerx, mob.rect.centery, (50, 50, 50), 10, self.particles)

        if self.player.just_healed:
            self.emitter.heal_effect(self.player.rect.centerx, self.player.rect.centery, self.particles)
            self.player.just_healed = False
        
        if self.player.just_damaged:
            self.emitter.player_hurt(self.player.rect.centerx, self.player.rect.centery, self.particles)
            self.player.just_damaged = False
        
        death_status = self.player.check_death()
        if death_status:
            self.trigger_death(death_status)

    def trigger_death(self, reason):
        if not self.death_triggered:
            if self.player.has_shield:
                 self.player.has_shield = False
                 self.player.invincible = True
                 self.player.invincibility_timer = 60
                 return
            self.death_triggered = True
            self.arrest_status = reason
            self.player.status = 'dead'
            self.player.frame_index = 0
            self.player.direction.x = 0 
            self.police.status = 'idle'
            
            if reason == "ARRESTED":
                play_sfx("arrest", 0.8)
            else:
                play_sfx("game_over", 0.8)

    def draw(self, surface):
        self.render_surface.fill((25, 25, 30))
        self.render_surface.fill((25, 25, 30))
        self.parallax_bg.draw(self.render_surface, self.camera_x)
        
        if self.next_parallax_bg:
            # Dessine le prochain background sur une surface temporaire avec de l'alpha pour le fondu
            temp_bg = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            temp_bg.set_colorkey((0,0,0)) # Transparence
            self.next_parallax_bg.draw(temp_bg, self.camera_x)
            temp_bg.set_alpha(int(self.fade_alpha))
            self.render_surface.blit(temp_bg, (0,0))

        for sprite in self.all_sprites:
            hitbox_rect = sprite.rect.move(-self.camera_x, 0)
            offset_x = getattr(sprite, 'visual_offset_x', 0)
            offset_y = getattr(sprite, 'visual_offset_y', 0)
            visual_rect = sprite.image.get_rect(midbottom=hitbox_rect.midbottom)
            visual_rect.x += offset_x
            visual_rect.y += offset_y
            self.render_surface.blit(sprite.image, visual_rect)
        
        for particle in self.particles:
             p_offset = (particle.rect.x - self.camera_x, particle.rect.y)
             self.render_surface.blit(particle.image, p_offset)
             
        if self.show_hitboxes:
            for s in self.all_sprites:
                if hasattr(s, 'mask'):
                    pts = s.mask.outline()
                    if pts:
                         h_rect = s.rect.move(-self.camera_x, 0)
                         v_rect = s.image.get_rect(midbottom=h_rect.midbottom)
                         v_rect.x += getattr(s, 'visual_offset_x', 0)
                         v_rect.y += getattr(s, 'visual_offset_y', 0)
                         
                         pts_adj = [(p[0] + v_rect.x, p[1] + v_rect.y) for p in pts]
                         if len(pts_adj) > 1:
                            pygame.draw.lines(self.render_surface, (50, 255, 50), True, pts_adj, 1)
             
        final_surface = self.apply_shake(self.render_surface)
        surface.blit(final_surface, (0, 0))
        
        self.hud.draw_hearts(surface, HUD_X, HUD_Y, self.player.hp, self.player.max_hp)
        if not self.game_over:
            hearts_offset = self.player.max_hp * (HEART_SIZE + 5) + 20
            self.hud.draw_withdrawal_bar(surface, HUD_X + hearts_offset, HUD_Y + 10, self.player.withdrawal, self.player.max_withdrawal)
            
            from progression import progression
            key, _ = progression.get_active_collectible()
            weed_img = asset_loader.fetch_img(ASSETS["items"][key])
            self.hud.draw_item_count(surface, SCREEN_WIDTH - 150, HUD_Y, weed_img, self.player.weed_count)
            
            font = pygame.font.Font(None, 40)
            score_text = font.render(f"DIST: {self.score}m", True, (255, 255, 255))
            surface.blit(score_text, (SCREEN_WIDTH // 2 - score_text.get_width() // 2, 25))
            
            self.hud.draw_powerup_bar(surface, HUD_X, HUD_Y + 60, self.player.shield_timer, 1200, (100, 200, 255), "SHIELD")
            self.hud.draw_powerup_bar(surface, HUD_X + 170, HUD_Y + 60, self.player.magnet_timer, 1200, (255, 100, 100), "MAGNET")
            
            if self.player.combo_counter > 1:
                combo_font = pygame.font.Font(None, 60)
                combo_text = combo_font.render(f"{self.player.combo_counter}x COMBO!", True, C_GOLD)
                surface.blit(combo_text, (SCREEN_WIDTH // 2 - combo_text.get_width() // 2, 80))
        
        if self.paused: 
            self.hud.draw_pause_menu(surface, self.show_missions)

    def apply_shake(self, surface):
        if self.game_over: return surface
        shake_x, shake_y = 0, 0
        if self.player.withdrawal > 40:
            intensity = int((self.player.withdrawal - 40) / 10) 
            shake_x += random.randint(-intensity, intensity)
            shake_y += random.randint(-intensity, intensity)
        if self.player.hurt_timer > 0:
            shake_x += random.randint(-5, 5)
            shake_y += random.randint(-5, 5)
        if shake_x == 0 and shake_y == 0: return surface
        new_surf = pygame.Surface(surface.get_size())
        new_surf.blit(surface, (shake_x, shake_y))
        return new_surf
