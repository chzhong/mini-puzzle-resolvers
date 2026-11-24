import heapq
from collections import deque
from typing import Literal

type Row = list[int]
type Matrix = list[Row]
type Point = tuple[int, int]
type Algorithms = Literal["BFS", "A*", "Optimized"]


class LightPuzzle:
    m: int
    n: int
    initial_state: Matrix
    holes: set[Point]
    on_unclickable: bool

    @staticmethod
    def simple(n: int) -> "LightPuzzle":
        return LightPuzzle(n, n)

    def __init__(
        self,
        m: int,
        n: int,
        *,
        initial_state: Matrix | None = None,
        holes: list[Point] | set[Point] | None = None,
        on_unclickable: bool = False,
    ):
        self.m = m
        self.n = n
        if initial_state is None:
            initial_state = [[0] * n for _ in range(m)]
        self.initial_state = initial_state
        
        if holes is None:
            holes = set()
        self.holes = set(holes)
        self.on_unclickable = on_unclickable

    @property
    def _is_simple(self) -> bool:
        """判断是否为最标准的 n×n 全关无空洞无限制状况"""
        return (
            self.m == self.n
            and all(not any(row) for row in self.initial_state)
            and not self.holes
            and not self.on_unclickable
        )

    def resolve(self, *, algorithm: Algorithms = "BFS") -> Matrix | list[Point]:
        """
        核心求解入口
        - 标准状况：返回 Matrix (0/1 矩阵，表示点击集合)
        - 变种2状况：返回 list[Point] (点击顺序)
        """
        if self._is_simple:
            return self._solve_simple()
        
        if not self.on_unclickable:
            # 标准规则（可重复点击），顺序无关，返回 Matrix
            return self._solve_gaussian()
        else:
            # 变种2（开启后不可点），必须搜索合法顺序，返回 list[Point]
            if algorithm == "BFS":
                return self._solve_general_bfs(use_astar=False)
            elif algorithm == "A*":
                return self._solve_general_bfs(use_astar=True)
            elif algorithm == "Optimized":
                return self._solve_general_optimized()
            else:
                raise ValueError(f"Unknown algorithm: {algorithm}")

    def verify_solution(self, solution: Matrix | list[Point]) -> tuple[bool, str]:
        """验证一个解是否正确，自动识别 Matrix 或 顺序列表"""
        path = self._parse_solution(solution)
        state = [row[:] for row in self.initial_state]
        
        for step, (r, c) in enumerate(path):
            if (r, c) in self.holes:
                return False, f"步骤 {step + 1}: 点击了空洞位置 {r},{c}"
            if self.on_unclickable and state[r][c] == 1:
                return False, f"步骤 {step + 1}: 尝试点击已开启的开关 {r},{c}"
                
            state[r][c] ^= 1
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < self.m and 0 <= nc < self.n and (nr, nc) not in self.holes:
                    state[nr][nc] ^= 1
                    
        for r in range(self.m):
            for c in range(self.n):
                if (r, c) not in self.holes and state[r][c] != 1:
                    return False, f"位置 {r},{c} 未开启"
        return True, "验证通过"

    def demo_solution(
        self,
        solution: Matrix | list[Point],
        *,
        ligth_on="🟢",
        light_off="🔴",
        hole="〇",
    ):
        """核心演示函数：根据给定的点击路径，逐步打印盘面状态"""
        path = self._parse_solution(solution)
        state = [row[:] for row in self.initial_state]
        
        def print_grid(step_desc):
            print(f"\n--- {step_desc} ---")
            for r in range(self.m):
                row_str = ""
                for c in range(self.n):
                    if (r, c) in self.holes:
                        row_str += f"{hole} "
                    elif state[r][c] == 1:
                        row_str += f"{ligth_on} "
                    else:
                        row_str += f"{light_off} "
                print(row_str)
            print("-" * (self.n * 2 + 2))

        print_grid("初始状态")
        for i, (r, c) in enumerate(path):
            if (r, c) in self.holes:
                print(f"❌ 步骤 {i + 1}: 尝试点击空洞 ({r}, {c})，非法！")
                return
            if self.on_unclickable and state[r][c] == 1:
                print(f"❌ 步骤 {i + 1}: 尝试点击已开启的开关 ({r}, {c})，非法！")
                return
                
            state[r][c] ^= 1
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < self.m and 0 <= nc < self.n and (nr, nc) not in self.holes:
                    state[nr][nc] ^= 1
            print_grid(f"步骤 {i + 1}: 点击 ({r}, {c})")
            
        all_on = all(
            state[r][c] == 1
            for r in range(self.m)
            for c in range(self.n)
            if (r, c) not in self.holes
        )
        if all_on:
            print("\n🎉 恭喜，所有开关已成功开启！")
        else:
            print("\n⚠️ 步骤执行完毕，但未达到全开目标。")

    # ================= 内部辅助与求解方法 =================

    def _parse_solution(self, solution: Matrix | list[Point]) -> list[Point]:
        """将 Matrix 或 list[Point] 统一解析为 list[Point]"""
        if isinstance(solution, list) and len(solution) > 0 and isinstance(solution[0], tuple):
            return solution
        elif isinstance(solution, list) and len(solution) > 0 and isinstance(solution[0], list):
            path = []
            for r in range(self.m):
                for c in range(self.n):
                    if solution[r][c] == 1:
                        path.append((r, c))
            return path
        return []

    def _solve_simple(self) -> Matrix:
        """简易版：n×n 标准点灯游戏（全关 → 全开，无限制）"""
        N = self.n * self.n
        A = [[0] * N for _ in range(N)]
        b = [1] * N
        
        def idx(r, c): return r * self.n + c
            
        for r in range(self.n):
            for c in range(self.n):
                i = idx(r, c)
                A[i][i] = 1
                for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < self.n and 0 <= nc < self.n:
                        A[i][idx(nr, nc)] = 1
                        
        M = [row[:] + [b[i]] for i, row in enumerate(A)]
        pivot_cols, row = [], 0
        for col in range(N):
            pivot_row = next((r for r in range(row, N) if M[r][col] == 1), -1)
            if pivot_row == -1: continue
            M[row], M[pivot_row] = M[pivot_row], M[row]
            for r in range(N):
                if r != row and M[r][col] == 1:
                    M[r] = [(M[r][c] ^ M[row][c]) for c in range(N + 1)]
            pivot_cols.append(col)
            row += 1
            
        if any(M[r][N] == 1 for r in range(row, N)): return None
            
        x = [0] * N
        for k, col in enumerate(pivot_cols): x[col] = M[k][N]
            
        return [[x[idx(r, c)] for c in range(self.n)] for r in range(self.n)]

    def _solve_gaussian(self) -> Matrix:
        """通用高斯消元：支持 m×n、空洞、任意初始状态（标准规则）"""
        valid_positions = [(r, c) for r in range(self.m) for c in range(self.n) if (r, c) not in self.holes]
        num_valid = len(valid_positions)
        pos_to_idx = {pos: i for i, pos in enumerate(valid_positions)}
        
        A = [[0] * num_valid for _ in range(num_valid)]
        b = [0] * num_valid
        
        for r, c in valid_positions:
            i = pos_to_idx[(r, c)]
            b[i] = 1 - self.initial_state[r][c]
            A[i][i] = 1
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = r + dr, c + dc
                if (nr, nc) in pos_to_idx:
                    A[i][pos_to_idx[(nr, nc)]] = 1
                    
        M = [row[:] + [b[i]] for i, row in enumerate(A)]
        pivot_cols, row = [], 0
        for col in range(num_valid):
            pivot_row = next((r for r in range(row, num_valid) if M[r][col] == 1), -1)
            if pivot_row == -1: continue
            M[row], M[pivot_row] = M[pivot_row], M[row]
            for r in range(num_valid):
                if r != row and M[r][col] == 1:
                    M[r] = [(M[r][c] ^ M[row][c]) for c in range(num_valid + 1)]
            pivot_cols.append(col)
            row += 1
            
        if any(M[r][num_valid] == 1 for r in range(row, num_valid)): return None
            
        x = [0] * num_valid
        for k, col in enumerate(pivot_cols): x[col] = M[k][num_valid]
            
        result = [[0] * self.n for _ in range(self.m)]
        for i, (r, c) in enumerate(valid_positions):
            result[r][c] = x[i]
        return result

    def _solve_general_bfs(self, use_astar: bool = False) -> list[Point]:
        """全状态空间搜索（支持变种2约束）"""
        valid_positions = [(r, c) for r in range(self.m) for c in range(self.n) if (r, c) not in self.holes]
        num_valid = len(valid_positions)
        pos_to_idx = {pos: i for i, pos in enumerate(valid_positions)}
        
        goal_mask = (1 << num_valid) - 1
        start_mask = sum(1 << pos_to_idx[(r, c)] for r, c in valid_positions if self.initial_state[r][c] == 1)
        if start_mask == goal_mask: return []
            
        click_masks, pos_bits = {}, {}
        for r, c in valid_positions:
            mask = 1 << pos_to_idx[(r, c)]
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = r + dr, c + dc
                if (nr, nc) in pos_to_idx: mask |= 1 << pos_to_idx[(nr, nc)]
            click_masks[(r, c)], pos_bits[(r, c)] = mask, 1 << pos_to_idx[(r, c)]
            
        if not use_astar:
            parent = {start_mask: None}
            queue = deque([start_mask])
            while queue:
                state = queue.popleft()
                if state == goal_mask:
                    path, s = [], state
                    while parent[s] is not None:
                        prev_state, click = parent[s]
                        path.append(click)
                        s = prev_state
                    return path[::-1]
                for pos in valid_positions:
                    if not (state & pos_bits[pos]):  # 变种2核心：只能点 OFF
                        new_state = state ^ click_masks[pos]
                        if new_state not in parent:
                            parent[new_state] = (state, pos)
                            queue.append(new_state)
            return None
        else:
            def heuristic(state): return (num_valid - bin(state).count("1") + 4) // 5
            parent, g_score, counter = {start_mask: None}, {start_mask: 0}, 0
            pq = [(heuristic(start_mask), counter, start_mask)]
            while pq:
                _, _, state = heapq.heappop(pq)
                if state == goal_mask:
                    path, s = [], state
                    while parent[s] is not None:
                        prev_state, click = parent[s]
                        path.append(click)
                        s = prev_state
                    return path[::-1]
                g = g_score[state]
                for pos in valid_positions:
                    if not (state & pos_bits[pos]):
                        new_state = state ^ click_masks[pos]
                        new_g = g + 1
                        if new_state not in g_score or new_g < g_score[new_state]:
                            g_score[new_state] = new_g
                            parent[new_state] = (state, pos)
                            counter += 1
                            heapq.heappush(pq, (new_g + heuristic(new_state), counter, new_state))
            return None

    def _solve_general_optimized(self) -> list[Point]:
        """优化版：先高斯消元求集合，再 BFS 搜索合法顺序（支持变种2约束）"""
        valid_positions = [(r, c) for r in range(self.m) for c in range(self.n) if (r, c) not in self.holes]
        num_valid = len(valid_positions)
        pos_to_idx = {pos: i for i, pos in enumerate(valid_positions)}
        
        A = [[0] * num_valid for _ in range(num_valid)]
        b = [1 - self.initial_state[r][c] for r, c in valid_positions]
        for r, c in valid_positions:
            i = pos_to_idx[(r, c)]
            A[i][i] = 1
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = r + dr, c + dc
                if (nr, nc) in pos_to_idx: A[i][pos_to_idx[(nr, nc)]] = 1
                    
        M = [row[:] + [b[i]] for i, row in enumerate(A)]
        pivot_cols, pivot_rows, row = [], {}, 0
        for col in range(num_valid):
            pivot_row = next((r for r in range(row, num_valid) if M[r][col] == 1), -1)
            if pivot_row == -1: continue
            M[row], M[pivot_row] = M[pivot_row], M[row]
            for r in range(num_valid):
                if r != row and M[r][col] == 1:
                    M[r] = [(M[r][c] ^ M[row][c]) for c in range(num_valid + 1)]
            pivot_cols.append(col)
            pivot_rows[col] = row
            row += 1
            
        if any(M[r][num_valid] == 1 for r in range(row, num_valid)): return None
            
        free_vars = [c for c in range(num_valid) if c not in pivot_cols]
        click_grid_masks = {}
        for r, c in valid_positions:
            mask = 1 << pos_to_idx[(r, c)]
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = r + dr, c + dc
                if (nr, nc) in pos_to_idx: mask |= 1 << pos_to_idx[(nr, nc)]
            click_grid_masks[(r, c)] = mask
            
        initial_grid = sum(1 << pos_to_idx[(r, c)] for r, c in valid_positions if self.initial_state[r][c] == 1)
        goal_grid = (1 << num_valid) - 1
        
        for mask in range(1 << len(free_vars)):
            x = [0] * num_valid
            for i, fv in enumerate(free_vars): x[fv] = (mask >> i) & 1
            for col in reversed(pivot_cols):
                r = pivot_rows[col]
                val = M[r][num_valid]
                for c in range(num_valid):
                    if c != col and M[r][c] == 1: val ^= x[c]
                x[col] = val
                
            click_set = [valid_positions[i] for i in range(num_valid) if x[i] == 1]
            if not click_set:
                if initial_grid == goal_grid: return []
                continue
                
            k = len(click_set)
            start_subset, goal_subset = 0, (1 << k) - 1
            parent, grid_cache = {start_subset: None}, {start_subset: initial_grid}
            queue = deque([start_subset])
            found = False
            while queue:
                subset = queue.popleft()
                if subset == goal_subset:
                    found = True
                    break
                current_grid = grid_cache[subset]
                for i, pos in enumerate(click_set):
                    if not (subset & (1 << i)):
                        pos_bit = 1 << pos_to_idx[pos]
                        if not (current_grid & pos_bit):  # 变种2核心：只能点 OFF
                            new_subset = subset | (1 << i)
                            if new_subset not in parent:
                                grid_cache[new_subset] = current_grid ^ click_grid_masks[pos]
                                parent[new_subset] = (subset, pos)
                                queue.append(new_subset)
            if found:
                path, s = [], goal_subset
                while parent[s] is not None:
                    prev_subset, click = parent[s]
                    path.append(click)
                    s = prev_subset
                return path[::-1]
        return None


if __name__ == "__main__":
    print("=== 简易版测试 ===")
    for n in [2, 3, 4, 5]:
        puzzle = LightPuzzle.simple(n)
        sol = puzzle.resolve()
        if sol:
            clicks = sum(sum(row) for row in sol)
            print(f"{n}×{n}: 需要点击 {clicks} 个开关")
            valid, msg = puzzle.verify_solution(sol)
            print(f"  验证: {msg}")
        else:
            print(f"{n}×{n}: 无解")

    print("\n=== 通用版测试 ===")
    
    # 2×2 全关 (标准规则)
    print("2×2 全关 → 全开 (标准规则):")
    puzzle = LightPuzzle(2, 2)
    path = puzzle.resolve()
    if path:
        valid, msg = puzzle.verify_solution(path)
        print(f"  验证: {msg}")
        puzzle.demo_solution(path)

    # 3×3 全关（变种2，BFS）
    print("\n3×3 全关 → 全开 (变种2, BFS):")
    puzzle = LightPuzzle(3, 3, on_unclickable=True)
    path = puzzle.resolve(algorithm="BFS")
    if path:
        print(f"  步数: {len(path)}")
        valid, msg = puzzle.verify_solution(path)
        print(f"  验证: {msg}")

    # 3×3 带空洞 (变种2，Optimized)
    print("\n3×3 带空洞 (中心为空) → 全开 (变种2, Optimized):")
    puzzle = LightPuzzle(3, 3, holes={(1, 1)}, on_unclickable=True)
    path = puzzle.resolve(algorithm="Optimized")
    if path:
        print(f"  步数: {len(path)}")
        valid, msg = puzzle.verify_solution(path)
        print(f"  验证: {msg}")
        puzzle.demo_solution(path)
    else:
        print("  无解")

    # 4×4 全关（变种2，A*）
    print("\n4×4 全关 → 全开 (变种2, A*):")
    puzzle = LightPuzzle(4, 4, on_unclickable=True)
    path = puzzle.resolve(algorithm="A*")
    if path:
        print(f"  步数: {len(path)}")
        valid, msg = puzzle.verify_solution(path)
        print(f"  验证: {msg}")

    # 3×5 带空洞（变种2，A*）
    print("\n3×5 带空洞 → 全开 (变种2, A*):")
    puzzle = LightPuzzle(3, 5, holes=[(0, 2), (2, 2)], on_unclickable=True)
    path = puzzle.resolve(algorithm="A*")
    if path:
        print(f"  步数: {len(path)}")
        valid, msg = puzzle.verify_solution(path)
        print(f"  验证: {msg}")
        puzzle.demo_solution(path)