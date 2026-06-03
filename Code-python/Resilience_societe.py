import numpy as np
import matplotlib.pyplot as plt

# --- CONFIGURATION ---
TAILLE_GRILLE = 60
DUREE_SIM = 1000
# VOISINS = 8 (calculé automatiquement)

# --- PARAMÈTRES DE BASE ---
DENSITE_INITIALE = 0.40
ENERGIE_INITIALE = 0.95

# --- PARAMÈTRES DU CHOC ---
AMPLITUDE_CHOC_MAX = 0.90
DUREE_CHOC = 100
VITESSE_CHOC = 20.5

# --- CORRECTION CRITIQUE ---
COEFFICIENT_DEFENSE = 0.0004
COUT_MAINTENANCE_BASE = 0.0015
COUT_DEFENSE_INDIVIDUEL = 0.0001 
SEUIL_MORTALITE = 0.05 
FACTEUR_DEGRADATION = 0.8

# NOUVEAU : PARAMÈTRES DE REPRODUCTION
SEUIL_NAISSANCE_MIN = 2
SEUIL_NAISSANCE_MAX = 3
PROBA_NAISSANCE = 0.4
ENERGIE_NAISSANCE = 0.5

def lancer_simulation_survie(seed_val):
    np.random.seed(seed_val)
    grille_vie = np.random.rand(TAILLE_GRILLE, TAILLE_GRILLE) > (1 - DENSITE_INITIALE)
    grille_energie = np.full((TAILLE_GRILLE, TAILLE_GRILLE), ENERGIE_INITIALE)
    
    hist_chaos_externe = [] 
    hist_chaos_local = []   
    hist_vie = []
    
    step_choc = 300
    
    for i in range(DUREE_SIM):
        alive_count = np.sum(grille_vie)
        total_energie = np.sum(grille_energie * grille_vie)
        avg_energie = total_energie / (alive_count + 1e-9)

        # 1. CHAOS EXTERNE
        # 1. CHAOS EXTERNE (La tempête : Montée -> Pic -> Descente)
        if i < step_choc:
            # Phase 1 : Calme
            chaos_externe = 0.0
            
        elif i < step_choc + DUREE_CHOC:
            # Phase 2 : Montée (L'attaque)
            prog = (i - step_choc) / DUREE_CHOC
            # On monte exponentiellement jusqu'à 0.90
            chaos_externe = AMPLITUDE_CHOC_MAX * (1 - np.exp(-prog * VITESSE_CHOC))
            
        elif i < step_choc + DUREE_CHOC + DUREE_CHOC:
            # Phase 3 : Descente (La tempête s'éloigne)
            # On commence à descendre après 300 frames de pic
            # On prend la valeur actuelle et on la fait redescendre exponentiellement
            # Ou simplement on inverse la courbe
            prog_desc = (i - (step_choc + DUREE_CHOC)) / DUREE_CHOC
            # On descend de 0.90 vers 0
            # Formule : Max * exp(-vitesse * temps)
            chaos_externe = AMPLITUDE_CHOC_MAX * np.exp(-prog_desc * VITESSE_CHOC)
            
        else:
            # Phase 4 : Retour au calme total
            chaos_externe = 0.0
            
        # 2. DÉFENSE
        capacite_dissipation = alive_count * avg_energie * COEFFICIENT_DEFENSE
        chaos_local = max(0.0, chaos_externe - capacite_dissipation)
        
        hist_chaos_externe.append(chaos_externe)
        hist_chaos_local.append(chaos_local)
        
        # Calcul des voisins (réutilisé pour la reproduction)
        voisins_vivants = np.zeros_like(grille_vie, dtype=int)
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0: continue
                voisins_vivants += np.roll(np.roll(grille_vie, dx, axis=0), dy, axis=1)

        nouvelle_grille_vie = grille_vie.copy()
        nouvelle_grille_energie = grille_energie.copy()

        for x in range(TAILLE_GRILLE):
            for y in range(TAILLE_GRILLE):
                if not grille_vie[x, y]: 
                    continue
                
                nb_voisins = voisins_vivants[x, y]
                energie = grille_energie[x, y]
                
                risque = 0.0
                
                # A. Mortalité de base
                risque += 0.0005
                
                # B. Mortalité par Chaos
                if chaos_local > SEUIL_MORTALITE:
                    depassement = chaos_local - SEUIL_MORTALITE
                    risque += depassement * FACTEUR_DEGRADATION
                
                # C. Mortalité par Surpopulation
                if nb_voisins > 6:
                    risque += 0.02 * (nb_voisins - 6)
                
                # Application de la mort
                if np.random.rand() < risque:
                    nouvelle_grille_vie[x, y] = False
                    nouvelle_grille_energie[x, y] = 0
                else:
                    # D. DÉPENSE ÉNERGÉTIQUE
                    cout_total = COUT_MAINTENANCE_BASE
                    gain_nutrition = 0.003
                    
                    nouvelle_grille_energie[x, y] = min(1.0, max(0, energie - cout_total + gain_nutrition))
                    
                    if nouvelle_grille_energie[x, y] <= 0:
                        nouvelle_grille_vie[x, y] = False
        
        # --- NOUVEAU BLOC DE REPRODUCTION ---
        # On applique la reproduction sur la grille temporaire (nulle part ailleurs)
        for x in range(TAILLE_GRILLE):
            for y in range(TAILLE_GRILLE):
                if not grille_vie[x, y] and nouvelle_grille_vie[x, y] == False:
                    # Si c'est une cellule morte (dans la grille actuelle)
                    # Et qu'on a calculé les voisins (qui sont basés sur la grille actuelle)
                    if SEUIL_NAISSANCE_MIN <= voisins_vivants[x, y] <= SEUIL_NAISSANCE_MAX:
                        if np.random.rand() < PROBA_NAISSANCE:
                            nouvelle_grille_vie[x, y] = True
                            nouvelle_grille_energie[x, y] = ENERGIE_NAISSANCE

        grille_vie = nouvelle_grille_vie
        grille_energie = nouvelle_grille_energie
        
        densite = np.sum(grille_vie) / (TAILLE_GRILLE * TAILLE_GRILLE)
        hist_vie.append(densite)

    return hist_vie, hist_chaos_externe, hist_chaos_local

# --- LANCEMENT ---
plt.figure(figsize=(14, 8))

vie, chaos_externe, chaos_local = lancer_simulation_survie(seed_val=42)

# Graphique 1
plt.subplot(2, 1, 1)
plt.plot(vie, label="Densité de Vie", color='green', linewidth=2)
plt.axvline(300, color='black', linestyle='--', alpha=0.3, label="Début de la tempête")
plt.title("Survie : La Vie résiste et se reproduit", fontsize=14)
plt.xlabel("Temps (Steps)")
plt.ylabel("Densité de Vie")
plt.legend()
plt.grid(True, alpha=0.3)

# Graphique 2
plt.subplot(2, 1, 2)
plt.plot(chaos_externe, label="Chaos Externe", color='red', linestyle='--', linewidth=2)
plt.plot(chaos_local, label="Chaos Local", color='orange', linewidth=2, alpha=0.8)
plt.axvline(300, color='black', linestyle=':', alpha=0.3)
plt.title("Chaos : Tempete, Crise", fontsize=12)
plt.xlabel("Temps (Steps)")
plt.ylabel("Niveau de Chaos")
plt.legend()
plt.grid(True, alpha=0.3)
plt.ylim(bottom=-0.05, top=1.05)

plt.tight_layout()
plt.show()

print("\n--- RÉSULTATS : SURVIE AVEC REPRODUCTION ---")
print(f"Chaos Externe Max : {max(chaos_externe):.2f}")
print(f"Chaos Local Max : {max(chaos_local):.4f}")
print(f"Densité de Vie Finale : {vie[-1]:.4f}")
print(f"Densité de Vie Initiale : {vie[1]:.4f}")

if vie[-1] > 0.2: # Si on a gardé plus de 20%
    print("SUCCÈS : La population est stable grâce à la reproduction")
else:
    print("⚠️  Échec : La population a trop diminué (vérifiez les probas de naissance).")
