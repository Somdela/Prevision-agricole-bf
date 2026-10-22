# Anticiper la campagne agricole au Burkina Faso

Tableau de bord de démonstration du projet de data science de **Romba Abdoul Aziz** (École Mohammadia d'Ingénieurs). Il présente :

- la prévision des prix des céréales ;
- la prévision de la sécheresse en cours de saison ;
- la prévision des rendements avant la récolte.

Toutes ces prévisions reposent sur des données ouvertes.

## Contenu

| Fichier | Rôle |
| --- | --- |
| `app.py` | l'application Streamlit (lecture et affichage des résultats) |
| `requirements.txt` | les bibliothèques à installer |
| `data/` | les résultats produits dans Google Colab (étapes 8 à 12 du projet) |

Les modèles sont entraînés dans Colab ; l'application ne fait qu'afficher leurs résultats. Pour mettre à jour un résultat, remplacer le fichier correspondant dans `data/`.

## Sources

- Prix : Programme alimentaire mondial (HDX).
- Rendements : HarvestStat Africa, FAOSTAT.
- Pluie : CHIRPS v3.
- Température et humidité : ERA5-Land.
- Végétation : MODIS NDVI.
- Zones cultivées : ESA WorldCover.

Les rendements 2023 sont corrigés avec des agrégats par province de l'Enquête Permanente Agricole (EPA 2023-2024), DGESS. Les microdonnées elles-mêmes ne figurent pas dans ce dépôt.
