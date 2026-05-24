# Simulation MRCC: Bullet Cluster Dynamics
# Visualizes why Dark Matter and Galaxies pass through each other while Gas stops.
# Mechanism: Dark Matter (spacetime curvature) has zero friction (inertia). Gas has high friction (shock).
# Outcome: Mass (DM) and Light (Stars) separate from the Gas cloud, validating the "Memory Topology" hypothesis.

import pygame
import numpy as np
import random

# ==============================================================================
# CONFIGURATION PHYSIQUE (MRCC-COSMO)
# ==============================================================================
pygame.init()
WIDTH, HEIGHT = 1200, 900
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("MRCC-COSMO : Formation des Structures & Bullet Cluster")
clock = pygame.time.Clock()
FPS = 60

# Couleurs
COLOR_BG = (5, 5, 20)
COLOR_DARK_MATTER = (200, 200, 255)  # Bleu clair (Les Puits de Potentiel / Mémoire)
COLOR_GAS = (255, 100, 100)          # Rouge (Gaz Baryonique - Friction)
COLOR_STARS = (255, 255, 255)        # Blanc (Étoiles - Suivent les Puits)
COLOR_TEXT = (255, 255, 255)

# Paramètres Physiques
DT = 0.1
GRAVITY_STRENGTH = 0.5  # Force d'attraction vers les puits
FRICTION_GAS = 0.85     # Friction forte pour le gaz (s'arrête)
FRICTION_STARS = 0.999  # Friction nulle pour les étoiles (traversent)
FRICTION_DM = 0.9999    # Friction nulle pour les puits (structure de l'espace)

# Zone de collision (pour activer la friction du gaz)
COLLISION_RADIUS = 50.0
CENTER_X, CENTER_Y = 50.0, 50.0

def world_to_screen(x, y):
    scale = 12.0
    return int((x - 50) * scale + WIDTH/2), int(HEIGHT/2 - (y - 50) * scale)

# ==============================================================================
# CLASSES
# ==============================================================================

class PotentialWell:
    """
    La Matière Noire : Un puits de potentiel statique ou lent.
    C'est la "Mémoire" de l'univers, créée au Big Bang.
    """
    def __init__(self, x, y):
        self.x, self.y = x, y
        self.vx, self.vy = 0.0, 0.0
        self.active = True

    def update(self):
        # Mouvement inertiel très faible (les puits peuvent bouger lentement)
        self.vx *= FRICTION_DM
        self.vy *= FRICTION_DM
        self.x += self.vx * DT
        self.y += self.vy * DT

    def draw(self, surface):
        pos_screen = world_to_screen(self.x, self.y)
        if 0 <= pos_screen[0] < WIDTH and 0 <= pos_screen[1] < HEIGHT:
            # Dessin d'un cercle plus grand pour le puits
            pygame.draw.circle(surface, COLOR_DARK_MATTER, pos_screen, 6)
            # Un halo pour montrer le potentiel
            pygame.draw.circle(surface, (150, 150, 200), pos_screen, 15, 1)

class GasParticle:
    """
    Le Gaz Baryonique : Attiré par les puits, mais subit une friction massive au centre.
    """
    def __init__(self, pos, target_well):
        self.x, self.y = pos
        self.vx, self.vy = 0.0, 0.0
        self.target_well = target_well
        self.active = True

    def update(self):
        # 1. Attraction vers le puits de matière noire (Gravité)
        dx = self.target_well.x - self.x
        dy = self.target_well.y - self.y
        dist = np.sqrt(dx*dx + dy*dy) + 1.0
        
        # Force gravitationnelle (loi en 1/r pour simplifier, ou constante si proche)
        force = GRAVITY_STRENGTH / (dist * 0.5)
        self.vx += (dx / dist) * force
        self.vy += (dy / dist) * force

        # 2. Friction globale (pour stabiliser l'orbite)
        self.vx *= 0.995
        self.vy *= 0.995

        # 3. Friction massive au centre de la collision (Bullet Cluster effect)
        dist_to_center = np.sqrt((self.x - CENTER_X)**2 + (self.y - CENTER_Y)**2)
        if dist_to_center < COLLISION_RADIUS:
            self.vx *= FRICTION_GAS
            self.vy *= FRICTION_GAS

        self.x += self.vx * DT
        self.y += self.vy * DT

    def draw(self, surface):
        pos_screen = world_to_screen(self.x, self.y)
        if 0 <= pos_screen[0] < WIDTH and 0 <= pos_screen[1] < HEIGHT:
            pygame.draw.circle(surface, COLOR_GAS, pos_screen, 2)

class StarParticle:
    """
    Les Étoiles : Attirées par les puits, pas de friction (traversent la collision).
    """
    def __init__(self, pos, target_well):
        self.x, self.y = pos
        self.vx, self.vy = 0.0, 0.0
        self.target_well = target_well
        self.active = True

    def update(self):
        # 1. Attraction vers le puits
        dx = self.target_well.x - self.x
        dy = self.target_well.y - self.y
        dist = np.sqrt(dx*dx + dy*dy) + 1.0
        
        force = GRAVITY_STRENGTH / (dist * 0.5)
        self.vx += (dx / dist) * force
        self.vy += (dy / dist) * force

        # 2. Pas de friction au centre (elles traversent)
        # Juste une très légère friction pour la stabilité
        self.vx *= FRICTION_STARS
        self.vy *= FRICTION_STARS

        self.x += self.vx * DT
        self.y += self.vy * DT

    def draw(self, surface):
        pos_screen = world_to_screen(self.x, self.y)
        if 0 <= pos_screen[0] < WIDTH and 0 <= pos_screen[1] < HEIGHT:
            pygame.draw.circle(surface, COLOR_STARS, pos_screen, 1)

# ==============================================================================
# INITIALISATION
# ==============================================================================
wells = []
gas_particles = []
star_particles = []

# Création des deux Puits de Potentiel (Matière Noire)
# Ils sont placés de part et d'autre du centre
well_left = PotentialWell(30.0, 50.0)
well_right = PotentialWell(70.0, 50.0)
wells.append(well_left)
wells.append(well_right)

# Création des galaxies autour des puits
# Chaque galaxie a du Gaz et des Étoiles
def create_galaxy(well, count_gas, count_stars, offset_x):
    for _ in range(count_gas):
        angle = random.uniform(0, 2 * np.pi)
        dist = random.uniform(5, 15)
        x = well.x + dist * np.cos(angle) + offset_x
        y = well.y + dist * np.sin(angle)
        gas_particles.append(GasParticle((x, y), well))
    
    for _ in range(count_stars):
        angle = random.uniform(0, 2 * np.pi)
        dist = random.uniform(5, 15)
        x = well.x + dist * np.cos(angle) + offset_x
        y = well.y + dist * np.sin(angle)
        star_particles.append(StarParticle((x, y), well))

# Initialisation des deux galaxies
create_galaxy(well_left, 150, 100, -2)
create_galaxy(well_right, 150, 100, 2)

# Vitesse initiale pour la collision (les galaxies se rapprochent)
# On donne une petite vitesse aux puits pour qu'ils se rapprochent lentement
well_left.vx = 0.8
well_right.vx = -0.8

font = pygame.font.SysFont("Arial", 18)
small_font = pygame.font.SysFont("Arial", 14)

# ==============================================================================
# BOUCLE PRINCIPALE
# ==============================================================================
running = True
frame = 0
collision_phase = "FORMATION" # FORMATION, COLLISION, SEPARATION

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
            if event.key == pygame.K_r:
                # Reset
                wells = []
                gas_particles = []
                star_particles = []
                well_left = PotentialWell(30.0, 50.0)
                well_right = PotentialWell(70.0, 50.0)
                wells.append(well_left)
                wells.append(well_right)
                create_galaxy(well_left, 150, 100, -2)
                create_galaxy(well_right, 150, 100, 2)
                well_left.vx = 0.8
                well_right.vx = -0.8
                collision_phase = "FORMATION"

    screen.fill(COLOR_BG)

    # Mise à jour des Puits (Matière Noire)
    for well in wells:
        well.update()
        well.draw(screen)

    # Mise à jour des Étoiles (Suivent les puits, traversent)
    for star in star_particles:
        star.update()
        star.draw(screen)

    # Mise à jour du Gaz (S'arrête au centre)
    for gas in gas_particles:
        gas.update()
        gas.draw(screen)

    # Détection de phase
    dist_between_wells = np.sqrt((wells[0].x - wells[1].x)**2 + (wells[0].y - wells[1].y)**2)
    if dist_between_wells < 20 and collision_phase == "FORMATION":
        collision_phase = "COLLISION"
    elif dist_between_wells > 40 and collision_phase == "COLLISION":
        collision_phase = "SEPARATION"

    # Interface
    text = font.render(f"Phase: {collision_phase} | Puits (Bleu) = Mémoire | Gaz (Rouge) = Friction", True, COLOR_TEXT)
    screen.blit(text, (10, 10))
    
    if collision_phase == "COLLISION":
        status = "Collision en cours : Le gaz s'arrête, les puits traversent !"
    elif collision_phase == "SEPARATION":
        status = "Séparation : La masse (puits) est décalée par rapport au gaz !"
    else:
        status = "Formation : Les galaxies s'effondrent dans les puits de potentiel"
    
    status_text = small_font.render(status, True, (200, 200, 200))
    screen.blit(status_text, (10, 40))
    
    instr = small_font.render("Appuie sur 'R' pour recommencer", True, (150, 150, 150))
    screen.blit(instr, (10, 70))

    pygame.display.flip()
    clock.tick(FPS)
    frame += 1

pygame.quit()
