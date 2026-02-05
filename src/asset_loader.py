import pygame
import os
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
        # On stocke tout ici pour pas recharger 50 fois la même image
        self.cache_img = {}
        self.cache_snd = {}
        self.cache_anim = {}
        self.silent = False # Pour couper les logs d'erreurs

    def fetch_img(self, chemin, alpha=True):
        """ Charge une image et la met en cache. Renvoie un carré rose si ça plante. """
        chemin = str(chemin)
        # On normalise le path pour éviter les galères Windows/Linux
        full_path = os.path.join(str(ASSET_DIR), chemin)
        
        if full_path in self.cache_img:
            return self.cache_img[full_path]
            
        # Si le fichier existe pas, on gagne du temps
        if not os.path.isfile(full_path):
            return self._get_placeholder(full_path)

        try:
            surf = pygame.image.load(full_path)
            # Optimisation indispensable pour pygame
            if alpha:
                surf = surf.convert_alpha()
            else:
                surf = surf.convert()
            
            self.cache_img[full_path] = surf
            return surf
        except Exception as e:
            return self._get_placeholder(full_path)

    def _get_placeholder(self, ref):
        # Juste pour debug sans faire crasher le jeu
        if not self.silent:
            print(f"[Assets] Texture manquante : {ref}")
        
        pink_sq = pygame.Surface((32, 32))
        pink_sq.fill((255, 0, 255))
        return pink_sq

    def fetch_snd(self, chemin):
        if not pygame.mixer.get_init():
            return None # Pas de son, pas de problème
            
        full_path = os.path.join(str(ASSET_DIR), str(chemin))
        
        if full_path in self.cache_snd:
            return self.cache_snd[full_path]

        if os.path.exists(full_path):
            try:
                snd = pygame.mixer.Sound(full_path)
                self.cache_snd[full_path] = snd
                return snd
            except:
                print(f"[Assets] Fichier son corrompu : {full_path}")
        
        return None

    def load_sheet(self, chemin, w, h, count=None, scale=1.0):
        # Clé unique pour le cache d'anim
        uid = f"{chemin}_{w}_{h}_{scale}"
        if uid in self.cache_anim:
            return self.cache_anim[uid]

        source = self.fetch_img(chemin)
        sw, sh = source.get_size()
        
        # Si w est 0 (config foireuse), on évite la division par zéro
        if w < 1: w = 32
        
        # Si pas de count défini, on prend toute la largeur
        total = count if count else (sw // w)
        
        frames = []
        for i in range(int(total)):
            # Calcul de la zone à découper
            x_pos = i * w
            if x_pos + w > sw: break # On sort si ça dépasse
            
            rect = (x_pos, 0, w, min(h, sh))
            try:
                sub = source.subsurface(rect)
                if scale != 1.0:
                    target_size = (int(w * scale), int(h * scale))
                    sub = pygame.transform.scale(sub, target_size)
                frames.append(sub)
            except ValueError:
                continue # Skip les frames buggées
        
        # Sécurité : faut jamais renvoyer une liste vide
        if not frames:
            frames = [source]

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
        base = os.path.join(str(ASSET_DIR), "graphics/characters/boutique")
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

        # Helper local pour charger une anim spécifique
        def _load(name):
            p = f"{target}/{name}"
            # Petite astuce : on check si le fichier existe avant de lancer le loader
            # pour éviter de spammer la console d'erreurs
            real_p = os.path.join(str(ASSET_DIR), p)
            if not os.path.exists(real_p):
                return None
            
            self.silent = True
            res = self.load_sheet(p, 128, 128, scale=scale)
            self.silent = False
            return res

        # On construit le dico d'animations
        # L'ordre est important pour les fallbacks (Dead -> Hurt, Idle -> Run)
        anims = {}
        anims["run"] = _load("Run.png")
        anims["idle"] = _load("Idle.png") or anims["run"]
        anims["walk"] = anims["run"]
        anims["jump"] = _load("Jump.png")
        anims["hurt"] = _load("Hurt.png")
        anims["dead"] = _load("Dead.png") or anims["hurt"]
        
        # Nettoyage des clés vides
        return {k: v for k, v in anims.items() if v}

    def load_player(self, scale=1.0):
        # Attention : import local obligatoire ici pour éviter cycle
        # progression.py importe souvent asset_loader
        try:
            from progression import progression
            skin = progression.state.get("active_skin_set", "default")
        except:
            skin = "default"

        # 1. Skin de base
        if skin == "default":
            pl_assets = ASSETS.get("player", {})
            return {k: self.get_anim("player", k, scale) for k in pl_assets}, 0.15

        # 2. C'est un set complet ?
        sets = ASSETS.get("boutique_sets", {})
        if skin in sets:
            cfg = sets[skin]
            try:
                from progression import progression
                # On prend la variante active ou la première
                var = progression.state.get("active_variant", cfg["variants"][0])
            except:
                var = cfg.get("variants", ["default"])[0]
                
            return self.load_skin_variant(var, scale), (cfg.get("fps", 10) / 60.0)

        # 3. C'est un item isolé ?
        items = ASSETS.get("boutique_items", {})
        if skin in items:
            cfg = items[skin]
            return self.load_skin_variant(cfg.get("var"), scale), (cfg.get("fps", 10) / 60.0)
            
        # Fallback ultime
        return self.load_player(scale) if skin != "default" else ({}, 0.15)

    def load_police(self, scale=1.0):
        # Charge tous les assets définis dans la catégorie police
        pol = ASSETS.get("police", {})
        return {k: self.get_anim("police", k, scale) for k in pol}

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