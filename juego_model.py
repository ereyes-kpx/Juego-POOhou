#Samuel Esteban Reyes Uribe
import random

class GameState:
    def __init__(self):
        self.dificultad = "Normal"
        self.tiempo_total = 240
        self.vidas = 3
        self.en_juego = False
        self.velocidad_global_factor = 1.0

class JugadorModel:
    def __init__(self, x, y, size, vel):
        self.x = x
        self.y = y
        self.size = size
        self.vel = vel
        self.invencible = False
        self.tiene_escudo = False

    def mover(self, dx, dy, bounds):
        min_x, min_y, max_x, max_y = bounds
        nx = self.x + dx
        ny = self.y + dy
        if nx < min_x: nx = min_x
        if nx > max_x: nx = max_x
        if ny < min_y: ny = min_y
        if ny > max_y: ny = max_y
        self.x, self.y = nx, ny

class EnemigoModel:
    def __init__(self, x, y, size, vel, tipo="normal"):
        self.x = x
        self.y = y
        self.size = size
        self.vel = vel
        self.tipo = tipo
        # movimiento en zigzag
        self.dx = random.choice([-1, 1]) * max(1, size//10)

class PowerUpModel:
    def __init__(self, x, y, size, vel, tipo):
        self.x = x
        self.y = y
        self.size = size
        self.vel = vel
        self.tipo = tipo
