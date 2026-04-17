

from collections import deque
from typing import Dict, List, Optional, Tuple
import tkinter as tk

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
    print("Entrez les motifs Aho-Corasick, un par ligne. Laissez une ligne vide pour terminer.")
    patterns: List[str] = []
    index = 1
    while True:
        motif = input(f"Motif {index} = ")
        if motif == "":
            break
        patterns.append(motif)
        index += 1
    return patterns


def read_single_pattern() -> str:
    motif = input("Motif = ").strip()
    return motif


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


def main() -> None:
    print('Choisissez l\'algorithme :')
    print('1 - Boyer-Moore')
    print('2 - Aho-Corasick')
    choix = input('Votre choix (1 ou 2) : ').strip()

    text = input('Texte T = ')
    if choix == '1':
        motif = read_single_pattern()
        if motif == '':
            print('Aucun motif fourni. Fin du programme.')
            return
        run_boyer_moore(text, [motif])
    else:
        patterns = read_patterns()
        if not patterns:
            print('Aucun motif fourni. Fin du programme.')
            return
        run_aho_corasick(text, patterns)


if __name__ == '__main__':
    main()
##Texte T = ABC-ABCDAB-ABCDABCDABDE
##Motif M = ABCDABD