
import pygame
import sys
from settings import SCREEN_WIDTH, SCREEN_HEIGHT, TITLE, FPS, ASSET_DIR
from state_machine import StateStack
from states.game_state import GameState
from states.menu_state import MenuState
from asset_loader import asset_loader

class Game:
    def __init__(self):
        # On initialise tout le bazar de Pygame
        pygame.init()
        
        # ICONE DU JEU (Weed)
        try:
            icon_path = ASSET_DIR / "graphics/items/weed.png"
            icon = pygame.image.load(icon_path)
            pygame.display.set_icon(icon)
        except Exception as e:
            print(f"Impossible de charger l'icône : {e}")
        
        # On définit l'écran en premier
        self.fullscreen = False
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption(TITLE)
        
        # Le son !!!
        pygame.mixer.init() 

        # Lancer la musique dès le démarrage
        self.init_music()
        
        self.clock = pygame.time.Clock()
        self.running = True
        
        # Pile d'états (menu, jeu, etc)
        self.brain = StateStack()
        self.brain.change(MenuState(self.brain))
        
    def run(self):
        # La boucle infinie du jeu
        while self.running:
            # dt (delta time) pour que le jeu tourne à la même vitesse partout
            dt = self.clock.tick(FPS) / 1000.0
            
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    self.running = False
                    
                # F11 pour toggle fullscreen
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_F11:
                        self.toggle_fullscreen()
                        
            # Mise à jour et dessin de l'état actuel
            self.brain.update(dt, events)
            
            self.screen.fill((12, 12, 18)) # Un poil moins noir
            self.brain.draw(self.screen)
            
            pygame.display.flip()
            
        self.quit()

    def init_music(self):
        # Lance la musique de fond dès le démarrage
        try:
            if not pygame.mixer.get_init():
                return

            from assets_registry import ASSETS
            from progression import progression

            music_path = ASSET_DIR / ASSETS["audio"]["music_bg"]
            pygame.mixer.music.load(str(music_path))

            # Applique le volume sauvegardé
            vol = progression.state.get("volume_music", 0.2)
            pygame.mixer.music.set_volume(vol)

            # Joue en boucle infinie
            pygame.mixer.music.play(-1)
        except Exception as e:
            print(f"Impossible de charger la musique : {e}")
    
    def toggle_fullscreen(self):
        # Bascule entre plein écran et mode fenêtré
        self.fullscreen = not self.fullscreen
        if self.fullscreen:
            self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)
        else:
            self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    
    def quit(self):
        # On nettoie tout avant de se barrer
        asset_loader.clear()
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    jeu = Game()
    jeu.run()
