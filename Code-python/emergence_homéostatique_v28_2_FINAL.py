import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from collections import deque
import time

# --- CONFIGURATION ---
PISTE_INERTIA = 0.995       
PISTE_NOISE = 0.15          
AGENT_INERTIA = 0.10        
FRICTION = 0.95             
NOISE_AGENT = 0.02          

MEMORY_SIZE = 50            
TOTAL_STEPS = 2000
OUTPUT_IMAGE = "resultats_emergence_homéostatique_v28_2_FINAL.png"
SHOW_REALTIME = True

class HomoeostaticAgent:
    def __init__(self):
        self.x_agent = 0.0
        self.vx_agent = 0.0
        
        self.x_piste = 0.0
        self.vx_piste = 0.0
        
        self.piste_memory = deque(maxlen=MEMORY_SIZE)
        
        # Historiques
        self.dissonance_history = []
        self.memory_centroid_history = []
        self.pos_agent_history = []
        self.pos_piste_history = []
        self.pressure_history = []
        
        # Historiques vitesses
        self.vx_agent_history = []
        self.vx_piste_history = []

    def update_memory(self):
        self.piste_memory.append(self.x_piste)

    def get_memory_centroid(self):
        if len(self.piste_memory) < 2:
            return 0.0
        return np.mean(list(self.piste_memory))

    def step(self):
        # 1. PISTE
        random_step = np.random.randn() * PISTE_NOISE
        self.vx_piste *= PISTE_INERTIA
        self.vx_piste += random_step * 0.5
        self.x_piste += self.vx_piste
        
        # 2. MÉMOIRE
        self.update_memory()
        
        # 3. CŒUR DE L'AGENT
        target_centroid = self.get_memory_centroid()
        self.memory_centroid_history.append(target_centroid)
        
        pressure = self.x_agent - target_centroid
        self.pressure_history.append(pressure)
        
        # 4. ACTION
        force = -pressure * 0.15 
        self.vx_agent *= AGENT_INERTIA
        self.vx_agent += force
        self.vx_agent += np.random.randn() * NOISE_AGENT
        self.vx_agent *= FRICTION
        self.vx_agent = np.clip(self.vx_agent, -2.0, 2.0)
        self.x_agent += self.vx_agent
        
        # 5. ÉNERGIE
        internal_energy = (pressure ** 2) * 1.0 
        external_error = (self.x_agent - self.x_piste) ** 2
        total_energy = internal_energy + (external_error * 0.2)
        
        # Stockage
        self.dissonance_history.append(total_energy)
        self.pos_agent_history.append(self.x_agent)
        self.pos_piste_history.append(self.x_piste)
        self.vx_agent_history.append(self.vx_agent)
        self.vx_piste_history.append(self.vx_piste)

def run_simulation_realtime():
    print(">>> DÉMARRAGE : V28.2 (Final - Grille épurée)")
    
    system = HomoeostaticAgent()
    
    plt.ion()
    fig, axs = plt.subplots(3, 2, figsize=(14, 10))
    fig.suptitle('Simulation Homéostatique - V28.2 (Temps Réel)', fontsize=16)

    # --- 1. Trajectoires (Haut Gauche) ---
    ax_traj = axs[0, 0]
    line_agent, = ax_traj.plot([], [], color='green', linestyle='-', label='Agent', linewidth=2)
    line_piste, = ax_traj.plot([], [], color='orange', linestyle='--', label='Piste', linewidth=2)
    line_mem, = ax_traj.plot([], [], color='purple', linestyle=':', label='Mémoire (Cible)', linewidth=2)
    ax_traj.set_title('Trajectoires (Position vs Temps)')
    ax_traj.set_xlabel('Temps'); ax_traj.set_ylabel('Position X')
    ax_traj.legend(); ax_traj.grid(True, alpha=0.3)
    ax_traj.set_xlim(0, TOTAL_STEPS)
    ax_traj.set_ylim(-4000, 4000)

    # --- 2. Espace des Phases (Haut Droite - CORRIGÉ) ---
    ax_space = axs[0, 1]
    # On trace la relation X_agent vs X_piste
    # Si l'agent suit la piste, la ligne suit la diagonale
    line_phase, = ax_space.plot([], [], color='blue', marker='.', markersize=1, linestyle='-', label='Trajectoire (X_agent vs X_piste)')
    
    # Ligne de référence (diagonale parfaite)
    # On la trace une fois avec des données fixes
    lim = 2000
    ax_space.plot([-lim, lim], [-lim, lim], color='gray', linestyle='--', alpha=0.5, label='Corrélation parfaite')
    
    ax_space.set_title('Espace des Phases (Agent vs Piste)')
    ax_space.set_xlabel('Position Agent'); ax_space.set_ylabel('Position Piste')
    ax_space.legend(); ax_space.grid(True, alpha=0.3)
    ax_space.set_xlim(-lim, lim); ax_space.set_ylim(-lim, lim)
    ax_space.set_aspect('equal', 'box') # Important pour voir la diagonale à 45°

    # --- 3. Énergie (Milieu Gauche) ---
    ax_energy = axs[1, 0]
    line_energy, = ax_energy.plot([], [], color='red', linestyle='-', label='Énergie Totale')
    line_internal, = ax_energy.plot([], [], color='blue', linestyle='-', label='Énergie Interne', alpha=0.7)
    ax_energy.set_title('Énergie (Dissonance)')
    ax_energy.set_xlabel('Temps'); ax_energy.set_ylabel('Énergie')
    ax_energy.legend(); ax_energy.grid(True, alpha=0.3)
    ax_energy.set_xlim(0, TOTAL_STEPS)
    ax_energy.set_ylim(-5, 100000)

    # --- 4. Vitesse
    # On réutilise la case du milieu droite pour la vitesse
    ax_speed = axs[1, 1]
    line_v_agent, = ax_speed.plot([], [], color='green', linestyle='-', label='Vitesse Agent')
    line_v_piste, = ax_speed.plot([], [], color='orange', linestyle='-', label='Vitesse Piste')
    ax_speed.set_title('Vitesse (Agent vs Piste)')
    ax_speed.set_xlabel('Temps'); ax_speed.set_ylabel('Vitesse')
    ax_speed.grid(True, alpha=0.3)
    ax_speed.set_xlim(0, TOTAL_STEPS); ax_speed.set_ylim(-5, 5)
    ax_speed.legend()

    # --- 5. Statistiques (Bas Gauche) ---
    ax_stat = axs[2, 0]
    ax_stat.set_title('Statistiques en direct')
    ax_stat.axis('off')
    stat_text = ax_stat.text(0.1, 0.5, "", transform=ax_stat.transAxes, fontsize=12, va='center')

    # --- 6. Vide ou autre (Bas Droite) ---
    # On laisse vide ou on met un petit résumé
    ax_empty = axs[2, 1]
    ax_empty.axis('off')
    ax_empty.text(0.5, 0.5, "Visualisation Temps Réel\n(Suppression graphique mémoire)", 
                  ha='center', va='center', fontsize=12, alpha=0.5)

    x_data = []
    start_time = time.time()

    try:
        for i in range(TOTAL_STEPS):
            system.step()
            x_data.append(i)
            
            # Mise à jour Trajectoires
            line_agent.set_data(x_data, system.pos_agent_history)
            line_piste.set_data(x_data, system.pos_piste_history)
            line_mem.set_data(x_data, system.memory_centroid_history)
            
            # Mise à jour Espace des Phases (X_agent, X_piste)
            line_phase.set_data(system.pos_agent_history, system.pos_piste_history)
            
            # Mise à jour Énergie
            if len(system.dissonance_history) > 0:
                line_energy.set_data(x_data, system.dissonance_history)
                pressure_vals = system.pressure_history
                energy_internal = [p**2 for p in pressure_vals]
                line_internal.set_data(x_data, energy_internal)
            
            # Mise à jour Vitesse
            line_v_agent.set_data(x_data, system.vx_agent_history)
            line_v_piste.set_data(x_data, system.vx_piste_history)

            # Stats
            if i > 0:
                avg_energy = np.mean(system.dissonance_history[-50:]) if len(system.dissonance_history) > 50 else np.mean(system.dissonance_history)
                current_pressure = system.pressure_history[-1]
                text_content = f"Étape: {i}\nÉnergie Moy: {avg_energy:.4f}\nPression Act: {current_pressure:.4f}\nAgent X: {system.x_agent:.2f}\nPiste X: {system.x_piste:.2f}"
                stat_text.set_text(text_content)

            plt.pause(0.001)
            
            if i % 200 == 0:
                print(f"Étape {i}: Énergie Moyenne = {np.mean(system.dissonance_history[-50:]):.4f}")

    except KeyboardInterrupt:
        print("\nSimulation arrêtée par l'utilisateur.")

    plt.ioff()
    plt.tight_layout()
    
    fig.canvas.draw()
    fig.canvas.flush_events()
    
    # Sauvegarde de la grille complète (optionnel, pour debug)
    # plt.savefig("debug_full_grid.png", dpi=150) 

    if OUTPUT_IMAGE:
        # --- CRÉATION D'UNE NOUVELLE FIGURE UNIQUEMENT POUR LE GRAPHIQUE 1 ---
        fig_final, ax_final = plt.subplots(figsize=(16, 9))
        
        # Reproduction des données pour la figure finale
        ax_final.plot(system.pos_agent_history, color='green', label='Agent', linewidth=2)
        ax_final.plot(system.pos_piste_history, color='orange', linestyle='--', label='Piste (Cible)', linewidth=2)
        ax_final.plot(system.memory_centroid_history, color='purple', linestyle=':', label='Mémoire (Cible)', linewidth=2)
        
        ax_final.set_title(f'Trajectoire Émergente Homéostatique (V28.2)\nMémoire={MEMORY_SIZE}, Steps={TOTAL_STEPS}', fontsize=16, fontweight='bold')
        ax_final.set_xlabel('Itérations (Temps)', fontsize=12)
        ax_final.set_ylabel('Position X', fontsize=12)
        ax_final.legend(fontsize=11)
        ax_final.grid(True, alpha=0.3)
        
        # Sauvegarde
        plt.savefig(OUTPUT_IMAGE, dpi=150, bbox_inches='tight')
        print(f"Graphique final sauvegardé (Grand Trajet) : {OUTPUT_IMAGE}")
        plt.close(fig_final)

    # Affichage de la grille interactive à la fin
    plt.show()

if __name__ == "__main__":
    if SHOW_REALTIME:
        run_simulation_realtime()
    else:
        print("Mode temps réel désactivé.")
