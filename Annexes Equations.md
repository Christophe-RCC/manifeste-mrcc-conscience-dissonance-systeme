# Annexe Technique : Formalisation Mathématique du MRCC (v2.0)

## 1. Principe Fondamental : Minimisation de l'Énergie Libre Dynamique

Le système $S$ cherche à minimiser sa **dissonance informationnelle** $D$, définie comme la divergence entre son modèle interne $P_{model}$ et la réalité observée $P_{reality}$. Cette minimisation est régie par une descente de gradient stochastique, pondérée par l'inertie temporelle du système.

$$ \frac{d\theta}{dt} = -\frac{\eta}{\tau} \cdot \nabla_{\theta} F(\theta; R) + \xi(t) $$

Où :
*   $\theta$ : Paramètres internes du système (croyances, poids synaptiques, lois).
*   $\eta$ : Taux d'adaptation intrinsèque (plasticité).
*   $\tau$ : **Facteur d'échelle temporelle** ($\tau_{neurone} \ll \tau_{société}$), introduisant la dilatation du temps d'apprentissage selon l'échelle.
*   $\xi(t)$ : Bruit stochastique (indéterminisme quantique/chaotique), empêchant la convergence vers des minima locaux rigides et favorisant l'exploration.

## 2. Définition Opérationnelle de la Dissonance ($D$) et du Seuil Critique

La dissonance $D$ est quantifiée par la **divergence de Kullback-Leibler** (KL), mais avec un **seuil critique dynamique** $D_{crit}(t)$ qui évolue avec l'état énergétique du système.

$$ D(t) = D_{KL}(P_{reality} || P_{model}) = \int P_{reality}(x) \ln \left( \frac{P_{reality}(x)}{P_{model}(x)} \right) dx $$

### Le Seuil Critique Dynamique
Le seuil de rupture n'est pas fixe. Il diminue lorsque le système est déjà en état de haute dissonance (fatigue du système), rendant l'effondrement plus probable.

$$ D_{crit}(t) = D_{base} \cdot \left( 1 - \alpha \cdot \frac{1}{1 + e^{-\beta (D(t) - D_{threshold})}} \right) $$

*   $D_{base}$ : Seuil de résistance nominal du système.
*   $\alpha$ : Coefficient de fragilisation (0 < $\alpha$ < 1).
*   $\beta$ : Raideur de la transition (sensibilité à la saturation).
*   **Interprétation :** Plus $D(t)$ est élevé, plus $D_{crit}(t)$ baisse, créant un effet de "boule de neige" vers l'effondrement si la régulation échoue.

## 3. Le Couplage Réciproque (Agent-Environnement)

Contrairement aux modèles passifs, le MRCC postule une **interaction bidirectionnelle**. L'agent modifie l'environnement, qui en retour modifie les observations.

Soit $E$ l'environnement et $A$ l'agent.
$$ \frac{d\theta_A}{dt} = -\frac{\eta_A}{\tau_A} \nabla_{\theta_A} D_A(\theta_A, E) $$
$$ \frac{d\theta_E}{dt} = -\frac{\eta_E}{\tau_E} \nabla_{\theta_E} D_E(\theta_E, A) $$

La **dissonance globale** du système couplé est :
$$ D_{total} = D_A + D_E + \lambda \cdot | \theta_A - \theta_E |^2 $$
Où $\lambda$ est la force de couplage. La minimisation de $D_{total}$ force l'agent et l'environnement à s'aligner (synchronisation), illustrant le concept d'**"Artisan de ses effets"**.

## 4. Critères de Falsification Révisés

1.  **Effondrement Prédictible :** Si $D(t) > D_{crit}(t)$, le système doit subir une transition de phase (changement brutal de $\theta$ ou effondrement structurel).
2.  **Invariance d'Échelle Temporelle :** Une fois normalisée par $\tau$, la courbe d'adaptation $\frac{d\theta}{dt}$ doit être identique pour un neurone et une société.
3.  **Efficacité du Couplage :** Un système avec couplage réciproque ($\lambda > 0$) doit atteindre un état stable avec une énergie totale dissipée inférieure à un système sans couplage (agent passif).
