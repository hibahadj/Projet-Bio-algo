"""
Algorithme de Commentz-Walter
==============================
Recherche multi-motifs combinant Aho-Corasick et Boyer-Moore.

Référence : Commentz-Walter, B. (1979). A string matching algorithm fast on
            the average. ICALP, LNCS 71, pp. 118-132.
"""

from collections import deque


# ─────────────────────────────────────────────────────────────────────────────
# 1. NŒUD DU TRIE (motifs renversés)
# ─────────────────────────────────────────────────────────────────────────────

class TrieNode:
    def __init__(self):
        self.children   = {}   # char -> TrieNode
        self.fail       = None # lien d'échec (Aho-Corasick)
        self.output     = []   # motifs (originaux) acceptés ici
        self.depth      = 0    # profondeur dans le trie


# ─────────────────────────────────────────────────────────────────────────────
# 2. CONSTRUCTION DU TRIE (motifs renversés)
# ─────────────────────────────────────────────────────────────────────────────

def build_trie(patterns: list[str]) -> TrieNode:
    """
    Construit le trie des motifs renversés.
    Ex. motifs ["he", "she"] → on insère "eh" et "ehs".
    """
    root = TrieNode()

    for pattern in patterns:
        node = root
        for ch in reversed(pattern):          # on insère le motif à l'envers
            if ch not in node.children:
                child = TrieNode()
                child.depth = node.depth + 1
                node.children[ch] = child
            node = node.children[ch]
        node.output.append(pattern)           # motif original reconnu ici

    return root


# ─────────────────────────────────────────────────────────────────────────────
# 3. LIENS D'ÉCHEC (Aho-Corasick) sur le trie renversé
# ─────────────────────────────────────────────────────────────────────────────

def build_fail_links(root: TrieNode) -> None:
    """
    Calcule les liens d'échec par BFS (style Aho-Corasick).
    Propage aussi les sorties (output links).
    """
    queue = deque()

    # Niveau 1 : échec → racine
    for child in root.children.values():
        child.fail = root
        queue.append(child)

    while queue:
        node = queue.popleft()

        for ch, child in node.children.items():
            # Cherche l'état d'échec le plus long pour ce caractère
            fail = node.fail
            while fail is not None and ch not in fail.children:
                fail = fail.fail
            child.fail = fail.children[ch] if (fail and ch in fail.children) else root

            # Propagation des sorties
            child.output = child.output + child.fail.output

            queue.append(child)


# ─────────────────────────────────────────────────────────────────────────────
# 4. TABLES DE SAUT (Boyer-Moore adapté multi-motifs)
# ─────────────────────────────────────────────────────────────────────────────

def build_shift_tables(
    patterns: list[str]
) -> tuple[dict[str, int], dict[str, int], int]:
    """
    Construit les trois tables de saut de Commentz-Walter.

    Retourne :
        shift1  : table du mauvais caractère
                  shift1[c] = plus petit i tel que P[len-1-i] == c
                  (position de c dans un motif, depuis la droite)
        shift2  : table du bon suffixe (valeur globale simplifiée)
        min_len : longueur du plus court motif (shift3 implicite)
    """
    min_len = min(len(p) for p in patterns)

    # ── shift1 : mauvais caractère ──────────────────────────────────────────
    # Pour chaque caractère c, la valeur minimale de décalage telle que
    # c apparaisse dans un des motifs à la position adéquate.
    shift1: dict[str, int] = {}

    for pattern in patterns:
        n = len(pattern)
        for i, ch in enumerate(reversed(pattern)):
            # position depuis la droite : 0 = dernier caractère
            pos_from_right = i
            if ch not in shift1 or shift1[ch] > pos_from_right:
                shift1[ch] = pos_from_right

    # ── shift2 : bon suffixe (valeur par motif, on prend le minimum) ────────
    # Pour chaque motif, calcule le décalage du bon suffixe (BM classique),
    # puis on retient la valeur minimale sur tous les motifs.
    shift2_val = min_len  # valeur de repli

    for pattern in patterns:
        n = len(pattern)
        gs = _good_suffix_shift(pattern)
        shift2_val = min(shift2_val, min(gs))

    shift2: dict[str, int] = {"_default": max(1, shift2_val)}

    return shift1, shift2, min_len


def _good_suffix_shift(pattern: str) -> list[int]:
    """
    Calcule la table du bon suffixe pour un motif unique (Boyer-Moore).
    Retourne un tableau de longueur len(pattern).
    """
    n = len(pattern)
    shift = [n] * n
    border = [0] * (n + 1)

    # Phase 1 : calcul du tableau de bords
    i, j = n, n + 1
    border[i] = j
    while i > 0:
        while j <= n and pattern[i - 1] != pattern[j - 1]:
            if shift[j - 1] == n:
                shift[j - 1] = j - i
            j = border[j]
        i -= 1
        j -= 1
        border[i] = j

    # Phase 2 : remplissage des cases restantes
    j = border[0]
    for i in range(n + 1):
        if i < n and shift[i] == n:
            shift[i] = j
        if i == j:
            j = border[j]

    return shift


# ─────────────────────────────────────────────────────────────────────────────
# 5. ALGORITHME PRINCIPAL : COMMENTZ-WALTER
# ─────────────────────────────────────────────────────────────────────────────

def commentz_walter(text: str, patterns: list[str]) -> dict[str, list[int]]:
    """
    Recherche tous les motifs dans le texte en utilisant
    l'algorithme de Commentz-Walter.

    Paramètres :
        text     : texte source dans lequel chercher
        patterns : liste de motifs à rechercher

    Retourne :
        dict { motif -> [positions de début dans text] }
    """
    if not patterns or not text:
        return {p: [] for p in patterns}

    # ── Prétraitement ──────────────────────────────────────────────────────
    root = build_trie(patterns)
    build_fail_links(root)
    shift1, shift2, min_len = build_shift_tables(patterns)

    results: dict[str, list[int]] = {p: [] for p in patterns}

    # ── Recherche ──────────────────────────────────────────────────────────
    n       = len(text)
    pos     = min_len - 1          # position de la fin de la fenêtre courante

    while pos < n:
        node  = root
        depth = 0

        # Lecture de droite à gauche dans la fenêtre
        j = pos
        while j >= 0:
            ch = text[j]

            # Transition dans le trie (avec liens d'échec)
            while node is not root and ch not in node.children:
                node = node.fail
            if ch in node.children:
                node = node.children[ch]
            else:
                break              # caractère absent du trie → saut

            depth += 1

            # Vérification des motifs reconnus
            # On lit de droite à gauche : à l'indice j, on a lu 'depth' caractères
            # couvrant text[j .. pos]. Un motif de longueur L reconnu ici
            # commence à j et se termine à j + L - 1.
            for pat in node.output:
                start = j
                end   = j + len(pat) - 1
                if start >= 0 and end < len(text):
                    results[pat].append(start)

            # On continue à lire tant que le nœud a des enfants (on peut encore matcher)
            # La profondeur min_len n'est pas un stop : c'est seulement le plancher du saut
            if not node.children and not node.output:
                break

            j -= 1

        # ── Calcul du saut ────────────────────────────────────────────────
        next_char = text[pos] if pos < n else None

        s1 = shift1.get(next_char, min_len) if next_char else min_len
        s1 = max(1, s1)

        s2 = shift2["_default"]
        s3 = min_len                          # plancher

        jump = max(s1, s2, s3)
        pos += jump

    # Trie et dédoublonnage des positions
    for p in results:
        results[p] = sorted(set(results[p]))

    return results


# ─────────────────────────────────────────────────────────────────────────────
# 6. AFFICHAGE
# ─────────────────────────────────────────────────────────────────────────────

def display_results(text: str, results: dict[str, list[int]]) -> None:
    """Affiche les résultats de façon lisible."""
    print(f"\nTexte  : {repr(text)}")
    print(f"Taille : {len(text)} caractères\n")
    print("─" * 50)

    found_any = False
    for pattern, positions in sorted(results.items()):
        if positions:
            found_any = True
            for pos in positions:
                snippet = text[max(0, pos-3):pos] + f"[{text[pos:pos+len(pattern)]}]" + text[pos+len(pattern):pos+len(pattern)+3]
                print(f"  «{pattern}»  à la position {pos:3d}  →  …{snippet}…")

    if not found_any:
        print("  Aucun motif trouvé.")
    print()


# ─────────────────────────────────────────────────────────────────────────────
# 7. TESTS
# ─────────────────────────────────────────────────────────────────────────────

def run_tests() -> None:
    print("=" * 60)
    print("  TESTS — Algorithme de Commentz-Walter")
    print("=" * 60)

    # ── Test 1 : exemple classique de la littérature ──────────────────────
    print("\n[TEST 1] Exemple classique (Aho-Corasick 1975)")
    text     = "ushers"
    patterns = ["he", "she", "his", "hers"]
    results  = commentz_walter(text, patterns)
    display_results(text, results)

    # Positions réelles : he@2, she@1, hers@2
    expected = {"he": [2], "she": [1], "his": [], "hers": [2]}
    for p, exp in expected.items():
        assert results[p] == exp, f"Erreur : {p} attendu {exp} obtenu {results[p]}"
    print("  ✓ Toutes les assertions passent.\n")

    # ── Test 2 : motifs qui se chevauchent ────────────────────────────────
    print("[TEST 2] Chevauchement de motifs")
    text     = "aababcababababd"
    patterns = ["ab", "aba", "abab"]
    results  = commentz_walter(text, patterns)
    display_results(text, results)

    # ── Test 3 : texte biologique (ADN) ───────────────────────────────────
    print("[TEST 3] Recherche dans une séquence ADN")
    text     = "ACGTACGTTAGCTAGCTAGCGT"
    patterns = ["ACG", "TAG", "GCT"]
    results  = commentz_walter(text, patterns)
    display_results(text, results)

    # ── Test 4 : motif absent ─────────────────────────────────────────────
    print("[TEST 4] Motif absent")
    text     = "hello world"
    patterns = ["xyz", "abc"]
    results  = commentz_walter(text, patterns)
    display_results(text, results)
    assert results == {"xyz": [], "abc": []}, "Erreur : des motifs absents ont été trouvés"
    print("  ✓ Aucun faux positif.\n")

    # ── Test 5 : texte long aléatoire (performance) ───────────────────────
    import random, string, time
    print("[TEST 5] Performance — texte de 100 000 caractères, 10 motifs")
    random.seed(42)
    alphabet = string.ascii_lowercase
    long_text  = "".join(random.choices(alphabet, k=100_000))
    many_pats  = ["".join(random.choices(alphabet, k=5)) for _ in range(10)]

    t0 = time.perf_counter()
    results_long = commentz_walter(long_text, many_pats)
    elapsed = time.perf_counter() - t0

    total = sum(len(v) for v in results_long.values())
    print(f"  Motifs    : {many_pats}")
    print(f"  Occurrences trouvées : {total}")
    print(f"  Durée     : {elapsed*1000:.2f} ms\n")

    print("=" * 60)
    print("  Tous les tests terminés avec succès.")
    print("=" * 60)


# ─────────────────────────────────────────────────────────────────────────────
# 8. POINT D'ENTRÉE
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    run_tests()

    # ── Utilisation rapide ─────────────────────────────────────────────────
    print("\n── Utilisation directe ──────────────────────────────────")
    text     = "ABC-ABCDAB-ABCDABCDABDE"
    patterns = ["ABC", "ABCD", "AB", "ABCDAB"]
    results  = commentz_walter(text, patterns)
    display_results(text, results)