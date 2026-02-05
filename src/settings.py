import os
from pathlib import Path
import sys

# Setup crado pour PyInstaller
# Setup crado pour PyInstaller
BASE_DIR = Path(sys._MEIPASS) if getattr(sys, 'frozen', False) else Path(__file__).parent.parent
ASSET_DIR = BASE_DIR / 'assets'

# --- ECRAN & RENDU ---
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FPS = 60
TITLE = "Get What U Need - Bad Trip Edition"

# --- PHYSIQUE ---
# Faut que ça saute bien, pas trop flottant
GRAVITY = 2000 
PLAYER_SPEED = 350 
JUMP_FORCE = -1150 
BOUNCE_FORCE = -600  # Rebond sur les ennemis
FAST_FALL_FORCE = 900  # Boost vers le bas en appuyant flèche bas en l'air
FLOOR_Y = 650 
DEATH_Y = SCREEN_HEIGHT + 200 

# --- GAMEPLAY & BALANCE ---
PLAYER_SCALE = 2.0 
PLAYER_FRAME_W = 32 
PLAYER_FRAME_H = 32

# Difficulté des mobs
RAT_SPEED = 100 
BIRD_SPEED = 120
BIRD_AMPLITUDE = 50

# Gestion du MANQUE (La barre de vie alternative)
WITHDRAWAL_RATE = 0.05 # Vitesse a laquelle ça monte
MAX_WITHDRAWAL = 100
WEED_WITHDRAWAL_REDUCE = 15 # Combien on recup par pochon

# Accélération progressive
SPEED_INCREMENT_RATE = 2.0
MAX_SPEED_BOOST = 300

# Generation procédurale
PLATFORM_HEIGHT = 180 
GAP_SIZE_MIN = 150
GAP_SIZE_MAX = 190 
CHUNK_SIZE = 1280

# --- UI & FONTS ---
# Palette un peu "Street" / Nuit
C_GOLD       = (255, 215,  60)
C_GOLD_DARK  = (180, 140,  20)
C_WHITE_DIM  = (200, 200, 200)
C_BLACK      = ( 0,   0,   0)

# Couleurs Menu
C_RULE_TITLE = (255, 180,  60)
C_RULE_TEXT  = (220, 210, 195)
C_BTN_HOVER  = (255, 240, 120)
C_BTN_SHADOW = ( 80,  50,  10)

# Layout
TITLE_Y = 140
BTN_W, BTN_H = 240, 60
BTN_GAP = 22
PANEL_W, PANEL_H = 850, 600

# HUD positions
HUD_X, HUD_Y = 30, 30
HEART_SIZE = 40
WITHDRAWAL_BAR_WIDTH = 250

# Audio global
MUSIC_VOLUME = 0.2
