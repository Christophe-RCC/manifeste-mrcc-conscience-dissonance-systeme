import matplotlib.pyplot as plt
import matplotlib.animation as animation
import random
import math

# --- CONFIGURATION ---
WIDTH, HEIGHT = 10, 10
AGENT_RADIUS = 0.25
FRICTION = 0.94
MAX_SPEED = 0.12
FORCE_STEERING = 0.05

# Paramètres de détection (Perception limitée pour éviter l'omniscience)
DETECTION_RADIUS = 2.5  # Réduit pour forcer une réaction plus rapide (plus "humain")
PANIC_RADIUS = 0.8      # Zone de panique très proche
MAX_REPULSION = 0.12

# Espacement des obstacles
MIN_SPAWN_GAP = 20
MAX_SPAWN_GAP = 60
BASE_SPEED = 0.08

# Couleurs
COLOR_BG = '#151520'
COLOR_TRACK = '#1a2520'
COLOR_OBSTACLE = '#00ffaa'
COLOR_AGENT = '#00ffaa'
COLOR_TEXT = '#ffffff'

# Initialisation
fig, ax = plt.subplots(figsize=(10, 10))
ax.set_xlim(0, 10)
ax.set_ylim(0, 10)
ax.set_aspect('equal')
ax.set_facecolor(COLOR_BG)
ax.grid(False)
ax.set_xticks([])
ax.set_yticks([])
ax.set_title("MRCC : Perception Limitée et Apprentissage de la Friction", color=COLOR_TEXT, fontsize=16, pad=20)

# Variables globales
agent = None
obstacles = []
frame_count = 0
paused = False
last_spawn_frame = -MAX_SPAWN_GAP

class Obstacle:
    def __init__(self, x_center):
        self.w = random.uniform(1.0, 2.0)
        self.h = 0.4
        min_x = x_center - 1.8 + self.w/2
        max_x = x_center + 1.8 - self.w/2
        self.x = random.uniform(min_x, max_x) if min_x < max_x else x_center
        
        self.y = -0.5
        self.speed = BASE_SPEED
        self.color = COLOR_OBSTACLE
        self.rect = None
        self.passed = False

    def update(self):
        self.y += self.speed

class Agent:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.vx = 0.0
        self.dissonance = 0.0
        self.score = 0
        self.anticipation = 0.0
        self.target_x = x
        self.circle = None
        self.line = None
        self.text = None
        self.history_x = [x]
        self.history_y = [y]
        self.safety_margin = 0.35

    def get_track_bounds(self):
        return 3.0, 7.0

    def move(self, obstacles):
        left_bound, right_bound = self.get_track_bounds()
        center_x = 5.0

        # 1. Champ de Force Prédictif (Perception)
        total_repulsion_x = 0.0
        max_dissonance_local = 0.0

        for obs in obstacles:
            if obs.y < self.y and obs.y > self.y - DETECTION_RADIUS:
                dx = obs.x - self.x
                dy = obs.y - self.y
                dist = math.hypot(dx, dy)

                if dist < DETECTION_RADIUS and dist > 0:
                    # Calcul de la force de répulsion (Loi exponentielle)
                    # Plus on est proche, plus la force augmente vite
                    ratio = (DETECTION_RADIUS - dist) / (DETECTION_RADIUS - PANIC_RADIUS)
                    if ratio < 0: ratio = 0
                    
                    repulsion = MAX_REPULSION * (ratio ** 2.5) # Exponentielle plus forte pour réactivité
                    
                    # Direction opposée à l'obstacle
                    force_x = -dx / dist * repulsion
                    total_repulsion_x += force_x
                    
                    # Mise à jour de la dissonance
                    local_d = repulsion * 8
                    if local_d > max_dissonance_local:
                        max_dissonance_local = local_d

        # 2. Calcul de la cible (Minimisation de l'énergie)
        # La cible est le centre, poussé par la répulsion
        target_x = center_x + (total_repulsion_x * 60)
        
        # Limites
        target_x = max(left_bound + self.safety_margin, min(right_bound - self.safety_margin, target_x))

        # 3. Physique et Apprentissage (Anticipation)
        force = (target_x - self.x) * FORCE_STEERING
        
        # Si dissonance élevée, on ralentit pour stabiliser
        if max_dissonance_local > 1.0:
            current_max_speed = MAX_SPEED * 0.6
        else:
            current_max_speed = MAX_SPEED

        self.vx += force
        self.vx *= FRICTION
        
        if self.vx > current_max_speed: self.vx = current_max_speed
        if self.vx < -current_max_speed: self.vx = -current_max_speed
        
        self.x += self.vx

        # Contraintes
        if self.x < left_bound + self.safety_margin:
            self.x = left_bound + self.safety_margin
            self.vx *= -0.5
        elif self.x > right_bound - self.safety_margin:
            self.x = right_bound - self.safety_margin
            self.vx *= -0.5

        # Mise à jour de la dissonance globale (lissage)
        self.dissonance = max(0, max_dissonance_local - 0.03)

        # --- LOGIQUE D'APPRENTISSAGE (Anticipation) ---
        # L'anticipation augmente si le système est fluide (faible dissonance) et qu'il a réussi à éviter
        # Elle diminue si le système est en panique
        if self.dissonance < 0.4:
            self.anticipation = min(0.9, self.anticipation + 0.005) # Apprentissage lent
        else:
            self.anticipation = max(0.0, self.anticipation - 0.01) # Perte d'assurance en cas de danger

    def update_history(self):
        self.history_x.append(self.x)
        self.history_y.append(self.y)
        if len(self.history_x) > 100:
            self.history_x.pop(0)
            self.history_y.pop(0)

def init():
    global agent, obstacles, frame_count, last_spawn_frame
    frame_count = 0
    last_spawn_frame = -MAX_SPAWN_GAP
    obstacles = []
    
    agent = Agent(5.0, 8.0)
    
    agent.circle = plt.Circle((agent.x, agent.y), AGENT_RADIUS, color=COLOR_AGENT, zorder=10, ec='white', lw=0.5)
    ax.add_patch(agent.circle)
    agent.line, = ax.plot([], [], color=COLOR_AGENT, alpha=0.4, linewidth=2, zorder=9)
    agent.text = ax.text(agent.x, agent.y + 0.5, "", color=COLOR_TEXT, fontsize=10, ha='center', fontweight='bold', zorder=11)

    # Piste
    ax.add_patch(plt.Rectangle((3.0, 0), 4.0, 10.0, color=COLOR_TRACK, alpha=0.6, zorder=1))
    ax.plot([3.0, 3.0], [0, 10], color='#445', linewidth=1, zorder=0)
    ax.plot([7.0, 7.0], [0, 10], color='#445', linewidth=1, zorder=0)
    ax.plot([5.0, 5.0], [0, 10], color='#333', linewidth=0.5, linestyle='--', zorder=0)

    ax.text(5, 0.5, "ESPACE: Pause | R: Reset", color=COLOR_TEXT, fontsize=10, ha='center', alpha=0.8, zorder=12)
    
    return [agent.circle, agent.line, agent.text]

def animate(frame):
    global frame_count, obstacles, last_spawn_frame, paused
    
    if not paused:
        frame_count += 1
        
        # 1. Spawn
        time_since_last = frame_count - last_spawn_frame
        if time_since_last >= MIN_SPAWN_GAP:
            prob = (time_since_last - MIN_SPAWN_GAP) / (MAX_SPAWN_GAP - MIN_SPAWN_GAP)
            prob = min(1.0, max(0.0, prob))
            if random.random() < prob:
                obs = Obstacle(5.0)
                obs.rect = plt.Rectangle((obs.x - obs.w/2, obs.y), obs.w, obs.h, color=obs.color, zorder=5, ec='white', lw=0.5)
                ax.add_patch(obs.rect)
                obstacles.append(obs)
                last_spawn_frame = frame_count
        
        # 2. Mise à jour et Nettoyage (Correction du bug de figement)
        new_obs = []
        for obs in obstacles:
            obs.update()
            obs.rect.set_x(obs.x - obs.w/2)
            obs.rect.set_y(obs.y)
            
            # Collision
            if (agent.y + AGENT_RADIUS > obs.y and 
                agent.y - AGENT_RADIUS < obs.y + obs.h and
                agent.x + AGENT_RADIUS > obs.x - obs.w/2 and
                agent.x - AGENT_RADIUS < obs.x + obs.w/2):
                
                if not obs.passed:
                    agent.score -= 1
                    obs.passed = True
                    agent.vx *= -1.2
                    agent.x += (agent.x - obs.x) * 0.2
            
            # Obstacle passé
            if obs.y > 10.5 and not obs.passed:
                agent.score += 1
                obs.passed = True
                # Suppression propre de l'objet graphique
                if obs.rect in ax.patches:
                    obs.rect.remove()
            
            if obs.y < 10.5:
                new_obs.append(obs)
            else:
                # Nettoyage des obstacles hors écran non marqués
                if obs.rect in ax.patches:
                    obs.rect.remove()
        obstacles = new_obs

        # 3. Agent
        agent.move(obstacles)
        agent.update_history()
        
        agent.circle.set_center((agent.x, agent.y))
        agent.line.set_data(agent.history_x, agent.history_y)
        
        # Affichage
        dissonance_color = '#00ffaa' if agent.dissonance < 0.5 else '#ffaa00' if agent.dissonance < 1.0 else '#ff3333'
        
        txt = (f"Antic: {agent.anticipation:.2f} | "
               f"Dis: {agent.dissonance:.2f} | "
               f"Score: {agent.score}")
        
        agent.text.set_text(txt)
        agent.text.set_color(dissonance_color)
        agent.text.set_position((agent.x, agent.y + 0.5))

    return [agent.circle, agent.line, agent.text]

def on_key(event):
    global paused
    if event.key == ' ':
        paused = not paused
    elif event.key == 'r':
        for obs in obstacles: 
            if obs.rect in ax.patches:
                obs.rect.remove()
        obstacles.clear()
        init()

fig.canvas.mpl_connect('key_press_event', on_key)

ani = animation.FuncAnimation(fig, animate, init_func=init, frames=2000, interval=50, blit=False)

plt.show()
