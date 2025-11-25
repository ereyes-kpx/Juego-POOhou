#samuel esteban reyes uribe

import tkinter as tk
from tkinter import messagebox

#gameview del proyecto

class GameView:
    def __init__(self, root, width, height, vm):
        self.root = root
        self.vm = vm
        self.WIDTH = width
        self.HEIGHT = height
        self.TOP_UI = max(36, int(self.HEIGHT*0.04))

        # widgets
        self.progress = tk.Canvas(root, width=self.WIDTH, height=self.TOP_UI, bg="gray15", highlightthickness=0)
        self.canvas = tk.Canvas(root, width=self.WIDTH, height=self.HEIGHT - self.TOP_UI, bg="black", highlightthickness=0)
        self.status = tk.Label(root, text="", bg="gray15", fg="white", font=("Arial", 12))

        # visuales
        self.jugador_item = None
        self.enemigos = {}   # id -> canvas id
        self.powerups = {}   # id -> (canvas id, tipo)
        self.shield_icon = None

    def pack_ui(self):
        self.progress.pack(side="top", fill="x")
        self.status.place(x=8, y=4)
        self.canvas.pack(side="top", fill="both", expand=True)

    def hide_ui(self):
        try: self.progress.pack_forget()
        except: pass
        try: self.canvas.pack_forget()
        except: pass
        try: self.status.place_forget()
        except: pass

    # visual de jugador

    def draw_jugador(self, model):
        if self.jugador_item is None:
            self.jugador_item = self.canvas.create_rectangle(model.x, model.y, model.x+model.size, model.y+model.size, fill="cyan", tags="jugador")
        else:
            self.canvas.coords(self.jugador_item, model.x, model.y, model.x+model.size, model.y+model.size)
        # para mantener el escudo hasta que se desactive
        if model.tiene_escudo:
            self.show_shield_icon(model)
        else:
            self.hide_shield_icon()

    def show_shield_icon(self, model):
        cx = model.x + model.size/2
        cy = model.y - 18
        if self.shield_icon is None:
            self.shield_icon = self.canvas.create_oval(cx-14, cy-14, cx+14, cy+14, outline="cyan", width=3, tags="shield")
        else:
            self.canvas.coords(self.shield_icon, cx-14, cy-14, cx+14, cy+14)

    def hide_shield_icon(self):
        if self.shield_icon:
            try: self.canvas.delete(self.shield_icon)
            except: pass
            self.shield_icon = None

    # enemigos
    def create_enemy(self, model):
        # escoger forma dependiendo del tipo de enemigo que es
        if model.tipo == "normal":
            cid = self.canvas.create_oval(model.x, model.y, model.x+model.size, model.y+model.size, fill="red")
        elif model.tipo == "perseguidor":
            cid = self.canvas.create_rectangle(model.x, model.y, model.x+model.size, model.y+model.size, fill="blue")
        else:
            pts = (model.x, model.y, model.x+model.size, model.y, model.x+model.size/2, model.y+model.size)
            cid = self.canvas.create_polygon(*pts, fill="purple")
        self.enemigos[cid] = cid
        return cid

    def move_enemy_by(self, cid, dx, dy):
        if cid not in self.enemigos:
            return False
        try:
            self.canvas.move(cid, dx, dy)
            # bbox check and removal if out
            bbox = self.canvas.bbox(cid)
            if bbox and bbox[1] > self.HEIGHT + 100:
                self.canvas.delete(cid)
                del self.enemigos[cid]
                return False
            return True
        except Exception:
            if cid in self.enemigos: del self.enemigos[cid]
            return False

    def remove_enemy(self, cid):
        try:
            self.canvas.delete(cid)
            if cid in self.enemigos: del self.enemigos[cid]
        except: pass

    # power ups
    def create_powerup(self, model):
        pts = (model.x, model.y, model.x+model.size, model.y, model.x+model.size/2, model.y+model.size)
        cid = self.canvas.create_polygon(*pts, fill="lightgreen")
        self.powerups[cid] = (cid, model.tipo)
        return cid

    def move_powerup(self, cid, dy):
        if cid not in self.powerups: return False
        try:
            self.canvas.move(cid, 0, dy)
            bbox = self.canvas.bbox(cid)
            if bbox and bbox[1] > self.HEIGHT + 100:
                self.canvas.delete(cid)
                del self.powerups[cid]
                return False
            return True
        except Exception:
            if cid in self.powerups: del self.powerups[cid]
            return False

    def remove_powerup(self, cid):
        try:
            self.canvas.delete(cid)
            if cid in self.powerups: del self.powerups[cid]
        except: pass

    # cerificar colisiones
    def bbox_of(self, item):
        try:
            return self.canvas.bbox(item)
        except:
            return None

    def update_status(self, vidas, tiempo):
        self.status.config(text=f"Vidas: {vidas}  Tiempo: {tiempo}s")

    # verificar mensajes temporales
    def show_temp_message(self, text, color="white", duration=1000):
        midx = self.WIDTH//2
        midy = self.TOP_UI//2
        msg = self.canvas.create_text(midx, midy, text=text, fill=color, font=("Arial", max(12, int(self.TOP_UI*0.5))))
        self.root.after(duration, lambda: self.canvas.delete(msg))
