#Python version 3.12.10

import pygame
import numpy as np
import random
import sys

# ==============================================================================
# CONFIGURATION DE LA FENÊTRE ET DU TEMPS
# ==============================================================================
pygame.init()
WIDTH, HEIGHT = 1000, 800
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("MRCC v4.0 - Pygame Edition (Infinite Universe)")
clock = pygame.time.Clock()
FPS = 60

# Couleurs
COLOR_BG = (20, 20, 25)          # Fond sombre
COLOR_RESOURCE = (0, 191, 255)   # Bleu clair
COLOR_MAIN_RES = (0, 100, 255)   # Bleu foncé
COLOR_BASE_0 = (0, 0, 255)       # Bleu
COLOR_BASE_1 = (255, 0, 0)       # Rouge
COLOR_TEXT = (255, 255, 255)
COLOR_ATTRACTION = (50, 50, 50)  # Gris pour le centre

# ==============================================================================
# CONFIGURATION DU MONDE (Identique à la version Matplotlib)
# ==============================================================================
DT = 0.1                          # Pas de temps (delta time) pour la précision physique
ETA = 2.0                         # Facteur d'inertie temporelle (vitesse de réponse)
TAU = 0.3                         # Constante de relaxation (dissipation d'énergie)
SIGMA_NOISE = 0.12                # Amplitude du bruit stochastique (imprévisibilité quantique)
METABOLIC_COST = 0.03             # Coût énergétique de base (maintenance vitale)
HUNGER_PENALTY = 6.0              # Pénalité de dissonance liée à la faim
OVERLOAD_POWER = 3.0              # Puissance de la surcharge (effet non-linéaire de saturation)
OVERLOAD_BASE = 10.0               # Capacité maximale de l'inventaire (seuil de saturation)
CONFLICT_RISK = 1.3               # Coefficient de risque perçu en combat (force répulsive)
CONFLICT_GAIN = 1.1               # Coefficient de gain potentiel en combat (motivation à attaquer)
COUPLING_STRENGTH = 6.0           # Force de lien empathique vers sa propre base
STORAGE_BENEFIT = 10.0            # Réduction de dissonance (joie) au dépôt de ressources
RESOURCE_COST_GENERATION = 5.0    # Coût en ressources pour créer un nouvel agent
RESOURCE_DEPLETION_RATE_BASE = 0.02 # Taux de dégradation naturelle des ressources de la base
MAX_AGENTS_PER_BASE = 100           # Nombre maximal d'agents supportés par une base
RESOURCE_SPAWN_RATE = 0.1        # Probabilité d'apparition d'une nouvelle ressource secondaire
MAX_SUB_RESOURCES = 50             # Nombre maximum de ressources secondaires actives
D_THRESHOLD = 0.5                 # Seuil de dissonance critique (bascule en mode survie)
MEMORY_DECAY = 0.1                # Taux d'effacement des traces de la mémoire collective
COLLECTIVE_THRESHOLD = 0.3        # Seuil pour activer les effets de mémoire de groupe
SIGMOID_BETA = 5.0                # Pente de la sigmoïde (brusquerie de la transition d'état)
STATE_ALPHA = 0.7                 # Facteur de lissage temporel (poids actuel vs passé)
CENTER_X, CENTER_Y = 50.0, 50.0   # Coordonnées du centre d'attraction global de l'univers
ATTRACTION_STIFFNESS = 0.05       # Raideur de la force d'attraction vers le centre

# Échelle pour l'affichage (1 unité monde = 10 pixels écran)
SCALE = 10.0
OFFSET_X = 50.0
OFFSET_Y = 50.0

def world_to_screen(x, y):
    return int((x * SCALE) + OFFSET_X), int(HEIGHT - ((y * SCALE) + OFFSET_Y))

# ==============================================================================
# CLASSES (Logique Physique Identique)
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

class ResourceManager:
    def __init__(self, initial_amount=200):
        self.main_res = Resource(50, 50, initial_amount)
        self.sub_resources = []
        self.active_resources = [self.main_res]
        self.max_resources = 5
        
    def update(self, agents):
        # La ressource principale ne se régénère plus
        if self.main_res.amount <= 0.1:
            self.main_res.active = False
            
        # Gestion des ressources secondaires (pas de régénération)
        # Spawn de nouvelles ressources
        current_count = len(self.active_resources)
        if current_count < MAX_SUB_RESOURCES and random.random() < 0.02:
            rx = random.uniform(15, 85)
            ry = random.uniform(15, 85)
            new_res = Resource(rx, ry, amount=50)
            self.sub_resources.append(new_res)
            self.active_resources.append(new_res)
        
        # Nettoyage
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

class Resource:
    def __init__(self, x, y, amount=20):
        self.x, self.y, self.amount = x, y, amount
        self.active = True

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
        self.color = (0, 255, 0) if faction == 0 else (255, 0, 0)
        self.inventory = 0.0
        self.dissonance = 0.0
        self.seuil_critique = 1.0
        self.history_x, self.history_y = [self.x], [self.y]
        self.memory = []
        self.max_memory = 10

    def update(self, resource_manager, bases, all_agents):
        if not self.active: return

        # --- 1. FORCE FIELDS ---
        hunger_level = 1.0 - (self.inventory / OVERLOAD_BASE)
        hunger_level = max(0.0, min(1.0, hunger_level))
        overload_factor = (self.inventory / OVERLOAD_BASE) ** OVERLOAD_POWER
        overload_cost = overload_factor * 2.0
        velocity_magnitude = (self.vx**2 + self.vy**2)**0.5
        inertia_cost = 0.1 * (1.0 - velocity_magnitude)
        internal_dissonance = (hunger_level * HUNGER_PENALTY) + METABOLIC_COST + inertia_cost + overload_cost

        closest_res, dist_res = resource_manager.get_closest_resource(self)
        force_res_x, force_res_y = 0.0, 0.0
        if closest_res:
            dx = closest_res.x - self.x
            dy = closest_res.y - self.y
            dist = (dx**2 + dy**2)**0.5 + 1e-5
            magnitude = (closest_res.amount * hunger_level) / ((dist + 0.1) ** 0.9)
            force_res_x += (dx / dist) * magnitude
            force_res_y += (dy / dist) * magnitude

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

        force_mem_x, force_mem_y = collective_memory.get_force(self.x, self.y)

        # --- 2. DENSITY & ATTRACTION ---
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

        dx_center = CENTER_X - self.x
        dy_center = CENTER_Y - self.y
        dist_center = (dx_center**2 + dy_center**2)**0.5 + 1e-5
        urgency_factor = 1.0 + (self.dissonance * 0.5)
        force_rappel_magnitude = dist_center * ATTRACTION_STIFFNESS * urgency_factor
        F_rappel_x = (dx_center / dist_center) * force_rappel_magnitude
        F_rappel_y = (dy_center / dist_center) * force_rappel_magnitude

        # --- 3. SUM OF FORCES ---
        F_total_x = force_res_x + force_base_x + force_enemy_x + force_rep_x + force_mem_x + F_rappel_x
        F_total_y = force_res_y + force_base_y + force_enemy_y + force_rep_y + force_mem_y + F_rappel_y

        # --- 4. DISSONANCE ---
        new_dissonance = (
            internal_dissonance + 
            (1.0 / (dist_res + 1.0) if closest_res else internal_dissonance) + 
            (1.0 / (min_dist_own + 1.0) if closest_own_base and self.inventory > 0 else 0) +
            (1.0 / (min_enemy_dist + 1.0) if closest_enemy else 0)
        )
        self.dissonance = (STATE_ALPHA * new_dissonance) + ((1.0 - STATE_ALPHA) * self.dissonance)
        
        exponent_arg = -SIGMOID_BETA * (self.dissonance - D_THRESHOLD)
        exponent_arg = np.clip(exponent_arg, -500, 500)
        sigmoid_val = 1.0 / (1.0 + np.exp(exponent_arg))
        self.seuil_critique = 1.0 * (1.0 - 0.6 * sigmoid_val)

        # Continuous State Mapping & Color (RGB)
        state_intensity = min(1.0, max(0.0, self.dissonance / (self.seuil_critique * 1.5)))
        if self.faction == 0:
            r = int(255 * state_intensity)
            g = int(255 * (1 - state_intensity))
            b = 0
        else:
            r = int(255)
            g = int(255 * state_intensity * 0.8)
            b = 0
        self.color = (r, g, b)

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
            uptake_rate = max(0.0, (1.5 - dist_res)) * 0.2
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

# ==============================================================================
# INITIALISATION
# ==============================================================================
collective_memory = CollectiveMemory(max_points=15)
resource_manager = ResourceManager(initial_amount=200)
bases = [
    Base(15, 50, 0), 
    Base(85, 50, 1)  
]
agents = []
agents.append(MRCCAgent(20, 50, 0, 0))
agents.append(MRCCAgent(80, 50, 1, 1))

# Police pour le texte
font = pygame.font.SysFont("Arial", 18)
small_font = pygame.font.SysFont("Arial", 14)

# ==============================================================================
# BOUCLE PRINCIPALE (Game Loop)
# ==============================================================================
running = True
frame = 0

while running:
    # 1. Gestion des événements (Fermeture, etc.)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        # Touche ESC pour quitter
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False

    # 2. Mise à jour de la logique
    collective_memory.update()
    
    for base in bases:
        base.update(agents)
        if base.resources <= 0:
            base.active = False
            
    resource_manager.update(agents)
    
    for agent in agents:
        agent.update(resource_manager, bases, agents)
    
    # Nettoyage des agents morts
    agents[:] = [a for a in agents if a.active]

    # 3. Dessin
    screen.fill(COLOR_BG)
    
    alive_count = len(agents)
    avg_d = np.mean([a.dissonance for a in agents]) if agents else 0
    
    # Dessiner le centre d'attraction (optionnel, pour repère)
    center_screen = world_to_screen(CENTER_X, CENTER_Y)
    pygame.draw.circle(screen, COLOR_ATTRACTION, center_screen, 5)

    # Dessiner les ressources
    for res in resource_manager.active_resources:
        if res.active:
            pos = world_to_screen(res.x, res.y)
            color = COLOR_MAIN_RES if res == resource_manager.main_res else COLOR_RESOURCE
            radius = 6 if res == resource_manager.main_res else 4
            pygame.draw.circle(screen, color, pos, radius)
            # Texte quantité
            text = small_font.render(f"{int(res.amount)}", True, (255, 255, 255))
            screen.blit(text, (pos[0] - 5, pos[1] - 10))

    # Dessiner les bases
    for base in bases:
        if base.active:
            pos = world_to_screen(base.x, base.y)
            color = COLOR_BASE_0 if base.faction == 0 else COLOR_BASE_1
            # Rectangle pour la base
            rect_size = 10
            pygame.draw.rect(screen, color, (pos[0] - rect_size, pos[1] - rect_size, rect_size*2, rect_size*2))
            # Statut
            status = "OK" if base.resources > 50 else "STRESS" if base.resources > 20 else "CRITIQUE"
            txt = small_font.render(f"{int(base.resources)}", True, (255, 255, 255))
            screen.blit(txt, (pos[0] - 10, pos[1] - 20))

    # Dessiner les agents et leurs trajectoires
    for agent in agents:
        # Trajectoire (trace légère)
        if len(agent.history_x) > 1:
            # Conversion de l'histoire en points écran
            pts = [world_to_screen(x, y) for x, y in zip(agent.history_x, agent.history_y)]
            if len(pts) > 1:
                pygame.draw.lines(screen, agent.color, False, pts, 1)
        
        # Agent (cercle)
        pos = world_to_screen(agent.x, agent.y)
        pygame.draw.circle(screen, agent.color, (pos[0], pos[1]), 5)
        
        # Inventaire
        if agent.inventory > 0.1:
            txt = small_font.render(f"{agent.inventory:.1f}", True, (255, 255, 255))
            screen.blit(txt, (pos[0] - 8, pos[1] - 12))
        
        # Alert dissonance
        if agent.dissonance > agent.seuil_critique:
            pygame.draw.circle(screen, (255, 0, 0), pos, 7, 1) # Anneau rouge

    # Interface (HUD)
    hud_text = f"Frame: {frame} | Alive: {alive_count} | Avg Dissonance: {avg_d:.2f}"
    text_surface = font.render(hud_text, True, COLOR_TEXT)
    screen.blit(text_surface, (10, 10))
    
    # Info ressource principale
    if resource_manager.main_res.active:
        res_text = f"Base Res: {int(resource_manager.main_res.amount)}"
    else:
        res_text = "Base Res: EXPIRED (Survival Mode)"
    res_surface = small_font.render(res_text, True, COLOR_TEXT)
    screen.blit(res_surface, (10, 35))

    # 4. Affichage et contrôle du temps
    pygame.display.flip()
    clock.tick(FPS)
    frame += 1

pygame.quit()
sys.exit()       
