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

### États et compteurs supplémentaires

- **Freeleech** indique si l’API signale un Freeleech actif pour le profil (personnel, campagne ou fenêtre). Le capteur peut servir à notifier le début et la fin d’une période.
- **Téléchargement autorisé** reflète la décision de C411 pour le compte, par exemple en fonction du solde de téléchargement. Il ne mesure pas l’état du client BitTorrent.
- **SilverLeech** reflète le booléen distinct communiqué par l’API.
- Les compteurs supplémentaires exposent les XP totaux et restants, les Zen gagnés et dépensés, les volumes réellement transférés hors crédits, l’équipe et les quêtes terminées. Les champs absents ne sont pas interprétés comme des zéros.

Les identifiants de la carte sont des exemples. Home Assistant peut inclure le nom du service et celui de la zone dans les identifiants, comme dans `sensor.systeme_c411_mon_pseudo_ratio`.

## Générer la carte pour son compte

Dans **Outils de développement → Actions**, exécutez `c411.generate_card` et sélectionnez votre service C411. Copiez le contenu du champ `yaml` de la réponse dans une carte **Manuel**. La génération utilise les identifiants actuellement enregistrés, y compris après un renommage. Les ressources Mushroom et Button Card restent nécessaires.

Le capteur de diagnostic **Dernière synchronisation réussie** donne l'heure de la dernière lecture du profil acceptée. Il devient indisponible en cas d'échec, avec la dernière lecture réussie consultable dans son historique.

## Carte native et alertes

La [carte native](examples/native-card.yaml) utilise uniquement les cartes Markdown et Entités de Home Assistant. Collez son YAML dans une carte **Manuel** et remplacez les identifiants par ceux de votre service C411.

L’[exemple d’automatisation](examples/profile-alerts.yaml) crée une notification persistante au début d’un Freeleech ou quand C411 retire l’autorisation de télécharger. Adaptez les deux identifiants avant de l’activer.
