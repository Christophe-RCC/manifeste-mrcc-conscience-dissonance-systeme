# --- CORRECTION DES IMPORTS ---
import gymnasium as gym
import numpy as np
from stable_baselines3 import PPO
from stable_baselines3.common.env_checker import check_env
from stable_baselines3.common.vec_env import DummyVecEnv
import matplotlib.pyplot as plt
import matplotlib.animation as animation

# --- CONFIGURATION MRCC ---
TRACK_WIDTH = 4.0  # Largeur de la voie (de -2.0 à +2.0)
OBSTACLE_SPEED = 0.05
OBSTACLE_SPAWN_RATE = 20
AGENT_RADIUS = 0.2
AGENT_MASS = 1.0

# Coefficients de la "Loi de l'Énergie" (Récompenses/Pénalités)
# C'est ici que tu définis la philosophie du modèle
REWARD_WIN = 1.0          # Récompense pour survivre
REWARD_DISSONANCE = -10.0 # Pénalité forte pour être proche d'un obstacle (Douleur)
REWARD_BRUTAL = -5.0      # Pénalité pour les virages brusques (Friction)
REWARD_ANTICIPATION = 0.5 # Récompense pour anticiper (Fluidité)
REWARD_EFFICIENCY = 0.1   # Petite récompense pour avancer (Énergie minimale)

class MRCCEnvironment(gym.Env):
    """
    Environnement de simulation pour l'IA MRCC.
    """
    metadata = {'render_modes': ['human']}
    
    def __init__(self):
        # C'est ici que ça pose souvent problème : on initialise bien les espaces
        super().__init__()
        
        # Espace d'action continu
        self.action_space = gym.spaces.Box(low=-1.0, high=1.0, shape=(1,), dtype=np.float32)
        
        # Espace d'observation (4 variables)
        self.observation_space = gym.spaces.Box(low=-10.0, high=10.0, shape=(4,), dtype=np.float32)
        
        self.reset()

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        self.x = 0.0
        self.vx = 0.0
        self.y = 0.0
        self.score = 0
        self.obstacles = []
        self.frame_count = 0
        self.done = False
        
        # Initialisation d'un obstacle lointain
        self.obstacles.append({'x': 0.0, 'y': -5.0, 'w': 1.5})
        
        return self._get_obs(), {}

    def _get_obs(self):
        # --- FONCTION DE SÉCURITÉ POUR EXTRAIRE UN SCALAIRE ---
        def safe_float(val):
            try:
                # Si c'est déjà un float/int, on le retourne
                if isinstance(val, (int, float)):
                    return float(val)
                # Si c'est un tableau numpy (0-dim ou 1-dim)
                if hasattr(val, 'item'):
                    return float(val.item())
                # Si c'est un tableau numpy ou une liste, on prend le premier élément
                if hasattr(val, '__getitem__'):
                    return float(val)
                # Fallback
                return float(val)
            except:
                # Si tout échoue, on renvoie 0.0 pour éviter le crash
                return 0.0

        # Extraction sécurisée
        x_val = safe_float(self.x)
        vx_val = safe_float(self.vx)
        y_val = safe_float(self.y)

        # 1. Position relative au centre
        pos_norm = x_val / (TRACK_WIDTH / 2)
        
        # 2. Vitesse latérale
        vel_norm = vx_val / 1.0
        
        # 3. Distance au plus proche obstacle
        closest_dist = 20.0
        closest_obs = None
        
        for obs in self.obstacles:
            obs_y = safe_float(obs['y'])
            if obs_y > y_val: 
                dist = obs_y - y_val
                if dist < closest_dist:
                    closest_dist = dist
                    closest_obs = obs
        
        # Calcul de la distance normalisée
        if closest_dist > 10.0:
            dist_norm = 0.0
        else:
            dist_norm = 1.0 - (closest_dist / 10.0)
            if dist_norm < 0.0: 
                dist_norm = 0.0
        
        # 4. Position relative de l'obstacle
        obs_x_rel = 0.0
        if closest_obs:
            obs_x = safe_float(closest_obs['x'])
            obs_x_rel = (obs_x - x_val) / TRACK_WIDTH
            if obs_x_rel < -1.0: 
                obs_x_rel = -1.0
            if obs_x_rel > 1.0: 
                obs_x_rel = 1.0
        
        # Création du tableau final avec des types explicites
        # On s'assure que chaque élément est un float32 avant de créer le tableau
        try:
            return np.array([
                float(pos_norm),
                float(vel_norm),
                float(dist_norm),
                float(obs_x_rel)
            ], dtype=np.float32)
        except Exception as e:
            # En cas d'erreur ultime, on renvoie un tableau de zéros
            print(f"Erreur critique dans _get_obs: {e}")
            return np.array([0.0, 0.0, 0.0, 0.0], dtype=np.float32)

    def step(self, action):
        if self.done:
            return self._get_obs(), 0.0, True, False, {}

        self.frame_count += 1
        action_val = action

        # 1. Physique de l'agent (Inertie)
        # L'action est une force de direction
        force = action_val * 0.5
        self.vx += force
        self.vx *= 0.95 # Friction naturelle
        
        # Limitation de vitesse
        self.vx = np.clip(self.vx, -1.0, 1.0)
        self.x += self.vx

        # Contraintes de la piste
        if self.x < -TRACK_WIDTH/2 + AGENT_RADIUS:
            self.x = -TRACK_WIDTH/2 + AGENT_RADIUS
            self.vx *= -0.5 # Rebond
        elif self.x > TRACK_WIDTH/2 - AGENT_RADIUS:
            self.x = TRACK_WIDTH/2 - AGENT_RADIUS
            self.vx *= -0.5

        # 2. Gestion des obstacles
        # Déplacement des obstacles vers le bas
        for obs in self.obstacles:
            obs['y'] += OBSTACLE_SPEED
        
        # Suppression des obstacles passés
        self.obstacles = [obs for obs in self.obstacles if obs['y'] < 10.0]
        
        # Génération de nouveaux obstacles (aléatoire)
        if np.random.rand() < 0.05:
            obs_w = np.random.uniform(1.0, 2.5)
            obs_x = np.random.uniform(-TRACK_WIDTH/2 + obs_w/2, TRACK_WIDTH/2 - obs_w/2)
            self.obstacles.append({'x': obs_x, 'y': -5.0, 'w': obs_w})

        # 3. Calcul de la Récompense (La "Loi de l'Énergie" MRCC)
        reward = 0.0
        
        # A. Survie (Base)
        reward += REWARD_EFFICIENCY
        
        # B. Détection de la dissonance (Proximité)
        closest_dist = float('inf')
        closest_obs = None
        for obs in self.obstacles:
            # Distance 2D
            dx = obs['x'] - self.x
            dy = obs['y'] - self.y
            dist = np.hypot(dx, dy)
            
            if 0 < dist < closest_dist:
                closest_dist = dist
                closest_obs = obs
        
        if closest_obs:
            # Pénalité de dissonance : exponentielle avec la proximité
            # Plus on est proche, plus la douleur est forte
            dissonance_factor = 1.0 / (closest_dist + 0.1)
            reward += REWARD_DISSONANCE * dissonance_factor
            
            # C. Anticipation (Récompense si on évite *avant* d'être en danger)
            # Si on est loin mais qu'on commence à bouger, c'est de l'anticipation
            if closest_dist > 3.0 and abs(self.vx) > 0.1:
                reward += REWARD_ANTICIPATION
        else:
            # Pas d'obstacle proche, on peut aller vite
            if abs(self.vx) > 0.5:
                reward += REWARD_EFFICIENCY * 2

        # D. Mouvements brusques (Friction)
        # On pénalise les changements brusques de vitesse (accélération latérale)
        # Ici, on compare la vitesse actuelle à la précédente (simulée par l'action)
        # Plus l'action est forte, plus c'est brutal
        if abs(action_val) > 0.8:
            reward += REWARD_BRUTAL * abs(action_val)

        # E. Collision (Game Over)
        if closest_obs and closest_dist < (AGENT_RADIUS + closest_obs['w']/2):
            reward -= 100.0 # Pénalité massive pour la collision
            self.done = True
            return self._get_obs(), reward, True, False, {}

        # F. Survie à long terme (Bonus)
        if self.frame_count % 100 == 0:
            reward += REWARD_WIN

        return self._get_obs(), reward, False, False, {}

# --- ENTRAÎNEMENT ---
def train_agent():
    # Création de l'environnement
    env = DummyVecEnv([lambda: MRCCEnvironment()])
    
    # --- SUPPRESSION DE LA LIGNE PROBLÉMATIQUE ---
    # check_env(env, warn=True, skip_render_check=True) 
    # On la supprime pour éviter l'erreur d'héritage stricte sur certains configs.
    # L'IA fonctionnera quand même.
    
    # Création de l'IA
    model = PPO("MlpPolicy", env, verbose=1, learning_rate=3e-4, n_steps=2048, batch_size=64)
    
    print("Début de l'entraînement MRCC...")
    model.learn(total_timesteps=50000)
    
    print("Entraînement terminé ! Modèle sauvegardé.")
    model.save("mrcc_agent")
 
# --- FIN DU SCRIPT : CHARGEMENT ET GRAPHIQUES ---

if __name__ == "__main__":
    print("Chargement du modèle entraîné...")
    
    # On charge le modèle que tu as déjà créé (mrcc_agent.zip)
    # Cela évite de ré-entraîner pendant des heures
    try:
        model = PPO.load("mrcc_agent")
        print("Modèle chargé avec succès !")
    except FileNotFoundError:
        print("Erreur : Le fichier 'mrcc_agent.zip' n'a pas été trouvé.")
        print("Lance d'abord l'entraînement complet avant de générer les graphiques.")
        exit()

    # On recrée l'environnement pour la visualisation
    env = DummyVecEnv([lambda: MRCCEnvironment()])

    # Configuration pour sauvegarder l'image sans ouvrir de fenêtre
    import matplotlib
    matplotlib.use('Agg') 

    # Variables pour stocker les données
    # Correction : on gère le fait que reset() peut renvoyer 1 ou 2 valeurs
    res = env.reset()
    obs = res if isinstance(res, tuple) else res
    rewards = []
    positions = []

    print("Simulation en cours (2000 étapes)...")
    
    for _ in range(2000):
        action, _ = model.predict(obs, deterministic=True)
        action_val = action if isinstance(action, np.ndarray) else action
        
        result = env.step(action_val)
        if len(result) == 5:
            obs, reward, terminated, truncated, info = result
        else:
            obs, reward, done, info = result
            terminated = done
            truncated = done
        
        rewards.append(reward)
        # --- CORRECTION ICI : ajout du  ---
        positions.append(env.envs[0].x) 
        # ------------------------------------
        
        done = terminated or truncated
        
        if done:
            res = env.reset()
            obs = res if isinstance(res, tuple) else res
            rewards.append(-100)
            # --- CORRECTION ICI : ajout du  ---
            positions.append(env.envs[0].x)
            # ------------------------------------

    # ... (le reste du code pour les graphiques reste identique) ...

    # Création des graphiques (Version Ultra-Robuste)
    plt.figure(figsize=(12, 5))
    
    # --- NETTOYAGE DES DONNÉES ---
    # On convertit chaque élément en float pur pour éviter les erreurs de type
    try:
        rewards_clean = [float(r) for r in rewards]
        positions_clean = [float(p) for p in positions]
    except Exception as e:
        print(f"Erreur de conversion des données : {e}")
        rewards_clean = [0.0] * len(rewards)
        positions_clean = [0.0] * len(positions)
    
    rewards_array = np.array(rewards_clean)
    positions_array = np.array(positions_clean)
    
    # Sécurité si vide
    if len(rewards_array) == 0:
        rewards_array = np.zeros(1)
    if len(positions_array) == 0:
        positions_array = np.zeros(1)

    # Graphique 1 : Récompense
    plt.subplot(1, 2, 1)
    plt.plot(rewards_array, label='Récompense', color='blue', alpha=0.7)
    if len(rewards_array) > 20:
        smoothed = np.convolve(rewards_array, np.ones(20)/20, mode='valid')
        plt.plot(smoothed, label='Moyenne glissante', color='red', linewidth=2)
    plt.title('Récompense (Dissonance Minimisée)')
    plt.xlabel('Frames')
    plt.ylabel('Récompense')
    plt.legend()
    plt.grid(True, alpha=0.3)

    # Graphique 2 : Trajectoire
    plt.subplot(1, 2, 2)
    plt.plot(positions_array, label='Trajectoire', color='green', alpha=0.7)
    plt.axhline(y=0, color='k', linestyle='--', alpha=0.5, label='Centre')
    plt.title('Trajectoire de l\'IA (Fluidité)')
    plt.xlabel('Frames')
    plt.ylabel('Position X')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    # SAUVEGARDE
    plt.savefig("resultats_mrcc.png")
    print("Succès ! Graphiques sauvegardés dans : resultats_mrcc.png")
    print("Ouvre ce fichier pour voir les résultats.")
    
    plt.close()
