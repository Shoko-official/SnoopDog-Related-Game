import pygame

class State:
    """
    Classe abstraite de base pour les modules du jeu
    """
    def __init__(self, brain):
        self.brain = brain

    def update(self, dt, events):
        pass

    def draw(self, surface):
        pass

class StateStack:
    def __init__(self):
        self.now = None

    def change(self, next_state):
        self.now = next_state

    def update(self, dt, events):
        if self.now:
            self.now.update(dt, events)

    def draw(self, surface):
        if self.now:
            self.now.draw(surface)
