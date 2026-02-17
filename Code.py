import tkinter as tk
from collections import deque
import heapq
import math

# --- Grid Configuration ---
ROWS, COLS = 20, 20
CELL_SIZE = 30

# Visual Colors
EMPTY_COLOR = "white"
START_COLOR = "green"
TARGET_COLOR = "red"
FRONTIER_COLOR = "blue"
EXPLORED_COLOR = "lightgray"
PATH_COLOR = "yellow"

# 8-Directional Movement
DIRS = [(-1, 0), (-1, 1), (0, 1), (1, 1), (1, 0), (1, -1), (0, -1), (-1, -1)]

def in_bounds(r, c):
    return 0 <= r < ROWS and 0 <= c < COLS

class FinalPathfinderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("AI Search Visualizer (20x20)")

        # Control Panel (Top)
        self.controls = tk.Frame(root)
        self.controls.pack(pady=5)

        self.alg_var = tk.StringVar(value="BFS")
        tk.Label(self.controls, text="Algorithm:").grid(row=0, column=0, padx=5)
        tk.OptionMenu(self.controls, self.alg_var, "BFS", "DFS", "UCS", "DLS", "IDDFS", "Bidirectional").grid(row=0, column=1)

        tk.Button(self.controls, text="Set Start", command=lambda: self.set_mode("start")).grid(row=0, column=2, padx=2)
        tk.Button(self.controls, text="Set Target", command=lambda: self.set_mode("target")).grid(row=0, column=3, padx=2)
        tk.Button(self.controls, text="Run", command=self.start_search, bg="#90ee90", width=10).grid(row=0, column=4, padx=5)
        tk.Button(self.controls, text="Reset", command=self.reset_grid).grid(row=0, column=5, padx=2)

        # Main Grid Canvas
        self.canvas = tk.Canvas(root, width=COLS * CELL_SIZE, height=ROWS * CELL_SIZE, bg="white")
        self.canvas.pack(padx=10, pady=10)

        # State Variables
        self.start, self.target = None, None
        self.mode = None
        self.running = False
        self.cells = [[self.canvas.create_rectangle(c*CELL_SIZE, r*CELL_SIZE, (c+1)*CELL_SIZE, (r+1)*CELL_SIZE, fill=EMPTY_COLOR, outline="#d3d3d3") for c in range(COLS)] for r in range(ROWS)]
        
        self.canvas.bind("<Button-1>", self.on_click)

    def set_mode(self, mode):
        self.mode = mode

    def on_click(self, event):
        if self.running: return
        c, r = event.x // CELL_SIZE, event.y // CELL_SIZE
        if not in_bounds(r, c): return

        if self.mode == "start":
            if self.start: self.update_cell(*self.start, EMPTY_COLOR)
            self.start = (r, c)
            self.update_cell(r, c, START_COLOR)
        elif self.mode == "target":
            if self.target: self.update_cell(*self.target, EMPTY_COLOR)
            self.target = (r, c)
            self.update_cell(r, c, TARGET_COLOR)

    def update_cell(self, r, c, color):
        self.canvas.itemconfig(self.cells[r][c], fill=color)

    def reset_grid(self):
        self.running = False
        self.start, self.target = None, None
        for r in range(ROWS):
            for c in range(COLS):
                self.update_cell(r, c, EMPTY_COLOR)

    def start_search(self):
        if not self.start or not self.target or self.running: return
        self.running = True
        alg = self.alg_var.get()
        
        # Select Algorithm Generator
        if alg == "BFS": gen = self.bfs()
        elif alg == "DFS": gen = self.dfs()
        elif alg == "UCS": gen = self.ucs()
        elif alg == "DLS": gen = self.dls(self.start, 25) # Depth limit set for 20x20
        elif alg == "IDDFS": gen = self.iddfs()
        elif alg == "Bidirectional": gen = self.bidirectional()
        
        self.animate(gen)

    def animate(self, generator):
        try:
            state = next(generator)
            for r in range(ROWS):
                for c in range(COLS):
                    pos = (r, c)
                    if pos == self.start: self.update_cell(r, c, START_COLOR)
                    elif pos == self.target: self.update_cell(r, c, TARGET_COLOR)
                    elif "path" in state and pos in state["path"]: self.update_cell(r, c, PATH_COLOR)
                    elif pos in state.get("explored", []): self.update_cell(r, c, EXPLORED_COLOR)
                    elif pos in state.get("frontier", []): self.update_cell(r, c, FRONTIER_COLOR)
            
            self.root.after(20, lambda: self.animate(generator)) # Faster 20ms delay
        except StopIteration:
            self.running = False

    # --- Search Algorithms ---

    def bfs(self):
        queue = deque([self.start])
        came_from = {self.start: None}
        explored = []
        while queue:
            curr = queue.popleft()
            if curr == self.target:
                yield {"path": self.get_path(came_from), "explored": explored}
                return
            explored.append(curr)
            for dr, dc in DIRS:
                nb = (curr[0]+dr, curr[1]+dc)
                if in_bounds(*nb) and nb not in came_from:
                    came_from[nb] = curr
                    queue.append(nb)
                    yield {"frontier": list(queue), "explored": explored}

    def dfs(self):
        stack = [self.start]
        came_from = {self.start: None}
        explored = []
        while stack:
            curr = stack.pop()
            if curr == self.target:
                yield {"path": self.get_path(came_from), "explored": explored}
                return
            if curr not in explored:
                explored.append(curr)
                for dr, dc in DIRS:
                    nb = (curr[0]+dr, curr[1]+dc)
                    if in_bounds(*nb) and nb not in came_from:
                        came_from[nb] = curr
                        stack.append(nb)
                yield {"frontier": list(stack), "explored": explored}

    def ucs(self):
        pq = [(0, self.start)]
        came_from = {self.start: None}
        cost_so_far = {self.start: 0}
        explored = []
        while pq:
            cost, curr = heapq.heappop(pq)
            if curr == self.target:
                yield {"path": self.get_path(came_from), "explored": explored}
                return
            explored.append(curr)
            for dr, dc in DIRS:
                nb = (curr[0]+dr, curr[1]+dc)
                weight = 1.4 if dr!=0 and dc!=0 else 1.0 # Heuristic cost for diagonals
                new_cost = cost + weight
                if in_bounds(*nb) and (nb not in cost_so_far or new_cost < cost_so_far[nb]):
                    cost_so_far[nb] = new_cost
                    came_from[nb] = curr
                    heapq.heappush(pq, (new_cost, nb))
                    yield {"frontier": [x[1] for x in pq], "explored": explored}

    def dls(self, start, limit, explored_total=None):
        stack = [(start, 0)]
        came_from = {start: None}
        explored = explored_total if explored_total is not None else []
        while stack:
            curr, depth = stack.pop()
            if curr == self.target:
                return True, self.get_path(came_from), explored
            if depth < limit:
                explored.append(curr)
                for dr, dc in DIRS:
                    nb = (curr[0]+dr, curr[1]+dc)
                    if in_bounds(*nb) and nb not in explored:
                        came_from[nb] = curr
                        stack.append((nb, depth + 1))
                yield {"frontier": [x[0] for x in stack], "explored": explored}
        return False, [], explored

    def iddfs(self):
        for depth in range(ROWS * COLS):
            success, path, explored = yield from self.dls(self.start, depth)
            if success:
                yield {"path": path, "explored": explored}
                return

    def bidirectional(self):
        f_q, b_q = deque([self.start]), deque([self.target])
        f_came, b_came = {self.start: None}, {self.target: None}
        exp = []
        while f_q and b_q:
            # Forward expansion
            cf = f_q.popleft(); exp.append(cf)
            for dr, dc in DIRS:
                nb = (cf[0]+dr, cf[1]+dc)
                if in_bounds(*nb) and nb not in f_came:
                    f_came[nb] = cf; f_q.append(nb)
                    if nb in b_came:
                        yield {"path": self.merge_path(f_came, b_came, nb), "explored": exp}
                        return
            # Backward expansion
            cb = b_q.popleft(); exp.append(cb)
            for dr, dc in DIRS:
                nb = (cb[0]+dr, cb[1]+dc)
                if in_bounds(*nb) and nb not in b_came:
                    b_came[nb] = cb; b_q.append(nb)
                    if nb in f_came:
                        yield {"path": self.merge_path(f_came, b_came, nb), "explored": exp}
                        return
            yield {"frontier": list(f_q) + list(b_q), "explored": exp}

    # --- Path Helpers ---
    def get_path(self, came_from):
        path, curr = [], self.target
        while curr:
            path.append(curr)
            curr = came_from.get(curr)
        return path

    def merge_path(self, f_came, b_came, meeting):
        path_f, curr = [], meeting
        while curr: path_f.append(curr); curr = f_came.get(curr)
        path_b, curr = [], b_came.get(meeting)
        while curr: path_b.append(curr); curr = b_came.get(curr)
        return path_f[::-1] + path_b

if __name__ == "__main__":
    root = tk.Tk()
    app = FinalPathfinderApp(root)
    root.mainloop()
