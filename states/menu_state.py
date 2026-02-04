import pygame
import math
from state_machine import State
from settings import *
from asset_loader import asset_loader, play_sfx
from states.game_state import GameState
from progression import progression

class MenuState(State):
    def __init__(self, brain):
        super().__init__(brain)
        self.SW = SCREEN_WIDTH
        self.SH = SCREEN_HEIGHT

        self.bg = asset_loader.fetch_img("graphics/Menu_Background.png", alpha=False)

        if self.bg:
            self.bg = pygame.transform.scale(self.bg, (self.SW, self.SH))

        self.overlay = pygame.Surface((self.SW, self.SH), pygame.SRCALPHA)
        for y in range(self.SH):
            alpha = int(60 + 100 * (y / self.SH))
            self.overlay.fill((0, 0, 0, alpha), (0, y, self.SW, 1))

        self.font_title = pygame.font.SysFont("arial", 72, bold=True)
        self.font_btn   = pygame.font.SysFont("arial", 28, bold=True)
        self.font_rules_title = pygame.font.SysFont("arial", 22, bold=True)
        self.font_rules_body  = pygame.font.SysFont("arial", 16)
        self.font_price = pygame.font.SysFont("arial", 20, bold=True)

        centre_x = self.SW // 2
        top_y = self.SH // 2 - 120 

        # Boutons menu plus compacts et élégants
        bw, bh = 240, 55
        self.btn_play     = pygame.Rect(centre_x - bw // 2, top_y, bw, bh)
        self.btn_missions = pygame.Rect(centre_x - bw // 2, top_y + 70, bw, bh)
        self.btn_shop     = pygame.Rect(centre_x - bw // 2, top_y + 140, bw, bh)
        self.btn_locker   = pygame.Rect(centre_x - bw // 2, top_y + 210, bw, bh)
        self.btn_rules    = pygame.Rect(centre_x - bw // 2, top_y + 280, bw, bh)
        self.btn_quit     = pygame.Rect(centre_x - bw // 2, top_y + 350, bw, bh)

        self.show_rules = False
        self.show_missions = False
        self.show_shop = False
        self.show_locker = False
        self.rules_alpha = 0
        self.mission_alpha = 0
        self.shop_alpha = 0
        self.locker_alpha = 0
        self.shop_scroll = 0
        self.t = 0.0

        self.rules_lines = [
            ("title", "COMMANDES"),
            ("rule",  " ↑ Sauter"),
            ("rule",  " REBOND : Sauter sur rats/oiseaux"),
            ("sep",   ""),
            ("title", "VITALITÉ"),
            ("rule",  " WEED  →  Réduit le MANQUE"),
            ("rule",  " MANQUE à 100% → Mort"),
            ("rule",  " Plus de vie ? WASTED"),
            ("sep",   ""),
            ("title", "POWER-UPS"),
            ("rule",  " AIMANT  →  Attire la weed"),
            ("rule",  " BOUCLIER :"),
            ("rule",  "  • Brise poubelles & sacs"),
            ("rule",  "  • Tue les ennemis au contact"),
            ("rule",  "  • Repousse Ralphie"),
            ("sep",   ""),
            ("title", "ENNEMIS"),
            ("rule",  " POLICE : Attention, Ralphie vous traque sans relache"),
            ("rule",  " DRONE : Coriace (ne peut être écrasé), vole un coeur"),
            ("sep",   ""),
            ("title", "Objets"),
            ("rule",  " Attention les obstacles vous ralenissent,"),
            ("rule",  " Ralphie risque de vous attraper"),
        ]

    def _panel_rect(self):
        return pygame.Rect(
            self.SW // 2 - PANEL_W // 2,
            self.SH // 2 - PANEL_H // 2,
            PANEL_W, PANEL_H
        )

    def update(self, dt, events):
        self.t += dt
        souris = pygame.mouse.get_pos()

        if self.show_rules:
            self.rules_alpha = min(self.rules_alpha + 18, 255)
        else:
            self.rules_alpha = max(self.rules_alpha - 18, 0)
            
        if self.show_missions:
            self.mission_alpha = min(self.mission_alpha + 18, 255)
        else:
            self.mission_alpha = max(self.mission_alpha - 18, 0)

        if self.show_shop:
            self.shop_alpha = min(self.shop_alpha + 18, 255)
        else:
            self.shop_alpha = max(self.shop_alpha - 18, 0)

        if self.show_locker:
            self.locker_alpha = min(self.locker_alpha + 18, 255)
        else:
            self.locker_alpha = max(self.locker_alpha - 18, 0)

        for ev in events:
            if ev.type == pygame.MOUSEWHEEL:
                if self.show_shop:
                    # Scroll boutique
                    self.shop_scroll = max(0, self.shop_scroll - ev.y * 30)

            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                if self.show_rules:
                    panel = self._panel_rect()
                    # Hitbox pour fermer les regles
                    bouton_fermer = pygame.Rect(panel.right - 36, panel.top + 4, 32, 28)
                    if bouton_fermer.collidepoint(souris) or not panel.collidepoint(souris):
                        self.show_rules = False
                        play_sfx("click")
                elif self.show_shop:
                    panel = self._panel_rect()
                    bouton_fermer = pygame.Rect(panel.right - 36, panel.top + 4, 32, 28)
                    if bouton_fermer.collidepoint(souris) or not panel.collidepoint(souris):
                        self.show_shop = False
                        play_sfx("click")
                    
                    # Echange de weed (Vente)
                    ws = progression.state.get("weed_stash", 0)
                    if ws > 0:
                        # Position alignée avec le nouveau design
                        exch_btn = pygame.Rect(panel.right - 200, panel.top + 15, 140, 50)
                        if exch_btn.collidepoint(souris):
                            gain = int(ws * 8) 
                            progression.state["credits"] += gain
                            progression.state["weed_stash"] = 0
                            progression.commit()
                            play_sfx("click")
                    
                    # Clic sur les packs de la boutique
                    from assets_registry import ASSETS
                    sets = ASSETS["boutique_sets"]
                    items = ASSETS.get("boutique_items", {})
                    
                    combined = []
                    for sid, cfg in sets.items(): combined.append(("set", sid, cfg))
                    for iid, cfg in items.items(): combined.append(("item", iid, cfg))
                    
                    for i, (kind, uid, cfg) in enumerate(combined):
                        col, row = i % 3, i // 3
                        margin = (PANEL_W - 3 * 230) // 4
                        btn_rect = pygame.Rect(panel.left + margin + col * (230 + margin), panel.top + 130 + row * 300 - self.shop_scroll, 230, 280)
                        
                        if btn_rect.bottom > panel.top + 130 and btn_rect.top < panel.bottom:
                            if btn_rect.collidepoint(souris):
                                if kind == "set":
                                    if uid not in progression.state["unlocked_sets"]:
                                        if progression.state["credits"] >= cfg["price"]:
                                            progression.state["credits"] -= cfg["price"]
                                            progression.state["unlocked_sets"].append(uid)
                                            # On débloque aussi les variants individuellement ? 
                                            # Non, le pack suffit.
                                            progression.commit()
                                            play_sfx("click")
                                else: # Unité
                                    if uid not in progression.state["unlocked_items"]:
                                        if progression.state["credits"] >= cfg["price"]:
                                            progression.state["credits"] -= cfg["price"]
                                            progression.state["unlocked_items"].append(uid)
                                            progression.commit()
                                            play_sfx("click")
                elif self.show_locker:
                    panel = self._panel_rect()
                    bouton_fermer = pygame.Rect(panel.right - 36, panel.top + 4, 32, 28)
                    if bouton_fermer.collidepoint(souris) or not panel.collidepoint(souris):
                        self.show_locker = False
                        play_sfx("click")
                    
                    # Sélection du set (Grille 5xN)
                    from assets_registry import ASSETS
                    unlocked_sets = progression.state["unlocked_sets"]
                    unlocked_items = progression.state.get("unlocked_items", [])
                    box_size = 110
                    
                    # Combinaison pour la grille
                    all_unlocked = []
                    for sid in unlocked_sets: all_unlocked.append(("set", sid))
                    for iid in unlocked_items: all_unlocked.append(("item", iid))
                    
                    for i, (kind, uid) in enumerate(all_unlocked):
                        col, row = i % 5, i // 5
                        btn_rect = pygame.Rect(panel.left + 30 + col * (box_size + 15), panel.top + 120 + row * (box_size + 15), box_size, box_size)
                        if btn_rect.collidepoint(souris):
                            progression.state["active_skin_set"] = uid
                            if kind == "set" and uid != "default":
                                progression.state["active_variant"] = ASSETS["boutique_sets"][uid]["variants"][0]
                            else:
                                progression.state["active_variant"] = None
                            progression.commit()
                            play_sfx("click")
                    
                    # Sélection de la variante (Grille horizontale)
                    active_set = progression.state.get("active_skin_set", "default")
                    if active_set != "default":
                        cfg = ASSETS["boutique_sets"][active_set]
                        for j, var_id in enumerate(cfg["variants"]):
                            var_rect = pygame.Rect(panel.left + 30 + j * 125, panel.top + 380, 110, 110)
                            if var_rect.collidepoint(souris):
                                progression.state["active_variant"] = var_id
                                progression.commit()
                                play_sfx("click")
                elif self.show_missions:
                    panel = self._panel_rect()
                    bouton_fermer = pygame.Rect(panel.right - 36, panel.top + 4, 32, 28)
                    if bouton_fermer.collidepoint(souris) or not panel.collidepoint(souris):
                        self.show_missions = False
                        play_sfx("click")
                    
                    # Clic sur les boutons de récompense
                    for i, q in enumerate(progression.state["quests"]):
                        if q["completed"] and not q["claimed"]:
                            btn_claim = pygame.Rect(panel.left + PANEL_W - 160, panel.top + 100 + i * 140, 140, 40)
                            if btn_claim.collidepoint(souris):
                                if progression.claim(i):
                                    play_sfx("click")
                else:
                    if self.btn_play.collidepoint(souris):
                        play_sfx("click")
                        gs = GameState(self.brain)
                        self.brain.change(gs)

                    if self.btn_missions.collidepoint(souris):
                        play_sfx("click")
                        self.show_missions = True

                    if self.btn_shop.collidepoint(souris):
                        play_sfx("click")
                        self.show_shop = True

                    if self.btn_locker.collidepoint(souris):
                        play_sfx("click")
                        self.show_locker = True

                    if self.btn_rules.collidepoint(souris):
                        play_sfx("click")
                        self.show_rules = True
                    if self.btn_quit.collidepoint(souris):
                        play_sfx("click")
                        pygame.quit()
                        import sys
                        sys.exit()
            
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_g:
                    progression.state["credits"] += 1000
                    progression.commit()
                    play_sfx("click")

    def draw(self, surface):
        if self.bg:
            surface.blit(self.bg, (0, 0))
        surface.blit(self.overlay, (0, 0))

        self._draw_title(surface)

        souris = pygame.mouse.get_pos()
        self._draw_button(surface, self.btn_play,     "JOUER", souris)
        self._draw_button(surface, self.btn_missions, "MISSIONS", souris)
        self._draw_button(surface, self.btn_shop,     "BOUTIQUE", souris)
        self._draw_button(surface, self.btn_locker,   "CASIER", souris)
        self._draw_button(surface, self.btn_rules,    "RÈGLES", souris)
        self._draw_button(surface, self.btn_quit,     "QUITTER", souris)
        
        # Argent virtuel
        self._draw_currency(surface)

        if self.rules_alpha > 0:
            self._draw_rules_panel(surface)
        if self.mission_alpha > 0:
            self._draw_missions_panel(surface)
        if self.shop_alpha > 0:
            self._draw_shop_panel(surface)
        if self.locker_alpha > 0:
            self._draw_locker_panel(surface)

    def _draw_scrolling_label(self, surface, text, rect, font, color=(255, 255, 255)):
        img = font.render(text, True, color)
        
        # Calcul du clip sécurisé (intersection avec le clip parent pour pas dépasser de la zone de scroll)
        clip_prev = surface.get_clip()
        safe_clip = rect.clip(clip_prev)
        
        # Si la zone visible est vide (item hors écran), on dessine rien
        if safe_clip.width == 0 or safe_clip.height == 0:
            return

        # Si ça rentre large, on centre sans se prendre la tête
        if img.get_width() <= rect.width:
            surface.set_clip(safe_clip)
            surface.blit(img, (rect.left, rect.centery - img.get_height() // 2))
            surface.set_clip(clip_prev)
            return

        # Sinon, scroll infini de droite à gauche
        speed = 30
        offset = (self.t * speed) % (img.get_width() + 40) 
        
        surface.set_clip(safe_clip)
        
        y_pos = rect.centery - img.get_height() // 2
        
        # Premier passage
        x1 = rect.left - offset
        if x1 < rect.right:
            surface.blit(img, (x1, y_pos))
            
        # Deuxième passage pour la boucle
        x2 = x1 + img.get_width() + 40
        if x2 < rect.right:
            surface.blit(img, (x2, y_pos))
            
        surface.set_clip(clip_prev)

    def _draw_title(self, surface):
        centre_x = self.SW // 2
        mouvement = math.sin(self.t * 2.5) * 4

        # Titre text
        txt_raw = "GET MY WEED"

        # Ombre
        ombre = self.font_title.render(txt_raw, True, C_BLACK)
        surface.blit(ombre, ombre.get_rect(centerx=centre_x + 3, centery=TITLE_Y + mouvement + 3))

        # Cercle halo animé
        halo = self.font_title.render(txt_raw, True, C_GOLD_DARK)
        for dx, dy in [(-2, 0), (2, 0), (0, -2), (0, 2)]:
            surface.blit(halo, halo.get_rect(centerx=centre_x + dx, centery=TITLE_Y + mouvement + dy))

        # Titre
        titre = self.font_title.render(txt_raw, True, C_GOLD)
        surface.blit(titre, titre.get_rect(centerx=centre_x, centery=TITLE_Y + mouvement))

    def _draw_currency(self, surface):
        # On affiche le fric en haut a droite
        margin = 40
        txt = f"CREDITS : {progression.state['credits']}"
        
        # Petit liseré orange pour que ca pete
        glow_surf = self.font_btn.render(txt, True, (255, 100, 0))
        for dx, dy in [(-2,0),(2,0),(0,-2),(0,2)]:
            surface.blit(glow_surf, (self.SW - glow_surf.get_width() - margin + dx, margin + dy))
            
        surf = self.font_btn.render(txt, True, (255, 230, 0))
        surface.blit(surf, (self.SW - surf.get_width() - margin, margin))

    def _draw_button(self, surface, rect, texte, souris):
        # On anime un peu au survol
        survole = rect.collidepoint(souris) and not (self.show_rules or self.show_missions or self.show_shop or self.show_locker)
        
        if survole:
            # Effet de pulse
            glow_expand = math.sin(self.t * 5) * 5 + 5
            glow_rect = rect.inflate(glow_expand, glow_expand)
            pygame.draw.rect(surface, (255, 220, 100, 100), glow_rect, border_radius=15, width=3)
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)
        
        # Ombre bouton
        pygame.draw.rect(surface, (0, 0, 0, 150), rect.move(4, 4), border_radius=12)
        
        # Corps bouton
        body_col = (255, 240, 100) if survole else C_GOLD
        pygame.draw.rect(surface, body_col, rect, border_radius=12)
        
        # Reflet discret
        pygame.draw.rect(surface, (255, 255, 255, 100), (rect.left+5, rect.top+3, rect.width-10, 4), border_radius=2)
        
        # Bordures
        pygame.draw.rect(surface, (150, 100, 0), rect, width=2, border_radius=12)

        txt_btn = self.font_btn.render(texte, True, (30, 30, 0))
        surface.blit(txt_btn, txt_btn.get_rect(center=rect.center))

    def _draw_rules_panel(self, surface):
        panel = self._panel_rect()

        # Fond semi-transparent
        panneau = pygame.Surface((PANEL_W, PANEL_H), pygame.SRCALPHA)
        panneau.fill((0, 0, 0, min(self.rules_alpha, 200))) 
        surface.blit(panneau, panel.topleft)

        pygame.draw.rect(surface, C_GOLD, panel, width=3, border_radius=14)

        # Bouton fermer
        bouton_fermer = pygame.Rect(panel.right - 36, panel.top + 6, 28, 24)
        souris = pygame.mouse.get_pos()
        couleur = (255, 100, 100) if bouton_fermer.collidepoint(souris) else C_WHITE_DIM
        croix = self.font_rules_title.render("✕", True, couleur)
        surface.blit(croix, croix.get_rect(center=bouton_fermer.center))

        # Texte (avec alpha si possible, sinon simple blit)
        x = panel.left + 28
        y = panel.top + 26

        for type_ligne, texte in self.rules_lines:
            if type_ligne == "title":
                surface.blit(self.font_rules_title.render(texte, True, C_RULE_TITLE), (x, y))
                y += 28
            elif type_ligne == "rule":
                surface.blit(self.font_rules_body.render(texte, True, C_RULE_TEXT), (x + 14, y))
                y += 20
            elif type_ligne == "sep":
                pygame.draw.line(surface, C_GOLD_DARK, (x, y + 4), (panel.right - 28, y + 4), 1)
                y += 10

    def _draw_shop_panel(self, surface):
        panel = self._panel_rect()
        overlay = pygame.Surface((PANEL_W, PANEL_H), pygame.SRCALPHA)
        overlay.fill((10, 10, 15, 240)) # Base effet verre (glassmorphism)
        surface.blit(overlay, panel.topleft)
        pygame.draw.rect(surface, (0, 180, 255), panel, width=3, border_radius=20)

        # Barre d'en-tête
        header_rect = pygame.Rect(panel.left, panel.top, panel.width, 80)
        pygame.draw.rect(surface, (0, 180, 255, 50), header_rect, border_top_left_radius=20, border_top_right_radius=20)

        # Bouton fermer (X)
        btn_close = pygame.Rect(panel.right - 45, panel.top + 15, 30, 30)
        souris = pygame.mouse.get_pos()
        close_col = (255, 50, 50) if btn_close.collidepoint(souris) else (200, 200, 200)
        surface.blit(self.font_title.render("×", True, close_col), (panel.right - 55, panel.top - 10))

        title = self.font_title.render("BOUTIQUE", True, (255, 255, 255))
        title = pygame.transform.scale(title, (int(title.get_width() * 0.6), int(title.get_height() * 0.6)))
        surface.blit(title, (panel.left + 30, panel.top + 15))

        # Bouton vente weed mieux intégré
        ws = progression.state.get("weed_stash", 0)
        if ws > 0:
            # Même rect que dans update()
            exch_btn = pygame.Rect(panel.right - 200, panel.top + 15, 140, 50)
            hover_sell = exch_btn.collidepoint(pygame.mouse.get_pos())
            
            # Fond style "terminal financier"
            bg_col = (20, 50, 30) if hover_sell else (10, 30, 15)
            pygame.draw.rect(surface, bg_col, exch_btn, border_radius=10)
            
            # Bordure néon
            border_col = (100, 255, 100) if hover_sell else (40, 120, 60)
            pygame.draw.rect(surface, border_col, exch_btn, width=2, border_radius=10)
            
            # Infos
            gain = ws * 8
            # Ligne 1 : Action
            l1 = self.font_btn.render("VENDRE", True, (200, 255, 200))
            l1 = pygame.transform.scale(l1, (int(l1.get_width() * 0.7), int(l1.get_height() * 0.7)))
            surface.blit(l1, l1.get_rect(centerx=exch_btn.centerx, top=exch_btn.top + 6))
            
            # Ligne 2 : Montant
            l2 = self.font_rules_body.render(f"{ws}u -> {gain} Cr", True, (100, 255, 100))
            surface.blit(l2, l2.get_rect(centerx=exch_btn.centerx, bottom=exch_btn.bottom - 6))

        from assets_registry import ASSETS
        sets = ASSETS["boutique_sets"]
        items = ASSETS.get("boutique_items", {})
        
        combined = []
        for sid, cfg in sets.items(): combined.append(("set", sid, cfg))
        for iid, cfg in items.items(): combined.append(("item", iid, cfg))
        
        # Titre de section style Fortnite
        header_tag = self.font_rules_title.render("BOUTIQUE DE LA RUE", True, (255, 255, 255))
        surface.blit(header_tag, (panel.left + 30, panel.top + 85))
        pygame.draw.line(surface, (255, 255, 255, 50), (panel.left + 30, panel.top + 115), (panel.right - 30, panel.top + 115), 1)

        # Zone de contenu scrollable
        zone_clip = pygame.Rect(panel.left + 20, panel.top + 130, panel.width - 40, panel.height - 150)
        old_clip = surface.get_clip()
        surface.set_clip(zone_clip)

        for i, (kind, uid, cfg) in enumerate(combined):
            col, row = i % 3, i // 3
            bw, bh = 230, 280
            # On centre par rapport a la nouvelle largeur
            margin = (PANEL_W - 3 * bw) // 4
            rect = pygame.Rect(panel.left + margin + col * (bw + margin), panel.top + 130 + row * 300 - self.shop_scroll, bw, bh)
            
            # Débloqué si le pack est débloqué OU si l'item seul l'est
            if kind == "set":
                locked = uid not in progression.state["unlocked_sets"]
            else:
                # Un item est débloqué si son pack l'est OU si lui l'est
                parent_set = None
                for sid, scfg in ASSETS["boutique_sets"].items():
                    if uid in scfg["variants"]:
                        parent_set = sid
                        break
                locked = (uid not in progression.state.get("unlocked_items", [])) and (parent_set not in progression.state["unlocked_sets"])

            hover = rect.collidepoint(souris)
            
            # Palette rareté
            price = cfg["price"]
            r_col = (130, 130, 130)
            if price >= 2000: r_col = (255, 180, 50)
            elif price >= 1500: r_col = (180, 50, 255)
            elif price >= 1000: r_col = (50, 150, 255)
            else: r_col = (80, 200, 50)

            # Design de la carte
            dr = rect.inflate(10, 10) if hover else rect
            pygame.draw.rect(surface, (18, 18, 28), dr, border_radius=12)
            
            # Dégradé rareté
            bg_grad = pygame.Surface((dr.width, dr.height), pygame.SRCALPHA)
            for gy in range(dr.height):
                alpha = int(120 * (1 - gy/dr.height))
                pygame.draw.line(bg_grad, (r_col[0], r_col[1], r_col[2], alpha), (0, gy), (dr.width, gy))
            surface.blit(bg_grad, dr.topleft)

            # Preview tournante des variants ou sprite unique
            if kind == "set":
                v_list = cfg["variants"]
                v_id = v_list[int(self.t // 1.5) % len(v_list)]
            else:
                v_id = cfg["var"]
                
            try:
                data = asset_loader.load_skin_variant(v_id)
                frames = data.get("run") or data.get("idle")
                if frames:
                    s_fps = cfg.get("fps", 10)
                    f_idx = int(self.t * s_fps) % len(frames)
                    img = pygame.transform.scale(frames[f_idx], (180, 180))
                    
                    # Halo lumineux
                    halo = pygame.Surface((200, 200), pygame.SRCALPHA)
                    pygame.draw.circle(halo, (r_col[0], r_col[1], r_col[2], 50 if hover else 30), (100, 100), 85)
                    surface.blit(halo, halo.get_rect(center=(dr.centerx, dr.top + 105)))
                    
                    surface.blit(img, img.get_rect(center=(dr.centerx, dr.top + 105)))
            except: 
                pygame.draw.rect(surface, (30, 30, 40), (dr.centerx-40, dr.top+40, 80, 120), border_radius=8)

            # Footer
            foot_h = 80
            foot = pygame.Rect(dr.left, dr.bottom - foot_h, dr.width, foot_h)
            pygame.draw.rect(surface, (0, 0, 0, 160), foot, border_bottom_left_radius=12, border_bottom_right_radius=12)
            pygame.draw.rect(surface, r_col, (foot.left, foot.bottom - 4, foot.width, 4))

            # Labels (Scrollement automatique si trop long)
            n_txt = cfg["name"]
            label_rect = pygame.Rect(foot.left + 12, foot.top + 8, foot.width - 24, 25)
            self._draw_scrolling_label(surface, n_txt, label_rect, self.font_rules_title)
            
            type_tag = f"PACK ({len(cfg['variants'])})" if kind == "set" else "INDIVIDUEL"
            surface.blit(self.font_rules_body.render(type_tag, True, (160, 160, 160)), (foot.left + 12, foot.top + 35))

            if not locked:
                txt = self.font_rules_body.render("POSSÉDÉ", True, (100, 255, 120))
                surface.blit(txt, (foot.right - txt.get_width() - 15, foot.bottom - 28))
            else:
                enough = progression.state["credits"] >= price
                p_col = (255, 255, 255) if enough else (255, 80, 80)
                p_surf = self.font_price.render(str(price), True, p_col)
                surface.blit(p_surf, (foot.right - p_surf.get_width() - 35, foot.bottom - 32))
                pygame.draw.circle(surface, (255, 210, 50), (foot.right - 20, foot.bottom - 22), 8)

            if hover:
                pygame.draw.rect(surface, (255, 255, 255), dr, width=2, border_radius=12)

        surface.set_clip(old_clip)

    def _draw_locker_panel(self, surface):
        panel = self._panel_rect()
        overlay = pygame.Surface((PANEL_W, PANEL_H), pygame.SRCALPHA)
        overlay.fill((15, 10, 15, 240)) # Look glassmorphism
        surface.blit(overlay, panel.topleft)
        pygame.draw.rect(surface, (150, 255, 100), panel, width=3, border_radius=20)

        title = self.font_title.render("CASIER", True, (150, 255, 100))
        title = pygame.transform.scale(title, (int(title.get_width()*0.6), int(title.get_height()*0.6)))
        surface.blit(title, (panel.left + 30, panel.top + 15))

        from assets_registry import ASSETS
        unlocked = progression.state["unlocked_sets"]
        active_set = progression.state.get("active_skin_set", "default")
        souris = pygame.mouse.get_pos()

        # Grille des skins débloqués
        surface.blit(self.font_rules_title.render("COLLECTIONS & OBJETS", True, (150, 255, 100)), (panel.left + 30, panel.top + 80))
        
        unlocked_sets = progression.state["unlocked_sets"]
        unlocked_items = progression.state.get("unlocked_items", [])
        
        all_unlocked = []
        for sid in unlocked_sets: all_unlocked.append(("set", sid))
        for iid in unlocked_items: all_unlocked.append(("item", iid))

        for i, (kind, uid) in enumerate(all_unlocked):
            # Grille 5 colonnes
            c, r = i % 5, i // 5
            size = 110
            rect = pygame.Rect(panel.left + 30 + c * (size + 15), panel.top + 120 + r * (size + 15), size, size)
            
            is_active = (uid == active_set)
            is_hover = rect.collidepoint(souris)
            
            # Look premium
            bg = (60, 180, 80) if is_active else ((60, 60, 80) if is_hover else (30, 30, 45))
            pygame.draw.rect(surface, bg, rect, border_radius=12)
            
            # Aperçu
            try:
                if uid == "default":
                    c_id = ASSETS["player"]["idle"]
                    img = asset_loader.load_sheet(c_id["p"], c_id["w"], c_id["h"], count=1)[0]
                elif kind == "set":
                    v_name = ASSETS["boutique_sets"][uid]["variants"][0]
                    anims = asset_loader.load_skin_variant(v_name)
                    img = anims["idle"][0]
                else: # Item seul
                    v_name = ASSETS["boutique_items"][uid]["var"]
                    anims = asset_loader.load_skin_variant(v_name)
                    img = anims["idle"][0]
                        
                img = pygame.transform.scale(img, (95, 95))
                surface.blit(img, img.get_rect(center=rect.center))
            except: pass
            
            if is_active:
                pygame.draw.rect(surface, (255, 255, 255), rect, width=2, border_radius=12)
                pygame.draw.circle(surface, (100, 255, 100), (rect.right - 10, rect.top + 10), 7)

        # --- GRILLE DES VARIANTES (Si pack sélectionné) ---
        if active_set != "default":
            surface.blit(self.font_rules_title.render("VARIANTES", True, (0, 180, 255)), (panel.left + 30, panel.top + 340))
            cfg = ASSETS["boutique_sets"][active_set]
            active_var = progression.state.get("active_variant", cfg["variants"][0])
            
            for j, var_id in enumerate(cfg["variants"]):
                rect = pygame.Rect(panel.left + 30 + j * 125, panel.top + 380, 110, 110)
                is_active = (var_id == active_var)
                is_hover = rect.collidepoint(souris)
                
                col = (0, 150, 220) if is_active else ((50, 50, 80) if is_hover else (30, 30, 45))
                pygame.draw.rect(surface, col, rect, border_radius=12)
                
                try:
                    # Ici aussi, on utilise load_skin_variant pour pas s'embeter avec le kit_jap etc
                    anims = asset_loader.load_skin_variant(var_id)
                    p_img = anims["idle"][0]
                    p_img = pygame.transform.scale(p_img, (95, 95))
                    surface.blit(p_img, p_img.get_rect(center=rect.center))
                except: pass
                
                if is_active:
                    pygame.draw.rect(surface, (255, 255, 255), rect, width=2, border_radius=12)

    def _draw_missions_panel(self, surface):
        panel = self._panel_rect()
        panneau = pygame.Surface((PANEL_W, PANEL_H), pygame.SRCALPHA)
        panneau.fill((0, 0, 0, min(self.mission_alpha, 210))) 
        surface.blit(panneau, panel.topleft)
        pygame.draw.rect(surface, C_GOLD, panel, width=3, border_radius=14)

        # Bouton fermer
        bouton_fermer = pygame.Rect(panel.right - 36, panel.top + 6, 28, 24)
        souris = pygame.mouse.get_pos()
        couleur = (255, 100, 100) if bouton_fermer.collidepoint(souris) else C_WHITE_DIM
        croix = self.font_rules_title.render("✕", True, couleur)
        surface.blit(croix, croix.get_rect(center=bouton_fermer.center))

        title = self.font_title.render("MISSIONS DE RUE", True, C_RULE_TITLE)
        surface.blit(title, title.get_rect(centerx=panel.centerx, top=panel.top + 20))

        # Missions
        for i, q in enumerate(progression.state["quests"]):
            y = panel.top + 100 + i * 140
            rect = pygame.Rect(panel.left + 20, y, PANEL_W - 40, 130)
            
            # Fond de la carte mission
            bg_color = (35, 35, 45, 180)
            if q["claimed"]: bg_color = (25, 25, 30, 120)
            pygame.draw.rect(surface, bg_color, rect, border_radius=15)
            
            # Bordure brillante si complétée
            if q["completed"] and not q["claimed"]:
                pygame.draw.rect(surface, (100, 255, 100), rect, width=2, border_radius=15)
            else:
                pygame.draw.rect(surface, (70, 70, 80), rect, width=1, border_radius=15)
            
            # Titre mission
            status_tag = ""
            if q["claimed"]: status_tag = " [VALIDÉ]"
            elif q["completed"]: status_tag = " [PRÊT]"
            
            color = (120, 255, 120) if q["completed"] else (220, 220, 230)
            if q["claimed"]: color = (100, 100, 100)
            
            q_title = self.font_rules_title.render(q["title"] + status_tag, True, color)
            surface.blit(q_title, (rect.left + 25, rect.top + 18))
            
            # Description
            q_desc = self.font_rules_body.render(q["desc"], True, (180, 180, 190) if not q["claimed"] else (80, 80, 80))
            surface.blit(q_desc, (rect.left + 25, rect.top + 48))
            
            # Barre de progression plus stylée
            bar_w = 340
            bar_h = 8
            bar_rect = pygame.Rect(rect.left + 25, rect.top + 78, bar_w, bar_h)
            pygame.draw.rect(surface, (40, 40, 50), bar_rect, border_radius=4)
            
            progress = q["current"] / q["goal"]
            if progress > 0:
                p_color = (0, 180, 255) if not q["completed"] else (0, 255, 150)
                if q["claimed"]: p_color = (60, 60, 60)
                prog_rect = pygame.Rect(bar_rect.left, bar_rect.top, int(bar_w * progress), bar_h)
                pygame.draw.rect(surface, p_color, prog_rect, border_radius=4)
            
            # Texte progression
            p_txt = f"{q['current']} / {q['goal']}"
            p_surf = self.font_rules_body.render(p_txt, True, (200, 200, 210) if not q["claimed"] else (80, 80, 80))
            surface.blit(p_surf, (bar_rect.right + 20, bar_rect.top - 6))
            
            # Récompense avec icône (simulée par couleur)
            r_txt = f"Prime: {q['reward']} CR"
            r_surf = self.font_rules_body.render(r_txt, True, C_GOLD if not q["claimed"] else (80, 70, 40))
            surface.blit(r_surf, (rect.left + 25, rect.top + 98))

            # Bouton récupérer
            if q["completed"] and not q["claimed"]:
                btn_r = pygame.Rect(rect.right - 170, rect.top + 45, 150, 45)
                is_hover = btn_r.collidepoint(souris)
                # Effet de pulse/glow simulé
                btn_color = (100, 255, 150) if is_hover else (60, 180, 100)
                pygame.draw.rect(surface, btn_color, btn_r, border_radius=12)
                pygame.draw.rect(surface, C_WHITE_DIM, btn_r, width=2, border_radius=12)
                
                r_text = self.font_btn.render("RÉCUPÉRER", True, (20, 40, 20))
                r_text = pygame.transform.scale(r_text, (130, 32))
                surface.blit(r_text, r_text.get_rect(center=btn_r.center))
