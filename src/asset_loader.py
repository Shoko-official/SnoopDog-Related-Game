import pygame
import os
from pathlib import Path
# Fusionné avec le code de Shoko (A)
# Gestion des imports un peu fragile si le dossier est pas propre
try:
    from settings import ASSET_DIR
except ImportError:
    print("Warning: settings.py introuvable, on utilise le dossier courant.")
    ASSET_DIR = "."

try:
    from assets_registry import ASSETS
except ImportError:
    # Fallback pour éviter le crash direct si le registre manque
    ASSETS = {
        "player": {}, "boutique_sets": {}, "boutique_items": {}, 
        "police": {}, "drones": {}, "audio": {"sfx": {}}
    }


class AssetLoader:
    def __init__(self):
        # Le cache pour pas tout charger en boucle
        self.cache_img, self.cache_snd, self.cache_anim = {}, {}, {}
        self.silent = False

    def fetch_img(self, chemin, alpha=True):
        # On passe par Path pour pas s'embêter avec les slashs/backslashs
        p_ch = Path(chemin)
        full_path = ASSET_DIR / p_ch
        s_path = str(full_path.absolute())
        
        if s_path in self.cache_img: return self.cache_img[s_path]
            
        if not full_path.exists(): return self._get_placeholder(s_path)

        try:
            surf = pygame.image.load(s_path)
            # On optimise seulement si l'écran est lancé
            if pygame.display.get_init() and pygame.display.get_surface():
                surf = surf.convert_alpha() if alpha else surf.convert()
            
            self.cache_img[s_path] = surf
            return surf
        except:
            return self._get_placeholder(s_path)

    def _get_placeholder(self, ref):
        # Texture manquante -> on met un carré rose pour alerter
        if not self.silent: print(f"[Assets] Erreur texture : {ref}")
        pink = pygame.Surface((32, 32))
        pink.fill((255, 0, 255))
        return pink

    def fetch_snd(self, chemin):
        if not pygame.mixer.get_init(): return None
            
        full_path = ASSET_DIR / Path(chemin)
        s_path = str(full_path.absolute())
        
        if s_path in self.cache_snd: return self.cache_snd[s_path]

        if full_path.exists():
            try:
                snd = pygame.mixer.Sound(s_path)
                self.cache_snd[s_path] = snd
                return snd
            except:
                print(f"[Assets] Son pété : {s_path}")
        return None

    def load_sheet(self, chemin, w, h, count=None, scale=1.0):
        # Cache d'anim via une clé unique
        uid = f"{chemin}_{w}_{h}_{scale}"
        if uid in self.cache_anim: return self.cache_anim[uid]

        src = self.fetch_img(chemin)
        sw, sh = src.get_size()
        
        if w < 1: w = 32
        nb = count if count else (sw // w)
        
        frames = []
        for i in range(int(nb)):
            x = i * w
            if x + w > sw: break
            
            try:
                sub = src.subsurface((x, 0, w, min(h, sh)))
                if scale != 1.0:
                    sub = pygame.transform.scale(sub, (int(w * scale), int(h * scale)))
                frames.append(sub)
            except: continue
        
        if not frames: frames = [src]
        self.cache_anim[uid] = frames
        return frames

    def get_anim(self, cat, key, scale=1.0):
        # Récup data depuis le registre global
        data = ASSETS.get(cat, {}).get(key)
        if not data:
            return [self._get_placeholder(f"{cat}/{key}")]
            
        return self.load_sheet(
            data.get('p', ''), 
            data.get('w', 32), 
            data.get('h', 32), 
            data.get('c'), 
            scale
        )

    def load_skin_variant(self, variant, scale=1.0):
        # Petit hack pour le set par défaut
        if variant == "default" or variant == "player":
             pl = ASSETS.get("player", {})
             return {k: self.get_anim("player", k, scale) for k in pl}

        # Logique un peu compliquée pour trouver le dossier du skin
        base = os.path.normpath(os.path.join(str(ASSET_DIR), "graphics/characters/boutique"))
        target = None
        
        # On check d'abord si c'est un dossier direct
        direct = os.path.join(base, variant)
        if os.path.isdir(direct):
            target = f"graphics/characters/boutique/{variant}"
        else:
            # Sinon on cherche dans les sous-dossiers (les sets)
            if os.path.isdir(base):
                for d in os.listdir(base):
                    sub = os.path.join(base, d)
                    if os.path.isdir(sub) and variant in os.listdir(sub):
                        target = f"graphics/characters/boutique/{d}/{variant}"
                        break
        
        # Si on a rien trouvé, on tente le chemin "naïf"
        if not target:
            target = f"graphics/characters/boutique/{variant}"

        # Helper local pour charger une anim par fichier
        def _load(name):
            p = f"{target}/{name}"
            # On vérifie sur le disque avant pour pas spammer de logs
            if not os.path.exists(os.path.normpath(os.path.join(str(ASSET_DIR), p))):
                return None
            
            self.silent = True
            res = self.load_sheet(p, 128, 128, scale=scale)
            self.silent = False
            return res

        # On fait le dico dans l'ordre de priorité (Idle -> Run si manque)
        anims = {}
        anims["run"] = _load("Run.png")
        anims["idle"] = _load("Idle.png") or anims["run"]
        anims["walk"] = anims["run"]
        anims["jump"] = _load("Jump.png")
        anims["hurt"] = _load("Hurt.png")
        anims["dead"] = _load("Dead.png") or anims["hurt"]
        
        return {k: v for k, v in anims.items() if v}

    def load_player(self, scale=1.0):
        # Import local pour pas faire de boucle d'imports
        try:
            from progression import progression
            sk = progression.state.get("active_skin_set", "default")
        except:
            sk = "default"

        # 1. Skin d'origine
        if sk == "default":
            pl = ASSETS.get("player", {})
            return {k: self.get_anim("player", k, scale) for k in pl}, 0.15

        # 2. Set de la boutique
        sets = ASSETS.get("boutique_sets", {})
        if sk in sets:
            cfg = sets[sk]
            try:
                from progression import progression
                # On check la variante choisie
                v = progression.state.get("active_variant", cfg["variants"][0])
            except:
                v = cfg.get("variants", ["default"])[0]
                
            return self.load_skin_variant(v, scale), (cfg.get("fps", 10) / 60.0)

        # 3. Juste un item
        it = ASSETS.get("boutique_items", {})
        if sk in it:
            cfg = it[sk]
            return self.load_skin_variant(cfg.get("var"), scale), (cfg.get("fps", 10) / 60.0)
            
        # Fallback au cas où
        return self.load_player(scale) if sk != "default" else ({}, 0.15)

    def load_police(self, scale=1.0):
        # Charge tout ce qui est étiqueté police
        pols = ASSETS.get("police", {})
        return {k: self.get_anim("police", k, scale) for k in pols}

    def load_drone(self, model, scale=1.0):
        # Les drones sont définis par modèle dans le registre
        mdl = str(model)
        drones = ASSETS.get("drones", {})
        
        if mdl not in drones:
            return {}
            
        res = {}
        for action, data in drones[mdl].items():
            res[action] = self.load_sheet(
                data['p'], data['w'], data['h'], data.get('c'), scale
            )
        return res

    def play_sfx(self, nom, vol=1.0):
        try:
            path = ASSETS["audio"]["sfx"].get(nom)
            if path:
                s = self.fetch_snd(path)
                if s:
                    s.set_volume(vol)
                    s.play()
        except KeyError:
            pass # Clé audio manquante, pas grave

    def clear(self):
        # Vide tout, utile pour le changement de niveau
        self.cache_img.clear()
        self.cache_snd.clear()
        self.cache_anim.clear()

# Singleton accessible partout
asset_loader = AssetLoader()

# Alias pour compatibilité avec le reste du code
fetch_image = asset_loader.fetch_img
play_sfx = asset_loader.play_sfx