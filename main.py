#Samuel Esteban Reyes Uribe
import tkinter as tk
import threading, time, random
from juego_model import GameState, JugadorModel, EnemigoModel, PowerUpModel
from juego_view import GameView

#viewmodel y archivo de ejecucion
class GameViewModel:
    def __init__(self, root, width, height):
        self.root = root
        self.WIDTH = width
        self.HEIGHT = height
        self.view = GameView(root, width, height, self)
        self.state = GameState()
        self.jugador = None
        self.enemigos = {}   # id para creacion del diseño en tkinter
        self.powerups = {}   # id para creacion del diseño en tkinter
        self.lock = threading.Lock()

    def start_menu(self):
        # pantalla de menu de inicio
        self.menu = tk.Frame(self.root, bg="#0b3d91")
        self.menu.place(relwidth=1, relheight=1)
        tk.Label(self.menu, text="POOhou", font=("Arial", 32), bg="#0b3d91", fg="white").pack(pady=30)
        tk.Button(self.menu, text="Jugar", font=("Arial", 18), bg="#e33", fg="white", command=self.start_game).pack(pady=8)
        tk.Button(self.menu, text="Salir", font=("Arial", 14), bg="#888", fg="white", command=self.root.quit).pack(pady=8)

    def start_game(self):
        # desactiva el menu
        try: self.menu.destroy()
        except: pass

        # prepara el HUD del juego
        self.view.pack_ui()

        # create jugador model proportionally
        size = max(24, int(self.WIDTH * 0.06))
        vel = max(4, int(self.WIDTH * 0.006))
        x = (self.WIDTH - size)//2
        y = self.HEIGHT - size - 80
        self.jugador = JugadorModel(x, y, size, vel)
        self.state.en_juego = True
        self.state.velocidad_global_factor = 1.0

        # dificultad normal 
        self.state.dificultad = "Normal"
        self.state.tiempo_total = 240
        self.state.vidas = 3

        # mostrar en pantalla al personaje principal
        self.view.draw_jugador(self.jugador)
        self.view.update_status(self.state.vidas, self.state.tiempo_total)

        # asignacion de controles
        self.teclas = set()
        self.root.bind("<KeyPress>", self.key_down)
        self.root.bind("<KeyRelease>", self.key_up)

        # hilos para supervisar que las tareas se completen sin interrumpir las demas
        threading.Thread(target=self.loop_movement, daemon=True).start()
        threading.Thread(target=self.enemy_spawner, daemon=True).start()
        threading.Thread(target=self.powerup_spawner, daemon=True).start()
        threading.Thread(target=self.timer_thread, daemon=True).start()

    # controles
    def key_down(self, e):
        self.teclas.add(e.keysym.lower())

    def key_up(self, e):
        self.teclas.discard(e.keysym.lower())

    def loop_movement(self):
        while self.state.en_juego:
            dx = dy = 0
            if "left" in self.teclas or "a" in self.teclas: dx -= self.jugador.vel
            if "right" in self.teclas or "d" in self.teclas: dx += self.jugador.vel
            if "up" in self.teclas or "w" in self.teclas: dy -= self.jugador.vel
            if "down" in self.teclas or "s" in self.teclas: dy += self.jugador.vel
            if dx != 0 or dy != 0:
                bounds = (0, 0, self.WIDTH - self.jugador.size, self.HEIGHT - self.jugador.size - self.view.TOP_UI)
                self.jugador.mover(dx, dy, bounds)
                self.view.draw_jugador(self.jugador)
            time.sleep(0.02)

    # enemigos
    def enemy_spawner(self):
        counter = 0
        while self.state.en_juego:
            vel = random.randint(3,7)
            size = random.randint(max(18, int(self.WIDTH*0.03)), max(28, int(self.WIDTH*0.07)))
            x = random.randint(0, max(0, self.WIDTH - size))
            tipo = random.choice(["normal", "zigzag", "perseguidor"])
            model = EnemigoModel(x, -size, size, vel, tipo)
            cid = self.view.create_enemy(model)
            self.enemigos[cid] = model
            threading.Thread(target=self.enemy_runner, args=(cid,), daemon=True).start()
            counter += 1
            time.sleep(random.uniform(0.6, 1.2))

    def enemy_runner(self, cid):
        # visualizacion fluida de los enemigos 
        steps = 6
        delay = 0.009
        while self.state.en_juego and cid in self.enemigos:
            model = self.enemigos.get(cid)
            if not model: break
            dy = model.vel/steps
            dx = 0
            if model.tipo == "zigzag":
                if model.x <= 0 or model.x >= self.WIDTH - model.size:
                    model.dx *= -1
                dx = model.dx/steps
            elif model.tipo == "perseguidor":
                target = self.jugador.x + self.jugador.size/2
                my = model.x + model.size/2
                dx = (1 if target>my else -1) * max(1, int(self.WIDTH*0.002)) / steps
            alive = self.view.move_enemy_by(cid, dx, dy)
            model.x += dx
            model.y += dy
            # detectar colision con el jugador
            if self.view.jugador_item and cid in self.view.enemigos:
                bbox_e = self.view.bbox_of(cid)
                bbox_j = self.view.bbox_of(self.view.jugador_item)
                if bbox_e and bbox_j:
                    ex1,ey1,ex2,ey2 = bbox_e
                    jx1,jy1,jx2,jy2 = bbox_j
                    if not (jx2 < ex1 or jx1 > ex2 or jy2 < ey1 or jy1 > ey2):
                        # colision
                        # si el jugador tienes escudo lo anula
                        if not self.jugador.invencible and not self.jugador.tiene_escudo:
                            self.apply_damage()
                        # eliminar enemigo
                        try: self.view.remove_enemy(cid)
                        except: pass
                        if cid in self.enemigos: del self.enemigos[cid]
                        return
            if not alive:
                if cid in self.enemigos: del self.enemigos[cid]
                return
            time.sleep(delay)

    # poderes
    def powerup_spawner(self):
        while self.state.en_juego:
            time.sleep(random.uniform(8, 14))
            size = max(18, int(self.WIDTH*0.04))
            x = random.randint(0, max(0, self.WIDTH - size))
            tipo = random.choice(["slow", "vida_extra", "escudo"])
            model = PowerUpModel(x, -size, size, max(3, int(self.HEIGHT*0.002)), tipo)
            pid = self.view.create_powerup(model)
            self.powerups[pid] = model
            threading.Thread(target=self.powerup_runner, args=(pid,), daemon=True).start()

    def powerup_runner(self, pid):
        while self.state.en_juego and pid in self.powerups:
            model = self.powerups.get(pid)
            alive = self.view.move_powerup(pid, model.vel)
            # verificar colision con el jugador
            if self.view.jugador_item and pid in self.view.powerups:
                bbox_p = self.view.bbox_of(pid)
                bbox_j = self.view.bbox_of(self.view.jugador_item)
                if bbox_p and bbox_j:
                    ex1,ey1,ex2,ey2 = bbox_p
                    jx1,jy1,jx2,jy2 = bbox_j
                    if not (jx2 < ex1 or jx1 > ex2 or jy2 < ey1 or jy1 > ey2):
                        # recoger poder
                        self.collect_powerup(pid, model.tipo)
                        try: self.view.remove_powerup(pid)
                        except: pass
                        if pid in self.powerups: del self.powerups[pid]
                        return
            if not alive:
                if pid in self.powerups: del self.powerups[pid]
                return
            time.sleep(0.03)

    def collect_powerup(self, pid, tipo):
        # aplicar efectos
        if tipo == "slow":
            self.state.velocidad_global_factor = max(0.5, self.state.velocidad_global_factor * 0.7)
            # restauracion de la habilidad
            self.root.after(6000, lambda: setattr(self.state, "velocidad_global_factor", 1.0))
            self.view.show_temp_message("SLOW!", "lightgreen", 900)
        elif tipo == "vida_extra":
            self.state.vidas += 1
            self.view.show_temp_message("VIDA +1", "pink", 900)
            self.view.update_status(self.state.vidas, self.state.tiempo_total)
        elif tipo == "escudo":
            # escudo
            self.jugador.tiene_escudo = True
            self.view.show_temp_message("ESCUDO!", "cyan", 900)
            self.view.show_shield_icon(self.jugador)
            self.root.after(3000, self.remove_shield)

    def remove_shield(self):
        self.jugador.tiene_escudo = False
        self.view.hide_shield_icon()

    # vida y daño
    def apply_damage(self):
        # si tiene escudo ignorar
        if self.jugador.tiene_escudo or self.jugador.invencible:
            return
        self.state.vidas -= 1
        self.view.update_status(self.state.vidas, self.state.tiempo_total)
        #parpadeo en la invulnerabilidad, despues de recibir daño
        self.jugador.invencible = True
        self.view.show_temp_message("-1 VIDA", "white", 700)
        self.root.after(1000, lambda: setattr(self.jugador, "invencible", False))
        if self.state.vidas <= 0:
            self.end_game(False)

    #temporizador
    def timer_thread(self):
        t = self.state.tiempo_total
        while t > 0 and self.state.en_juego:
            self.view.update_status(self.state.vidas, t)
            time.sleep(1)
            t -= 1
        if self.state.en_juego:
            self.end_game(True)

    # fin del juego
    def end_game(self, victory):
        self.state.en_juego = False
        # quitar asignacion de teclas (para evitar problemas en el menu)
        try:
            self.root.unbind("<KeyPress>")
            self.root.unbind("<KeyRelease>")
        except: pass
        # mostrar victoria
        frm = tk.Frame(self.root, bg="#222")
        frm.place(relwidth=1, relheight=1)
        txt = "¡GANASTE!" if victory else "GAME OVER"
        tk.Label(frm, text=txt, font=("Arial", 40), fg="white", bg="#222").pack(pady=30)
        tk.Button(frm, text="Reintentar", command=lambda: (frm.destroy(), self.reset_and_restart())).pack(pady=8)
        tk.Button(frm, text="Menú", command=lambda: (frm.destroy(), self.show_menu())).pack(pady=8)

    def reset_and_restart(self):
        # despejar lo que esta en pantalla
        try: self.view.canvas.delete("all")
        except: pass
        self.enemigos.clear(); self.powerups.clear()
        self.start_game()

    def show_menu(self):
        # despejar y regresar al menu
        try: self.view.canvas.delete("all")
        except: pass
        self.enemigos.clear(); self.powerups.clear()
        self.state.en_juego = False
        self.start_menu()

def main():
    root = tk.Tk()
    # pantalla completa
    root.attributes("-fullscreen", True)
    root.bind("<Escape>", lambda e: root.attributes("-fullscreen", False))
    w = root.winfo_screenwidth(); h = root.winfo_screenheight()
    app = GameViewModel(root, w, h)
    app.start_menu()
    root.mainloop()

if __name__ == "__main__":
    main()
