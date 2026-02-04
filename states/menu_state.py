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
        self.font_btn   = pygame.font.SysFont("arial", 32, bold=True)
        self.font_rules_title = pygame.font.SysFont("arial", 22, bold=True)
        self.font_rules_body  = pygame.font.SysFont("arial", 16)

        centre_x = self.SW // 2
        top = self.SH // 2 - 80 

        self.btn_play     = pygame.Rect(centre_x - BTN_W // 2, top, BTN_W, BTN_H)
        self.btn_missions = pygame.Rect(centre_x - BTN_W // 2, top + BTN_H + BTN_GAP, BTN_W, BTN_H)
        self.btn_rules    = pygame.Rect(centre_x - BTN_W // 2, top + (BTN_H + BTN_GAP) * 2, BTN_W, BTN_H)
        self.btn_quit     = pygame.Rect(centre_x - BTN_W // 2, top + (BTN_H + BTN_GAP) * 3, BTN_W, BTN_H)

        self.show_rules = False
        self.show_missions = False
        self.rules_alpha = 0
        self.mission_alpha = 0
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

        for ev in events:
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                if self.show_rules:
                    panel = self._panel_rect()
                    bouton_fermer = pygame.Rect(panel.right - 36, panel.top + 4, 32, 28)
                    if bouton_fermer.collidepoint(souris) or not panel.collidepoint(souris):
                        self.show_rules = False
                        play_sfx("click")
                elif self.show_missions:
                    panel = self._panel_rect()
                    bouton_fermer = pygame.Rect(panel.right - 36, panel.top + 4, 32, 28)
                    if bouton_fermer.collidepoint(souris) or not panel.collidepoint(souris):
                        self.show_missions = False
                        play_sfx("click")
                    
                    # Clic sur les boutons de récompense
                    for i, q in enumerate(progression.data["quests"]):
                        if q["completed"] and not q["claimed"]:
                            btn_claim = pygame.Rect(panel.left + PANEL_W - 160, panel.top + 100 + i * 140, 140, 40)
                            if btn_claim.collidepoint(souris):
                                if progression.claim_reward(i):
                                    play_sfx("click")
                else:
                    if self.btn_play.collidepoint(souris):
                        play_sfx("click")
                        gs = GameState(self.brain)
                        self.brain.change(gs)

                    if self.btn_missions.collidepoint(souris):
                        play_sfx("click")
                        self.show_missions = True

                    if self.btn_rules.collidepoint(souris):
                        play_sfx("click")
                        self.show_rules = True
                    if self.btn_quit.collidepoint(souris):
                        play_sfx("click")
                        pygame.quit()
                        import sys
                        sys.exit()

    def draw(self, surface):
        if self.bg:
            surface.blit(self.bg, (0, 0))
        surface.blit(self.overlay, (0, 0))

        self._draw_title(surface)

        souris = pygame.mouse.get_pos()
        self._draw_button(surface, self.btn_play,     "JOUER", souris)
        self._draw_button(surface, self.btn_missions, "MISSIONS", souris)
        self._draw_button(surface, self.btn_rules,    "RÈGLES", souris)
        self._draw_button(surface, self.btn_quit,     "QUITTER", souris)
        
        # Argent virtuel
        self._draw_currency(surface)

        if self.rules_alpha > 0:
            self._draw_rules_panel(surface)
        if self.mission_alpha > 0:
            self._draw_missions_panel(surface)

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

    def _draw_button(self, surface, rect, texte, souris):
        survole = rect.collidepoint(souris) and not self.show_rules

        pygame.draw.rect(surface, C_BTN_SHADOW, rect.move(3, 4), border_radius=12)
        pygame.draw.rect(surface, C_BTN_HOVER if survole else C_GOLD, rect, border_radius=12)
        pygame.draw.rect(surface, C_GOLD_DARK, rect, width=2, border_radius=12)

        txt = self.font_btn.render(texte, True, C_BLACK)
        surface.blit(txt, txt.get_rect(center=rect.center))

        if survole:
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)
        else:
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)

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

    def _draw_currency(self, surface):
        txt = f"CREDITS : {progression.data['money']}"
        surf = self.font_btn.render(txt, True, C_GOLD)
        surface.blit(surf, (self.SW - surf.get_width() - 30, 30))

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
        for i, q in enumerate(progression.data["quests"]):
            y = panel.top + 100 + i * 140
            rect = pygame.Rect(panel.left + 20, y, PANEL_W - 40, 130)
            pygame.draw.rect(surface, (40, 40, 50, 100), rect, border_radius=10)
            
            # Titre mission
            color = (100, 255, 100) if q["completed"] else C_WHITE_DIM
            q_title = self.font_rules_title.render(q["title"], True, color)
            surface.blit(q_title, (rect.left + 20, rect.top + 15))
            
            # Description
            q_desc = self.font_rules_body.render(q["desc"], True, C_RULE_TEXT)
            surface.blit(q_desc, (rect.left + 20, rect.top + 45))
            
            # Barre de progression
            bar_w = 300
            bar_h = 10
            bar_rect = pygame.Rect(rect.left + 20, rect.top + 75, bar_w, bar_h)
            pygame.draw.rect(surface, (60, 60, 60), bar_rect, border_radius=5)
            
            progress = q["current"] / q["goal"]
            prog_rect = pygame.Rect(bar_rect.left, bar_rect.top, int(bar_w * progress), bar_h)
            pygame.draw.rect(surface, (100, 200, 255), prog_rect, border_radius=5)
            
            # Texte progression
            p_txt = f"{q['current']} / {q['goal']}"
            p_surf = self.font_rules_body.render(p_txt, True, C_WHITE_DIM)
            surface.blit(p_surf, (bar_rect.right + 15, bar_rect.top - 5))
            
            # Récompense
            r_txt = f"Récompense: {q['reward']} CR"
            r_surf = self.font_rules_body.render(r_txt, True, C_GOLD)
            surface.blit(r_surf, (rect.left + 20, rect.top + 95))

            # Bouton récupérer
            if q["completed"] and not q["claimed"]:
                btn_r = pygame.Rect(rect.right - 150, rect.top + 40, 140, 40)
                is_hover = btn_r.collidepoint(souris)
                pygame.draw.rect(surface, (80, 200, 100) if is_hover else (50, 150, 50), btn_r, border_radius=8)
                r_text = self.font_btn.render("RÉCUPÉRER", True, C_WHITE_DIM)
                # On triche un peu sur la taille de font
                r_text = pygame.transform.scale(r_text, (120, 30))
                surface.blit(r_text, r_text.get_rect(center=btn_r.center))
            elif q["claimed"]:
                claimed_txt = self.font_rules_title.render("TERMINÉ", True, (100, 100, 100))
                surface.blit(claimed_txt, claimed_txt.get_rect(midright=(rect.right - 20, rect.centery)))
