import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
from matplotlib.animation import FuncAnimation
import random

# --- CONFIGURATION DU MODÈLE MRCC (v2.1 - CORRIGÉ) ---
SIMULATION_LENGTH = 5000
NUM_AGENTS = 4
NUM_RESOURCES = 10
DT = 0.1

# Paramètres physiques
ETA = 0.3
TAU = 2.5
SIGMA_NOISE = 0.3
D_BASE = 1.0
ALPHA_FRAG = 0.6
BETA_RIGID = 5.0
D_THRESHOLD = 0.4
COUPLING_LAMBDA = 0.2

# --- CLASSES ---
class MRCCAgent:
    def __init__(self, x, y, agent_id):
        self.id = agent_id
        self.x = x
        self.y = y
        self.vx = 0.0
        self.vy = 0.0
        self.dissonance = 0.0
        self.seuil_critique = D_BASE
        self.state = "Normal"
        self.active = True
        self.color = '#00FF00'
        
        # Historique pour les graphiques
        self.history_dissonance = []
        self.history_distance = []
        self.history_threshold = []
        self.history_x = [x]
        self.history_y = [y]
        
    def update(self, resources, all_agents):
        if not self.active: return

        # 1. Trouver la ressource la plus proche
        min_dist = float('inf')
        closest_res = None
        for res in resources:
            if not res.active: continue
            dx = self.x - res.x
            dy = self.y - res.y
            dist = np.sqrt(dx**2 + dy**2)
            if dist < min_dist:
                min_dist = dist
                closest_res = res
        
        # 2. Calcul de la Dissonance
        speed = np.sqrt(self.vx**2 + self.vy**2)
        self.dissonance = (min_dist * 0.1) + (speed * 0.5)
        
        # 3. Calcul du Seuil Critique Dynamique
        sigmoid_val = 1.0 / (1.0 + np.exp(-BETA_RIGID * (self.dissonance - D_THRESHOLD)))
        self.seuil_critique = D_BASE * (1.0 - ALPHA_FRAG * sigmoid_val)
        
        # 4. Mise à jour de l'état
        if self.dissonance < self.seuil_critique * 0.5:
            self.state = "Normal"
            self.color = '#00FF00'
        elif self.dissonance < self.seuil_critique:
            self.state = "Adaptation"
            self.color = '#FFFF00'
        else:
            self.state = "Saturation/Crise"
            self.color = '#FF4500'

        # 5. Équation de Langevin (Mouvement)
        if closest_res:
            dx = closest_res.x - self.x
            dy = closest_res.y - self.y
            dist = np.sqrt(dx**2 + dy**2) + 1e-5
            dir_x = dx / dist
            dir_y = dy / dist
            
            force_magnitude = (ETA / TAU) * (1.0 / (1.0 + self.dissonance))
            F_det_x = force_magnitude * dir_x
            F_det_y = force_magnitude * dir_y
        else:
            F_det_x, F_det_y = 0, 0

        noise_scale = SIGMA_NOISE
        if self.state == "Saturation/Crise": noise_scale *= 3.0
        F_noise_x = np.random.normal(0, noise_scale)
        F_noise_y = np.random.normal(0, noise_scale)

        self.vx += (F_det_x + F_noise_x) * DT
        self.vy += (F_det_y + F_noise_y) * DT
        self.vx *= 0.95
        self.vy *= 0.95
        self.x += self.vx * DT
        self.y += self.vy * DT

        if self.x < 0 or self.x > 100: self.vx *= -1
        if self.y < 0 or self.y > 100: self.vy *= -1

        # Enregistrement des données
        self.history_dissonance.append(self.dissonance)
        self.history_distance.append(min_dist)
        self.history_threshold.append(self.seuil_critique)
        
        self.history_x.append(self.x)
        self.history_y.append(self.y)
        if len(self.history_x) > 50:
            self.history_x.pop(0)
            self.history_y.pop(0)
        if len(self.history_dissonance) > 200:
            self.history_dissonance.pop(0)
            self.history_distance.pop(0)
            self.history_threshold.pop(0)

class Resource:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.active = True
        self.vx = 0.0
        self.vy = 0.0
        
    def update(self, agents):
        total_force_x = 0
        total_force_y = 0
        for agent in agents:
            if not agent.active: continue
            dx = agent.x - self.x
            dy = agent.y - self.y
            dist = np.sqrt(dx**2 + dy**2)
            if dist < 20:
                force = COUPLING_LAMBDA / (dist + 1)
                total_force_x += (dx / dist) * force
                total_force_y += (dy / dist) * force
        
        self.vx += total_force_x * 0.1
        self.vy += total_force_y * 0.1
        self.vx *= 0.9
        self.vy *= 0.9
        self.x += self.vx * DT
        self.y += self.vy * DT
        if self.x < 0 or self.x > 100: self.vx *= -1
        if self.y < 0 or self.y > 100: self.vy *= -1

# --- INITIALISATION ---
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10), gridspec_kw={'height_ratios': [2, 1]})
fig.suptitle("MRCC v2.1 : Analyse Physique en Temps Réel", fontsize=16, fontweight='bold')

ax1.set_xlim(0, 100)
ax1.set_ylim(0, 100)
ax1.set_title("Espace Physique (Agents vs Ressources)", fontsize=12)
ax1.grid(True, alpha=0.3)

ax2.set_xlim(0, 200)
ax2.set_ylim(0, 1.5)
ax2.set_title("Évolution de la Dissonance (Agent 1)", fontsize=12)
ax2.set_xlabel("Temps (Frames)")
ax2.set_ylabel("Valeur")
ax2.grid(True, alpha=0.3)

agents = []
resources = []

for i in range(NUM_AGENTS):
    agents.append(MRCCAgent(np.random.uniform(10, 90), np.random.uniform(10, 90), i+1))
for i in range(NUM_RESOURCES):
    resources.append(Resource(np.random.uniform(10, 90), np.random.uniform(10, 90)))

def update(frame):
    # Mise à jour logique
    for res in resources: res.update(agents)
    for agent in agents: agent.update(resources, agents)
    
    # --- Dessin Graphique 1 (Simulation) ---
    ax1.clear()
    ax1.set_xlim(0, 100)
    ax1.set_ylim(0, 100)
    ax1.set_title(f"Frame: {frame} | Agents: {len([a for a in agents if a.active])}", fontsize=12)
    ax1.grid(True, alpha=0.3)
    
    for res in resources:
        circle = Circle((res.x, res.y), 3, color='#00BFFF', alpha=0.6)
        ax1.add_patch(circle)
        
    for agent in agents:
        if len(agent.history_x) > 1:
            ax1.plot(agent.history_x, agent.history_y, color=agent.color, alpha=0.3, linewidth=1)
        circle = Circle((agent.x, agent.y), 3, color=agent.color, zorder=5)
        ax1.add_patch(circle)
        if agent.state == "Saturation/Crise":
            ax1.text(agent.x, agent.y + 4, f"{agent.state}", fontsize=6, color='red', ha='center')

    # --- Dessin Graphique 2 (Données) ---
    ax2.clear()
    ax2.set_xlim(0, 200)
    ax2.set_ylim(0, 1.5)
    ax2.set_title("Analyse de l'Agent 1 (Dissonance vs Distance vs Seuil)", fontsize=12)
    ax2.set_xlabel("Temps (Frames)")
    ax2.set_ylabel("Valeur")
    ax2.grid(True, alpha=0.3)
    
    # CORRECTION ICI : Sélectionner le premier agent actif, pas la liste
    target_agent = None
    for a in agents:
        if a.active:
            target_agent = a
            break
    
    # Si aucun agent actif, on prend le premier de la liste (pour éviter crash)
    if target_agent is None and len(agents) > 0:
        target_agent = agents

    if target_agent and len(target_agent.history_dissonance) > 0:
        # On trace les données
        line1 = ax2.plot(target_agent.history_dissonance, label='Dissonance (D)', color='red', linewidth=2)
        line2 = ax2.plot(target_agent.history_distance, label='Distance (D)', color='blue', linestyle='--', alpha=0.7)
        line3 = ax2.plot(target_agent.history_threshold, label='Seuil Critique (D_crit)', color='green', linestyle=':', alpha=0.7)
        
        # Ligne de référence
        ax2.axhline(y=D_THRESHOLD, color='gray', linestyle='-', alpha=0.3, label='Seuil de fragilisation')
        
        # Affichage de la légende seulement si on a tracé des lignes
        ax2.legend(loc='upper right')

# Lancer
ani = FuncAnimation(fig, update, frames=SIMULATION_LENGTH, interval=50, blit=False)
plt.show()
