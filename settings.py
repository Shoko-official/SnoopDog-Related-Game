import os
from pathlib import Path
import sys

# Gestion du chemin racine pour la compatibilité PyInstaller/exécutable
if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys._MEIPASS)
else:
    BASE_DIR = Path(__file__).parent

ASSET_DIR = BASE_DIR / 'assets'

# Paramètres d'affichage
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FPS = 60
TITLE = "Get My Weed - Bad Trip Edition"

# Palette de couleurs UI
C_GOLD       = (255, 215,  60)
C_GOLD_DARK  = (180, 140,  20)
C_WHITE_DIM  = (200, 200, 200)
C_BLACK      = ( 0,   0,   0)
C_RULE_TITLE = (255, 180,  60)
C_RULE_TEXT  = (220, 210, 195)
C_BTN_HOVER  = (255, 240, 120)
C_BTN_SHADOW = ( 80,  50,  10)

TITLE_Y      = 140
BTN_W        = 240
BTN_H        = 60
BTN_GAP      = 22
PANEL_W      = 700
PANEL_H      = 600

# Interface utilisateur (HUD)
HUD_X = 30
HUD_Y = 30
HEART_SIZE = 40
WITHDRAWAL_BAR_WIDTH = 250

# Constantes physiques et cinématiques
GRAVITY = 2000 
PLAYER_SPEED = 350 
JUMP_FORCE = -1150 
BOUNCE_FORCE = -600 
FLOOR_Y = 650 
DEATH_Y = SCREEN_HEIGHT + 200 

# Dimensions et mise à l'échelle du joueur
PLAYER_SCALE = 2.0 
PLAYER_FRAME_WIDTH = 32 
PLAYER_FRAME_HEIGHT = 32

# Paramètres des entités ennemies
RAT_SPEED = 100 
BIRD_SPEED = 120
BIRD_AMPLITUDE = 50

# Audio
MUSIC_VOLUME = 0.2

# Logique de sevrage et mécaniques de jeu
WITHDRAWAL_RATE = 0.05
MAX_WITHDRAWAL = 100
WEED_WITHDRAWAL_REDUCE = 15 

SPEED_INCREMENT_RATE = 2.0
MAX_SPEED_BOOST = 300

# Génération procédurale de segments (chunks)
PLATFORM_HEIGHT = 180 
GAP_SIZE_MIN = 150
GAP_SIZE_MAX = 190 
CHUNK_SIZE = 1280