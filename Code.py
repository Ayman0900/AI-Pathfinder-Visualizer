import tkinter as tk
from collections import deque
import heapq

# --- Configuration (Based on Assignment Instructions) ---
ROWS, COLS = 10, 10  # Shorter 10x10 grid as per Task 7
CELL_SIZE = 50       # Larger cells for better visibility
TITLE = "GOOD PERFORMANCE TIME APP"

# Cyber-Grid Color Palette
COLOR_BG      = "#0F172A"  # Midnight Blue
COLOR_EMPTY   = "#1E293B"  # Slate Tile
COLOR_BORDER  = "#334155"  # Muted Border
COLOR_START   = "#22C55E"  # Neon Green (s)
COLOR_TARGET  = "#3B82F6"  # Bright Blue (t)
COLOR_FRONTIER= "#EAB308"  # Gold
COLOR_EXPLORED= "#64748B"  # Muted Blue/Gray
COLOR_PATH    = "#EC4899"  # Pink/Magenta

# STRICT CLOCKWISE 8-DIRECTIONAL ORDER (As per requirements)
# 1.Up, 2.Top-Right, 3.Right, 4.Bottom-Right, 5.Bottom, 6.Bottom-Left, 7.Left, 8.Top-Left
DIRS = [(-1, 0), (-1, 1), (0, 1), (1, 1), (1, 0), (1, -1), (0, -1), (-1, -1)]

def in_bounds(r, c):
    return 0 <= r < ROWS and 0 <= c < COLS

class PathfinderApp:
    def __init__(self, root):
        self.root = root
        self.root.title(TITLE)
        self.root.configure(bg=COLOR_BG)

        # UI Controls
        self.controls = tk.Frame(root, bg=COLOR_BG)
        self.controls.pack(pady=10)

        self.alg_var = tk.StringVar(value="BFS")
        tk.Label(self.controls, text="SEARCH:", bg=COLOR_BG, fg="white", font=("Courier", 12, "bold")).grid(row=0, column=0, padx=5)
        
        opt = tk.OptionMenu(self.controls, self.alg_var, "BFS", "DFS", "UCS", "DLS", "IDDFS", "Bidirectional")
        opt.config(bg="#334155", fg="white", highlightthickness=0)
        opt.grid(row=0, column=1, padx=5)

        tk.Button(self.controls, text="RUN", command=self.start_search, bg=COLOR_START, fg="white", font=("Arial", 10, "bold"), width=10).grid(row=0, column=2, padx=10)
        tk.Button(self.controls, text="RESET", command=self.reset_grid, bg="#EF4444", fg="white", font=("Arial", 10, "bold")).grid(row=0, column=3, padx=5)

        # Grid Canvas
        self.canvas = tk.Canvas(root, width=COLS * CELL_SIZE, height=ROWS * CELL_SIZE, bg=COLOR_BG, highlightthickness=0)
        self.canvas.pack(padx=20, pady=20)

        self.start, self.target = None, None
        self.running = False
        self.cells = []
        for r in range(ROWS):
            row_cells = []
            for c in range(COLS):
                rect = self.canvas.create_rectangle(
                    c*CELL_SIZE+2, r*CELL_SIZE+2, (c+1)*CELL_SIZE-2, (r+1)*CELL_SIZE-2, 
                    fill=COLOR_EMPTY, outline=COLOR_BORDER
                )
                row_cells.append(rect)
            self.cells.append(row_cells)
        
        self.canvas.bind("<Button-1>", self.on_click)

    def on_click(self, event):
        if self.running: return
        c, r = event.x // CELL_SIZE, event.y // CELL_SIZE
        if not in_bounds(r, c): return
        if not self.start:
            self.start = (r, c)
            self.update_cell(r, c, COLOR_START)
        elif not self.target and (r, c) != self.start:
            self.target = (r, c)
            self.update_cell(r, c, COLOR_TARGET)

    def update_cell(self, r, c, color):
        self.canvas.itemconfig(self.cells[r][c], fill=color)

    def reset_grid(self):
        self.running = False
        self.start, self.target = None, None
        for r in range(ROWS):
            for c in range(COLS):
                self.update_cell(r, c, COLOR_EMPTY)

    def animate(self, generator):
        try:
            state = next(generator)
            for r in range(ROWS):
                for c in range(COLS):
                    pos = (r, c)
                    if pos == self.start: self.update_cell(r, c, COLOR_START)
                    elif pos == self.target: self.update_cell(r, c, COLOR_TARGET)
                    elif "path" in state and pos in state["path"]: self.update_cell(r, c, COLOR_PATH)
                    elif pos in state.get("explored", []): self.update_cell(r, c, COLOR_EXPLORED)
                    elif pos in state.get("frontier", []): self.update_cell(r, c, COLOR_FRONTIER)
            self.root.after(50, lambda: self.animate(generator)) 
        except StopIteration: self.running = False

    def start_search(self):
        if not self.start or not self.target or self.running: return
        self.running = True
        alg = self.alg_var.get()
        if alg == "BFS": gen = self.bfs()
        elif alg == "DFS": gen = self.dfs()
        elif alg == "UCS": gen = self.ucs()
        elif alg == "DLS": gen = self.dls(self.start, 15) 
        elif alg == "IDDFS": gen = self.iddfs()
        elif alg == "Bidirectional": gen = self.bidirectional()
        self.animate(gen)

    # --- Search Logic ---

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
                # Reversed to maintain clockwise priority in a stack (LIFO)
                for dr, dc in reversed(DIRS):
                    nb = (curr[0]+dr, curr[1]+dc)
                    if in_bounds(*nb) and nb not in explored:
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
                weight = 1.4 if dr!=0 and dc!=0 else 1.0 # Diagonal weight
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
                for dr, dc in reversed(DIRS):
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
            # Forward
            cf = f_q.popleft(); exp.append(cf)
            for dr, dc in DIRS:
                nb = (cf[0]+dr, cf[1]+dc)
                if in_bounds(*nb) and nb not in f_came:
                    f_came[nb] = cf; f_q.append(nb)
                    if nb in b_came:
                        yield {"path": self.merge_path(f_came, b_came, nb), "explored": exp}
                        return
            # Backward
            cb = b_q.popleft(); exp.append(cb)
            for dr, dc in DIRS:
                nb = (cb[0]+dr, cb[1]+dc)
                if in_bounds(*nb) and nb not in b_came:
                    b_came[nb] = cb; b_q.append(nb)
                    if nb in f_came:
                        yield {"path": self.merge_path(f_came, b_came, nb), "explored": exp}
                        return
            yield {"frontier": list(f_q) + list(b_q), "explored": exp}

    def get_path(self, came_from):
        path, curr = [], self.target
        while curr:
            path.append(curr)
            curr = came_from.get(curr)
        return path

    def merge_path(self, f_came, b_came, meeting):
        p1, curr = [], meeting
        while curr: p1.append(curr); curr = f_came.get(curr)
        p2, curr = [], b_came.get(meeting)
        while curr: p2.append(curr); curr = b_came.get(curr)
        return p1[::-1] + p2

if __name__ == "__main__":
    root = tk.Tk()
    app = PathfinderApp(root)
    root.mainloop()
