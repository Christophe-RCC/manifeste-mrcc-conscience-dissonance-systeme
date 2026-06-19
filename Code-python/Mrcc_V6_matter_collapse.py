#Works in python 3.12.10
#Blackhole analogy, formation

import numpy as np
import scipy.ndimage as ndimage
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.colors import LinearSegmentedColormap

# ==========================================
# CONFIGURATION : MRCC v10.2 - AVEC RAYONNEMENT DE HAWKING
# ==========================================

class UniversMRCC_Stable:
    def __init__(self, resolution, dt):
        self.resolution = resolution
        self.dt = dt
        
        self.M = np.zeros(resolution)
        self.F = np.zeros(resolution)
        self.vx = np.zeros(resolution)
        self.vy = np.zeros(resolution)
        self.rho = np.zeros(resolution)
        
        # --- PARAMÈTRES PHYSIQUES ---
        self.M_planck = 3.0
        self.gamma_fric = 0.002 
        
        # --- RAYONNEMENT DE HAWKING (NOUVEAU) ---
        self.hawking_threshold = 2.5  # Seuil de densité où l'évaporation commence
        self.hawking_coeff = 0.008   # Coefficient d'évaporation (force du rayonnement)
        self.hawking_range = 3.0      # Rayon d'émission du rayonnement autour du trou noir

        # --- BRUIT DE FOND ---
        self.sigma_bruit_fond = 0.0001
        self.amplitude_bruit_matiere = 0.05
        
        # --- SOURCE ÉNERGÉTIQUE ---
        self.source_strength = 0.25
        self.source_radius = 20.0
        
        # --- EXPANSION ---
        self.seuil_expansion = 4.0
        self.max_vitesse = 2.5
        
        # --- CONFINEMENT ---
        self.rayon_critique = 80
        self.force_rappel_coeff = 0.1
        
        # Diffusion
        self.D_chaleur = 0.00001
        self.D_matiere = 0.001
        
        # Initialisation
        cy, cx = resolution[0]//2, resolution[1]//2
        # Initialisation des vecteurs de position (nécessaires plus tard)
        self.y_grid, self.x_grid = np.ogrid[:resolution[0], :resolution[1]]
        self.dist = np.sqrt((self.x_grid - cx)**2 + (self.y_grid - cy)**2)
        
        # Noyau + Bruit
        self.M = np.zeros(resolution)
        self.M[self.dist < 10] = 0.25
        self.M[self.dist < 25] += 0.025
        
        bruit_fond = np.random.normal(0, self.sigma_bruit_fond, resolution)
        self.M += bruit_fond * self.amplitude_bruit_matiere
        self.M = np.clip(self.M, 0, self.M_planck)
        
        self.F = np.zeros(resolution)
        self.vx = np.zeros(resolution)
        self.vy = np.zeros(resolution)
        
        self.etape = "STABLE (CŒUR ACTIF)"

    def update_step(self):
        resolution = self.resolution
        cy, cx = resolution[0]/2, resolution[1]/2
        
        # --- 0. CALCUL DES COORDONNÉES (Toujours exécuté) ---
        x = self.x_grid
        y = self.y_grid
        dist = self.dist
        
        # Gestion du zéro pour les divisions futures
        dist_safe = np.where(dist > 1e-10, dist, 1e-10)
        
        # Vecteurs radiaux
        dx_vec = x - cx
        dy_vec = y - cy

        # --- 1. SOURCE CONTINUE ---
        source_mask = dist < self.source_radius
        source_F = self.source_strength * np.exp(-dist**2 / (self.source_radius**2 / 2))
        source_M = 0.0 * np.exp(-dist**2 / (self.source_radius**2 / 2))
        
        self.F += self.dt * source_F
        self.M += self.dt * source_M
        self.M = np.clip(self.M, 0, self.M_planck)

        # --- 2. BRUIT DE FOND ---
        bruit_fond = np.random.normal(0, self.sigma_bruit_fond, resolution)
        self.F += bruit_fond * 0.5
        self.M += bruit_fond * self.amplitude_bruit_matiere
        self.M = np.clip(self.M, 0, self.M_planck)

        # --- 3. DYNAMIQUE DE CHALEUR ---
        dF_dx = ndimage.sobel(self.F, axis=1, mode='nearest')
        dF_dy = ndimage.sobel(self.F, axis=0, mode='nearest')
        laplacien_F = ndimage.sobel(dF_dx, axis=1, mode='nearest') + ndimage.sobel(dF_dy, axis=0, mode='nearest')
        pertes = -0.005 * self.F
        self.F = self.F + self.dt * (self.D_chaleur * laplacien_F + pertes)

        # --- 4. EXPANSION (Conversion F -> V) ---
        condition_explosion = (self.F > self.seuil_expansion) & (self.M > 0.05)
        
        if np.any(condition_explosion):
            u_x = dx_vec / dist_safe
            u_y = dy_vec / dist_safe
            
            accel = 0.8 * (self.F - self.seuil_expansion)
            
            self.vx += u_x * accel * self.dt
            self.vy += u_y * accel * self.dt
            
            self.F[condition_explosion] *= 0.6
            self.M[condition_explosion] *= 0.98

        # --- 5. CONFINEMENT (Force de rappel) ---
        condition_loin = dist > self.rayon_critique
        
        if np.any(condition_loin):
            u_x_inward = -dx_vec / dist_safe
            u_y_inward = -dy_vec / dist_safe
            
            force_mag = self.force_rappel_coeff * (dist - self.rayon_critique)
            force_mag = np.where(condition_loin, force_mag, 0)
            
            self.vx += u_x_inward * force_mag * self.dt
            self.vy += u_y_inward * force_mag * self.dt

        # --- 6. FRICTION & LIMITES ---
        # Correction : On décompose le tableau de friction pour ne garder que la bonne dimension
        friction = -self.gamma_fric * np.stack((self.vx, self.vy), axis=0)
        
        # On extrait la couche X (index 0) et Y (index 1) du tableau de friction
        friction_x = friction[0]
        friction_y = friction[1]
        
        self.vx += friction_x * self.dt
        self.vy += friction_y * self.dt
        
        # Limiter la vitesse
        self.vx = np.clip(self.vx, -self.max_vitesse, self.max_vitesse)
        self.vy = np.clip(self.vy, -self.max_vitesse, self.max_vitesse)

        # --- 7. DYNAMIQUE DE MATIÈRE (Advection) ---
        flux_x = self.M * self.vx
        flux_y = self.M * self.vy
        
        div_flux_x = ndimage.sobel(flux_x, axis=1, mode='nearest')
        div_flux_y = ndimage.sobel(flux_y, axis=0, mode='nearest')
        divergence = div_flux_x + div_flux_y
        
        self.M = self.M - self.dt * divergence
        self.M = ndimage.gaussian_filter(self.M, sigma=0.5)
        self.M = np.clip(self.M, 0, self.M_planck)

        # --- 8. DENSITÉ CAUSALE ---
        max_F = np.max(self.F) + 1e-10
        self.rho = self.M / max_F

        # ==========================================
        # 9. RAYONNEMENT DE HAWKING (AJOUTÉ)
        # ==========================================
        # Le trou noir s'évapore si la densité locale dépasse le seuil
        # Plus M est grand, plus le trou noir s'évapore vite (inverse de la masse)
        
        # Condition : Densité très élevée (Cœur du trou noir)
        condition_hawking = self.M > self.hawking_threshold
        
        if np.any(condition_hawking):
            # Calcul de la puissance d'évaporation : 1 / M (plus c'est dense, plus ça évapore)
            # On normalise pour éviter des valeurs infinies
            evaporation_rate = self.hawking_coeff / (self.M[condition_hawking] + 0.1)
            
            # Perte de matière (M)
            self.M[condition_hawking] -= evaporation_rate * self.dt
            
            # --- GAIN D'ÉNERGIE (F) ---
            
            # 1. Créer une grille de taux d'évaporation de la même taille que la simulation (300, 300)
            # On initialise avec des zéros
            global_evap_grid = np.zeros_like(self.M)
            
            # 2. On remplit cette grille uniquement pour les pixels qui sont des trous noirs
            # On utilise la même condition pour indexer
            global_evap_grid[condition_hawking] = evaporation_rate
            
            # 3. Maintenant, on applique l'évaporation sur la grille entière
            # global_evap_grid est (300, 300) et self.hawking_range est (300, 300) -> ÇA MARCHE !
            self.F += (global_evap_grid * self.dt) * self.hawking_range

            # ... (Le reste reste identique)
            # Petit bruit quantique pour simuler l'aléatoire des photons
            self.F += np.random.normal(0, 0.01, resolution)

        # --- ÉTAT ---
        max_F = np.max(self.F)
        max_M = np.max(self.M)
        
        # Mise à jour de l'état textuel pour détecter l'évaporation
        if max_F > self.seuil_expansion + 1:
            self.etape = "EXPANSION (ONDE DE CHOC)"
        elif max_M > self.hawking_threshold:
            if np.any(condition_hawking):
                self.etape = "ÉVAPORATION (RAYONNEMENT HAWKING)"
            else:
                self.etape = "EFFONDREMENT (CŒUR DENSE)"
        else:
            self.etape = "DILUTION (GAZ TENU)"

        return self.M, self.F, self.rho, self.vx, self.vy, self.etape

# ==========================================
# LANCEMENT
# ==========================================
resolution = (300, 300)
dt = 0.02
universe = UniversMRCC_Stable(resolution=resolution, dt=dt)

# --- VISUALISATION ---
fig, axes = plt.subplots(2, 3, figsize=(20, 6))
fig.patch.set_color('black')

# 1. Définir la colormap "Arc-en-ciel vers Blanc"
colors = [
    (0.0, 0.0, 0.0),       # Noir (M = 0)
    (0.8, 0.2, 0.2),       # Rouge (M ~ 25% de max)
    (0.9, 0.8, 0.2),       # Jaune/Orange (M ~ 50%)
    (0.2, 0.8, 0.2),       # Vert (M ~ 60%)
    (0.2, 0.2, 0.8),       # Bleu (M ~ 75%)
    (0.5, 0.5, 1.0),       # Indigo/Violet (M ~ 85%)
    (1.0, 1.0, 1.0)        # Blanc (M = Max)
]

cmap_arc = LinearSegmentedColormap.from_list("mcc_rainbow_white", colors, N=256)
cmap_F = LinearSegmentedColormap.from_list("shock", [(0,0,0), (0.3,0.1,0.1), (1.0, 0.8, 0.0), (1.0, 0.0, 0.0)], N=256)
cmap_M = LinearSegmentedColormap.from_list("matter", [(0,0,0), (0.1,0.6,0.1), (0.9,0.9,0.9)], N=256)
cmap_vel = plt.cm.RdBu_r

# Initialisation des images avec des limites par défaut (elles seront écrasées par set_vmin/set_vmax)
# On met une valeur arbitraire (ex: 1) pour commencer
im_F = axes[0, 0].imshow(universe.F, cmap=cmap_arc, vmin=0, vmax=1, origin='lower')
axes[0, 0].set_title("Chaleur (F)", color='white', fontsize=12)

im_M = axes[0, 1].imshow(universe.M, cmap=cmap_arc, vmin=0, vmax=3.5, origin='lower')
axes[0, 1].set_title("Matière (M)", color='white', fontsize=12)

im_rho = axes[0, 2].imshow(universe.rho, cmap=cmap_arc, vmin=-1.0, vmax=1.0, origin='lower')
axes[0, 2].set_title("Densité Causale (ρ)", color='white', fontsize=12)

speed = np.sqrt(universe.vx**2 + universe.vy**2)
im_vel = axes[1, 0].imshow(speed, cmap=cmap_arc, vmin=-10, vmax=3.0, origin='lower')
axes[1, 0].set_title("Vitesse (Magnitude)", color='white', fontsize=12)

im_int = axes[1, 1].imshow(universe.F * universe.M, cmap=cmap_arc, vmin=0, vmax=3.0, origin='lower')
axes[1, 1].set_title("Interaction (F × M)", color='white', fontsize=12)

stats_text = fig.text(0.5, 0.95, "En attente...", transform=fig.transFigure, ha='center', color='white', fontsize=14, fontweight='bold')

for ax in axes.flatten():
    ax.set_facecolor('black')
    ax.set_xticks([])
    ax.set_yticks([])

def update(frame):
    # 1. Mise à jour des données
    M, F, rho, vx, vy, etape = universe.update_step()
    
    # Calcul des vitesses et interactions
    speed = np.sqrt(vx**2 + vy**2)
    interaction = F * M
    
    # --- 2. DÉFINITION DES LIMITES DYNAMIQUES (CORRIGÉ avec set_clim) ---
    eps = 1e-8  # Petit epsilon pour éviter les div/0 ou vmin=vmax=0
    
    # A. Chaleur (F)
    max_F_val = np.max(F)
    im_F.set_array(F)
    limit_F = max(max_F_val, eps) 
    im_F.set_clim(0, limit_F)  # Remplacement de set_vmin/set_vmax
    
    # B. Matière (M)
    max_M_val = np.max(M)
    im_M.set_array(M)
    limit_M = max(max_M_val, eps)
    im_M.set_clim(0, limit_M)
    
    # C. Densité Causale (Rho)
    min_rho = np.min(rho)
    max_rho = np.max(rho)
    range_rho = max(abs(min_rho), abs(max_rho), eps)
    im_rho.set_array(rho)
    im_rho.set_clim(-range_rho, range_rho)
    
    # D. Vitesse
    max_speed_val = np.max(speed)
    im_vel.set_array(speed)
    limit_speed = max(max_speed_val, eps)
    im_vel.set_clim(0, limit_speed)
    
    # E. Interaction (F x M)
    max_int_val = np.max(interaction)
    im_int.set_array(interaction)
    limit_int = max(max_int_val, eps)
    im_int.set_clim(0, limit_int)
    
    # --- 3. MISE À JOUR DU TEXTE ---
    color_text = 'orange' if "EXPANSION" in etape else ('red' if "EFFONDREMENT" in etape else ('lime' if "ÉVAPORATION" in etape else 'white'))
    stats_text.set_text(f"État : {etape}\nMrcc\nMax(M): {max_M_val:.4f} Max(F): {max_F_val:.4f}\nMax Vitesse: {max_speed_val:.4f}")
    stats_text.set_color(color_text)
    
    return (im_F, im_M, im_rho, im_vel, im_int, stats_text)

ani = animation.FuncAnimation(fig, update, frames=500, interval=30, blit=False)

plt.show()
