import pygame
import math
from state_machine import State
from settings import *
from asset_loader import asset_loader
from progression import progression

class GameOverState(State):
    def __init__(self, brain, score, status, run_stats=None):
        super().__init__(brain)
        self.score = score
        self.status = status
        
        if run_stats:
            progression.update_progress(run_stats)
        self.SW = SCREEN_WIDTH
        self.SH = SCREEN_HEIGHT

        # On réutilise le fond du menu ou un truc sombre
        self.bg = asset_loader.fetch_img("graphics/Menu_Background.png", alpha=False)        

        self.bg = pygame.transform.scale(self.bg, (self.SW, self.SH))

        self.overlay = pygame.Surface((self.SW, self.SH), pygame.SRCALPHA)
        # Teinte plus rouge pour la mort
        for y in range(self.SH):
            alpha = int(100 + 100 * (y / self.SH))
            self.overlay.fill((40, 0, 0, alpha), (0, y, self.SW, 1))

        self.font_title = pygame.font.SysFont("arial", 72, bold=True)
        self.font_info  = pygame.font.SysFont("arial", 48, bold=True)
        self.font_btn   = pygame.font.SysFont("arial", 32, bold=True)

        centre_x = self.SW // 2
        top = self.SH // 2 + 60

        self.btn_retry = pygame.Rect(centre_x - BTN_W // 2, top, BTN_W, BTN_H)
        self.btn_menu  = pygame.Rect(centre_x - BTN_W // 2, top + BTN_H + BTN_GAP, BTN_W, BTN_H)

        self.t = 0.0

    def update(self, dt, events):
        self.t += dt
        souris = pygame.mouse.get_pos()

        for ev in events:
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                if self.btn_retry.collidepoint(souris):
                    from states.game_state import GameState
                    self.brain.change(GameState(self.brain))
                if self.btn_menu.collidepoint(souris):
                    from states.menu_state import MenuState
                    self.brain.change(MenuState(self.brain))

    def draw(self, surface):
        surface.blit(self.overlay, (0, 0))

        self._draw_title(surface)
        self._draw_score(surface)

        souris = pygame.mouse.get_pos()
        self._draw_button(surface, self.btn_retry, "REJOUER", souris)
        self._draw_button(surface, self.btn_menu,  "MENU", souris)

    def _draw_title(self, surface):
        centre_x = self.SW // 2
        mouvement = math.sin(self.t * 3.0) * 5

        title_str = "WASTED"
        if self.status == "ARRESTED": title_str = "CHOPÉ PAR LES FLICS !"
        elif self.status == "OVERDOSE": title_str = "ÉPUISÉ PAR LE MANQUE..."
        elif self.status == "WASTED": title_str = "TUÉ DANS LE GHETTO..."

        # Ombre
        ombre = self.font_title.render(title_str, True, C_BLACK)
        surface.blit(ombre, ombre.get_rect(centerx=centre_x + 3, centery=TITLE_Y + mouvement + 3))

        # Titre (Rouge pour la mort)
        titre = self.font_title.render(title_str, True, (255, 50, 50))
        surface.blit(titre, titre.get_rect(centerx=centre_x, centery=TITLE_Y + mouvement))

    def _draw_score(self, surface):
        centre_x = self.SW // 2
        txt = f"SCORE : {self.score}"
        score_surf = self.font_info.render(txt, True, C_GOLD)
        surface.blit(score_surf, score_surf.get_rect(center=(centre_x, self.SH // 2 - 20)))

    def _draw_button(self, surface, rect, texte, souris):
        survole = rect.collidepoint(souris)

        pygame.draw.rect(surface, C_BTN_SHADOW, rect.move(3, 4), border_radius=12)
        pygame.draw.rect(surface, C_BTN_HOVER if survole else C_GOLD, rect, border_radius=12)
        pygame.draw.rect(surface, C_GOLD_DARK, rect, width=2, border_radius=12)

        txt = self.font_btn.render(texte, True, C_BLACK)
        surface.blit(txt, txt.get_rect(center=rect.center))

        if survole:
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)
        else:
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)
