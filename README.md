# 🔎 String Matching Algorithms

A Python project implementing and comparing several **string pattern matching algorithms**, with detailed execution traces, automaton visualizations, and performance analysis.

The project was developed as an algorithmic study of different approaches to searching for one or multiple patterns inside a text.

## 📌 Algorithms Implemented

The project includes the following algorithms:

- **Naïve String Matching**
- **Boyer-Moore**
- **Aho-Corasick**
- **Commentz-Walter**
- **Wu-Manber**

It also provides performance comparisons between:

- Naïve vs Boyer-Moore
- Commentz-Walter vs Aho-Corasick
- Commentz-Walter vs Wu-Manber

---

## ✨ Features

### 🔹 Naïve Algorithm

The classical brute-force pattern matching approach.

For each possible position in the text, the algorithm compares the pattern character by character and records:

- Pattern occurrences
- Their positions
- Number of character comparisons
- Detailed search steps

### 🔹 Boyer-Moore

An implementation using the **bad-character heuristic**.

The program builds a bad-character table and searches the text from right to left within each window, allowing the pattern to skip several positions after a mismatch.

The implementation also displays the generated `d[c][j]` table and the calculated shifts during the search.

### 🔹 Aho-Corasick

A multi-pattern matching algorithm based on a **Trie / prefix automaton**.

The implementation includes:

- Trie construction
- Failure links
- Output function
- Multi-pattern search
- Search path tracing
- Tkinter visualization of the Trie
- Tkinter visualization of the complete automaton
- Tkinter visualization of the search path

The automaton is built by inserting all patterns and then constructing failure links using a queue. 

### 🔹 Commentz-Walter

A multi-pattern matching algorithm combining ideas from:

- Trie structures
- Failure links
- Good-suffix shifting
- Pattern matching from right to left

Patterns are stored in a trie using their **reversed characters**, and shift tables are constructed to skip positions during the search.

### 🔹 Wu-Manber

A multi-pattern matching algorithm based on:

- Block-based searching
- Shift tables
- Hash tables
- Prefix filtering

The implementation uses a configurable block size, with the performance tests using:

```text
B = 2
```

---

# 📊 Performance Analysis

The project includes automated benchmarks comparing the algorithms.

## Naïve vs Boyer-Moore

The benchmark tests text sizes:

```text
50
100
200
```

with a pattern length of:

```text
m = 8
```

and performs multiple repetitions to obtain more stable timing measurements.

The program compares:

- Number of comparisons
- Execution time
- Execution-time evolution as text size increases
- Approximate speedup

The pattern is also inserted into the generated text at least once.

---

## Commentz-Walter vs Aho-Corasick

The benchmark generates:

- `10` random patterns
- Pattern length: `8`
- Text sizes: `50`, `100`, `200`
- Alphabet: `A-Z`
- Multiple repetitions

It measures both:

- Approximate number of operations/comparisons
- Execution time

The program also generates graphs comparing both algorithms.

### General observation

Aho-Corasick is particularly well suited to multi-pattern searching because it builds a shared prefix automaton and processes the text in a single traversal.

Commentz-Walter can benefit from larger shifts, especially when the patterns and text allow many positions to be skipped.

---

## Commentz-Walter vs Wu-Manber

Another benchmark compares Commentz-Walter and Wu-Manber under the same general experimental setup.

Wu-Manber uses block-based shift information. When the suffix block does not correspond to a pattern, the algorithm can skip several positions.

Its performance can depend strongly on:

- Block size `B`
- Pattern characteristics
- Text repetition
- Number of candidate patterns produced by the hash table

---

# 📈 Graph Generation

Performance graphs are automatically generated using **Matplotlib**.

The program produces graphs for:

```text
Execution time vs text size
Comparisons vs text size
```

for each benchmark.

Generated graphs are saved inside a:

```text
graphs/
```

directory.

The filenames contain the random seed used for the experiment, for example:

```text
courbe_cw_vs_ac_temps_seed_<seed>.png
courbe_cw_vs_ac_comparaisons_seed_<seed>.png
courbe_cw_vs_wm_temps_seed_<seed>.png
courbe_cw_vs_wm_comparaisons_seed_<seed>.png
courbe_naif_vs_bm_temps_seed_<seed>.png
courbe_naif_vs_bm_comparaisons_seed_<seed>.png
```

---

# 🖥️ Interactive Menu

When the program starts, the following menu is displayed:

```text
Choisissez l'algorithme :

1 - Naïf
2 - Boyer-Moore
3 - Aho-Corasick
4 - Commentz-Walter
5 - Wu-Manber
6 - Tests perf (CW vs Wu-Manber)
7 - Tests perf (CW vs Aho-Corasick)
8 - Tests/Analyse (Naïf vs Boyer-Moore)
0 - Quitter
```

For the single-pattern algorithms, the user enters:

```text
Texte T =
Motif =
```

For multi-pattern algorithms, multiple patterns can be entered, one per line, until an empty line is entered.

---

# 🧩 Project Structure

The main Python file contains the complete implementation:

```text
Devoirfinale.py
```

The code is organized into several sections:

```text
PARTIE 1 : BOYER-MOORE
PARTIE 2 : AHO-CORASICK
PARTIE 3 : ALGORITHME NAÏF
PARTIE 4 : COMMENTZ-WALTER
PARTIE 5 : WU-MANBER
```

It also contains:

- Input handling
- Performance utilities
- Random test generation
- Benchmarking
- ASCII performance curves
- Matplotlib graph generation
- Interactive Tkinter visualizations
- Main interactive menu

---

# 🛠️ Requirements

## Python

Python **3.10+** is recommended.

The project uses standard Python modules including:

```text
collections
typing
tkinter
random
string
time
io
contextlib
```

For performance graphs, install Matplotlib:

```bash
pip install matplotlib
```

Tkinter is also required for the Aho-Corasick graphical visualizations.

### Windows

Tkinter is generally included with standard Python installations.

---

# 🚀 How to Run

Clone the repository:

```bash
git clone https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git
cd YOUR_REPOSITORY
```

Install the optional graphing dependency:

```bash
pip install matplotlib
```

Run the program:

```bash
python Devoirfinale.py
```

Then select an algorithm from the interactive menu.

---

# 🧪 Example

Example text:

```text
ABC-ABCDAB-ABCDABCDABDE
```

Example pattern:

```text
ABCDABD
```

The program then displays the search process, comparisons, shifts, and occurrence positions depending on the selected algorithm.

---

# 📚 Educational Objectives

This project aims to provide a practical understanding of:

- Exact string matching
- Single-pattern vs multi-pattern searching
- Trie data structures
- Failure functions
- Automata
- Pattern preprocessing
- Shift heuristics
- Hash-based filtering
- Algorithmic complexity
- Performance benchmarking
- Empirical algorithm comparison

Rather than only returning the final occurrence positions, the program exposes the internal steps of several algorithms to make their behavior easier to study and compare.

---

# ⚠️ Benchmarking Notes

The benchmark results are **machine-dependent**.

Execution time can vary depending on:

- CPU
- Operating system
- Python version
- Background processes
- Randomly generated input
- Number and characteristics of patterns

The benchmark uses the **minimum execution time across repeated runs** to reduce timing noise.

The comparison counters for Aho-Corasick, Commentz-Walter, and Wu-Manber represent approximate operation counts and are **not necessarily equivalent character-by-character measurements**.

Therefore, the benchmark results should primarily be interpreted as **performance trends**, rather than absolute measurements.

---

# 👩‍💻 Authors

**Hadjiedj Amel Hiba**

USTHB — Faculty of Computer Science

---

# 📄 License

This project was developed for educational and academic purposes.