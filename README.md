# C411 pour Home Assistant

Cette intégration lit le profil C411 toutes les cinq minutes. Elle expose le pseudo, l’avatar, le niveau, le rang, les Zen, les volumes comptabilisés, le ratio et la marge de téléchargement. Les capteurs binaires **Freeleech** et **Téléchargement autorisé** peuvent servir de déclencheurs d’automatisation.

## Installation via HACS

1. Dans HACS, ouvrez **⋮ → Dépôts personnalisés**.
2. Ajoutez `https://github.com/oOBenjaminOo/ha-c411` dans la catégorie **Intégration**.
3. Téléchargez **C411**, puis redémarrez Home Assistant.
4. Dans [les intégrations C411](https://c411.org/user/integrations), créez une clé API avec **Profil (lecture)**.
5. Dans Home Assistant, ouvrez **Paramètres → Appareils et services → Ajouter une intégration → C411**. Collez la clé.

Si C411 révoque la clé, Home Assistant demande de la remplacer. Une clé destinée à Torznab peut ne pas disposer de la permission Profil (lecture).

## Carte de tableau de bord

Installez **Mushroom** et **Button Card** via HACS. Dans votre tableau de bord, ajoutez une carte **Manuel**, puis collez le contenu de [mushroom-card.yaml](examples/mushroom-card.yaml). Si vos identifiants diffèrent, utilisez ceux affichés dans la liste des entités de l’intégration.

La carte indique en orange une marge positive inférieure à 10 Go et en rouge une marge nulle ou négative. Les volumes sont affichés en Go ou en To selon leur taille, avec des conversions binaires. Les entités restent utilisables dans les cartes natives de Home Assistant.

## Données

Le ratio utilise les volumes comptabilisés par C411, crédits compris. Il est indéterminé lorsque le total téléchargé est nul. La marge est estimée avec un seuil de ratio de 0,8. Les statuts Freeleech et téléchargement proviennent directement de l’API.
