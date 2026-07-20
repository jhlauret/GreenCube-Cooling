###  À quoi sert cette webApp ?

Cette webApp est un configurateur thermique et un outil de dimensionnement du refroidissement pour un bâtiment GreenCube.

Son objectif est de permettre à un utilisateur — commercial, bureau d’études, installateur ou chef de projet — de décrire un bâtiment, puis d’estimer :

- la puissance frigorifique nécessaire ;
- les principales charges thermiques du bâtiment ;
- le niveau de confort attendu ;
- une ou plusieurs solutions de climatisation compatibles ;
- les hypothèses et résultats techniques associés à l’étude.

Elle doit servir de pont entre une configuration commerciale simplifiée et un calcul thermique traçable dans Odoo.



### Parcours fonctionnel prévu
**1. Création d’une étude**

L’utilisateur crée un nouveau projet de refroidissement et renseigne notamment :

- le type de bâtiment : studio, bureau, habitat ou commerce ;
- l’adresse ou la localisation ;
- la surface et les dimensions ;
- l’orientation ;
- les ouvertures et vitrages ;
- l’isolation et les propriétés de l’enveloppe ;
- l’usage et le nombre d’occupants ;
- les équipements générant de la chaleur ;
- les objectifs de confort ;
- les protections solaires ou occultations.


**2. Enrichissement climatique**

À partir de l’adresse ou des coordonnées, l’application doit récupérer des données climatiques telles que :

- température extérieure de référence ;
- conditions estivales ;
- rayonnement solaire ;
- caractéristiques climatiques locales.

Ces données alimentent ensuite le moteur de calcul.

**3. Calcul de la charge frigorifique**

Le moteur MERCURE doit déterminer la puissance nécessaire en prenant en compte :

- les apports solaires ;
- les pertes et gains à travers les parois ;
- les vitrages ;
- les occupants ;
- les équipements internes ;
- la ventilation et les infiltrations ;
- les consignes de température ;
- les marges de dimensionnement.

Le résultat doit produire une puissance exprimée, par exemple, en watts ou en kilowatts.

**4. Présentation des résultats**

La webApp doit ensuite afficher :

- la puissance frigorifique calculée ;
- la ventilation du résultat par poste ;
- les hypothèses retenues ;
- un indice de confiance ;
- les éventuelles alertes ;
- la recommandation de dimensionnement.

**5. Sélection d’équipements****

À partir de la puissance calculée, l’application doit proposer des équipements compatibles issus du catalogue Odoo :
- climatiseur ;
- pompe à chaleur ;
- unité intérieure ou extérieure ;
- système monobloc ou multisplit ;
- équipement correspondant aux contraintes techniques du projet.


**6. Validation et traçabilité**

L’étude doit pouvoir être :
- enregistrée dans Odoo ;
- révisée ;
- validée ;
- figée sous forme de snapshot ;
recalculée dans une nouvelle révision sans modifier l’étude validée ;
rattachée à un devis ou à une sélection de produits.
