#python version 3.12.10

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider

# Paramètres
nx, ny = 100, 100
dt = 0.01
n_steps = 500
alpha = 0.01
beta = 0.005
S = 1.0
F_crit = 0.5
kappa = 0.2
n = 2
delta = 0.01
sigma0 = 0.01
sigma1 = 0.02
sigma2 = 0.02
vitesse_anim = 100

# Initialisation
F = np.random.rand(nx, ny) * 0.1
M = np.zeros((nx, ny))

def diffuse(field):
    laplacian = (
        np.roll(field, 1, axis=0) + np.roll(field, -1, axis=0) +
        np.roll(field, 1, axis=1) + np.roll(field, -1, axis=1) -
        4 * field
    )
    return laplacian

# Création de la figure plus grande
fig = plt.figure(figsize=(12, 8))
ax = fig.add_subplot(111)
im = ax.imshow(M, cmap='inferno', vmin=0, vmax=10)
ax.set_title("Simulation ajustable en temps réel")
plt.colorbar(im, ax=ax)

# Zone d'info à gauche
ax_info = plt.axes([0.02, 0.5, 0.2, 0.4])  # position : gauche
ax_info.axis('off')  # pas de cadre
text_info = ax_info.text(0.5, 0.5, '', ha='center', va='center', wrap=True, fontsize=10)

# Sliders
ax_kappa = plt.axes([0.25, 0.05, 0.65, 0.03])
ax_speed = plt.axes([0.25, 0.01, 0.65, 0.03])
slider_kappa = Slider(ax_kappa, 'Kappa', 0.01, 1.0, valinit=kappa)
slider_speed = Slider(ax_speed, 'Vitesse(ms)', 50, 1000, valinit=200)

def update_params(val):
    global kappa, vitesse_anim
    kappa = slider_kappa.val
    vitesse_anim = int(slider_speed.val)

slider_kappa.on_changed(update_params)
slider_speed.on_changed(update_params)

def update(frame):
    global F, M
    sigma = sigma0 + sigma1 * F + sigma2 * M
    noise = sigma * np.random.randn(nx, ny)

    # Mise à jour de F
    lap_F = diffuse(F)
    dF = alpha * lap_F - beta * F * (1 - M) + S + noise
    F += dt * dF
    F = np.maximum(F, 0)

    # Mise à jour de M
    growth = (F - F_crit) * (F > F_crit)
    M += dt * (kappa * M ** n + growth - delta * M)
    M = np.clip(M, 0, 10)

    # Mise à jour de l’image
    im.set_data(M)

    # Calcul et affichage des infos
    mean_M = np.mean(M)
    max_M = np.max(M)
    var_M = np.var(M)
    if max_M > 8:
        state = "Phase de motifs très développés"
    elif max_M > 4:
        state = "Transition ou motifs modérés"
    elif max_M > 1:
        state = "Phase stable, peu de motifs"
    else:
        state = "Système stable, peu d'activité"

    info_str = (f"Mean M: {mean_M:.2f}\n"
                f"Max M: {max_M:.2f}\n"
                f"Var M: {var_M:.3f}\n"
                f"État: {state}")
    text_info.set_text(info_str)

    ax.set_title(f"Step {frame}")
    return [im, text_info]

from matplotlib.animation import FuncAnimation
ani = FuncAnimation(fig, update, frames=n_steps, interval=vitesse_anim, blit=True)

plt.show()
