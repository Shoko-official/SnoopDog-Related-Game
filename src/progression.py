# Correction du Merge Conflict
import json
import random
from pathlib import Path
from settings import BASE_DIR

# Sauvegarde
SAVE_FILE = Path(BASE_DIR) / "save_data.json"

# Config des missions (ID, Titre, desc, reward, min/max obj)
QUEST_DEFS = [
    {"id": "weed",   "label": "Grossiste",       "txt": "Collecte {n} pochons",      "rwd": 100, "min": 20,  "max": 50},
    {"id": "dist",   "label": "Marathonien",     "txt": "Parcours {n}m",             "rwd": 150, "min": 500, "max": 2000},
    {"id": "rats",   "label": "Dératiseur",      "txt": "Écrase {n} rats",           "rwd": 120, "min": 5,   "max": 15},
    {"id": "birds",  "label": "Chasseur",        "txt": "Élimine {n} pigeons",       "rwd": 130, "min": 5,   "max": 10},
    {"id": "drones", "label": "Cyber-Guerrier",  "txt": "Détruis {n} drones",        "rwd": 250, "min": 2,   "max": 5},
    {"id": "shield", "label": "Blindé",          "txt": "Utilise {n} boucliers",     "rwd": 80,  "min": 3,   "max": 8},
    {"id": "magnet", "label": "Aimant",          "txt": "Active {n} aimants",        "rwd": 80,  "min": 3,   "max": 8},
    {"id": "combo",  "label": "Stylé",           "txt": "Fais un combo x{n}",        "rwd": 200, "min": 3,   "max": 6},
]

class PlayerProfile:
    # Gère tout ce qui est persistant : thunes, missions, stats
    def __init__(self):
        self.state = {
            "credits": 0,
            "quests": [],
            "unlocked_sets": ["default"],
            "unlocked_items": [],
            "active_skin_set": "default",
            "active_variant": None,
            "stats": {"total_dist": 0, "total_weed": 0, "total_kills": 0},
            "weed_stash": 0
        }
        self.reload()

    def reload(self):
        # On charge ou on init si rien n'existe
        if not SAVE_FILE.exists():
            self._init_quests()
            return

        try:
            text = SAVE_FILE.read_text(encoding="utf-8")
            if not text: return
                
            loaded = json.loads(text)
            
            # ptit fix de compatibilité pour les vieux fichiers
            if "money" in loaded: loaded["credits"] = loaded.pop("money")
            
            # On update proprement sans écraser les nouvelles clés
            # (genre si on a rajouté une stat dans une mise à jour)
            for k, v in loaded.items():
                if k == "stats" and isinstance(v, dict):
                    self.state["stats"].update(v)
                else:
                    self.state[k] = v
                    
            if not self.state["quests"]:
                self._init_quests()
                
        except:
            # Si le fichier est pourri, tant pis on garde les valeurs par défaut
            print("Save corrompue ou illisible, reset")

    def commit(self):
        # Ecriture atomique pour éviter les corruptions si ça crash pendant la save
        temp = SAVE_FILE.with_suffix(".tmp")
        try:
            temp.write_text(json.dumps(self.state, indent=2, ensure_ascii=False), encoding="utf-8")
            temp.replace(SAVE_FILE)
        except OSError:
            if temp.exists(): temp.unlink()

    def get_active_collectible(self):
        # Récupère le type de collectible (et son nom) selon le skin actif
        from assets_registry import ASSETS
        active = self.state.get("active_skin_set", "default")
        c_map = ASSETS.get("collectible_map", {})
        
        key = c_map.get(active)
        if not key:
            key = "weed" 
            for s_name, s_cfg in ASSETS.get("boutique_sets", {}).items():
                if active == s_name or active in s_cfg.get("variants", []):
                    key = c_map.get(s_name, "weed")
                    break
                    
        # Mapping
        names = {
            "weed": "pochons",
            "blood": "fioles de sang",
            "biceps": "protéines",
            "ramen": "bols de ramen",
            "red_cap": "casquettes",
            "ammo_box": "munitions"
        }
        return key, names.get(key, "items")

    def _init_quests(self):
        # On prend 3 missions au pif
        self.state["quests"] = []
        selection = random.sample(QUEST_DEFS, 3)
        
        _, item_name = self.get_active_collectible()
        
        for tpl in selection:
            target = random.randint(tpl["min"], tpl["max"])
            
            txt = tpl["txt"]
            # Si c'est la quête de collecte, on adapte le texte
            if tpl["id"] == "weed":
                 txt = f"Collecte {{n}} {item_name}"
            
            self.state["quests"].append({
                "id": tpl["id"], 
                "title": tpl["label"],
                "desc": txt.format(n=target),
                "goal": target,
                "current": 0,
                "reward": tpl["rwd"],
                "completed": False,
                "claimed": False
            })
        self.commit()

    def update(self, run_data):
        # run_data c'est un dict {'dist': 500, 'weed': 10} etc
        changed = False
        
        # On stocke la weed ramassée
        w = run_data.get("weed", 0)
        if w > 0:
            self.state["weed_stash"] = self.state.get("weed_stash", 0) + w
            # Update stats globales aussi tant qu'à faire
            self.state["stats"]["total_weed"] += w
            self.state["stats"]["total_dist"] += run_data.get("dist", 0)
            changed = True
        
        for q in self.state["quests"]:
            if q["completed"]: continue
                
            val = run_data.get(q["id"], 0)
            if val <= 0: continue
                
            changed = True
            
            if q["id"] == "combo":
                # Le combo c'est un "max atteint", pas un cumul
                if val > q["current"]: q["current"] = val
            else:
                q["current"] += val
                
            if q["current"] >= q["goal"]:
                q["current"] = q["goal"]
                q["completed"] = True
                
        if changed: self.commit()

    def claim(self, index):
        # Récup moula
        try:
            q = self.state["quests"][index]
        except IndexError: return False

        if q["completed"] and not q["claimed"]:
            self.state["credits"] += q["reward"]
            q["claimed"] = True
            
            # Si tout est fini, on relance la machine à missions ?
            # Allez, soyons généreux, on refresh direct
            if all(x["claimed"] for x in self.state["quests"]):
                self._init_quests()
            else:
                self.commit()
            return True
            
        return False

# Instance unique
progression = PlayerProfile()
