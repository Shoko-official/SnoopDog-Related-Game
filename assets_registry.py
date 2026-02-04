
# TODO: ajouter les sfx
CHR_DIR = "graphics/characters"
ENV_DIR = "graphics/environment"

ASSETS = {
    "player": {
        "idle": {"p": f"{CHR_DIR}/player/idle.png", "w": 128, "h": 128, "c": 11},
        "run":  {"p": f"{CHR_DIR}/player/run.png",  "w": 128, "h": 128, "c": 8},
        "walk": {"p": f"{CHR_DIR}/player/run.png",  "w": 128, "h": 128, "c": 8},
        "jump": {"p": f"{CHR_DIR}/player/jump.png", "w": 128, "h": 128, "c": 16},
        "hurt": {"p": f"{CHR_DIR}/player/hurt.png", "w": 128, "h": 128, "c": 3},
        "dead": {"p": f"{CHR_DIR}/player/dead.png", "w": 128, "h": 128, "c": 4},
    },
    
    "police": {
        "idle":   {"p": f"{CHR_DIR}/police/idle.png",   "w": 128, "h": 128, "c": 11},
        "run":    {"p": f"{CHR_DIR}/police/run.png",    "w": 128, "h": 128, "c": 10},
        "walk":   {"p": f"{CHR_DIR}/police/walk.png",   "w": 128, "h": 128, "c": 10},
        "jump":   {"p": f"{CHR_DIR}/police/jump.png",   "w": 128, "h": 128, "c": 10},
        "attack": {"p": f"{CHR_DIR}/police/attack.png", "w": 128, "h": 128, "c": 3},
        "dead":   {"p": f"{CHR_DIR}/police/dead.png",   "w": 128, "h": 128, "c": 5},
    },
    
    "environment": {
        "backgrounds": {
            "ville": {
                "1": f"{ENV_DIR}/background/ville/1.png", "2": f"{ENV_DIR}/background/ville/2.png",
                "3": f"{ENV_DIR}/background/ville/3.png", "4": f"{ENV_DIR}/background/ville/4.png",
                "5": f"{ENV_DIR}/background/ville/5.png",
            },
            "foret": {
                "1": f"{ENV_DIR}/background/forêt/1.png", "2": f"{ENV_DIR}/background/forêt/2.png",
                "3": f"{ENV_DIR}/background/forêt/3.png", "4": f"{ENV_DIR}/background/forêt/4.png",
                "5": f"{ENV_DIR}/background/forêt/5.png",
            }
        },
        "ground": f"{ENV_DIR}/props/ground.png",
        "ground_street": f"{ENV_DIR}/props/ground.png",
        "ground_park": f"{ENV_DIR}/props/ground_park.png", 
        "ground_rooftop": f"{ENV_DIR}/props/toit.png",
        "ground_forest": f"{ENV_DIR}/props/ground_park.png",
    },

    "items": {
        "weed": "graphics/items/weed.png", 
        "heart": "graphics/items/heart.png",
        "magnet": "graphics/items/magnet.png",
        "shield": "graphics/items/shield.png",
    },

    "bird": {
        "walk":  {"p": f"{ENV_DIR}/mobs/bird/walk.png",  "w": 32, "h": 32, "c": 6},
        "death": {"p": f"{ENV_DIR}/mobs/bird/death.png", "w": 32, "h": 32, "c": 4},
        "idle":  {"p": f"{ENV_DIR}/mobs/bird/idle.png",  "w": 32, "h": 32, "c": 4},
    },

    "rat": {
        "walk":  {"p": f"{ENV_DIR}/mobs/rat/walk.png",  "w": 32, "h": 32, "c": 4},
        "death": {"p": f"{ENV_DIR}/mobs/rat/death.png", "w": 32, "h": 32, "c": 4},
        "idle":  {"p": f"{ENV_DIR}/mobs/rat/idle.png",  "w": 32, "h": 32, "c": 4},
    },

    "loup": {
        "walk":  {"p": f"{ENV_DIR}/mobs/loup/run.png",  "w": 80, "h": 80, "c": 6}, 
        "run":   {"p": f"{ENV_DIR}/mobs/loup/run.png",  "w": 80, "h": 80, "c": 6},
        "idle":  {"p": f"{ENV_DIR}/mobs/loup/loup.png", "w": 80, "h": 80, "c": 4},
        "death": {"p": f"{ENV_DIR}/mobs/loup/loup.png", "w": 80, "h": 80, "c": 4},
    },

    "ours": {
        "walk":  {"p": f"{ENV_DIR}/mobs/ours/run.png",  "w": 80, "h": 80, "c": 6},
        "run":   {"p": f"{ENV_DIR}/mobs/ours/run.png",  "w": 80, "h": 80, "c": 6},
        "idle":  {"p": f"{ENV_DIR}/mobs/ours/run.png",  "w": 80, "h": 80, "c": 6}, 
        "death": {"p": f"{ENV_DIR}/mobs/ours/dead.png", "w": 80, "h": 80, "c": 4},
    },
    
    "drones": {
        "1": {
            "idle":  {"p": f"{ENV_DIR}/mobs/drone/1/Idle.png",  "w": 48, "h": 48, "c": 4},
            "walk":  {"p": f"{ENV_DIR}/mobs/drone/1/Walk.png",  "w": 48, "h": 48, "c": 4},
            "scan":  {"p": f"{ENV_DIR}/mobs/drone/1/Scan.png",  "w": 48, "h": 48, "c": 4},
            "death": {"p": f"{ENV_DIR}/mobs/drone/1/Death.png", "w": 48, "h": 48, "c": 4},
        },
        "2": {
            "idle": {"p": f"{ENV_DIR}/mobs/drone/2/Drop.png", "w": 96, "h": 96, "c": 6},
            "walk": {"p": f"{ENV_DIR}/mobs/drone/2/Drop.png", "w": 96, "h": 96, "c": 6},
            "bomb": {"p": f"{ENV_DIR}/mobs/drone/2/Bomb.png", "w": 96, "h": 16, "c": 6},
        },
        "3": {
            "idle":  {"p": f"{ENV_DIR}/mobs/drone/3/Idle.png",    "w": 48, "h": 48, "c": 4},
            "walk":  {"p": f"{ENV_DIR}/mobs/drone/3/Forward.png", "w": 48, "h": 48, "c": 4},
            "back":  {"p": f"{ENV_DIR}/mobs/drone/3/Back.png",    "w": 48, "h": 48, "c": 4},
            "death": {"p": f"{ENV_DIR}/mobs/drone/3/Death.png",   "w": 48, "h": 48, "c": 4},
        },
        "4": {
            "idle":  {"p": f"{ENV_DIR}/mobs/drone/4/Idle.png",  "w": 96, "h": 96, "c": 4},
            "walk":  {"p": f"{ENV_DIR}/mobs/drone/4/Walk.png",  "w": 96, "h": 96, "c": 4},
            "death": {"p": f"{ENV_DIR}/mobs/drone/4/Death.png", "w": 96, "h": 96, "c": 4},
        },
        "5": {
            "idle":  {"p": f"{ENV_DIR}/mobs/drone/5/Idle.png",  "w": 72, "h": 72, "c": 4},
            "walk":  {"p": f"{ENV_DIR}/mobs/drone/5/Walk.png",  "w": 72, "h": 72, "c": 4},
            "death": {"p": f"{ENV_DIR}/mobs/drone/5/Death.png", "w": 72, "h": 72, "c": 4},
        },
        "6": {
            "idle":    {"p": f"{ENV_DIR}/mobs/drone/6/Walk.png",    "w": 48, "h": 48, "c": 4},
            "walk":    {"p": f"{ENV_DIR}/mobs/drone/6/Walk.png",    "w": 48, "h": 48, "c": 4},
            "drop":    {"p": f"{ENV_DIR}/mobs/drone/6/Drop.png",    "w": 48, "h": 48, "c": 4},
            "capsule": {"p": f"{ENV_DIR}/mobs/drone/6/Capsule.png", "w": 48, "h": 48, "c": 4},
        }
    },

    "decorations": {
        "sheet": f"{ENV_DIR}/props/Decoration.png",
        "trash": {
            "sac_poubelle":  {"x": 0,   "y": 0, "w": 80, "h": 80},
            "sacs_poubelle": {"x": 80,  "y": 0, "w": 80, "h": 80},
            "poubelle":      {"x": 160, "y": 0, "w": 80, "h": 80},
            "benne_rouge":   {"x": 240, "y": 0, "w": 80, "h": 80},
        },
        "poles": {
            "feu_poteau":          {"x": 320, "y": 0, "w": 80, "h": 320},
            "feu_poteau_vertical": {"x": 400, "y": 0, "w": 80, "h": 320},
            "lampadaire":          {"x": 480, "y": 0, "w": 80, "h": 320},
            "poteau":              {"x": 560, "y": 0, "w": 80, "h": 320}
        },
        "signs": {
            "sens_interdit":             {"x": 0,   "y": 80,  "w": 80, "h": 80},
            "interdiction":              {"x": 80,  "y": 80,  "w": 80, "h": 80},
            "panneau_stop":              {"x": 160, "y": 80,  "w": 80, "h": 80},
            "stationnement_interdit":    {"x": 240, "y": 80,  "w": 80, "h": 80},
            "triangle_inverse":          {"x": 0,   "y": 160, "w": 80, "h": 80},
            "danger_ecole":              {"x": 80,  "y": 160, "w": 80, "h": 80},
            "cedez_le_passage":          {"x": 160, "y": 160, "w": 80, "h": 80},
            "danger_general":            {"x": 240, "y": 160, "w": 80, "h": 80},
            "obligation_tout_droit":     {"x": 0,   "y": 240, "w": 80, "h": 80},
            "obligation_tourner_droite": {"x": 80,  "y": 240, "w": 80, "h": 80},
            "panneau_parking":           {"x": 160, "y": 240, "w": 80, "h": 80},
        }
    },
    
    "forest_props": {
        "bush": f"{ENV_DIR}/props/items/bush.png",
        "log": f"{ENV_DIR}/props/items/log.png",
        "rock": f"{ENV_DIR}/props/items/rock.png",
    },

    "audio": {
        "music_bg": "audio/music/background_music.wav"
    }
}