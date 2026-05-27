"""Generador de topologies sintètiques per a tests i benchmarks.

Produeix un diccionari amb el mateix esquema que un JSON de ShadowScan
(`nodes`, `edges`, `entry_point`, `target`, `metadata`) per poder reutilitzar
`scanner.parser.NetworkParser` i `scanner.normalizer.normalize`.
"""

from __future__ import annotations

import random
from typing import Dict, List


# Tipus de nodes que podem tenir a la xarxa. No és exhaustiu, però per ara
# amb aquests cinc ja tenim prou varietat per simular topologies realistes.
_NODE_TYPES = ("router", "server", "workstation", "fileserver", "database")

# Cada tipus de node té els seus ports "naturals". Un router no té el 3306
# obert per defecte, i una workstation no hauria de tenir el 53... en
# condicions normals. Aquí modelem el cas ideal, els riscos venen després.
_PORTS_BY_TYPE = {
    "router": [22, 53, 80, 443],
    "server": [22, 80, 443, 3306],
    "workstation": [445, 139, 3389],
    "fileserver": [445, 139, 21, 2049],
    "database": [22, 3306, 5432],
}

# Mapatge port -> nom del servei. Útil per generar el camp `services` dels
# nodes sense haver de repetir la lògica a tot arreu. Si un port no hi és,
# posem "unknown" i ja apanyarem.
_SERVICES = {
    22: "ssh", 23: "telnet", 21: "ftp", 53: "dns", 80: "http", 139: "netbios",
    443: "https", 445: "smb", 2049: "nfs", 3306: "mysql", 3389: "rdp",
    5432: "postgresql", 161: "snmp",
}


def generate_topology(
    n_nodes: int,
    edge_density: float = 0.25,
    critical_ratio: float = 0.2,
    seed: int | None = None,
) -> Dict:
    """Genera una topologia sintètica amb n_nodes hosts.

    Parameters
    ----------
    n_nodes : int
        Nombre de nodes (mínim 2).
    edge_density : float
        Probabilitat d'existència d'una aresta dirigida entre dos nodes
        diferents (0.0 = mínim connex, 1.0 = graf complet).
    critical_ratio : float
        Fracció aproximada de nodes amb risc >= 0.80.
    seed : int | None
        Llavor per a reproducibilitat.

    Returns
    -------
    dict compatible amb scanner.parser.NetworkParser.
    """
    # Validacions bàsiques. Preferim petar aviat amb un missatge clar que no
    # pas deixar que el codi exploti en algun lloc estrany més endavant.
    if n_nodes < 2:
        raise ValueError("n_nodes ha de ser >= 2")
    if not 0.0 <= edge_density <= 1.0:
        raise ValueError("edge_density fora de [0, 1]")
    if not 0.0 <= critical_ratio <= 1.0:
        raise ValueError("critical_ratio fora de [0, 1]")

    # Fem servir un Random propi en comptes del global per no destorbar
    # altres parts del codi que també puguin usar random. Així la llavor
    # és completament aïllada i els tests surten reproducibles.
    rng = random.Random(seed)

    # Generació de nodes

    nodes: List[Dict] = []
    for i in range(n_nodes):
        # Triem el tipus a l'atzar. Tots tenen la mateixa probabilitat,
        # cosa que no reflecteix la realitat però simplifica molt el codi.
        # Si algun dia cal ponderar-ho, aquí és on tocar.
        ntype = rng.choice(_NODE_TYPES)

        # Comencem amb els ports "oficials" del tipus i després hi afegim
        # els problemàtics. Fem una còpia per no mutar el diccionari global.
        ports = list(_PORTS_BY_TYPE[ntype])

        # Aquí decidim si el node serà "crític" o no. critical_ratio controla
        # quina fracció de la xarxa volem que tingui risc alt. Un 0.2 vol dir
        # que aproximadament 1 de cada 5 nodes serà problemàtic.
        if rng.random() < critical_ratio:
            # Afegim un port d'alt risc: telnet, ftp o rdp sense xifrat.
            # En una xarxa real trobar el 23 obert és un mal senyal.
            ports.append(rng.choice([23, 21, 3389]))
            # Risc alt, però no sempre el màxim; posem un rang realista.
            risk = round(rng.uniform(0.80, 0.98), 2)
        elif rng.random() < 0.4:
            # Zona grisa: el node no és segur del tot, però tampoc és un
            # desastre imminent. Típic d'un servidor mal configurat però
            # sense ports obertament perillosos.
            risk = round(rng.uniform(0.40, 0.70), 2)
        else:
            # La majoria de nodes haurien de caure aquí: poc risc, tot
            # correcte, res a destacar. La xarxa "normal".
            risk = round(rng.uniform(0.10, 0.35), 2)

        # Construïm l'adreça IP a partir de l'índex. Per nodes >= 256
        # el primer octet del tercer segment puja sol gràcies al // 256.
        # No és un esquema d'adreces real, però és prou llegible per als logs.
        nodes.append({
            "id": f"10.0.{i // 256}.{i % 256}",
            "type": ntype,
            "ports": ports,
            # El diccionari de serveis el generem aquí mateix per tenir-ho
            # tot junt. Les claus són strings perquè el JSON no admet ints.
            "services": {str(p): _SERVICES.get(p, "unknown") for p in ports},
            "risk": risk,
        })

    # Generació d'arestes

    # Garantim un camí Hamiltonià que va de nodes[0] fins a nodes[-1] en
    # ordre seqüencial. Sense això podríem generar grafs desconnectats i el
    # pathfinder no trobaria mai el target. És el mínim de connectivitat.
    edges: List[Dict] = []
    for i in range(n_nodes - 1):
        edges.append({
            "from": nodes[i]["id"],
            "to": nodes[i + 1]["id"],
            # El pes representa el cost/dificultat de travessar l'aresta.
            # Valors alts = més difícil de comprometre. Ho posem aleatori
            # per simular heterogeneïtat en les defenses de la xarxa.
            "weight": round(rng.uniform(0.20, 0.90), 2),
        })

    # Ara afegim arestes extra per simular la complexitat real d'una xarxa.
    # Un edge_density de 0.25 vol dir que aproximadament una de cada quatre
    # connexions possibles existirà. Amb densitat 1.0 tindríem un graf complet.
    existing = {(e["from"], e["to"]) for e in edges}
    for i in range(n_nodes):
        for j in range(n_nodes):
            # Un node no es connecta amb ell mateix. Sembla obvi, però sense
            # aquest check apareixien bucles autoreferencials als tests.
            if i == j:
                continue
            pair = (nodes[i]["id"], nodes[j]["id"])
            # Si ja existeix (del camí Hamiltonià), no la dupliquem.
            if pair in existing:
                continue
            if rng.random() < edge_density:
                edges.append({
                    "from": pair[0],
                    "to": pair[1],
                    "weight": round(rng.uniform(0.15, 0.95), 2),
                })
                # Afegim al set per evitar duplicats en iteracions futures.
                existing.add(pair)

    # Muntem el diccionari final amb l'esquema que espera NetworkParser.
    # Si canvies alguna clau aquí, recorda actualitzar el parser també!
    return {
        "metadata": {
            "generated_by": "ShadowScan",
            # Marca explícita que això no és un scan real. Útil per filtrar
            # als dashboards i no barrejar dades reals amb sintètiques.
            "synthetic": True,
            "version": "1.0-synth",
            "hosts_active": n_nodes,
        },
        "nodes": nodes,
        "edges": edges,
        # El primer i últim node fan de punt d'entrada i objectiu,
        # respectivament. Coincideix amb l'ordre del camí Hamiltonià.
        "entry_point": nodes[0]["id"],
        "target": nodes[-1]["id"],
    }


def save_topology(topo: Dict, path: str) -> None:
    """Escriu el diccionari de topologia a disc com a JSON."""
    import json
    from pathlib import Path

    # Creem els directoris pare si no existeixen. Sense això peta si la
    # carpeta de destí encara no s'ha creat, cosa que passa sovint en
    # entorns de CI on el directori d'output és nou cada vegada.
    Path(path).parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        # indent=2 per llegibilitat; si el fitxer creix massa i el tamany
        # importa, es pot treure sense que res es trenqui funcionalment.
        json.dump(topo, f, indent=2)
