import matplotlib.pyplot as plt
import matplotlib.animation as animation
import random
import math

# --- CONFIGURATION ---
WIDTH, HEIGHT = 10, 10
AGENT_SIZE = 0.25
OBSTACLE_SPEED = 0.08
OBSTACLE_SPAWN_RATE = 12

# Couleurs
COLOR_BG = '#151520'
COLOR_TRACK_MRCC = '#1a2520'
COLOR_TRACK_LF = '#201515'
COLOR_OBSTACLE_MRCC = '#00ffaa'  # Vert vif
COLOR_OBSTACLE_LF = '#ff4444'    # Rouge vif
COLOR_AGENT_MRCC = '#00ffaa'
COLOR_AGENT_LF = '#ff4444'
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
ax.set_title("MRCC (Gauche) vs Libre Arbitre (Droite)", color=COLOR_TEXT, fontsize=16, pad=20)

# Variables globales
agents = []
obstacles_mrcc = []
obstacles_lf = []
frame_count = 0
paused = False

# --- CLASSES ---

class Obstacle:
    def __init__(self, x_center, color):
        self.w = random.uniform(1.0, 2.2)  # Largeur max 2.2 pour laisser un passage
        self.h = 0.4
        # Position X : on le place aléatoirement mais en laissant toujours un passage
        min_x = x_center - 1.5 + self.w/2
        max_x = x_center + 1.5 - self.w/2
        if min_x < max_x:
            self.x = random.uniform(min_x, max_x)
        else:
            self.x = x_center
        self.y = -0.5
        # Vitesse FIXE pour créer un flux constant (pas de variation aléatoire)
        self.speed = OBSTACLE_SPEED 
        self.color = color
        self.rect = None

    def update(self):
        self.y += self.speed

    

class Agent:
    def __init__(self, x, y, color, name, agent_type, lane_x):
        self.x = x
        self.y = y
        self.color = color
        self.name = name
        self.type = agent_type
        self.lane_x = lane_x
        self.history_x = [x]
        self.history_y = [y]
        self.dissonance = 0.0
        self.score = 0
        self.stuck_timer = 0
        self.learning_rate = 0.04
        self.anticipation_factor = 0.0
        self.target_x = x
        self.circle = None
        self.line = None
        self.text = None

    def get_track_bounds(self):
        return self.lane_x - 1.5, self.lane_x + 1.5

    def move(self, obstacles):
        left_bound, right_bound = self.get_track_bounds()
        center_x = self.lane_x

        if self.type == 'mrcc':
            closest_obs = None
            min_dist = float('inf')
            
            for obs in obstacles:
                if obs.y < self.y and obs.y > self.y - 2.5:
                    dist = math.hypot(obs.x - self.x, obs.y - self.y)
                    if dist < min_dist:
                        min_dist = dist
                        closest_obs = obs

            if closest_obs:
                self.dissonance = 2.0 / (min_dist + 0.1)
                obs_left = closest_obs.x - closest_obs.w / 2
                obs_right = closest_obs.x + closest_obs.w / 2
                
                if obs_left < center_x < obs_right:
                    space_left = center_x - obs_left
                    space_right = obs_right - center_x
                    
                    if space_left > space_right:
                        self.target_x = obs_left - 0.3
                    else:
                        self.target_x = obs_right + 0.3
                    
                    if self.score > 5:
                        self.anticipation_factor = min(0.8, self.anticipation_factor + 0.005)
                else:
                    self.target_x = center_x
            else:
                self.target_x = center_x
                self.dissonance = max(0, self.dissonance - 0.05)
                self.anticipation_factor = max(0, self.anticipation_factor - 0.002)

             # --- LOGIQUE DE RÉGULATION ET CORRECTION (MRCC) ---
            # Si la dissonance est trop élevée (choc imminent ou erreur), on réduit l'anticipation
            # pour éviter la sur-réaction et permettre une stabilisation.
            if self.dissonance > 1.0:
                # Panique contrôlée : on réduit l'anticipation et on ralentit la réaction
                self.anticipation_factor = max(0.2, self.anticipation_factor - 0.05)
                reaction_speed = self.learning_rate * 0.5  # Réaction plus prudente
            else:
                # État normal : on utilise l'anticipation accumulée pour fluidifier
                reaction_speed = self.learning_rate + (self.anticipation_factor * 0.1)

            self.x += (self.target_x - self.x) * reaction_speed
            
            if self.x < left_bound + AGENT_SIZE:
                self.x = left_bound + AGENT_SIZE
            elif self.x > right_bound - AGENT_SIZE:
                self.x = right_bound - AGENT_SIZE

        elif self.type == 'libre_arbitre':
            script_triggered = False
            target_script_x = self.x

            for obs in obstacles:
                if obs.y < self.y and obs.y > self.y - 1.5:
                    obs_left = obs.x - obs.w / 2
                    obs_right = obs.x + obs.w / 2
                    
                    if obs_left < self.x < obs_right:
                        target_script_x = obs_right + 0.4
                        script_triggered = True
                        break
            
            if not script_triggered:
                target_script_x = center_x

            step = 0.08 
            
            if target_script_x > self.x:
                self.x += step
            elif target_script_x < self.x:
                self.x -= step
            
            if self.x < left_bound + AGENT_SIZE:
                self.x = left_bound + AGENT_SIZE
            elif self.x > right_bound - AGENT_SIZE:
                self.x = right_bound - AGENT_SIZE

            for obs in obstacles:
                if (self.y + AGENT_SIZE > obs.y and 
                    self.y - AGENT_SIZE < obs.y + obs.h and
                    self.x + AGENT_SIZE > obs.x - obs.w/2 and
                    self.x - AGENT_SIZE < obs.x + obs.w/2):
                    self.stuck_timer += 1
                else:
                    self.stuck_timer = 0

    def update_history(self):
        self.history_x.append(self.x)
        self.history_y.append(self.y)
        if len(self.history_x) > 100:
            self.history_x.pop(0)
            self.history_y.pop(0)

def init():
    global agents, obstacles_mrcc, obstacles_lf, frame_count
    frame_count = 0
    paused = False
    
    agents = [
        Agent(3.0, 8.0, COLOR_AGENT_MRCC, "MRCC", "mrcc", 3.0),
        Agent(7.0, 8.0, COLOR_AGENT_LF, "Libre Arbitre", "libre_arbitre", 7.0)
    ]
    
    for agent in agents:
        agent.circle = plt.Circle((agent.x, agent.y), AGENT_SIZE, color=agent.color, zorder=10, ec='white', lw=0.5)
        ax.add_patch(agent.circle)
        agent.line, = ax.plot([], [], color=agent.color, alpha=0.4, linewidth=2, zorder=9)
        agent.text = ax.text(agent.x, agent.y + 0.5, "", color=agent.color, fontsize=9, ha='center', fontweight='bold', zorder=11)

    # Piste Gauche
    ax.add_patch(plt.Rectangle((1.5, 0), 3.0, 10.0, color=COLOR_TRACK_MRCC, alpha=0.6, zorder=1))
    ax.plot([1.5, 1.5], [0, 10], color='#445', linewidth=1, zorder=0)
    ax.plot([4.5, 4.5], [0, 10], color='#445', linewidth=1, zorder=0)
    
    # Piste Droite
    ax.add_patch(plt.Rectangle((5.5, 0), 3.0, 10.0, color=COLOR_TRACK_LF, alpha=0.6, zorder=1))
    ax.plot([5.5, 5.5], [0, 10], color='#544', linewidth=1, zorder=0)
    ax.plot([8.5, 8.5], [0, 10], color='#544', linewidth=1, zorder=0)

    ax.text(5, 0.5, "ESPACE: Pause | R: Reset", color=COLOR_TEXT, fontsize=10, ha='center', alpha=0.8, zorder=12)

    return []

def animate(frame):
    global frame_count, obstacles_mrcc, obstacles_lf, paused
    
    # Nettoyage de l'écran (optionnel avec blit=False, mais utile pour forcer le redessin)
    # On ne supprime pas les objets statiques (pistes, textes) pour éviter les bugs
    
    if not paused:
        frame_count += 1
        
      # Génération obstacles (plus régulière)
        if frame_count % OBSTACLE_SPAWN_RATE == 0:
            obs = Obstacle(3.0, COLOR_OBSTACLE_MRCC)
            obs.rect = plt.Rectangle((obs.x - obs.w/2, obs.y), obs.w, obs.h, color=obs.color, zorder=5, ec='white', lw=0.5)
            ax.add_patch(obs.rect)
            obstacles_mrcc.append(obs)

        if frame_count % (OBSTACLE_SPAWN_RATE + 7) == 0:
            obs = Obstacle(7.0, COLOR_OBSTACLE_LF)
            obs.rect = plt.Rectangle((obs.x - obs.w/2, obs.y), obs.w, obs.h, color=obs.color, zorder=5, ec='white', lw=0.5)
            ax.add_patch(obs.rect)
            obstacles_lf.append(obs)

        # Mise à jour et nettoyage obstacles MRCC
        new_obs = []
        for obs in obstacles_mrcc:
            obs.update()
            obs.rect.set_x(obs.x - obs.w/2)
            obs.rect.set_y(obs.y)
            if obs.y < 10.5:
                new_obs.append(obs)
            else:
                # L'obstacle est passé ! On incrémente le score de l'agent MRCC
                # On trouve l'agent MRCC pour mettre à jour son score
                for agent in agents:
                    if agent.type == 'mrcc':
                        agent.score += 1
                        break
                obs.rect.remove()
        obstacles_mrcc = new_obs

        # Mise à jour et nettoyage obstacles LF
        new_obs = []
        for obs in obstacles_lf:
            obs.update()
            obs.rect.set_x(obs.x - obs.w/2)
            obs.rect.set_y(obs.y)
            if obs.y < 10.5:
                new_obs.append(obs)
            else:
                # L'obstacle est passé ! On incrémente le score de l'agent Libre Arbitre
                for agent in agents:
                    if agent.type == 'libre_arbitre':
                        agent.score += 1
                        break
                obs.rect.remove()
        obstacles_lf = new_obs

        # Mise à jour agents
        for agent in agents:
            obs_list = obstacles_mrcc if agent.type == 'mrcc' else obstacles_lf
            
            agent.move(obs_list)
            agent.update_history()
            
            for obs in obs_list:
                if (agent.y + AGENT_SIZE > obs.y and 
                    agent.y - AGENT_SIZE < obs.y + obs.h and
                    agent.x + AGENT_SIZE > obs.x - obs.w/2 and
                    agent.x - AGENT_SIZE < obs.x + obs.w/2):
                    
                    if agent.type == 'libre_arbitre':
                        agent.stuck_timer += 10
                        agent.x += random.choice([-0.2, 0.2])
                    else:
                        agent.dissonance = 2.0
                        if agent.x < obs.x:
                            agent.x -= 0.2
                        else:
                            agent.x += 0.2
                        agent.dissonance = max(0, agent.dissonance - 0.5)

            agent.circle.set_center((agent.x, agent.y))
            agent.line.set_data(agent.history_x, agent.history_y)
            
            if agent.type == 'mrcc':
                txt = f"MRCC: Antic {agent.anticipation_factor:.2f} | Dis {agent.dissonance:.1f}"
                color = COLOR_AGENT_MRCC
            else:
                status = "BLOQUÉ" if agent.stuck_timer > 10 else "Actif"
                txt = f"Libre: {status} | Bloc {agent.stuck_timer}"
                color = COLOR_AGENT_LF
            
            agent.text.set_text(txt)
            agent.text.set_color(color)
            agent.text.set_position((agent.x, agent.y + 0.5))

    # Retour d'une liste vide car on ne blitte pas (tout est redessiné)
    return []

def on_key(event):
    global paused
    if event.key == ' ':
        paused = not paused
    elif event.key == 'r':
        for obs in obstacles_mrcc: obs.rect.remove()
        for obs in obstacles_lf: obs.rect.remove()
        obstacles_mrcc.clear()
        obstacles_lf.clear()
        init()

fig.canvas.mpl_connect('key_press_event', on_key)

# IMPORTANT : blit=False pour forcer le redessin complet et voir les obstacles
ani = animation.FuncAnimation(fig, animate, init_func=init, frames=2000, interval=50, blit=False)

plt.show()
