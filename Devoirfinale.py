

from collections import deque
from typing import Dict, List, Optional, Tuple
import tkinter as tk
import random
import string
import time
import io
from contextlib import redirect_stdout


def _safe_input(prompt: str = "") -> str:
    """Input robuste pour VS Code/Windows: Ctrl+C est capturé immédiatement.

    Sur certains terminaux Windows, `input()` peut retarder KeyboardInterrupt
    jusqu'à une frappe supplémentaire. Ici on lit caractère-par-caractère via
    `msvcrt` et on lève KeyboardInterrupt dès '\x03'.
    """
    import sys

    if sys.platform != "win32":
        return input(prompt)

    try:
        import msvcrt  # type: ignore
    except Exception:
        return input(prompt)

    sys.stdout.write(prompt)
    sys.stdout.flush()

    buf: List[str] = []
    while True:
        ch = msvcrt.getwch()

        # Ctrl+C
        if ch == "\x03":
            raise KeyboardInterrupt

        # Enter
        if ch in ("\r", "\n"):
            sys.stdout.write("\n")
            sys.stdout.flush()
            return "".join(buf)

        # Backspace
        if ch == "\b":
            if buf:
                buf.pop()
                # Efface le dernier caractère à l'écran
                sys.stdout.write("\b \b")
                sys.stdout.flush()
            continue

        # Ignore touches spéciales (flèches, F1...) qui arrivent en deux temps
        if ch in ("\x00", "\xe0"):
            _ = msvcrt.getwch()
            continue

        buf.append(ch)
        sys.stdout.write(ch)
        sys.stdout.flush()

######## PARTIE 1 : BOYER-MOORE ###############

def build_bad_character_table(pattern: str) -> Dict[str, List[int]]:
    """Construit le tableau d[c][j] des dernières occurrences avant j pour chaque caractère du motif."""
    m = len(pattern)
    chars = sorted(set(pattern))
    table: Dict[str, List[int]] = {char: [-1] * m for char in chars}
    last_occurrence: Dict[str, int] = {char: -1 for char in chars}

    for j in range(m):
        for char in chars:
            table[char][j] = last_occurrence[char]
        last_occurrence[pattern[j]] = j

    return table


def print_bad_character_table(table: Dict[str, List[int]], pattern: str) -> None:
    """Affiche le tableau d[c][j] pour le motif."""
    m = len(pattern)
    print("Tableau dictionnaire d[c][j] :")
    header = "c\\j | " + " ".join(f"{j:3}" for j in range(m))
    print(header)
    print("-" * len(header))
    for char in sorted(table.keys()):
        row = " ".join(f"{table[char][j]:3}" for j in range(m))
        print(f"{char!r:3} | {row}")
    print(f"Motif M = {pattern}\n")


def boyer_moore_search(text: str, pattern: str) -> Tuple[List[int], int]:
    """Recherche toutes les occurrences de pattern dans text avec BM et compte les comparaisons."""
    n = len(text)
    m = len(pattern)
    if m == 0:
        raise ValueError("Le motif ne peut pas être vide.")

    bad_char = build_bad_character_table(pattern)
    print_bad_character_table(bad_char, pattern)

    occurrences: List[int] = []
    comparisons = 0
    shift = 0

    print("Phase de recherche :\n")
    while shift <= n - m:
        window = text[shift:shift + m]
        print(f"Fenêtre positionnée à {shift} : '{window}'")

        j = m - 1
        while j >= 0:
            comparisons += 1
            print(
                f"  Comparaison {comparisons}: text[{shift + j}]='{text[shift + j]}' "
                f"vs pattern[{j}]='{pattern[j]}'"
            )
            if pattern[j] == text[shift + j]:
                j -= 1
            else:
                break

        if j < 0:
            print(f"  --> Occurrence trouvée à la position {shift}")
            occurrences.append(shift)
            shift_value = 1
            print(f"  Cas de correspondance complète. Décalage = {shift_value}\n")
            shift += shift_value
        else:
            mismatched_char = text[shift + j]
            d_j = bad_char.get(mismatched_char, [-1] * m)[j]
            shift_value = max(1, j - d_j)
            print(f"  Échec sur pattern[{j}] à la position texte {shift + j}.")
            print(f"  Caractère mismatch = '{mismatched_char}'.")
            print(f"  d[{mismatched_char!r}][{j}] = {d_j}")
            print(f"  Décalage calculé = max(1, {j} - {d_j}) = {shift_value}")
            print(f"  Comparaisons jusqu'ici = {comparisons}\n")
            shift += shift_value

    print("Recherche terminée.")
    print(f"Nombre total de comparaisons = {comparisons}")
    if occurrences:
        print(f"Positions des occurrences trouvées : {occurrences}")
    else:
        print("Aucune occurrence trouvée.")

    return occurrences, comparisons


def run_boyer_moore(text: str, patterns: List[str]) -> None:
    print('\n--- Boyer-Moore ---')
    print(f"Texte: '{text}'")
    for pattern in patterns:
        print(f"\nRecherche du motif '{pattern}' :")
        boyer_moore_search(text, pattern)
    print('\n--- Fin Boyer-Moore ---\n')


######## PARTIE 2 : AHO-CORASICK ###############

class AhoCorasickNode:
    def __init__(self, node_id: int, char: Optional[str] = None, parent: Optional['AhoCorasickNode'] = None):
        self.id = node_id
        self.char = char
        self.parent = parent
        self.transitions: Dict[str, 'AhoCorasickNode'] = {}
        self.fail: Optional['AhoCorasickNode'] = None
        self.output: List[str] = []

    def add_transition(self, char: str, node: 'AhoCorasickNode') -> None:
        self.transitions[char] = node

    def get_transition(self, char: str) -> Optional['AhoCorasickNode']:
        return self.transitions.get(char)

    def is_terminal(self) -> bool:
        return len(self.output) > 0

    def prefix(self) -> str:
        node = self
        chars: List[str] = []
        while node is not None and node.char is not None:
            chars.append(node.char)
            node = node.parent
        return ''.join(reversed(chars))

    def __repr__(self) -> str:
        return f"Node(id={self.id}, prefix='{self.prefix()}')"


class AhoCorasick:
    def __init__(self):
        self.root = AhoCorasickNode(0)
        self.root.fail = self.root
        self.nodes: List[AhoCorasickNode] = [self.root]
        self._next_id = 1

    def add_pattern(self, pattern: str) -> None:
        node = self.root
        for char in pattern:
            child = node.get_transition(char)
            if child is None:
                child = AhoCorasickNode(self._next_id, char=char, parent=node)
                node.add_transition(char, child)
                self.nodes.append(child)
                self._next_id += 1
            node = child
        node.output.append(pattern)

    def build_automaton(self) -> None:
        queue = deque()

        for char, child in self.root.transitions.items():
            child.fail = self.root
            queue.append(child)

        while queue:
            current = queue.popleft()
            for char, next_node in current.transitions.items():
                queue.append(next_node)
                fail_state = current.fail
                while fail_state is not self.root and fail_state.get_transition(char) is None:
                    fail_state = fail_state.fail
                candidate = fail_state.get_transition(char)
                next_node.fail = candidate if candidate is not None else self.root
                next_node.output += next_node.fail.output

    def _node_name(self, node: AhoCorasickNode) -> str:
        return '&' if node is self.root else node.prefix()

    def search(self, text: str) -> Tuple[List[Tuple[int, str, List[str]]], List[str]]:
        node = self.root
        occurrences: List[Tuple[int, str, List[str]]] = []
        path_steps: List[str] = []

        path_steps.append(f"pos=-1 état={self._node_name(node)}")

        for index, char in enumerate(text):
            current_name = self._node_name(node)
            while node is not self.root and node.get_transition(char) is None:
                fail_name = self._node_name(node.fail)
                path_steps.append(
                    f"pos={index} char='{char}' état={current_name} - pas de transition, échec vers {fail_name}"
                )
                node = node.fail
                current_name = self._node_name(node)

            next_node = node.get_transition(char)
            if next_node is not None:
                next_name = self._node_name(next_node)
                path_steps.append(
                    f"pos={index} char='{char}' état={current_name} -> transition vers {next_name}"
                )
                node = next_node
            else:
                path_steps.append(
                    f"pos={index} char='{char}' état={current_name} - aucune transition, retour à &"
                )
                node = self.root

            if node.output:
                for pattern in node.output:
                    start = index - len(pattern) + 1
                    occurrences.append((start, pattern, node.output.copy()))
                    path_steps.append(
                        f"  motif trouvé: '{pattern}' à la position {start} (état {self._node_name(node)})"
                    )

        return occurrences, path_steps

    def print_search_tree(self, text: str) -> None:
        _, path_steps = self.search(text)
        print('--- Arbre de recherche ---')
        for step in path_steps:
            if 'échec vers' in step:
                print('    ' + step)
            elif 'aucune transition' in step:
                print('  ' + step)
            else:
                print(step)
        print('--- Fin de l\'arbre de recherche ---\n')

    def print_trie(self) -> None:
        print('--- Automate des préfixes (trie) ---')
        for node in self.nodes:
            parent_id = node.parent.id if node.parent else None
            print(
                f"Node {node.id}: prefix='{node.prefix()}' char='{node.char}' parent={parent_id} "
                f"transitions={[k for k in node.transitions.keys()]} terminal={node.is_terminal()}"
            )
        print('--- Fin du trie ---\n')

    def print_automaton(self) -> None:
        print('--- Automate Aho-Corasick complet ---')
        for node in self.nodes:
            transitions = ', '.join(
                f"'{char}'=>Node {child.id}" for char, child in node.transitions.items()
            )
            fail_id = node.fail.id if node.fail else 'None'
            fail_prefix = node.fail.prefix() if node.fail else 'None'
            output_list = node.output if node.output else []
            print(
                f"Node {node.id}: prefix='{node.prefix()}' transitions={{ {transitions} }} "
                f"fail=Node {fail_id} prefix='{fail_prefix}' output={output_list}"
            )
        print('--- Fin de l\'automate complet ---\n')

    def print_failures(self) -> None:
        print('--- Fonction de suppléance (fail) ---')
        for node in self.nodes:
            if node is self.root:
                print(f"Node {node.id} (racine): fail -> racine")
            else:
                fail_prefix = node.fail.prefix() if node.fail else 'None'
                print(
                    f"Node {node.id}: prefix='{node.prefix()}' -> fail vers Node {node.fail.id} "
                    f"prefix='{fail_prefix}'"
                )
        print('--- Fin de la fonction de suppléance ---\n')

    def print_outputs(self) -> None:
        print('--- Fonction de sortie (output) ---')
        for node in self.nodes:
            if node.output:
                print(
                    f"Node {node.id}: prefix='{node.prefix()}' output={node.output}"
                )
        print('--- Fin de la fonction de sortie ---\n')

    def _compute_horizontal_positions(self) -> Dict[int, Tuple[int, int]]:
        levels: Dict[int, List[AhoCorasickNode]] = {}
        queue = [(self.root, 0)]
        visited = set()

        while queue:
            node, depth = queue.pop(0)
            if node.id in visited:
                continue
            visited.add(node.id)
            levels.setdefault(depth, []).append(node)
            for _, child in sorted(node.transitions.items()):
                queue.append((child, depth + 1))

        positions: Dict[int, Tuple[int, int]] = {}
        max_depth = max(levels.keys(), default=0)
        max_nodes = max((len(nodes) for nodes in levels.values()), default=1)
        height = max(520, max_nodes * 120)

        for depth, nodes in sorted(levels.items()):
            x = 120 + depth * 200
            count = len(nodes)
            for index, node in enumerate(nodes):
                if count == 1:
                    y = height // 2
                else:
                    y = 80 + index * ((height - 160) // (count - 1))
                positions[node.id] = (x, y)

        return positions

    def _draw_circle_node(self, canvas: 'tk.Canvas', x: float, y: float, text: str, fill: str = '#fff5b1', radius: int = 40, font_size: int = 10) -> None:
        canvas.create_oval(x - radius, y - radius, x + radius, y + radius, fill=fill, outline='#333333', width=2)
        canvas.create_text(x, y, text=text, font=('Arial', font_size, 'bold'))

    def _draw_arrow(self, canvas: 'tk.Canvas', x1: float, y1: float, x2: float, y2: float, color: str = '#1f4b99') -> None:
        canvas.create_line(x1, y1, x2, y2, width=2, fill=color, arrow='last', arrowshape=(12, 14, 6))

    def draw_tkinter_trie(self) -> None:
        window = tk.Tk()
        window.title('Automate des préfixes (trie)')

        positions = self._compute_horizontal_positions()
        width = max(x for x, _ in positions.values()) + 180
        height = max(y for _, y in positions.values()) + 180
        canvas = tk.Canvas(window, width=width, height=height, bg='#f0f4f9')
        canvas.pack(fill='both', expand=True)

        canvas.create_text(30, 28, anchor='nw', text='Automate des préfixes (trie)', font=('Arial', 14, 'bold'))

        for node in self.nodes:
            x, y = positions[node.id]
            fill = '#fff5b1' if node is self.root else '#8fd3ff'
            label = '&' if node is self.root else node.prefix()
            if node.output:
                label = f"{label}\nout={node.output}"
            self._draw_circle_node(canvas, x, y, label, fill=fill)

        for node in self.nodes:
            x, y = positions[node.id]
            for char, child in node.transitions.items():
                cx, cy = positions[child.id]
                dist = ((cx - x) ** 2 + (cy - y) ** 2) ** 0.5
                if dist == 0:
                    continue
                start_x = x + (cx - x) * 40 / dist
                start_y = y + (cy - y) * 40 / dist
                end_x = cx - (cx - x) * 40 / dist
                end_y = cy - (cy - y) * 40 / dist
                self._draw_arrow(canvas, start_x, start_y, end_x, end_y)
                tx = (start_x + end_x) / 2
                ty = (start_y + end_y) / 2 - 10
                canvas.create_text(tx, ty, text=char, font=('Arial', 10, 'bold'), fill='#b30000')

        window.mainloop()

    def draw_tkinter_complete_automaton(self) -> None:
        window = tk.Tk()
        window.title('Automate Aho-Corasick complet')

        positions = self._compute_horizontal_positions()
        width = max(x for x, _ in positions.values()) + 180
        height = max(y for _, y in positions.values()) + 180
        canvas = tk.Canvas(window, width=width, height=height, bg='#f9fff1')
        canvas.pack(fill='both', expand=True)

        canvas.create_text(30, 28, anchor='nw', text='Automate Aho-Corasick complet', font=('Arial', 14, 'bold'))

        for node in self.nodes:
            x, y = positions[node.id]
            if node is self.root:
                fill = '#fff5b1'
            elif node.is_terminal():
                fill = '#90ee90'
            else:
                fill = '#8fd3ff'
            label = '&' if node is self.root else node.prefix()
            if node.output:
                label = f"{label}\nout={node.output}"
            self._draw_circle_node(canvas, x, y, label, fill=fill)

        for node in self.nodes:
            x, y = positions[node.id]
            for char, child in node.transitions.items():
                cx, cy = positions[child.id]
                dist = ((cx - x) ** 2 + (cy - y) ** 2) ** 0.5
                if dist == 0:
                    continue
                start_x = x + (cx - x) * 40 / dist
                start_y = y + (cy - y) * 40 / dist
                end_x = cx - (cx - x) * 40 / dist
                end_y = cy - (cy - y) * 40 / dist
                self._draw_arrow(canvas, start_x, start_y, end_x, end_y)
                tx = (start_x + end_x) / 2
                ty = (start_y + end_y) / 2 - 10
                canvas.create_text(tx, ty, text=char, font=('Arial', 10, 'bold'), fill='#b30000')

        for node in self.nodes:
            if node is not self.root and node.fail is not None:
                x, y = positions[node.id]
                fx, fy = positions[node.fail.id]
                dist = ((fx - x) ** 2 + (fy - y) ** 2) ** 0.5
                if dist == 0:
                    continue
                start_x = x + (fx - x) * 40 / dist
                start_y = y + (fy - y) * 40 / dist
                end_x = fx - (fx - x) * 40 / dist
                end_y = fy - (fy - y) * 40 / dist
                self._draw_arrow(canvas, start_x, start_y, end_x, end_y, color='#666666')
                tx = (start_x + end_x) / 2
                ty = (start_y + end_y) / 2 + 10
                canvas.create_text(tx, ty, text='fail', font=('Arial', 8), fill='#666666')

        window.mainloop()

    def draw_tkinter_search_tree(self, text: str) -> None:
        window = tk.Tk()
        window.title('Arbre de recherche')

        search_nodes: List[str] = []
        edge_labels: List[str] = []
        node = self.root
        search_nodes.append(self._node_name(node))

        for char in text:
            while node is not self.root and node.get_transition(char) is None:
                node = node.fail
            next_node = node.get_transition(char)
            if next_node is not None:
                node = next_node
            else:
                node = self.root
            search_nodes.append(self._node_name(node))
            edge_labels.append(char)

        visible_width = 1000
        height = 320
        total_width = max(visible_width, len(search_nodes) * 170 + 120)

        frame = tk.Frame(window)
        frame.pack(fill='both', expand=True)

        canvas = tk.Canvas(frame, width=visible_width, height=height, bg='#f7f7ff', scrollregion=(0, 0, total_width, height))
        hbar = tk.Scrollbar(frame, orient='horizontal', command=canvas.xview)
        canvas.configure(xscrollcommand=hbar.set)

        canvas.pack(side='top', fill='both', expand=True)
        hbar.pack(side='bottom', fill='x')

        canvas.create_text(30, 28, anchor='nw', text='Arbre de recherche du chemin', font=('Arial', 14, 'bold'))

        x = 100
        y = 170
        previous_x = None
        radius = 28
        for i, state_label in enumerate(search_nodes):
            self._draw_circle_node(canvas, x, y, state_label, fill='#ffe2b3', radius=radius, font_size=8)
            if previous_x is not None:
                start_x = previous_x + radius
                end_x = x - radius
                self._draw_arrow(canvas, start_x, y, end_x, y, color='#444444')
                char = edge_labels[i - 1]
                tx = (start_x + end_x) / 2
                canvas.create_text(tx, y + radius + 14, text=char, font=('Arial', 10, 'bold'))
            previous_x = x
            x += 170

        canvas.config(scrollregion=(0, 0, total_width, height))
        window.mainloop()


def read_patterns() -> List[str]:
    return read_patterns_for('Aho-Corasick')


def read_single_pattern() -> str:
    motif = _safe_input("Motif = ").strip()
    return motif


def read_patterns_for(algorithm_name: str) -> List[str]:
    print(f"Entrez les motifs ({algorithm_name}), un par ligne. Laissez une ligne vide pour terminer.")
    patterns: List[str] = []
    index = 1
    while True:
        motif = _safe_input(f"Motif {index} = ").strip()
        if motif == "":
            break
        patterns.append(motif)
        index += 1
    return patterns


def run_aho_corasick(text: str, patterns: List[str]) -> None:
    print('\n--- Aho-Corasick ---')
    automaton = AhoCorasick()
    for pattern in patterns:
        automaton.add_pattern(pattern)

    automaton.build_automaton()
    automaton.print_trie()
    automaton.print_failures()
    automaton.print_outputs()
    automaton.print_automaton()

    print('--- Recherche dans le texte ---')
    print(f"Texte: '{text}'")
    occurrences, _ = automaton.search(text)
    automaton.print_search_tree(text)

    print('Positions des occurrences trouvées:')
    if occurrences:
        for start, pattern, _ in occurrences:
            print(f"motif='{pattern}' trouvé à la position {start}")
    else:
        print('Aucune occurrence trouvée.')

    automaton.draw_tkinter_trie()
    automaton.draw_tkinter_complete_automaton()
    automaton.draw_tkinter_search_tree(text)


######## PARTIE 3 : ALGORITHME NAÏF ###############

def naive_search(text: str, pattern: str) -> Tuple[List[int], int]:
    n = len(text)
    m = len(pattern)
    if m == 0:
        raise ValueError("Le motif ne peut pas être vide.")

    occurrences: List[int] = []
    comparisons = 0

    print("Phase de recherche (naïf) :\n")
    for shift in range(0, n - m + 1):
        window = text[shift:shift + m]
        print(f"Fenêtre positionnée à {shift} : '{window}'")

        matched = True
        for j in range(m):
            comparisons += 1
            print(
                f"  Comparaison {comparisons}: text[{shift + j}]='{text[shift + j]}' "
                f"vs pattern[{j}]='{pattern[j]}'"
            )
            if text[shift + j] != pattern[j]:
                matched = False
                break

        if matched:
            print(f"  --> Occurrence trouvée à la position {shift}\n")
            occurrences.append(shift)
        else:
            print(f"  --> Échec à la position {shift}\n")

    print("Recherche terminée (naïf).")
    print(f"Nombre total de comparaisons = {comparisons}")
    if occurrences:
        print(f"Positions des occurrences trouvées : {occurrences}")
    else:
        print("Aucune occurrence trouvée.")

    return occurrences, comparisons


def run_naive(text: str, pattern: str) -> None:
    print('\n--- Algorithme naïf ---')
    print(f"Texte: '{text}'")
    print(f"Motif: '{pattern}'\n")
    naive_search(text, pattern)
    print('--- Fin Algorithme naïf ---\n')


######## PARTIE 4 : COMMENTZ-WALTER ###############

class CWTrieNode:
    def __init__(self):
        self.children: Dict[str, 'CWTrieNode'] = {}
        self.fail: Optional['CWTrieNode'] = None
        self.output: List[str] = []
        self.depth: int = 0


def cw_build_trie(patterns: List[str]) -> CWTrieNode:
    root = CWTrieNode()
    for pattern in patterns:
        node = root
        for ch in reversed(pattern):
            if ch not in node.children:
                child = CWTrieNode()
                child.depth = node.depth + 1
                node.children[ch] = child
            node = node.children[ch]
        node.output.append(pattern)
    return root


def cw_build_fail_links(root: CWTrieNode) -> None:
    queue = deque()
    for child in root.children.values():
        child.fail = root
        queue.append(child)

    while queue:
        node = queue.popleft()
        for ch, child in node.children.items():
            fail = node.fail
            while fail is not None and ch not in fail.children:
                fail = fail.fail
            child.fail = fail.children[ch] if (fail and ch in fail.children) else root
            child.output = child.output + child.fail.output
            queue.append(child)


def cw_good_suffix_shift(pattern: str) -> List[int]:
    n = len(pattern)
    shift = [n] * n
    border = [0] * (n + 1)

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

    j = border[0]
    for i in range(n + 1):
        if i < n and shift[i] == n:
            shift[i] = j
        if i == j:
            j = border[j]

    return shift


def cw_build_shift_tables(patterns: List[str]) -> Tuple[Dict[str, int], Dict[str, int], int]:
    min_len = min(len(p) for p in patterns)

    shift1: Dict[str, int] = {}
    for pattern in patterns:
        for i, ch in enumerate(reversed(pattern)):
            if ch not in shift1 or shift1[ch] > i:
                shift1[ch] = i

    shift2_val = min_len
    for pattern in patterns:
        gs = cw_good_suffix_shift(pattern)
        shift2_val = min(shift2_val, min(gs))
    shift2: Dict[str, int] = {"_default": max(1, shift2_val)}

    return shift1, shift2, min_len


def commentz_walter(text: str, patterns: List[str]) -> Dict[str, List[int]]:
    if not patterns or not text:
        return {p: [] for p in patterns}

    root = cw_build_trie(patterns)
    cw_build_fail_links(root)
    shift1, shift2, min_len = cw_build_shift_tables(patterns)

    results: Dict[str, List[int]] = {p: [] for p in patterns}

    n = len(text)
    pos = min_len - 1

    while pos < n:
        node = root
        depth = 0
        j = pos

        while j >= 0:
            ch = text[j]
            while node is not root and ch not in node.children:
                node = node.fail  # type: ignore[assignment]
            if ch in node.children:
                node = node.children[ch]
            else:
                break

            depth += 1

            for pat in node.output:
                start = j
                end = j + len(pat) - 1
                if start >= 0 and end < len(text):
                    results[pat].append(start)

            if not node.children and not node.output:
                break

            j -= 1

        next_char = text[pos] if pos < n else None
        s1 = shift1.get(next_char, min_len) if next_char else min_len
        s1 = max(1, s1)
        s2 = shift2["_default"]
        s3 = min_len
        jump = max(s1, s2, s3)
        pos += jump

    for p in results:
        results[p] = sorted(set(results[p]))
    return results


def cw_display_results(text: str, results: Dict[str, List[int]]) -> None:
    print(f"\nTexte  : {repr(text)}")
    print(f"Taille : {len(text)} caractères\n")
    print("─" * 50)

    found_any = False
    for pattern, positions in sorted(results.items()):
        if positions:
            found_any = True
            for pos in positions:
                snippet = (
                    text[max(0, pos - 3):pos]
                    + f"[{text[pos:pos + len(pattern)]}]"
                    + text[pos + len(pattern):pos + len(pattern) + 3]
                )
                print(f"  «{pattern}»  à la position {pos:3d}  →  …{snippet}…")

    if not found_any:
        print("  Aucun motif trouvé.")
    print()


def run_commentz_walter(text: str, patterns: List[str]) -> None:
    print('\n--- Commentz-Walter ---')
    results = commentz_walter(text, patterns)
    cw_display_results(text, results)
    print('--- Fin Commentz-Walter ---\n')


######## PARTIE 5 : WU-MANBER ###############

def _wm_choose_B(B: int, m: int) -> int:
    if m <= 0:
        return 1
    if B <= 0:
        B = 2
    return min(B, m)


def wu_manber_preprocess(patterns: List[str], B: int = 2) -> Tuple[int, int, int, Dict[str, int], Dict[str, List[str]], Dict[str, List[str]]]:
    if not patterns:
        raise ValueError("La liste des motifs ne peut pas être vide.")

    m = min(len(p) for p in patterns)
    if m == 0:
        raise ValueError("Les motifs ne peuvent pas être vides.")

    B = _wm_choose_B(B, m)
    shift_default = m - B + 1

    shift: Dict[str, int] = {}
    hash_table: Dict[str, List[str]] = {}
    prefix_table: Dict[str, List[str]] = {}

    for pattern in patterns:
        key_part = pattern[:m]

        suffix_block = key_part[m - B:m]
        hash_table.setdefault(suffix_block, []).append(pattern)

        prefix_block = key_part[:B]
        prefix_table.setdefault(prefix_block, []).append(pattern)

        for q in range(0, m - B + 1):
            block = key_part[q:q + B]
            value = m - B - q
            if value < 0:
                value = 0
            if block not in shift or value < shift[block]:
                shift[block] = value

    return m, B, shift_default, shift, hash_table, prefix_table


def print_wu_manber_tables(m: int, B: int, shift_default: int, shift: Dict[str, int], hash_table: Dict[str, List[str]], prefix_table: Dict[str, List[str]]) -> None:
    print('--- Prétraitement Wu-Manber ---')
    print(f"m (longueur minimale) = {m}")
    print(f"B (taille du bloc) = {B}")
    print(f"Valeur par défaut Shift = {shift_default}\n")

    print('Table Shift (blocs -> décalage) :')
    for block in sorted(shift.keys()):
        print(f"  {block!r} : {shift[block]}")
    print('\nTable Hash (suffixe de taille B -> liste de motifs) :')
    for block in sorted(hash_table.keys()):
        print(f"  {block!r} : {hash_table[block]}")
    print('\nTable Prefix (préfixe de taille B -> liste de motifs) :')
    for block in sorted(prefix_table.keys()):
        print(f"  {block!r} : {prefix_table[block]}")
    print('--- Fin prétraitement Wu-Manber ---\n')


def wu_manber_search(text: str, patterns: List[str], B: int = 2, verbose: bool = True) -> Dict[str, List[int]]:
    if not text:
        return {p: [] for p in patterns}
    if not patterns:
        return {}

    m, B, shift_default, shift, hash_table, prefix_table = wu_manber_preprocess(patterns, B=B)
    if verbose:
        print_wu_manber_tables(m, B, shift_default, shift, hash_table, prefix_table)

    results: Dict[str, List[int]] = {p: [] for p in patterns}
    n = len(text)
    i = m - 1

    if verbose:
        print('Phase de recherche Wu-Manber :\n')
    while i < n:
        block = text[i - B + 1:i + 1]
        s = shift.get(block, shift_default)
        window_start = i - m + 1

        if verbose:
            window = text[window_start:window_start + m] if window_start >= 0 else ''
            print(f"i={i} fenêtre='{window}' suffixeBloc={block!r} Shift={s}")

        if s > 0:
            i += s
            continue

        candidates = hash_table.get(block, [])
        prefix_block = text[window_start:window_start + B]
        allowed = set(prefix_table.get(prefix_block, []))

        any_match = False
        for pat in candidates:
            if pat not in allowed:
                continue
            if window_start >= 0 and window_start + len(pat) <= n and text[window_start:window_start + len(pat)] == pat:
                results[pat].append(window_start)
                any_match = True
                if verbose:
                    print(f"  --> Occurrence trouvée: motif='{pat}' à la position {window_start}")

        i += 1
        if verbose:
            if any_match:
                print('  Décalage après correspondance = 1\n')
            else:
                print('  Aucun motif confirmé. Décalage = 1\n')

    for p in results:
        results[p] = sorted(set(results[p]))

    if verbose:
        print('Recherche terminée (Wu-Manber).')
        found_any = any(len(v) > 0 for v in results.values())
        if found_any:
            for p in patterns:
                if results[p]:
                    print(f"motif='{p}' trouvé aux positions {results[p]}")
        else:
            print('Aucune occurrence trouvée.')

    return results


def run_wu_manber(text: str, patterns: List[str]) -> None:
    print('\n--- Wu-Manber ---')
    print(f"Texte: '{text}'")
    wu_manber_search(text, patterns, B=2, verbose=True)
    print('--- Fin Wu-Manber ---\n')


def _run_silently(func, *args, **kwargs):
    with redirect_stdout(io.StringIO()):
        return func(*args, **kwargs)


def _format_table(headers: List[str], rows: List[List[object]]) -> str:
    str_rows = [[str(cell) for cell in row] for row in rows]
    widths = [len(h) for h in headers]
    for row in str_rows:
        for i, cell in enumerate(row):
            if i < len(widths):
                widths[i] = max(widths[i], len(cell))

    def fmt_row(parts: List[str]) -> str:
        return " | ".join(parts[i].ljust(widths[i]) for i in range(len(widths)))

    out = []
    out.append(fmt_row(headers))
    out.append("-+-".join("-" * w for w in widths))
    for row in str_rows:
        out.append(fmt_row(row))
    return "\n".join(out)


def _bench_ms(fn, *args, repeats: int = 3, **kwargs) -> Tuple[float, float]:
    times: List[float] = []
    for _ in range(repeats):
        t0 = time.perf_counter()
        fn(*args, **kwargs)
        times.append(time.perf_counter() - t0)
    return min(times) * 1000, (sum(times) / len(times)) * 1000


def _avg(values: List[float]) -> float:
    return (sum(values) / len(values)) if values else 0.0


def _slope_ms_per_char(sizes: List[int], times_ms: List[float]) -> float:
    """Pente approx. entre le premier et le dernier point (ms/caractère)."""
    if len(sizes) < 2 or len(times_ms) < 2:
        return 0.0
    dn = float(sizes[-1] - sizes[0])
    if dn == 0:
        return 0.0
    return (times_ms[-1] - times_ms[0]) / dn


def _speedup(a_ms: float, b_ms: float) -> float:
    """Combien de fois A est plus lent que B (A/B)."""
    if b_ms <= 0:
        return float('inf')
    return a_ms / b_ms


def _ascii_curve(title: str, sizes: List[int], times_ms: List[float]) -> None:
    print(title)
    if not sizes or not times_ms:
        print('  (aucune donnée)\n')
        return
    max_t = max(times_ms)
    scale = 40 / max_t if max_t > 0 else 1
    for n, t in zip(sizes, times_ms):
        bar = '#' * max(1, int(t * scale))
        print(f"  n={n:<6d} {t:>10.6f} ms | {bar}")
    print()


def _plot_curves(
    title: str,
    sizes: List[int],
    series: Dict[str, List[float]],
    ylabel: str,
    filename: str | None = None,
) -> None:
    """Affiche un graphique (et l'enregistre en PNG si filename est fourni)."""
    try:
        import matplotlib.pyplot as plt  # type: ignore
    except ModuleNotFoundError:
        print("[Graph] matplotlib n'est pas installé. Installe-le avec: pip install matplotlib")
        return

    from pathlib import Path

    def _unique_path(path: Path) -> Path:
        if not path.exists():
            return path
        stem = path.stem
        suffix = path.suffix
        parent = path.parent
        i = 2
        while True:
            candidate = parent / f"{stem}_{i}{suffix}"
            if not candidate.exists():
                return candidate
            i += 1

    fig, ax = plt.subplots()
    for label, values in series.items():
        if len(values) != len(sizes):
            continue
        ax.plot(sizes, values, marker='o', label=label)

    ax.set_title(title)
    ax.set_xlabel('Taille du texte (n)')
    ax.set_ylabel(ylabel)
    ax.grid(True, linestyle='--', alpha=0.4)
    if len(series) > 1:
        ax.legend()

    if filename:
        graphs_dir = Path(__file__).resolve().parent / 'graphs'
        graphs_dir.mkdir(parents=True, exist_ok=True)
        base_path = graphs_dir / filename
        out_path = _unique_path(base_path)
        fig.savefig(out_path, dpi=160, bbox_inches='tight')
        print(f"[Graph] Sauvegardé: {out_path}")

    # Non-bloquant: laisse les fenêtres ouvertes pendant que le programme continue.
    plt.show(block=False)
    plt.pause(0.001)


def _generate_patterns(k: int, L: int, rng, alphabet: str) -> List[str]:
    return [''.join(rng.choice(alphabet) for _ in range(L)) for _ in range(k)]


def _generate_text_with_embedded(text_len: int, patterns: List[str], rng, alphabet: str) -> str:
    text_list = [rng.choice(alphabet) for _ in range(text_len)]
    for pat in patterns:
        if len(pat) > text_len:
            continue
        pos = rng.randrange(0, text_len - len(pat) + 1)
        text_list[pos:pos + len(pat)] = list(pat)
    return ''.join(text_list)


def aho_corasick_search_multiple_stats(text: str, patterns: List[str]) -> Tuple[Dict[str, List[int]], int]:
    automaton = AhoCorasick()
    for pattern in patterns:
        automaton.add_pattern(pattern)
    automaton.build_automaton()

    node = automaton.root
    results: Dict[str, List[int]] = {p: [] for p in patterns}
    comparisons = 0

    for index, char in enumerate(text):
        # On compte chaque tentative de transition / test de transition comme une comparaison.
        while node is not automaton.root and node.get_transition(char) is None:
            comparisons += 1
            node = node.fail  # type: ignore[assignment]

        comparisons += 1
        next_node = node.get_transition(char)
        if next_node is not None:
            node = next_node
        else:
            node = automaton.root

        if node.output:
            for pat in node.output:
                start = index - len(pat) + 1
                results.setdefault(pat, []).append(start)

    for p in results:
        results[p] = sorted(set(results[p]))
    return results, comparisons


def commentz_walter_stats(text: str, patterns: List[str]) -> Tuple[Dict[str, List[int]], int]:
    if not patterns or not text:
        return {p: [] for p in patterns}, 0

    root = cw_build_trie(patterns)
    cw_build_fail_links(root)
    shift1, shift2, min_len = cw_build_shift_tables(patterns)

    results: Dict[str, List[int]] = {p: [] for p in patterns}
    comparisons = 0

    n = len(text)
    pos = min_len - 1

    while pos < n:
        node = root
        j = pos
        while j >= 0:
            ch = text[j]

            while node is not root and ch not in node.children:
                comparisons += 1
                node = node.fail  # type: ignore[assignment]

            comparisons += 1
            if ch in node.children:
                node = node.children[ch]
            else:
                break

            for pat in node.output:
                results[pat].append(j)

            j -= 1

        next_char = text[pos] if pos < n else None
        s1 = shift1.get(next_char, min_len) if next_char else min_len
        s1 = max(1, s1)
        s2 = shift2["_default"]
        s3 = min_len
        pos += max(s1, s2, s3)

    for p in results:
        results[p] = sorted(set(results[p]))
    return results, comparisons


def wu_manber_search_stats(text: str, patterns: List[str], B: int = 2) -> Tuple[Dict[str, List[int]], int]:
    if not text:
        return {p: [] for p in patterns}, 0
    if not patterns:
        return {}, 0

    m, B, shift_default, shift, hash_table, prefix_table = wu_manber_preprocess(patterns, B=B)
    results: Dict[str, List[int]] = {p: [] for p in patterns}
    comparisons = 0

    n = len(text)
    i = m - 1
    while i < n:
        comparisons += 1  # lookup shift sur le bloc suffixe
        block = text[i - B + 1:i + 1]
        s = shift.get(block, shift_default)
        window_start = i - m + 1

        if s > 0:
            i += s
            continue

        candidates = hash_table.get(block, [])
        prefix_block = text[window_start:window_start + B]
        allowed = set(prefix_table.get(prefix_block, []))

        for pat in candidates:
            if pat not in allowed:
                continue
            # Comparaison caractère par caractère pour compter les comparaisons.
            ok = True
            if window_start < 0 or window_start + len(pat) > n:
                continue
            for a, b in zip(pat, text[window_start:window_start + len(pat)]):
                comparisons += 1
                if a != b:
                    ok = False
                    break
            if ok:
                results[pat].append(window_start)

        i += 1

    for p in results:
        results[p] = sorted(set(results[p]))
    return results, comparisons


def aho_corasick_search_multiple(text: str, patterns: List[str]) -> Dict[str, List[int]]:
    automaton = AhoCorasick()
    for pattern in patterns:
        automaton.add_pattern(pattern)
    automaton.build_automaton()

    occurrences, _ = automaton.search(text)
    results: Dict[str, List[int]] = {p: [] for p in patterns}
    for start, pattern, _ in occurrences:
        results.setdefault(pattern, []).append(start)
    for p in results:
        results[p] = sorted(set(results[p]))
    return results


def run_performance_tests_cw_vs_ac() -> None:
    print('\n--- Tests de performance : Commentz-Walter vs Aho-Corasick ---')
    print('Format: tableau (taille, comparaisons, temps) + courbes (ASCII + matplotlib).')

    seed = time.time_ns()
    rng = random.Random(seed)
    alphabet = string.ascii_uppercase

    sizes = [50, 100, 200]
    k = 10
    L = 8
    repeats = 5

    print('\nÉtapes du test:')
    print('1) Générer k motifs aléatoires (seed aléatoire affiché pour traçabilité).')
    print('2) Pour chaque taille n: générer un texte aléatoire et y insérer les motifs.')
    print('3) Mesurer le temps (min sur plusieurs répétitions) et compter des opérations.')
    print('4) Afficher tableaux + courbes et sauvegarder les figures.\n')
    print(f'Paramètres: tailles={sizes}, k={k}, L={L}, répétitions={repeats}, alphabet=A-Z, seed={seed}')

    patterns = _generate_patterns(k, L, rng, alphabet)

    rows: List[List[object]] = []
    cw_times: List[float] = []
    ac_times: List[float] = []
    cw_comps_list: List[int] = []
    ac_comps_list: List[int] = []

    for n in sizes:
        text = _generate_text_with_embedded(n, patterns, rng, alphabet)

        # CW
        _, cw_comps = commentz_walter_stats(text, patterns)
        cw_min_ms, _ = _bench_ms(commentz_walter, text, patterns, repeats=repeats)
        cw_times.append(cw_min_ms)
        cw_comps_list.append(cw_comps)
        rows.append([n, "CW", cw_comps, f"{cw_min_ms/1000:.6g}"])

        # AC
        _, ac_comps = aho_corasick_search_multiple_stats(text, patterns)
        ac_min_ms, _ = _bench_ms(aho_corasick_search_multiple, text, patterns, repeats=repeats)
        ac_times.append(ac_min_ms)
        ac_comps_list.append(ac_comps)
        rows.append([n, "AC", ac_comps, f"{ac_min_ms/1000:.6g}"])

    print(_format_table(["Taille", "Algorithme", "Comparaisons", "Temps (s)"], rows) + '\n')
    _ascii_curve('Courbe AC (temps ms) vs taille n:', sizes, ac_times)
    _ascii_curve('Courbe CW (temps ms) vs taille n:', sizes, cw_times)

    _plot_curves(
        'Temps d\'exécution vs taille du texte (CW vs AC)',
        sizes,
        {'CW': cw_times, 'AC': ac_times},
        'Temps (ms)',
        filename=f'courbe_cw_vs_ac_temps_seed_{seed}.png',
    )
    _plot_curves(
        'Comparaisons vs taille du texte (CW vs AC)',
        sizes,
        {'CW': [float(x) for x in cw_comps_list], 'AC': [float(x) for x in ac_comps_list]},
        'Comparaisons',
        filename=f'courbe_cw_vs_ac_comparaisons_seed_{seed}.png',
    )
    print('Analyse:')
    print('- Les courbes montrent l’évolution du temps d’exécution selon la taille du texte.')
    print('- Note: le temps mesuré inclut ici le prétraitement + la recherche (construction automate / trie, etc.).')
    print('- Note: les "comparaisons" pour AC/CW sont des compteurs d’opérations (approximation), pas un comptage exact caractère-par-caractère.')
    print(f"- Temps moyen (ms): AC={_avg(ac_times):.6g}, CW={_avg(cw_times):.6g}")
    print(f"- Tendance (pente approx ms/caractère): AC={_slope_ms_per_char(sizes, ac_times):.6g}, CW={_slope_ms_per_char(sizes, cw_times):.6g}")
    # Speedups par taille (CW vs AC)
    print('- Accélération (CW/AC):')
    for n, t_cw, t_ac in zip(sizes, cw_times, ac_times):
        print(f"  n={n}: {_speedup(t_cw, t_ac):.2f}x")
    print("  (Interprétation: >1 ⇒ CW plus lent que AC; <1 ⇒ CW plus rapide que AC)")

    print('- Détails par taille (comparaisons & temps):')
    for n, c_cw, c_ac, t_cw, t_ac in zip(sizes, cw_comps_list, ac_comps_list, cw_times, ac_times):
        comp_ratio = _speedup(float(c_cw), float(c_ac))
        time_ratio = _speedup(t_cw, t_ac)
        print(f"  n={n}: comps  CW={c_cw}, AC={c_ac} (×{comp_ratio:.2f})")
        print(f"        temps  CW={t_cw:.6g}ms, AC={t_ac:.6g}ms (×{time_ratio:.2f})")
    print()

    print('- Interprétation (pourquoi AC est souvent très bon en multi-motifs):')
    print("  • AC construit un automate des préfixes + liens d’échec, puis parcourt le texte une seule fois.")
    print("  • Quand le nombre de motifs k augmente, AC amortit bien la recherche car l’automate partage les préfixes.")
    print("  • Dans ce script, le prétraitement est compté dans le temps; AC peut rester compétitif même ainsi si k est significatif.")
    print()

    print('- Quand CW peut être compétitif (ou meilleur):')
    print("  • Si les décalages (shifts) sont grands, CW peut sauter des positions et réduire le nombre d’états visités.")
    print("  • Si les motifs sont longs / peu corrélés au texte, les échecs arrivent tôt et le saut peut être avantageux.")
    print()

    print('- Remarques méthodologie (important pour le rapport):')
    print("  • Les compteurs d’opérations AC/CW ne mesurent pas la même chose (transition/fail vs appartenance au trie) → comparer surtout les tendances.")
    print(
        "  • Le temps reporté est le minimum sur plusieurs répétitions (réduit le bruit).\n"
        "  • Pour isoler la phase de recherche pure, il faudrait prétraiter une seule fois et ne timer que la recherche; ici on mesure l’ensemble (prétraitement + recherche)."
    )
    print()

    print('- Conclusion: AC est généralement robuste en multi-motifs; CW dépend davantage de la structure des motifs et des sauts possibles.')
    print('--- Fin tests perf CW vs AC ---\n')


def run_performance_tests_cw_vs_wm() -> None:
    print('\n--- Tests de performance : Commentz-Walter vs Wu-Manber ---')
    print('Format: tableau (taille, comparaisons, temps) + courbes (ASCII + matplotlib).')

    seed = time.time_ns()
    rng = random.Random(seed)
    alphabet = string.ascii_uppercase

    sizes = [50, 100, 200]
    k = 10
    L = 8
    repeats = 5

    print('\nÉtapes du test:')
    print('1) Générer k motifs aléatoires (seed aléatoire affiché pour traçabilité).')
    print('2) Pour chaque taille n: générer un texte aléatoire et y insérer les motifs.')
    print('3) Mesurer le temps (min sur plusieurs répétitions) et compter des opérations.')
    print('4) Afficher tableaux + courbes et sauvegarder les figures.\n')
    print(f'Paramètres: tailles={sizes}, k={k}, L={L}, répétitions={repeats}, B=2, alphabet=A-Z, seed={seed}')

    patterns = _generate_patterns(k, L, rng, alphabet)

    rows: List[List[object]] = []
    cw_times: List[float] = []
    wm_times: List[float] = []
    cw_comps_list: List[int] = []
    wm_comps_list: List[int] = []

    for n in sizes:
        text = _generate_text_with_embedded(n, patterns, rng, alphabet)

        _, cw_comps = commentz_walter_stats(text, patterns)
        cw_min_ms, _ = _bench_ms(commentz_walter, text, patterns, repeats=repeats)
        cw_times.append(cw_min_ms)
        cw_comps_list.append(cw_comps)
        rows.append([n, "CW", cw_comps, f"{cw_min_ms/1000:.6g}"])

        _, wm_comps = wu_manber_search_stats(text, patterns, B=2)
        wm_min_ms, _ = _bench_ms(wu_manber_search, text, patterns, repeats=repeats, B=2, verbose=False)
        wm_times.append(wm_min_ms)
        wm_comps_list.append(wm_comps)
        rows.append([n, "WM", wm_comps, f"{wm_min_ms/1000:.6g}"])

    print(_format_table(["Taille", "Algorithme", "Comparaisons", "Temps (s)"], rows) + '\n')
    _ascii_curve('Courbe WM (temps ms) vs taille n:', sizes, wm_times)
    _ascii_curve('Courbe CW (temps ms) vs taille n:', sizes, cw_times)

    _plot_curves(
        'Temps d\'exécution vs taille du texte (CW vs WM)',
        sizes,
        {'CW': cw_times, 'WM': wm_times},
        'Temps (ms)',
        filename=f'courbe_cw_vs_wm_temps_seed_{seed}.png',
    )
    _plot_curves(
        'Comparaisons vs taille du texte (CW vs WM)',
        sizes,
        {'CW': [float(x) for x in cw_comps_list], 'WM': [float(x) for x in wm_comps_list]},
        'Comparaisons',
        filename=f'courbe_cw_vs_wm_comparaisons_seed_{seed}.png',
    )
    print('Analyse:')
    print('- Les courbes montrent l’évolution du temps d’exécution selon la taille du texte.')
    print('- Note: le temps mesuré inclut ici le prétraitement + la recherche (tables Shift/Hash/Prefix ou trie).')
    print('- Note: les "comparaisons" CW/WM sont des compteurs d’opérations (approximation) pour comparer des tendances.')
    print(f"- Temps moyen (ms): WM={_avg(wm_times):.6g}, CW={_avg(cw_times):.6g}")
    print(f"- Tendance (pente approx ms/caractère): WM={_slope_ms_per_char(sizes, wm_times):.6g}, CW={_slope_ms_per_char(sizes, cw_times):.6g}")
    print('- Accélération (CW/WM):')
    for n, t_cw, t_wm in zip(sizes, cw_times, wm_times):
        print(f"  n={n}: {_speedup(t_cw, t_wm):.2f}x")

    print('- Détails par taille (comparaisons & temps):')
    for n, c_cw, c_wm, t_cw, t_wm in zip(sizes, cw_comps_list, wm_comps_list, cw_times, wm_times):
        comp_ratio = _speedup(float(c_cw), float(c_wm))
        time_ratio = _speedup(t_cw, t_wm)
        print(f"  n={n}: comps  CW={c_cw}, WM={c_wm} (×{comp_ratio:.2f})")
        print(f"        temps  CW={t_cw:.6g}ms, WM={t_wm:.6g}ms (×{time_ratio:.2f})")
    print()

    print('- Interprétation (pourquoi WM peut être très rapide):')
    print("  • WM utilise des tables Shift/Hash/Prefix sur des blocs (ici B=2). Si Shift>0, il saute plusieurs positions.")
    print("  • Sur texte aléatoire, beaucoup de blocs suffixes ne correspondent à aucun motif → Shift est souvent >0 → gros gains.")
    print("  • Quand Shift=0, WM vérifie les candidats (comparaisons caractère-par-caractère) → coût local mais limité au nombre de candidats.")
    print()

    print('- Quand WM peut perdre du terrain:')
    print("  • Si beaucoup de blocs apparaissent dans les motifs (Hash chargé), on vérifie plus de candidats.")
    print("  • Si le texte est très répétitif, Shift peut être souvent petit (moins de sauts).")
    print("  • Le choix de B influence: B trop petit → plus de collisions/candidats; B trop grand → moins flexible si motifs courts.")
    print()

    print('- Remarques méthodologie (important pour le rapport):')
    print("  • Les compteurs d’opérations CW/WM ne sont pas identiques (trie/fail vs lookups + vérification) → comparer surtout les tendances.")
    print(
        "  • Le temps reporté est le minimum sur plusieurs répétitions (réduit le bruit).\n"
        "  • Ici on mesure prétraitement + recherche; WM et CW ont des coûts de prétraitement différents."
    )
    print()

    print('- Conclusion: WM est souvent excellent sur texte aléatoire grâce aux sauts; CW peut devenir intéressant si ses décalages sont grands et que les motifs/texte favorisent le trie.')
    print('--- Fin tests perf CW vs WM ---\n')


def run_tests_naive_vs_bm() -> None:
    print('\n--- Test et analyse : Naïf vs Boyer-Moore ---')
    print('On reporte: tailles (n,m), comparaisons et temps (ms), + courbes (ASCII + matplotlib).')

    seed = time.time_ns()
    rng = random.Random(seed)
    alphabet = string.ascii_uppercase

    sizes = [50, 100, 200]
    m = 8
    repeats = 10

    print('\nÉtapes du test:')
    print('1) Générer un motif P de longueur m (seed aléatoire affiché pour traçabilité).')
    print('2) Pour chaque taille n: générer un texte aléatoire et insérer P au moins une fois.')
    print('3) Mesurer le temps (min sur plusieurs répétitions) et compter les comparaisons exactes.')
    print('4) Afficher tableaux + courbes et sauvegarder les figures.\n')
    print(f'Paramètres: tailles={sizes}, m={m}, répétitions={repeats}, alphabet=A-Z, seed={seed}')

    pattern = ''.join(rng.choice(alphabet) for _ in range(m))

    headers = ["Taille", "Algorithme", "m", "Comparaisons", "Temps (s)"]
    rows: List[List[object]] = []
    naive_times: List[float] = []
    bm_times: List[float] = []
    naive_comps_list: List[int] = []
    bm_comps_list: List[int] = []

    for n in sizes:
        # Texte aléatoire + insertion du motif au moins une fois
        text = _generate_text_with_embedded(n, [pattern], rng, alphabet)

        occ, naive_comps = _run_silently(naive_search, text, pattern)
        naive_min_ms, _ = _bench_ms(lambda: _run_silently(naive_search, text, pattern), repeats=repeats)
        naive_times.append(naive_min_ms)
        naive_comps_list.append(naive_comps)
        rows.append([n, "Naïf", m, naive_comps, f"{naive_min_ms/1000:.6g}"])

        occ, bm_comps = _run_silently(boyer_moore_search, text, pattern)
        bm_min_ms, _ = _bench_ms(lambda: _run_silently(boyer_moore_search, text, pattern), repeats=repeats)
        bm_times.append(bm_min_ms)
        bm_comps_list.append(bm_comps)
        rows.append([n, "BM", m, bm_comps, f"{bm_min_ms/1000:.6g}"])

    print('\n' + _format_table(headers, rows) + '\n')
    _ascii_curve('Courbe Naïf (temps ms) vs taille n:', sizes, naive_times)
    _ascii_curve('Courbe BM (temps ms) vs taille n:', sizes, bm_times)

    _plot_curves(
        'Temps d\'exécution vs taille du texte (Naïf vs BM)',
        sizes,
        {'Naïf': naive_times, 'BM': bm_times},
        'Temps (ms)',
        filename=f'courbe_naif_vs_bm_temps_seed_{seed}.png',
    )
    _plot_curves(
        'Comparaisons vs taille du texte (Naïf vs BM)',
        sizes,
        {'Naïf': [float(x) for x in naive_comps_list], 'BM': [float(x) for x in bm_comps_list]},
        'Comparaisons',
        filename=f'courbe_naif_vs_bm_comparaisons_seed_{seed}.png',
    )
    print('Analyse:')
    print('- Les courbes montrent l’évolution du temps d’exécution selon la taille du texte.')
    print('- Ici, les comparaisons Naïf/BM sont comptées de manière directe (caractère-par-caractère).')
    print(f"- Temps moyen (ms): Naïf={_avg(naive_times):.6g}, BM={_avg(bm_times):.6g}")
    print(f"- Tendance (pente approx ms/caractère): Naïf={_slope_ms_per_char(sizes, naive_times):.6g}, BM={_slope_ms_per_char(sizes, bm_times):.6g}")
    print('- Accélération (Naïf/BM):')
    for n, t_nv, t_bm in zip(sizes, naive_times, bm_times):
        print(f"  n={n}: {_speedup(t_nv, t_bm):.2f}x")
    print('- Détails par taille (comparaisons & temps):')
    for n, c_nv, c_bm, t_nv, t_bm in zip(sizes, naive_comps_list, bm_comps_list, naive_times, bm_times):
        comp_ratio = _speedup(float(c_nv), float(c_bm))
        time_ratio = _speedup(t_nv, t_bm)
        print(f"  n={n}: comps  Naïf={c_nv}, BM={c_bm} (×{comp_ratio:.2f})")
        print(f"        temps  Naïf={t_nv:.6g}ms, BM={t_bm:.6g}ms (×{time_ratio:.2f})")
    print()

    print('- Interprétation (pourquoi BM est souvent meilleur):')
    print("  • Naïf aligne le motif à chaque position et compare jusqu’à la 1ère différence → beaucoup de comparaisons quand n grandit.")
    print("  • BM (ici: heuristique du mauvais caractère) compare depuis la fin du motif. En cas d’échec, il peut décaler de plusieurs positions → moins d’alignements testés.")
    print("  • Sur texte aléatoire (alphabet A–Z), les mismatches arrivent vite et les décalages peuvent être importants, donc BM gagne souvent.")
    print()

    print('- Quand BM gagne moins (ou peut se rapprocher du naïf):')
    print("  • Si le texte contient beaucoup de répétitions ou si le motif partage beaucoup de suffixes/prefixes avec le texte, les décalages sont plus petits.")
    print("  • Ce script force l’insertion du motif au moins une fois: près d’une occurrence, les comparaisons augmentent et l’avantage de BM peut diminuer.")
    print()

    print('- Remarques méthodologie:')
    print("  • Le temps reporté est le minimum sur plusieurs répétitions (réduit le bruit mais rend les résultats plus stables).")
    print("  • Ici BM n’utilise que le mauvais caractère (pas la bonne suffixe), donc le speedup observé est un gain ‘raisonnable’ mais pas le maximum théorique.")
    print('--- Fin test Naïf vs BM ---\n')


def main() -> None:
    try:
        while True:
            print('Choisissez l\'algorithme :')
            print('1 - Naïf')
            print('2 - Boyer-Moore')
            print('3 - Aho-Corasick')
            print('4 - Commentz-Walter')
            print('5 - Wu-Manber')
            print('6 - Tests perf (CW vs Wu-Manber)')
            print('7 - Tests perf (CW vs Aho-Corasick)')
            print('8 - Tests/Analyse (Naïf vs Boyer-Moore)')
            print('0 - Quitter')
            choix = _safe_input('Votre choix (0 à 8) : ').strip()

            if choix == '0':
                print('Fin du programme.')
                return

            if choix == '6':
                run_performance_tests_cw_vs_wm()
                _safe_input('Appuyez sur Entrée pour revenir au menu... ')
                print('--- Retour au menu ---\n')
                continue

            if choix == '7':
                run_performance_tests_cw_vs_ac()
                _safe_input('Appuyez sur Entrée pour revenir au menu... ')
                print('--- Retour au menu ---\n')
                continue

            if choix == '8':
                run_tests_naive_vs_bm()
                _safe_input('Appuyez sur Entrée pour revenir au menu... ')
                print('--- Retour au menu ---\n')
                continue

            if choix not in {'1', '2', '3', '4', '5'}:
                print('Choix invalide. Veuillez réessayer.\n')
                continue

            text = _safe_input('Texte T = ')

            if choix == '1':
                motif = read_single_pattern()
                if motif == '':
                    print('Aucun motif fourni. Retour au menu.\n')
                    continue
                run_naive(text, motif)
            elif choix == '2':
                motif = read_single_pattern()
                if motif == '':
                    print('Aucun motif fourni. Retour au menu.\n')
                    continue
                run_boyer_moore(text, [motif])
            elif choix == '3':
                patterns = read_patterns()
                if not patterns:
                    print('Aucun motif fourni. Retour au menu.\n')
                    continue
                run_aho_corasick(text, patterns)
            elif choix == '4':
                patterns = read_patterns_for('Commentz-Walter')
                if not patterns:
                    print('Aucun motif fourni. Retour au menu.\n')
                    continue
                run_commentz_walter(text, patterns)
            else:
                patterns = read_patterns_for('Wu-Manber')
                if not patterns:
                    print('Aucun motif fourni. Retour au menu.\n')
                    continue
                run_wu_manber(text, patterns)

            _safe_input('Appuyez sur Entrée pour revenir au menu... ')
            print('--- Retour au menu ---\n')
    except KeyboardInterrupt:
        print('\nInterrompu (Ctrl+C). Fin du programme.')
        return


if __name__ == '__main__':
    main()

##Texte T = ABC-ABCDAB-ABCDABCDABDE
##Motif M = ABCDABD