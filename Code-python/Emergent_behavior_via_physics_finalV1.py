import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle
from matplotlib.animation import FuncAnimation
import random

# ==============================================================================
# CONFIGURATION OF WORLD LAWS (MRCC v4.0 - INFINITE UNIVERSE WITH DISSONANCE ATTRACTION)
# ==============================================================================

# --- 1. TEMPORAL DYNAMICS ---
SIMULATION_LENGTH = 10000
DT = 0.1

# --- 2. AGENT PHYSICS (Inertia & Noise) ---
ETA = 2.0                 
TAU = 0.3                 
SIGMA_NOISE = 0.12        

# --- 3. DISSONANCE THERMODYNAMICS (Costs) ---
METABOLIC_COST = 0.03     
HUNGER_PENALTY = 6.0      
OVERLOAD_POWER = 3.0      
OVERLOAD_BASE = 5.0       
CONFLICT_RISK = 1.1       
CONFLICT_GAIN = 1.1       

# --- 4. RECIPROCAL COUPLING ---
COUPLING_STRENGTH = 6.0   
STORAGE_BENEFIT = 10.0     
RESOURCE_COST_GENERATION = 5.0

# --- 5. ECOSYSTEM (Resources) ---
RESOURCE_DEPLETION_RATE_BASE = 0.02 
MAX_AGENTS_PER_BASE = 6       
RESOURCE_SPAWN_RATE = 0.05  
MAX_SUB_RESOURCES = 8   

# --- 6. MEMORY & THRESHOLDS ---
D_THRESHOLD = 0.5           
MEMORY_DECAY = 0.1        
COLLECTIVE_THRESHOLD = 0.3  
SIGMOID_BETA = 5.0          
STATE_ALPHA = 0.7          

# --- 7. NEW: ATTRACTION PARAMETERS (Infinite Universe) ---
CENTER_X, CENTER_Y = 50.0, 50.0
ATTRACTION_STIFFNESS = 0.05  # Force du ressort (raideur)

# ==============================================================================
# CLASSES AND PHYSICAL LOGIC
# ==============================================================================

class CollectiveMemory:
    def __init__(self, max_points=10):
        self.points = [] 
        self.max_points = max_points
        self.decay_rate = MEMORY_DECAY

    def update(self):
        new_points = []
        for (x, y, t, intensity) in self.points:
            new_intensity = max(0.1, intensity * (1 - self.decay_rate))
            new_points.append((x, y, t, new_intensity))
        self.points = new_points
        self.points = [p for p in self.points if p[3] > 0.1]

    def record_event(self, x, y, event_type, intensity):
        if len(self.points) < self.max_points:
            self.points.append((x, y, event_type, intensity))
        else:
            min_intensity = float('inf')
            min_index = -1
            for i, p in enumerate(self.points):
                if p[3] < min_intensity:
                    min_intensity = p[3]
                    min_index = i
            if intensity > min_intensity:
                self.points[min_index] = (x, y, event_type, intensity)

    def get_force(self, agent_x, agent_y):
        force_mem_x, force_mem_y = 0.0, 0.0
        for (mx, my, m_type, intensity) in self.points:
            dx = mx - agent_x
            dy = my - agent_y
            dist = (dx**2 + dy**2)**0.5 + 0.5
            force_val = (m_type * intensity * 1.5) / (dist + 0.5)
            force_mem_x += (dx / dist) * force_val
            force_mem_y += (dy / dist) * force_val
        return force_mem_x, force_mem_y

    def draw(self, ax):
        pass

class ResourceManager:
    def __init__(self, initial_amount=200):
        self.main_res = Resource(50, 50, initial_amount)
        self.sub_resources = []
        self.active_resources = [self.main_res]
        self.max_resources = 5
        
    def update(self, agents):
        # Main Resource Regeneration
        if self.main_res.amount < 80.0:
            self.main_res.amount += RESOURCE_SPAWN_RATE * 5.0
            
        # Spawn New Resources
        current_count = len(self.active_resources)
        if current_count < MAX_SUB_RESOURCES and random.random() < 0.02:
            rx = random.uniform(15, 85)
            ry = random.uniform(15, 85)
            new_res = Resource(rx, ry, amount=20)
            self.sub_resources.append(new_res)
            self.active_resources.append(new_res)
        
        # Cleanup
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
        pass

class Base:
    def __init__(self, x, y, faction_id):
        self.x, self.y, self.faction = x, y, faction_id
        self.resources = 200.0
        self.active = True
        self.dissonance = 0.0
        
    def update(self, agents):
        if not self.active: return
        self.dissonance = 1.0 / (self.resources + 0.5) 
        self.resources -= RESOURCE_DEPLETION_RATE_BASE
        if self.resources < 1.0:
            self.resources = 1.0
            
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

        # --- 1. FORCE FIELDS CALCULATION ---
        
        # A. HUNGER & OVERLOAD
        hunger_level = 1.0 - (self.inventory / OVERLOAD_BASE)
        hunger_level = max(0.0, min(1.0, hunger_level))
        overload_factor = (self.inventory / OVERLOAD_BASE) ** OVERLOAD_POWER
        overload_cost = overload_factor * 2.0
        velocity_magnitude = (self.vx**2 + self.vy**2)**0.5
        inertia_cost = 0.1 * (1.0 - velocity_magnitude)
        internal_dissonance = (hunger_level * HUNGER_PENALTY) + METABOLIC_COST + inertia_cost + overload_cost

        # B. RESOURCE SEEKING
        closest_res, dist_res = resource_manager.get_closest_resource(self)
        force_res_x, force_res_y = 0.0, 0.0
        if closest_res:
            dx = closest_res.x - self.x
            dy = closest_res.y - self.y
            dist = (dx**2 + dy**2)**0.5 + 1e-5
            magnitude = (closest_res.amount * hunger_level) / ((dist + 0.1) ** 0.9)
            force_res_x += (dx / dist) * magnitude
            force_res_y += (dy / dist) * magnitude

        # C. OWN BASE COUPLING
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
            personal_gain = 0.0
            if self.inventory > 0.1:
                personal_gain = (self.inventory * STORAGE_BENEFIT) / ((dist + 0.1) ** 0.6)
            base_empathy_force = 0.0
            if closest_own_base.dissonance > 0.1:
                base_empathy_force = (closest_own_base.dissonance * COUPLING_STRENGTH) / ((dist + 0.1) ** 0.6)
            total_force_magnitude = personal_gain + base_empathy_force
            if total_force_magnitude > 0:
                force_base_x += (dx / dist) * total_force_magnitude
                force_base_y += (dy / dist) * total_force_magnitude

        # D. ENEMY BASE (Risk vs Gain)
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

        # E. ENEMY REPULSION
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

        # F. MEMORY FORCE
        force_mem_x, force_mem_y = collective_memory.get_force(self.x, self.y)

        # --- 2. CALCUL DE LA DENSITÉ DE CONTRAINTES (rho_local) ---
        rho_local = 0.0
        if closest_res and closest_res.amount < 5.0:
            rho_local += (5.0 - closest_res.amount) / 5.0 * 2.0
        if closest_enemy and min_enemy_dist < 5.0:
            rho_local += (5.0 - min_enemy_dist) / 5.0 * 3.0
        if closest_enemy_base and min_dist_enemy < 5.0:
            rho_local += (5.0 - min_dist_enemy) / 5.0 * 4.0
        if closest_own_base and closest_own_base.dissonance > 0.5:
            rho_local += closest_own_base.dissonance * 2.0
        rho_local = np.clip(rho_local, 0.0, 5.0)

        # --- 3. FORCE DE RAPPEL (Attracteur de Dissonance - Infinite Universe) ---
        dx_center = CENTER_X - self.x
        dy_center = CENTER_Y - self.y
        dist_center = (dx_center**2 + dy_center**2)**0.5 + 1e-5
        urgency_factor = 1.0 + (self.dissonance * 0.5)
        force_rappel_magnitude = dist_center * ATTRACTION_STIFFNESS * urgency_factor
        F_rappel_x = (dx_center / dist_center) * force_rappel_magnitude
        F_rappel_y = (dy_center / dist_center) * force_rappel_magnitude

        # --- 4. SUM OF FORCES ---
        F_total_x = force_res_x + force_base_x + force_enemy_x + force_rep_x + force_mem_x + F_rappel_x
        F_total_y = force_res_y + force_base_y + force_enemy_y + force_rep_y + force_mem_y + F_rappel_y

        # --- 5. DISSONANCE CALCULATION (Continu) ---
        new_dissonance = (
            internal_dissonance + 
            (1.0 / (dist_res + 1.0) if closest_res else internal_dissonance) + 
            (1.0 / (min_dist_own + 1.0) if closest_own_base and self.inventory > 0 else 0) +
            (1.0 / (min_enemy_dist + 1.0) if closest_enemy else 0)
        )
        self.dissonance = (STATE_ALPHA * new_dissonance) + ((1.0 - STATE_ALPHA) * self.dissonance)
        
        # Dynamic Critical Threshold
        exponent_arg = -SIGMOID_BETA * (self.dissonance - D_THRESHOLD)
        exponent_arg = np.clip(exponent_arg, -500, 500)
        sigmoid_val = 1.0 / (1.0 + np.exp(exponent_arg))
        self.seuil_critique = 1.0 * (1.0 - 0.6 * sigmoid_val)

        # Continuous State Mapping & Color
        state_intensity = min(1.0, max(0.0, self.dissonance / (self.seuil_critique * 1.5)))
        if self.faction == 0:
            r = int(255 * state_intensity)
            g = int(255 * (1 - state_intensity))
            b = 0
        else:
            r = int(255)
            g = int(255 * state_intensity * 0.8)
            b = 0
        self.color = f'#{r:02X}{g:02X}{b:02X}'

        # --- 6. MOVEMENT (Langevin Dynamics) ---
        current_dissonance = max(0.0, self.dissonance)
        noise_int_scale = SIGMA_NOISE * (1.0 + current_dissonance)
        noise_ext_scale = rho_local * 0.5
        total_noise_scale = np.sqrt(noise_int_scale**2 + noise_ext_scale**2)
        
        F_noise_x = np.random.normal(0, total_noise_scale)
        F_noise_y = np.random.normal(0, total_noise_scale)

        self.vx += (F_total_x + F_noise_x) * DT
        self.vy += (F_total_y + F_noise_y) * DT
        
        # Friction Non-Linéaire
        speed = (self.vx**2 + self.vy**2)**0.5
        base_friction = 0.85
        velocity_damping = 0.08 * speed 
        total_friction = np.clip(base_friction - velocity_damping, 0.4, 0.95)
        
        self.vx *= total_friction
        self.vy *= total_friction
        
        self.x += self.vx * DT
        self.y += self.vy * DT

        # --- 7. INTERACTIONS ---
        
        # A. Resource Collection
        if closest_res and dist_res < 2.5 and closest_res.amount > 0:
            uptake_rate = (1.5 - dist_res) * 0.2
            take = min(uptake_rate, closest_res.amount)
            closest_res.amount -= take
            self.inventory = min(self.inventory + take, OVERLOAD_BASE)
            self.dissonance -= 0.5 * (take / 0.2) 

        # B. Deposit at Base
        if closest_own_base and min_dist_own < 1.5 and self.inventory > 0.1:
            deposit_rate = (1.5 - min_dist_own) * self.inventory
            self.inventory -= deposit_rate
            closest_own_base.resources += deposit_rate
            self.dissonance -= STORAGE_BENEFIT * 0.8 * (deposit_rate / self.inventory) if self.inventory > 0 else 0

        # C. Pillaging Enemy Base
        if closest_enemy_base and min_dist_enemy < 1.5 and closest_enemy_base.resources > 0.1:
            if hunger_level > 0.01:
                steal_rate = (1.5 - min_dist_enemy) * 0.2
                steal = min(steal_rate, closest_enemy_base.resources)
                closest_enemy_base.resources -= steal
                self.inventory = min(self.inventory + steal, OVERLOAD_BASE)
                self.dissonance += CONFLICT_RISK * 0.2 * (steal / 0.2) 

        # D. Combat
        if closest_enemy and min_enemy_dist < 1.5:
            speed_rel = ((self.vx - closest_enemy.vx)**2 + (self.vy - closest_enemy.vy)**2)**0.5
            impact = speed_rel * 1.5 
            self.dissonance += impact * 0.5
            closest_enemy.dissonance += impact * 0.5
            
            death_prob = max(0, (self.dissonance - self.seuil_critique * 1.5) / (self.seuil_critique * 2))
            if np.random.random() < death_prob * 0.1:
                self.active = False
                
            enemy_death_prob = max(0, (closest_enemy.dissonance - closest_enemy.seuil_critique * 1.5) / (closest_enemy.seuil_critique * 2))
            if np.random.random() < enemy_death_prob * 0.1:
                closest_enemy.active = False

        # --- 8. MEMORY RECORDING ---
        if self.dissonance > D_THRESHOLD:
            trauma_intensity = (self.dissonance - D_THRESHOLD) * 2.0
            collective_memory.record_event(self.x, self.y, -1, trauma_intensity)
        
        if self.inventory > 1.8 and self.dissonance < 0.3:
            joy_intensity = (self.inventory - 1.8) * 3.0
            collective_memory.record_event(self.x, self.y, 1, joy_intensity)
        
        if self.dissonance > D_THRESHOLD * 1.5:
            self.memory.append((self.x, self.y, -1, self.dissonance))
        elif self.inventory > 1.8 and self.dissonance < 0.3:
            self.memory.append((self.x, self.y, 1, 1.0))
        
        if len(self.memory) > self.max_memory:
            self.memory.pop(0)

# --- INITIALIZATION GRAPHICS ---
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10), gridspec_kw={'height_ratios': [3, 1]})
fig.suptitle("MRCC v4.0: Infinite Universe with Dissonance Attraction", fontsize=16, fontweight='bold')

ax1.set_xlim(0, 100)
ax1.set_ylim(0, 100)
ax1.set_title("Physical Space (No Walls, Attractor at Center)", fontsize=12)
ax1.grid(True, alpha=0.3)

ax2.set_xlim(0, 200)
ax2.set_ylim(0, 3.0)
ax2.set_title("Global Dissonance Evolution", fontsize=12)
ax2.set_xlabel("Time (Frames)")
ax2.set_ylabel("Dissonance")
ax2.grid(True, alpha=0.3)

resource_manager = ResourceManager(initial_amount=200)
bases = [
    Base(15, 50, 0), 
    Base(85, 50, 1)  
]

collective_memory = CollectiveMemory(max_points=15)
agents = []
agents.append(MRCCAgent(20, 50, 0, 0))
agents.append(MRCCAgent(80, 50, 1, 1))

def update(frame):
    collective_memory.update()
    for base in bases:
        base.update(agents)
        if base.resources <= 0:
            base.active = False
            
    resource_manager.update(agents)
    
    for agent in agents:
        agent.update(resource_manager, bases, agents)
    
    agents[:] = [a for a in agents if a.active]

    # --- Drawing ---
    ax1.clear()
    ax1.set_xlim(0, 100)
    ax1.set_ylim(0, 100)
    
    alive_count = len(agents)
    avg_d = np.mean([a.dissonance for a in agents]) if agents else 0
    title = f"Frame: {frame} | Alive: {alive_count} | Avg Dissonance: {avg_d:.2f}"
    ax1.set_title(title, fontsize=12)
    ax1.grid(True, alpha=0.3)
    
    resource_manager.draw(ax1)
    
    # Draw Center Attractor
    ax1.plot(CENTER_X, CENTER_Y, 'k*', markersize=15, label='Center Attractor')

    for base in bases:
        if base.active:
            color = '#0000FF' if base.faction == 0 else '#FF0000'
            rect = Rectangle((base.x - 5, base.y - 5), 10, 10, color=color, alpha=0.6)
            ax1.add_patch(rect)
            status = "OK" if base.resources > 50 else "STRESS" if base.resources > 20 else "CRITIQUE"
            ax1.text(base.x, base.y, f"Base\n{int(base.resources)}\n{status}", ha='center', va='center', color='white', fontsize=8, fontweight='bold')

    for agent in agents:
        if len(agent.history_x) > 1:
            ax1.plot(agent.history_x, agent.history_y, color=agent.color, alpha=0.3, linewidth=1)
        circle = Circle((agent.x, agent.y), 2.5, color=agent.color, zorder=5)
        ax1.add_patch(circle)
        
        if agent.inventory > 0.1:
            ax1.text(agent.x, agent.y + 3, f"{agent.inventory:.1f}", fontsize=7, color='white', ha='center', fontweight='bold')
            
        if agent.dissonance > agent.seuil_critique:
            ax1.text(agent.x, agent.y - 3, "!", fontsize=8, color='red', ha='center', fontweight='bold')

    ax2.clear()
    ax2.set_xlim(0, 200)
    ax2.set_ylim(0, 3.0)
    ax2.set_title("Global Dissonance Evolution", fontsize=12)
    ax2.set_xlabel("Time (Frames)")
    ax2.set_ylabel("Dissonance")
    ax2.grid(True, alpha=0.3)
    
    if len(agents) > 0:
        avg_dissonance = np.mean([a.dissonance for a in agents])
        ax2.text(0.05, 0.95, f"Avg Dissonance: {avg_dissonance:.2f}", transform=ax2.transAxes, fontsize=12, color='blue', fontweight='bold')
        ax2.text(0.05, 0.90, f"Agents: {alive_count}", transform=ax2.transAxes, fontsize=12, color='black')
        ax2.axhline(y=D_THRESHOLD, color='gray', linestyle='--', alpha=0.5, label='Critical Threshold')
        ax2.legend(loc='upper right')

def close_fig(event=None):
    plt.close(fig)

fig.canvas.mpl_connect('close_event', close_fig)

ani = FuncAnimation(fig, update, frames=SIMULATION_LENGTH, interval=50, blit=False)
plt.show()
