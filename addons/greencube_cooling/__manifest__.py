# -*- coding: utf-8 -*-
{
    "name": "GreenCube Cooling",
    "summary": "Configurateur de besoin de refroidissement GreenCube — source de vérité métier",
    "description": """
GreenCube Cooling
=================

Module cœur du configurateur de refroidissement GreenCube :
études, révisions, catalogue thermique, scénarios climatiques,
moteur MERCURE, résultats et sélection d'équipement.

Odoo reste la source de vérité métier ; le frontend React est une
interface de saisie et de restitution, jamais une seconde base
de données métier.
    """,
    "version": "18.0.3.0.0",
    "category": "Services/Project",
    "author": "GreenCube",
    "license": "LGPL-3",
    "depends": [
        "base",
        "mail",
        "product",
        "contacts",
    ],
    "data": [
        "security/greencube_cooling_groups.xml",
        "security/ir.model.access.csv",
        "security/greencube_cooling_rules.xml",
        "data/sequence_data.xml",
        "data/solver_version_data.xml",
        "data/commercial_capacity_data.xml",
        "data/cooling_equipment_data.xml",
        "data/thermal_specification_catalog_data.xml",
        "views/cooling_study_views.xml",
        "views/thermal_specification_views.xml",
        "views/greencube_cooling_menus.xml",
    ],
    "demo": [
        "demo/greencube_cooling_demo.xml",
    ],
    "installable": True,
    "application": True,
}
