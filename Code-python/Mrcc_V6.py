#Python 3.12.10

import numpy as np
import scipy.ndimage as ndimage
import matplotlib.pyplot as plt
import matplotlib.animation as animation

class UniversMRCC_V6:
    def __init__(self, resolution, dt):
        self.resolution = resolution
        self.dt = dt
        
        # États du système (2D)
        self.M = np.zeros(resolution)
        self.F = np.zeros(resolution)
        self.v_M = np.zeros(resolution)
        
        # Paramètres
        self.M_planck = 1.0
        self.beta = 1.8
        self.epsilon = 1e-10
        self.mu = 1.0
        self.gamma_fric = 0.05
        self.lambda_accum = 0.4
        self.gamma_bounce = 1.0
        self.D_base = 1.0
        self.noise_scale = 0.01
        
        self.mode = 'nearest' 

    def update_step(self):
        # --- 1. CALCUL DE LA DIFFUSION DE F ---
        D = self.D_base + 0.5 * self.M
        
        # Dérivées (Sobel) : axis=0 est vertical (y), axis=1 est horizontal (x)
        dF_dy = ndimage.sobel(self.F, axis=0, mode=self.mode)
        dF_dx = ndimage.sobel(self.F, axis=1, mode=self.mode)
        
        dD_dy = ndimage.sobel(D, axis=0, mode=self.mode)
        dD_dx = ndimage.sobel(D, axis=1, mode=self.mode)
        
        # Calculs de divergence (évitant toute ambiguïté de shape)
        term_X = D * dF_dx
        term_Y = D * dF_dy
        
        div_X = ndimage.sobel(term_X, axis=1, mode=self.mode)
        div_Y = ndimage.sobel(term_Y, axis=0, mode=self.mode)
        
        diffusion_F = div_X + div_Y
        
        # --- Relaxation et Bruit ---
        relaxation_F = -0.1 * self.F
        noise_F = np.random.normal(0, self.noise_scale, self.F.shape)
        source_F = 0.05 
        
        # Mise à jour F
        self.F += self.dt * (diffusion_F + relaxation_F + noise_F + source_F)
        self.F = np.clip(self.F, -2.0, 3.0)

        # --- 2. FORCE D'ACCUMULATION ---
        force_accum = self.lambda_accum * np.maximum(0, self.F - 0.5)

        # --- 3. PRESSION DE SATURATION ---
        delta_M = self.M_planck - self.M
        pressure = np.zeros_like(self.M)
        
        mask_saturating = delta_M > 0.001
        if np.any(mask_saturating):
            pressure[mask_saturating] = self.gamma_bounce / (
                np.power(delta_M[mask_saturating], self.beta) + self.epsilon
            )
        
        # --- 4. INTÉGRATION DE M ---
        accel_M = (force_accum - pressure) / self.mu
        self.v_M += self.dt * (accel_M - self.gamma_fric * self.v_M)
        self.M += self.dt * self.v_M
        
        # --- 5. SÉCURITÉ ---
        if np.any(self.M > self.M_planck * 1.05):
            self.v_M[self.M > self.M_planck * 1.05] *= 0.1
            self.M = np.clip(self.M, -10, self.M_planck * 1.1)
            
        return self.M, self.F

# --- LANCEMENT ---
resolution = (120, 120)
dt = 0.05
universe = UniversMRCC_V6(resolution=resolution, dt=dt)

# --- INITIALISATION SANS INDICES   DANS LES CALCULS ---
# On définit les variables de centre explicitement pour éviter le bug d'interface
cy = resolution[0] // 2  # Coordonnée Y du centre
cx = resolution[1] // 2  # Coordonnée X du centre

# Création de la grille
y, x = np.ogrid[:resolution[0], :resolution[1]]

# Calcul de la distance : 
# On soustrait cx à x (colonnes) et cy à y (lignes)
# AUCUN index  ou  n'est utilisé ici, juste des variables nommées
dist = np.sqrt((x - cx)**2 + (y - cy)**2)

# Condition initiale : Source au centre
universe.F += 3.0 * np.exp(-(dist**2) / 150.0)

# --- VISUALISATION ---
fig, (ax_F, ax_M) = plt.subplots(1, 2, figsize=(12, 5))
fig.patch.set_facecolor('black')

im_F = ax_F.imshow(universe.F, cmap='RdBu_r', vmin=-2, vmax=3, origin='lower')
im_M = ax_M.imshow(universe.M, cmap='Greys', vmin=0, vmax=1.0, origin='lower')

ax_F.set_title("Énergie Libre (F)", color='white', fontsize=12)
ax_M.set_title("Mémoire (M)", color='white', fontsize=12)

ax_F.set_facecolor('black')
ax_M.set_facecolor('black')
ax_F.set_xticks([]); ax_F.set_yticks([])
ax_M.set_xticks([]); ax_M.set_yticks([])

stats_text = fig.text(0.5, 0.92, 'Initialisation...', transform=fig.transFigure, ha='center', color='white', fontsize=11)

def update(frame):
    M, F = universe.update_step()
    
    im_F.set_array(F)
    im_M.set_array(M)
    
    max_M = np.max(M)
    max_F = np.max(F)
    min_F = np.min(F)
    
    stats_text.set_text(f"Frame: {frame}\nM Max: {max_M:.4f} (Limit: {universe.M_planck})\nF Max: {max_F:.3f} (Min: {min_F:.3f})")
    
    return im_F, im_M, stats_text

ani = animation.FuncAnimation(fig, update, frames=800, interval=30, blit=False)
plt.show()
