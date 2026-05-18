#ce script illustre comment la société génère elle même des comportements destructeurs(ce que l'on appelle "monstre") à cause du modèle actuel du libre arbitre et comment le modèle MRCC s'adapte aux traumas

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.patches import Circle

# --- CONFIGURATION ---
SIMULATION_LENGTH = 1000
TRAUMA_STEP = 200
TRAUMA_MAGNITUDE = 0.6
SOCIAL_PRESSURE_START = 400
SOCIAL_PRESSURE_MAGNITUDE = 0.3
RESISTANCE_THRESHOLD = 0.8
MICRO_TRAUMA_PROB = 0.05

class Agent:
    def __init__(self, strategy, x, y, agent_id):
        self.strategy = strategy
        self.id = agent_id
        self.x = x
        self.y = y
        self.internal_model = 0.5
        self.dissonance = 0.0
        self.state = "Normal" 
        self.active = True
        self.color = 'green' if strategy == 'mrcc' else 'red'
        self.radius = 4
        self.history_x = [x]
        self.history_y = [y]
        
    def update(self, reality, social_pressure, all_agents):
        if not self.active:
            return

        base_dissonance = abs(reality - self.internal_model)
        
        if self.strategy == 'free_will':
            social_dissonance = social_pressure * 1.5
        else:
            social_dissonance = social_pressure * 0.2 
            
        self.dissonance = base_dissonance + social_dissonance
        
        if self.strategy == 'mrcc':
            if self.dissonance < 0.2:
                self.state = "Normal"
            elif self.dissonance < RESISTANCE_THRESHOLD:
                self.state = "Adaptation"
            else:
                self.state = "Saturation"
            
            target_x = reality * 100
            target_y = 50 + (reality * 20)
            
            # Fuite des monstres
            for other in all_agents:
                if other.strategy == 'free_will' and other.state == 'Monstre' and other.active:
                    dx = self.x - other.x
                    dy = self.y - other.y
                    dist = np.sqrt(dx**2 + dy**2)
                    if dist < 30:
                        speed = 2.0
                        self.x += (dx / dist) * speed
                        self.y += (dy / dist) * speed
                    else:
                        self.x += (target_x - self.x) * 0.05
                        self.y += (target_y - self.y) * 0.05
            else:
                self.x += (target_x - self.x) * 0.05
                self.y += (target_y - self.y) * 0.05

        elif self.strategy == 'free_will':
            if self.dissonance < 0.3:
                self.state = "Normal"
            elif self.dissonance < RESISTANCE_THRESHOLD:
                self.state = "Instable"
            elif self.dissonance > RESISTANCE_THRESHOLD and self.state != "Monstre":
                self.state = "Monstre"
                print(f"[Agent {self.id}] BASCULE EN 'MONSTRE' !")
            elif self.dissonance > RESISTANCE_THRESHOLD * 1.2:
                self.state = "Effondrement"
                self.active = False
                return
            else:
                self.state = "Culpabilité"
            
            if self.state == "Monstre":
                target = None
                min_dist = float('inf')
                for other in all_agents:
                    if other.strategy == 'mrcc' and other.active:
                        dx = other.x - self.x
                        dy = other.y - self.y
                        dist = np.sqrt(dx**2 + dy**2)
                        if dist < min_dist:
                            min_dist = dist
                            target = other
                
                if target:
                    dx = target.x - self.x
                    dy = target.y - self.y
                    dist = np.sqrt(dx**2 + dy**2)
                    if dist > 5:
                        speed = 3.0
                        self.x += (dx / dist) * speed
                        self.y += (dy / dist) * speed
                    if dist < 5:
                        target.active = False
                        print(f"[Agent {self.id}] a détruit l'agent MRCC {target.id} !")
                        self.dissonance = max(0, self.dissonance - 0.3)
                else:
                    self.x += np.random.normal(0, 2)
                    self.y += np.random.normal(0, 2)
            else:
                self.x += np.random.normal(0, 0.5)
                self.y += np.random.normal(0, 0.5)
        
        self.history_x.append(self.x)
        self.history_y.append(self.y)
        if len(self.history_x) > 20:
            self.history_x.pop(0)
            self.history_y.pop(0)

# --- INITIALISATION ---
fig, ax = plt.subplots(figsize=(12, 6))
ax.set_xlim(0, 100)
ax.set_ylim(0, 100)
ax.set_title("Simulation MRCC vs Libre Arbitre", fontsize=14, fontweight='bold')
ax.set_xlabel("Position X")
ax.set_ylabel("Position Y")
ax.grid(True, alpha=0.3)

agents = []
agent_counter = 0
current_env = 0.5
social_pressure = 0.0
frame = 0
env_data = []

# Ajout initial
agent_counter += 1
agents.append(Agent('mrcc', 50, 50, agent_counter))
agent_counter += 1
agents.append(Agent('free_will', 50, 50, agent_counter))

def update(frame):
    global current_env, social_pressure, env_data
    
    # Environnement
    change = np.random.normal(0, 0.02)
    current_env = current_env * 0.98 + change
    current_env = np.clip(current_env, 0, 1)
    
    if frame == TRAUMA_STEP:
        current_env = np.clip(current_env + TRAUMA_MAGNITUDE, 0, 1)
        # print(f"[{frame}] TRAUMA !")
    
    if frame >= SOCIAL_PRESSURE_START:
        social_pressure = SOCIAL_PRESSURE_MAGNITUDE
    
    if frame > SOCIAL_PRESSURE_START:
        if np.random.random() < MICRO_TRAUMA_PROB:
            micro_trauma = np.random.uniform(0.05, 0.15)
            current_env = np.clip(current_env + micro_trauma, 0, 1)
    
    # Mise à jour agents
    for agent in agents:
        if agent.active:
            agent.update(current_env, social_pressure, agents)
    
    agents[:] = [a for a in agents if a.active]
    
    # --- DESSIN (Sans blit pour éviter les erreurs) ---
    ax.clear()
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.set_title("Simulation MRCC vs Libre Arbitre", fontsize=14, fontweight='bold')
    ax.set_xlabel("Position X")
    ax.set_ylabel("Position Y")
    ax.grid(True, alpha=0.3)
    
    for agent in agents:
        # Cercle
        circle = Circle((agent.x, agent.y), agent.radius, color=agent.color, zorder=5)
        ax.add_patch(circle)
        
        # Traînée
        if len(agent.history_x) > 1:
            ax.plot(agent.history_x, agent.history_y, color=agent.color, alpha=0.3, linewidth=1, zorder=1)
        
        # Texte
        ax.text(agent.x, agent.y + 5, f"{agent.id}\n{agent.state}", fontsize=8, color='black', ha='center', zorder=6)
    
    # Titre dynamique
    monsters = [a for a in agents if a.strategy == 'free_will' and a.state == 'Monstre' and a.active]
    if monsters:
        ax.set_title(f"ATTENTION : {len(monsters)} MONSTRE(S) ACTIFS !", fontsize=14, fontweight='bold', color='red')
    
    # Info en bas
    info = f"Frame: {frame} | Env: {current_env:.2f} | Pression: {social_pressure:.2f}"
    ax.text(0.5, 0.02, info, transform=ax.transAxes, ha='center', fontsize=10, color='blue', zorder=10)

    env_data.append(current_env)
    if len(env_data) > 500:
        env_data.pop(0)

# Lancer l'animation (blit=False pour la stabilité)
ani = animation.FuncAnimation(fig, update, frames=SIMULATION_LENGTH, interval=100, blit=False)
plt.show()
