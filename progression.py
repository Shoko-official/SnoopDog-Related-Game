import json
import os
import random
from settings import BASE_DIR

FILE_PATH = os.path.join(BASE_DIR, "save_data.json")

QUEST_TEMPLATES = [
    {"id": "weed_collector", "title": "Grossiste", "desc": "Collecte {goal} pochons de weed", "goal_type": "weed", "reward": 100},
    {"id": "distance", "title": "Marathonien", "desc": "Parcours {goal}m dans le ghetto", "goal_type": "dist", "reward": 150},
    {"id": "kill_rats", "title": "Dératiseur", "desc": "Écrase {goal} rats d'égout", "goal_type": "rats", "reward": 120},
    {"id": "kill_birds", "title": "Chasseur urbain", "desc": "Élimine {goal} pigeons/oiseaux", "goal_type": "birds", "reward": 130},
    {"id": "kill_drones", "title": "Cyber-Guerrier", "desc": "Détruis {goal} drones de surveillance", "goal_type": "drones", "reward": 250},
    {"id": "use_shield", "title": "Blindé", "desc": "Utilise {goal} boucliers", "goal_type": "shield", "reward": 80},
    {"id": "use_magnet", "title": "Aimant à fric", "desc": "Active {goal} aimants", "goal_type": "magnet", "reward": 80},
    {"id": "combo", "title": "Stylé", "desc": "Atteins un combo de x{goal}", "goal_type": "combo", "reward": 200},
]

class ProgressionManager:
    def __init__(self):
        self.data = {
            "money": 0,
            "quests": [],
            "stats": {
                "total_dist": 0,
                "total_weed": 0,
                "total_kills": 0
            }
        }
        self.load()
        if not self.data["quests"]:
            self.generate_new_quests()

    def load(self):
        if os.path.exists(FILE_PATH):
            try:
                with open(FILE_PATH, 'r') as f:
                    self.data = json.load(f)
            except:
                pass

    def save(self):
        with open(FILE_PATH, 'w') as f:
            json.dump(self.data, f, indent=4)

    def generate_new_quests(self):
        self.data["quests"] = []
        templates = random.sample(QUEST_TEMPLATES, 3)
        for t in templates:
            # Randomize goals based on type
            goal = 0
            if t["goal_type"] == "weed": goal = random.randint(20, 50)
            elif t["goal_type"] == "dist": goal = random.randint(500, 2000)
            elif t["goal_type"] == "rats": goal = random.randint(5, 15)
            elif t["goal_type"] == "birds": goal = random.randint(5, 10)
            elif t["goal_type"] == "drones": goal = random.randint(2, 5)
            elif t["goal_type"] == "shield": goal = random.randint(3, 8)
            elif t["goal_type"] == "magnet": goal = random.randint(3, 8)
            elif t["goal_type"] == "combo": goal = random.randint(3, 6)

            quest = {
                "id": t["id"],
                "title": t["title"],
                "desc": t["desc"].format(goal=goal),
                "goal": goal,
                "current": 0,
                "reward": t["reward"],
                "goal_type": t["goal_type"],
                "completed": False,
                "claimed": False
            }
            self.data["quests"].append(quest)
        self.save()

    def update_progress(self, run_stats):
        """Met à jour les quêtes avec les stats d'une partie."""
        # run_stats = {"dist": 100, "weed": 5, "rats": 2, ...}
        for q in self.data["quests"]:
            if q["completed"]: continue
            
            val = run_stats.get(q["goal_type"], 0)
            
            if q["id"] == "combo":
                # Pour le combo on prend le max atteint
                if val > q["current"]:
                    q["current"] = val
            else:
                # Pour le reste on cumule
                q["current"] += val
            
            if q["current"] >= q["goal"]:
                q["current"] = q["goal"]
                q["completed"] = True
        self.save()

    def claim_reward(self, quest_index):
        q = self.data["quests"][quest_index]
        if q["completed"] and not q["claimed"]:
            self.data["money"] += q["reward"]
            q["claimed"] = True
            
            # Si toutes les quêtes sont réclamées, on en génère de nouvelles ? 
            # Non, on attend que le joueur les réclame toutes.
            all_claimed = all(quest["claimed"] for quest in self.data["quests"])
            if all_claimed:
                self.generate_new_quests()
            
            self.save()
            return True
        return False

progression = ProgressionManager()
