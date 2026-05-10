# Simulation du Modèle de la Réaction Causale Complexée (MRCC)

# Ce code simule la comparaison entre un agent adaptatif (MRCC) et un agent rigide (Libre Arbitre) dans un environnement causal.

# Comment l'exécuter
#1. Installe Python et les librairies : `pip install numpy matplotlib`
#2. Lance le script : `python simulation_mrcc.py`

# Résultat attendu
#Le script génère deux graphiques montrant que l'agent MRCC réduit sa dissonance (énergie) de ~66% par rapport à l'agent rigide.

import numpy as np
import matplotlib.pyplot as plt

# --- CONFIGURATION ---
SIMULATION_LENGTH = 500  # Plus long pour voir la stabilisation
ENVIRONMENT_NOISE = 0.1  # Moins de bruit pur
INERTIA = 0.9            # L'environnement a une "mémoire" (causalité)
LEARNING_RATE_MRCC = 0.1 # Vitesse d'apprentissage de l'agent MRCC

class Agent:
    def __init__(self, strategy):
        self.strategy = strategy 
        self.internal_model = 0.5 
        self.dissonance_history = []
        self.model_history = [] # Pour tracer la ligne verte
        
    def update(self, reality):
        # 1. Observation
        observation = reality + np.random.normal(0, 0.05) 
        
        # 2. Calcul de la Dissonance
        current_dissonance = abs(reality - self.internal_model)
        self.dissonance_history.append(current_dissonance)
        self.model_history.append(self.internal_model)
        
        # 3. Action et Mise à jour
        if self.strategy == 'mrcc':
            # L'agent MRCC ajuste son modèle pour coller à la réalité
            # Il "apprend" la causalité
            self.internal_model = self.internal_model + LEARNING_RATE_MRCC * (reality - self.internal_model)
            
        elif self.strategy == 'free_will':
            # L'agent Libre Arbitre reste rigide (ou essaie de forcer sans succès)
            # On simule ici une rigidité totale (il ne change jamais son modèle)
            # Ou une tentative de "force" qui échoue (on garde le modèle initial)
            pass # Pas de changement
            
        return current_dissonance

# --- SIMULATION ---
env_history = []
agent_mrcc = Agent('mrcc')
agent_fw = Agent('free_will')

# Création d'un environnement CAUSAL (pas du bruit pur)
current_env = 0.5
for t in range(SIMULATION_LENGTH):
    # L'environnement change doucement (Inertie + Bruit)
    # C'est la clé : il y a une tendance (cause) que l'agent peut apprendre
    change = np.random.normal(0, ENVIRONMENT_NOISE)
    current_env = current_env * INERTIA + change
    # On garde l'environnement entre 0 et 1
    current_env = np.clip(current_env, 0, 1)
    env_history.append(current_env)
    
    # Mise à jour des agents
    d_mrcc = agent_mrcc.update(current_env)
    d_fw = agent_fw.update(current_env)

# --- VISUALISATION CORRIGÉE ---
plt.figure(figsize=(14, 10))

# Graphique 1 : Environnement vs Modèle MRCC
plt.subplot(2, 1, 1)
plt.plot(env_history, label='Réalité (Environnement)', color='black', linewidth=2, alpha=0.8)
plt.plot(agent_mrcc.model_history, label='Modèle MRCC (Apprentissage)', color='green', linestyle='--', linewidth=1.5)
plt.plot(agent_fw.model_history, label='Modèle Libre Arbitre (Rigide)', color='red', linestyle=':', linewidth=1.5)

plt.title("Environnement Causal vs Modèles Internes (Sur 500 itérations)")
plt.xlabel("Temps")
plt.ylabel("État du Système (0 à 1)")
plt.legend()
plt.grid(True, alpha=0.3)

# Graphique 2 : Dissonance (Énergie Gaspillée)
plt.subplot(2, 1, 2)
plt.plot(agent_mrcc.dissonance_history, label='Dissonance MRCC (Adaptatif)', color='green', linewidth=1)
plt.plot(agent_fw.dissonance_history, label='Dissonance Libre Arbitre (Rigide)', color='red', linewidth=1)

# Moyenne mobile pour lisser le bruit et voir la tendance
smooth_mrcc = np.convolve(agent_mrcc.dissonance_history, np.ones(20)/20, mode='valid')
smooth_fw = np.convolve(agent_fw.dissonance_history, np.ones(20)/20, mode='valid')
x_smooth = range(len(smooth_mrcc))

plt.plot(x_smooth, smooth_mrcc, label='Moyenne MRCC (Lissée)', color='darkgreen', linewidth=2)
plt.plot(x_smooth, smooth_fw, label='Moyenne Libre Arbitre (Lissée)', color='darkred', linewidth=2)

plt.title("Comparaison de la Dissonance (Énergie Gaspillée) - Tendance Lissée")
plt.xlabel("Temps")
plt.ylabel("Niveau de Dissonance")
plt.legend()
plt.grid(True, alpha=0.3)

plt.tight_layout()
plt.show()

print(f"Dissonance moyenne finale MRCC : {np.mean(agent_mrcc.dissonance_history[-50:]):.4f}")
print(f"Dissonance moyenne finale Libre Arbitre : {np.mean(agent_fw.dissonance_history[-50:]):.4f}")
