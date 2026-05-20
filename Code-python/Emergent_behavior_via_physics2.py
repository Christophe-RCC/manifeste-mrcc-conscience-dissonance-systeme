import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle
from matplotlib.animation import FuncAnimation
import random

# ==============================================================================
# CONFIGURATION DES LOIS DU MONDE (MRCC v3.8 - ÉMERGENCE CONTINUE)
# ==============================================================================
# Modifiez ces valeurs pour changer la physique du système sans toucher au code logique.

# --- 1. DYNAMIQUE TEMPORELLE ---
SIMULATION_LENGTH = 3000  # Durée de la simulation (frames)
DT = 0.1                  # Pas de temps (Δt). Plus petit = mouvement plus fluide mais lent.

# --- 2. PHYSIQUE DES AGENTS (Inertie & Bruit) ---
ETA = 1.5                 # Taux d'apprentissage (plasticité). Force de réaction aux forces.
TAU = 1.0                 # Constante d'inertie. Plus haut = agents plus lourds/lents à changer de direction.
SIGMA_NOISE = 0.05        # Amplitude du bruit stochastique (ξ). Source d'exploration et de chaos.

# --- 3. THERMODYNAMIQUE DE LA DISSONANCE (Coûts) ---
# Ces paramètres définissent comment la douleur (dissonance) est calculée continûment.
METABOLIC_COST = 0.02     # Coût de base de l'existence (froid, faim de base).
HUNGER_PENALTY = 5.0      # Coût de la faim (dissonance interne).
OVERLOAD_POWER = 4.0      # Puissance de la surcharge. Plus haut = la douleur explose vite quand l'inventaire est plein.
OVERLOAD_BASE = 2.0       # Capacité maximale de l'inventaire (normalisation).
CONFLICT_RISK = 3.0       # Coût du conflit (stress physique immédiat).
CONFLICT_GAIN = 3.0       # Gain potentiel du conflit (ressources volées).

# --- 4. COUPLAGE RÉCIPROQUE (Lien Agent-Environnement) ---
# Ces paramètres définissent la force du lien entre l'agent et la base/environnement.
COUPLING_STRENGTH = 2.0   # Force de l'empathie/attraction vers la base. Plus haut = agents plus "sociaux".
STORAGE_BENEFIT = 5.0     # Réduction de dissonance lors du dépôt (soulagement).
RESOURCE_COST_GENERATION = 5.0 # Coût pour créer un nouvel agent (énergie nécessaire).

# --- 5. ÉCOSYSTÈME (Ressources) ---
RESOURCE_DEPLETION_RATE_BASE = 0.01 # Vitesse de consommation de la base.
MAX_AGENTS_PER_BASE = 5       # Capacité maximale de la base (contrôle démographique).
RESOURCE_SPAWN_RATE = 0.05    # Probabilité de régénération des ressources (si > 0, le système est auto-suffisant).

# ==============================================================================
# CLASSES ET LOGIQUE PHYSIQUE (AUCUNE RÈGLE "IF/ELSE" EXPLICITE DANS LA LOGIQUE)
# ==============================================================================

class ResourceManager:
    def __init__(self, initial_amount=200):
        self.main_res = Resource(50, 50, initial_amount)
        self.sub_resources = []
        self.active_resources = [self.main_res]
        self.max_resources = 5
        
    def update(self, agents):
        # Régénération continue des ressources (Loi de conservation/renouvellement)
        # Si la ressource principale est basse, elle se régénère doucement
        if self.main_res.amount < 50.0:
            self.main_res.amount += RESOURCE_SPAWN_RATE * 10.0
        else:
            # Légère consommation naturelle des ressources de l'environnement
            self.main_res.amount -= RESOURCE_SPAWN_RATE * 0.5
            
        # Régénération des sous-ressources
        for res in self.active_resources:
            if res.amount < 20.0:
                res.amount += RESOURCE_SPAWN_RATE * 5.0
            else:
                res.amount -= RESOURCE_SPAWN_RATE * 0.2

        # Gestion de la création de nouvelles ressources si elles sont trop rares
        current_count = len(self.active_resources)
        if current_count < self.max_resources and random.random() < 0.02:
            rx = random.uniform(15, 85)
            ry = random.uniform(15, 85)
            new_res = Resource(rx, ry, amount=20)
            self.sub_resources.append(new_res)
            self.active_resources.append(new_res)
        
        # Nettoyage des ressources épuisées
        self.active_resources = [r for r in self.active_resources if r.amount > 0.1]

    def get_closest_resource(self, agent):
        min_dist = float('inf')
        closest = None
        for res in self.active_resources:
            if not res.active: continue
            dx = agent.x - res.x
            dy = agent.y - res.y
            dist = (dx**2 + dy**2)**0.5
            if dist < min_dist:
                min_dist = dist
                closest = res
        return closest, min_dist

    def draw(self, ax):
        for res in self.active_resources:
            if res.active:
                color = '#00BFFF' if res == self.main_res else '#00FFFF'
                size = 6 if res == self.main_res else 4
                circle = Circle((res.x, res.y), size, color=color, alpha=0.8, zorder=2)
                ax.add_patch(circle)
                ax.text(res.x, res.y, f"{int(res.amount)}", ha='center', va='center', fontsize=8, color='black')

class Resource:
    def __init__(self, x, y, amount=20):
        self.x, self.y, self.amount = x, y, amount
        self.active = True
    
    def update(self, agents):
        # Pas de logique complexe ici, juste la gestion de l'état
        pass

class Base:
    def __init__(self, x, y, faction_id):
        self.x, self.y, self.faction = x, y, faction_id
        self.resources = 100.0
        self.active = True
        self.dissonance = 0.0
        
    def update(self, agents):
        if not self.active: return
        
        # --- LOI PHYSIQUE CONTINUE : La dissonance est une fonction inverse des ressources ---
        # Pas de "si". La douleur existe toujours, elle varie continûment.
        # Plus les ressources sont basses, plus la dissonance tend vers l'infini.
        self.dissonance = 1.0 / (self.resources + 0.5) 
        
        # Consommation continue
        self.resources -= RESOURCE_DEPLETION_RATE_BASE
        if self.resources < 1.0:
            self.resources = 1.0
            
        # Création d'agents si la base a assez d'énergie (Loi de croissance)
        if self.resources >= RESOURCE_COST_GENERATION:
            count = sum(1 for a in agents if a.faction == self.faction and a.active)
            if count < MAX_AGENTS_PER_BASE:
                self.resources -= RESOURCE_COST_GENERATION
                angle = random.uniform(0, 2 * np.pi)
                dist = random.uniform(2, 5)
                agents.append(MRCCAgent(
                    self.x + dist * np.cos(angle), 
                    self.y + dist * np.sin(angle), 
                    self.faction, 
                    len(agents)
                ))

class MRCCAgent:
    def __init__(self, x, y, faction, agent_id):
        self.id, self.x, self.y = agent_id, float(x), float(y)
        self.vx, self.vy = 0.0, 0.0
        self.faction, self.hp, self.active = faction, 1.0, True
        self.color = '#00FF00' if faction == 0 else '#FF0000'
        self.inventory = 0.0
        
        self.dissonance = 0.0
        self.seuil_critique = 1.0
        self.state = "Normal"
        self.history_x, self.history_y = [self.x], [self.y]
        self.history_dissonance = []
        self.memory = []
        self.max_memory = 10

    def update(self, resource_manager, bases, all_agents):
        if not self.active: return

        # --- 1. CALCUL DES CHAMPS DE FORCE (CONTINU) ---
        
        # A. FAIM & SURCHARGE (Lois continues, pas de seuils)
        # La faim est une fonction linéaire de l'inventaire
        hunger_level = 1.0 - (self.inventory / OVERLOAD_BASE)
        
        # La surcharge est une fonction exponentielle continue de l'inventaire
        # Même à 0, il y a un coût de base, mais il explose à la fin.
        overload_factor = (self.inventory / OVERLOAD_BASE) ** OVERLOAD_POWER
        overload_cost = overload_factor * 2.0
        
        # Coût de l'inertie (si on ne bouge pas, la dissonance monte)
        velocity_magnitude = (self.vx**2 + self.vy**2)**0.5
        inertia_cost = 0.1 * (1.0 - velocity_magnitude)
        
        internal_dissonance = (hunger_level * HUNGER_PENALTY) + METABOLIC_COST + inertia_cost + overload_cost

        # B. RECHERCHE DE RESSOURCE (Gradient de potentiel)
        closest_res, dist_res = resource_manager.get_closest_resource(self)
        force_res_x, force_res_y = 0.0, 0.0
        if closest_res:
            dx = closest_res.x - self.x
            dy = closest_res.y - self.y
            dist = (dx**2 + dy**2)**0.5 + 1e-5
            # Force proportionnelle à la faim et à la quantité de ressource
            magnitude = (closest_res.amount * hunger_level) / (dist + 0.1)
            force_res_x += (dx / dist) * magnitude
            force_res_y += (dy / dist) * magnitude

        # C. BASE PROPRE (Couplage Réciproque : Faim + Empathie)
        closest_own_base = None
        min_dist_own = float('inf')
        for base in bases:
            if base.faction == self.faction and base.active:
                d = ((base.x - self.x)**2 + (base.y - self.y)**2)**0.5
                if d < min_dist_own:
                    min_dist_own = d
                    closest_own_base = base
        
        force_base_x, force_base_y = 0.0, 0.0
        if closest_own_base:
            dx = closest_own_base.x - self.x
            dy = closest_own_base.y - self.y
            dist = (dx**2 + dy**2)**0.5 + 0.1
            
            # Force 1 : Soulagement personnel (si on a des ressources)
            personal_gain = 0.0
            if self.inventory > 0.1:
                personal_gain = (self.inventory * STORAGE_BENEFIT) / (dist + 0.1)
            
            # Force 2 : Empathie forcée (Couplage Réciproque)
            # L'agent est attiré par la douleur de la base, même s'il n'a rien à donner
            base_empathy_force = 0.0
            if closest_own_base.dissonance > 0.1:
                base_empathy_force = (closest_own_base.dissonance * COUPLING_STRENGTH) / (dist + 0.1)
            
            total_force_magnitude = personal_gain + base_empathy_force
            
            if total_force_magnitude > 0:
                force_base_x += (dx / dist) * total_force_magnitude
                force_base_y += (dy / dist) * total_force_magnitude

        # D. BASE ENNEMIE (Pillage)
        closest_enemy_base = None
        min_dist_enemy = float('inf')
        for base in bases:
            if base.faction != self.faction and base.active:
                d = ((base.x - self.x)**2 + (base.y - self.y)**2)**0.5
                if d < min_dist_enemy:
                    min_dist_enemy = d
                    closest_enemy_base = base
        
        force_enemy_x, force_enemy_y = 0.0, 0.0
        if closest_enemy_base:
            dx = closest_enemy_base.x - self.x
            dy = closest_enemy_base.y - self.y
            dist = (dx**2 + dy**2)**0.5 + 0.5
            risk_factor = CONFLICT_RISK / (dist + 0.5)
            gain_factor = (closest_enemy_base.resources * CONFLICT_GAIN * hunger_level) / (dist + 0.5)
            net_force = gain_factor - risk_factor
            if net_force > 0:
                force_enemy_x += (dx / dist) * net_force
                force_enemy_y += (dy / dist) * net_force

        # E. RÉPULSION ENNEMI (Loi de répulsion continue)
        closest_enemy = None
        min_enemy_dist = float('inf')
        for other in all_agents:
            if other.active and other.faction != self.faction:
                d = ((other.x - self.x)**2 + (other.y - self.y)**2)**0.5
                if d < min_enemy_dist:
                    min_enemy_dist = d
                    closest_enemy = other
        
        force_rep_x, force_rep_y = 0.0, 0.0
        if closest_enemy and min_enemy_dist < 5.0:
            dx = self.x - closest_enemy.x
            dy = self.y - closest_enemy.y
            dist = (dx**2 + dy**2)**0.5 + 0.1
            magnitude = 2.0 / (dist + 0.1)
            force_rep_x += (dx / dist) * magnitude
            force_rep_y += (dy / dist) * magnitude

        # --- 2. SOMME DES FORCES ---
        F_total_x = force_res_x + force_base_x + force_enemy_x + force_rep_x
        F_total_y = force_res_y + force_base_y + force_enemy_y + force_rep_y

        # --- 3. CALCUL DE LA DISSONANCE (Moyenne glissante) ---
        new_dissonance = (
            internal_dissonance + 
            (1.0 / (dist_res + 1.0) if closest_res else internal_dissonance) + 
            (1.0 / (min_dist_own + 1.0) if closest_own_base and self.inventory > 0 else 0) +
            (1.0 / (min_enemy_dist + 1.0) if closest_enemy else 0)
        )
        
        # Mémoire physique (lissage)
        alpha_mem = 0.7 
        self.dissonance = (alpha_mem * new_dissonance) + ((1.0 - alpha_mem) * self.dissonance)
        
        # Seuil critique dynamique (sigmoïde)
        sigmoid_val = 1.0 / (1.0 + np.exp(-5.0 * (self.dissonance - 0.5)))
        self.seuil_critique = 1.0 * (1.0 - 0.6 * sigmoid_val)

        # État de l'agent
        if self.dissonance < self.seuil_critique * 0.5:
            self.state = "Normal"
            self.color = '#00FF00' if self.faction == 0 else '#FF0000'
        elif self.dissonance < self.seuil_critique:
            self.state = "Adaptation"
            self.color = '#FFFF00'
        else:
            self.state = "Crise"
            self.color = '#FF4500'

        # --- 4. MOUVEMENT (Langevin) ---
        # Sécurité : garantir un bruit positif
        current_dissonance = max(0.0, self.dissonance)
        noise_scale = SIGMA_NOISE * (1.0 + current_dissonance)
        if noise_scale <= 0:
            noise_scale = SIGMA_NOISE * 0.1
            
        F_noise_x = np.random.normal(0, noise_scale)
        F_noise_y = np.random.normal(0, noise_scale)

        self.vx += (F_total_x + F_noise_x) * DT
        self.vy += (F_total_y + F_noise_y) * DT
        self.vx *= 0.92
        self.vy *= 0.92
        
        self.x += self.vx * DT
        self.y += self.vy * DT

        # Rebond sur les murs
        self.x = max(0.0, min(100.0, self.x))
        self.y = max(0.0, min(100.0, self.y))
        if self.x < 0 or self.x > 100: self.vx *= -1
        if self.y < 0 or self.y > 100: self.vy *= -1

        # --- 5. INTERACTIONS ---
        # A. Collecte
        if closest_res and dist_res < 1.5 and closest_res.amount > 0:
            take = min(0.2, closest_res.amount)
            closest_res.amount -= take
            self.inventory = min(self.inventory + take, OVERLOAD_BASE)
            self.dissonance -= 0.5 * (take / 0.2) 

        # B. Dépôt
        if closest_own_base and min_dist_own < 1.5 and self.inventory > 0.1:
            deposit = self.inventory
            self.inventory = 0.0
            closest_own_base.resources += deposit
            self.dissonance -= STORAGE_BENEFIT * 0.8

        # C. Pillage
        if closest_enemy_base and min_dist_enemy < 1.5 and closest_enemy_base.resources > 0.1:
            if hunger_level > 0.01:
                steal = min(0.2, closest_enemy_base.resources)
                closest_enemy_base.resources -= steal
                self.inventory = min(self.inventory + steal, OVERLOAD_BASE)
                self.dissonance += CONFLICT_RISK * 0.2 

        # D. Combat
        if closest_enemy and min_enemy_dist < 1.5:
            speed_rel = ((self.vx - closest_enemy.vx)**2 + (self.vy - closest_enemy.vy)**2)**0.5
            impact = speed_rel * 1.5 
            self.dissonance += impact * 0.5
            closest_enemy.dissonance += impact * 0.5
            
            if self.dissonance > self.seuil_critique * 1.5 and np.random.random() < 0.1:
                self.active = False
            if closest_enemy.dissonance > closest_enemy.seuil_critique * 1.5 and np.random.random() < 0.1:
                closest_enemy.active = False

        # --- ENREGISTREMENT ---
        self.history_dissonance.append(self.dissonance)
        self.history_x.append(self.x)
        self.history_y.append(self.y)
        if len(self.history_x) > 50:
            self.history_x.pop(0)
            self.history_y.pop(0)
        if len(self.history_dissonance) > 200:
            self.history_dissonance.pop(0)

# --- INITIALISATION GRAPHIQUE ---
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10), gridspec_kw={'height_ratios': [3, 1]})
fig.suptitle("MRCC v3.8 : Émergence de la Coopération par Couplage Réciproque", fontsize=16, fontweight='bold')

ax1.set_xlim(0, 100)
ax1.set_ylim(0, 100)
ax1.set_title("Espace Physique (Forces Continues)", fontsize=12)
ax1.grid(True, alpha=0.3)

ax2.set_xlim(0, 200)
ax2.set_ylim(0, 2.5)
ax2.set_title("Dissonance Moyenne (Indicateur de Stress Global)", fontsize=12)
ax2.set_xlabel("Temps (Frames)")
ax2.set_ylabel("Dissonance")
ax2.grid(True, alpha=0.3)

resource_manager = ResourceManager(initial_amount=200)
bases = [
    Base(15, 50, 0), 
    Base(85, 50, 1)  
]

agents = []
agents.append(MRCCAgent(20, 50, 0, 0))
agents.append(MRCCAgent(80, 50, 1, 1))

def update(frame):
    for base in bases:
        base.update(agents)
        if base.resources <= 0:
            base.active = False
            
    resource_manager.update(agents)
    
    for agent in agents:
        agent.update(resource_manager, bases, agents)
    
    agents[:] = [a for a in agents if a.active]

    ax1.clear()
    ax1.set_xlim(0, 100)
    ax1.set_ylim(0, 100)
    
    alive_count = len(agents)
    avg_d = np.mean([a.dissonance for a in agents]) if agents else 0
    title = f"Frame: {frame} | Alive: {alive_count} | Dissonance Moy: {avg_d:.2f}"
    ax1.set_title(title, fontsize=12)
    ax1.grid(True, alpha=0.3)
    
    resource_manager.draw(ax1)
    
    for base in bases:
        if base.active:
            color = '#0000FF' if base.faction == 0 else '#FF0000'
            rect = Rectangle((base.x - 5, base.y - 5), 10, 10, color=color, alpha=0.6)
            ax1.add_patch(rect)
            status = "OK" if base.resources > 20 else "CRITIQUE"
            ax1.text(base.x, base.y, f"Base\n{int(base.resources)}\n{status}", ha='center', va='center', color='white', fontsize=8, fontweight='bold')

    for agent in agents:
        if len(agent.history_x) > 1:
            ax1.plot(agent.history_x, agent.history_y, color=agent.color, alpha=0.3, linewidth=1)
        circle = Circle((agent.x, agent.y), 2.5, color=agent.color, zorder=5)
        ax1.add_patch(circle)
        
        if agent.inventory > 0.1:
            ax1.text(agent.x, agent.y + 3, f"{agent.inventory:.1f}", fontsize=7, color='white', ha='center', fontweight='bold')
            
        if agent.state == "Crise":
            ax1.text(agent.x, agent.y - 3, "!", fontsize=8, color='red', ha='center', fontweight='bold')

    ax2.clear()
    ax2.set_xlim(0, 200)
    ax2.set_ylim(0, 2.5)
    ax2.set_title("Évolution de la Dissonance Globale", fontsize=12)
    ax2.set_xlabel("Temps (Frames)")
    ax2.set_ylabel("Dissonance")
    ax2.grid(True, alpha=0.3)
    
    if len(agents) > 0:
        avg_dissonance = np.mean([a.dissonance for a in agents])
        ax2.text(0.05, 0.95, f"Avg Dissonance: {avg_dissonance:.2f}", transform=ax2.transAxes, fontsize=12, color='blue', fontweight='bold')
        ax2.text(0.05, 0.90, f"Agents: {alive_count}", transform=ax2.transAxes, fontsize=12, color='black')
        ax2.axhline(y=0.5, color='gray', linestyle='--', alpha=0.5, label='Seuil Critique')
        ax2.legend(loc='upper right')

def close_fig(event=None):
    plt.close(fig)

fig.canvas.mpl_connect('close_event', close_fig)

ani = FuncAnimation(fig, update, frames=SIMULATION_LENGTH, interval=50, blit=False)
plt.show()
