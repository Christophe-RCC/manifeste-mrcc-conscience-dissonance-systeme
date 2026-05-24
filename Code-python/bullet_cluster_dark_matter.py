import pygame
import numpy as np
import random

# ==============================================================================
# CONFIGURATION
# ==============================================================================
pygame.init()
WIDTH, HEIGHT = 1000, 800
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("TEST BULLET CLUSTER : Séparation des Cœurs")
clock = pygame.time.Clock()
FPS = 60

# Couleurs
COLOR_BG = (10, 10, 15)
COLOR_AGENT_A = (255, 50, 50)  # Rouge
COLOR_AGENT_B = (50, 50, 255)  # Bleu
COLOR_MEMORY = (150, 150, 150) # Gris (Matière Noire)
COLOR_TEXT = (255, 255, 255)
COLOR_LINE = (255, 255, 0)     # Jaune pour la ligne de mesure

# Paramètres Physiques
DT = 0.1
FRICTION = 0.9999  # Faible friction pour simuler la traversée
MEMORY_DECAY = 0.00001
MEMORY_LIFETIME = 90000 # Durée de vie longue pour voir la persistance

# Coordonnées du monde
CENTER_X, CENTER_Y = 50.0, 50.0

def world_to_screen(x, y):
    scale = 8.0
    return int((x - 50) * scale + WIDTH/2), int(HEIGHT/2 - (y - 50) * scale)

# ==============================================================================
# CLASSES
# ==============================================================================

class MemoryPoint:
    def __init__(self, pos, intensity):
        self.x, self.y = pos
        self.intensity = intensity
        self.age = 0

    def update(self):
        self.age += 1
        self.intensity = max(0, self.intensity * (1 - MEMORY_DECAY))
        return self.age < MEMORY_LIFETIME and self.intensity > 0.1

    def draw(self, surface):
        if self.intensity <= 0: return
        size = int(2 + self.intensity * 3)
        pos_screen = world_to_screen(self.x, self.y)
        if 0 <= pos_screen[0] < WIDTH and 0 <= pos_screen[1] < HEIGHT:
            pygame.draw.circle(surface, COLOR_MEMORY, pos_screen, max(1, size))

class Agent:
    def __init__(self, pos, faction):
        self.x, self.y = pos
        self.vx, self.vy = 0.0, 0.0
        self.faction = faction
        self.color = COLOR_AGENT_A if faction == 0 else COLOR_AGENT_B
        self.active = True

    def update(self, memory_points):
        # Friction
        self.vx *= FRICTION
        self.vy *= FRICTION
        
        # Interaction avec la mémoire (Matière Noire)
        for m in memory_points:
            if m.intensity <= 0: continue
            dx = m.x - self.x
            dy = m.y - self.y
            dist = np.sqrt(dx*dx + dy*dy) + 1.0
            if dist < 15.0:
                force = (m.intensity * 0.05) / (dist * 0.5)
                self.vx += (dx / dist) * force
                self.vy += (dy / dist) * force

        # Mouvement global vers le centre
        dx_center = CENTER_X - self.x
        dy_center = CENTER_Y - self.y
        dist_center = np.sqrt(dx_center**2 + dy_center**2) + 1.0
        if dist_center > 10.0:
            speed = 0.5
            self.vx += (dx_center / dist_center) * speed * 0.1
            self.vy += (dy_center / dist_center) * speed * 0.1

        self.x += self.vx * DT
        self.y += self.vy * DT

        # Rebond
        if self.x < 0 or self.x > 100: self.vx *= -1
        if self.y < 0 or self.y > 100: self.vy *= -1

    def draw(self, surface):
        pos_screen = world_to_screen(self.x, self.y)
        if 0 <= pos_screen[0] < WIDTH and 0 <= pos_screen[1] < HEIGHT:
            pygame.draw.circle(surface, self.color, pos_screen, 4)

# ==============================================================================
# INITIALISATION
# ==============================================================================
agents_a = [Agent((random.uniform(10, 30), random.uniform(30, 70)), 0) for _ in range(50)]
agents_b = [Agent((random.uniform(70, 90), random.uniform(30, 70)), 1) for _ in range(50)]
all_agents = agents_a + agents_b

memory_points = []
frame = 0
collision_occurred = False
max_distance = 0.0

font = pygame.font.SysFont("Arial", 18)

# ==============================================================================
# BOUCLE PRINCIPALE
# ==============================================================================
running = True

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
            if event.key == pygame.K_SPACE:
                # Forcer un trauma
                memory_points.append(MemoryPoint((CENTER_X, CENTER_Y), 1.0))

    screen.fill(COLOR_BG)

    # 1. Mise à jour des agents
    for agent in all_agents:
        agent.update(memory_points)

    # 2. Détection de collision
    if not collision_occurred:
        agent_a_ref = agents_a[0]
        agent_b_ref = agents_b[0]
        
        dist_a = np.sqrt((CENTER_X - agent_a_ref.x)**2 + (CENTER_Y - agent_a_ref.y)**2)
        dist_b = np.sqrt((CENTER_X - agent_b_ref.x)**2 + (CENTER_Y - agent_b_ref.y)**2)
        
        if dist_a < 15 and dist_b < 15:
            collision_occurred = True
            # Créer la mémoire
            for _ in range(5):
                mx = CENTER_X + random.uniform(-5, 5)
                my = CENTER_Y + random.uniform(-5, 5)
                memory_points.append(MemoryPoint((mx, my), 0.8 + random.random() * 0.2))
            
            for agent in all_agents:
                agent.vx *= 1.2
                agent.vy *= 1.2

    # 3. Calcul des Cœurs de Masse (Centres de gravité)
    # Cœur Visible (Agents)
    sum_x_vis = 0.0
    sum_y_vis = 0.0
    count_vis = 0
    for agent in all_agents:
        if agent.active:
            sum_x_vis += agent.x
            sum_y_vis += agent.y
            count_vis += 1
    
    center_vis_x = sum_x_vis / count_vis if count_vis > 0 else CENTER_X
    center_vis_y = sum_y_vis / count_vis if count_vis > 0 else CENTER_Y

    # Cœur Invisible (Mémoire)
    sum_x_mem = 0.0
    sum_y_mem = 0.0
    count_mem = 0
    for m in memory_points:
        if m.intensity > 0.1:
            sum_x_mem += m.x
            sum_y_mem += m.y
            count_mem += 1
            
    center_mem_x = sum_x_mem / count_mem if count_mem > 0 else CENTER_X
    center_mem_y = sum_y_mem / count_mem if count_mem > 0 else CENTER_Y

    # Distance entre les deux cœurs
    dist_between_centers = np.sqrt((center_vis_x - center_mem_x)**2 + (center_vis_y - center_mem_y)**2)
    
    if dist_between_centers > max_distance:
        max_distance = dist_between_centers

    # 4. Mise à jour et dessin de la mémoire
    active_memory = []
    for m in memory_points:
        if m.update():
            active_memory.append(m)
            m.draw(screen)
    memory_points = active_memory

    # 5. Dessin des agents
    for agent in all_agents:
        agent.draw(screen)

    # 6. Visualisation des Cœurs et de la Distance
    # Dessiner le Cœur Visible (Cercle Rouge)
    pos_vis = world_to_screen(center_vis_x, center_vis_y)
    pygame.draw.circle(screen, COLOR_AGENT_A, pos_vis, 6)
    
    # Dessiner le Cœur Invisible (Cercle Gris)
    pos_mem = world_to_screen(center_mem_x, center_mem_y)
    pygame.draw.circle(screen, COLOR_MEMORY, pos_mem, 6)
    
    # Dessiner la ligne de mesure
    if count_vis > 0 and count_mem > 0:
        pygame.draw.line(screen, COLOR_LINE, pos_vis, pos_mem, 2)

    # 7. Interface
    text = font.render(f"Frame: {frame} | Distance Cœurs: {dist_between_centers:.2f} | Max: {max_distance:.2f}", True, COLOR_TEXT)
    screen.blit(text, (10, 10))
    
    if collision_occurred:
        status = "COLLISION ! Les cœurs se séparent-ils ?"
    else:
        status = "En attente de collision..."
    
    status_text = font.render(status, True, (200, 200, 200))
    screen.blit(status_text, (10, 40))
    
    instr = font.render("ESPACE : Forcer un trauma", True, (100, 100, 100))
    screen.blit(instr, (10, 70))

    pygame.display.flip()
    clock.tick(FPS)
    frame += 1

pygame.quit()
