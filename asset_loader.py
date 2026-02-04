
import pygame
import os
from settings import ASSET_DIR
from assets_registry import ASSETS

class AssetLoader:
    def __init__(self):
        # caches pour les ressources
        self.images = {}
        self.sounds = {}
        self.anims = {}

    def fetch_img(self, path, alpha=True):
        # resolution chemin asset
        full_p = os.path.join(ASSET_DIR, path)
        
        if full_p not in self.images:
            try:
                s = pygame.image.load(full_p)
                if alpha:
                    self.images[full_p] = s.convert_alpha()
                else:
                    self.images[full_p] = s.convert()
            except Exception as e:
                print(f"FAILED LOADING IMG: {full_p} -> {e}")
                pygame.quit()
                import sys; sys.exit()
        return self.images[full_p]

    def fetch_snd(self, path):
        full_p = os.path.join(ASSET_DIR, path)
        if full_p not in self.sounds:
            try:
                self.sounds[full_p] = pygame.mixer.Sound(full_p)
            except:
                print(f"Son pas là: {full_p}")
                return None
        return self.sounds[full_p]

    def load_sheet(self, path, w, h, c=None, scale=1.0):
        # cache pour les sequences de sprites
        tag = f"{path}_{w}x{h}_{scale}"
        if tag in self.anims:
            return self.anims[tag]

        sheet = self.fetch_img(path)
        sw, sh = sheet.get_size()
        
        if c is None:
            c = sw // w
            
        frames = []
        for i in range(c):
            # petite box de decoupe
            box = (i * w, 0, w, min(h, sh))
            try:
                frm = sheet.subsurface(box)
                if scale != 1.0:
                    frm = pygame.transform.scale(frm, (int(w*scale), int(h*scale)))
                frames.append(frm)
            except:
                continue
        
        self.anims[tag] = frames
        return frames

    def get_anim(self, cat, sub, scale=1.0):
        cfg = ASSETS[cat][sub]
        return self.load_sheet(cfg['p'], cfg['w'], cfg['h'], cfg['c'], scale)

    def load_player(self, scale=1.0):
        return {k: self.get_anim("player", k, scale) for k in ASSETS["player"]}

    def load_police(self, scale=1.0):
        return {k: self.get_anim("police", k, scale) for k in ASSETS["police"]}

    def load_drone(self, model, scale=1.0):
        m = str(model)
        return {
            act: self.load_sheet(v['p'], v['w'], v['h'], v['c'], scale) 
            for act, v in ASSETS["drones"][m].items()
        }

    def clear(self):
        self.images.clear()
        self.sounds.clear()
        self.anims.clear()

# Instance unique
asset_loader = AssetLoader()

# raccourcis pour les faineants
fetch_image = asset_loader.fetch_img
get_animation = asset_loader.get_anim