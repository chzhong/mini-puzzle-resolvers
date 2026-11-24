const $ = (selector) => document.querySelector(selector);
const board = $("#board");

let rows = 5;
let cols = 5;
let mode = "solve";
let state = Array.from({ length: rows }, () => Array(cols).fill(0));
let holes = new Set();
let tool = "toggle";
let solution = null;
let solutionStep = 0;
let playbackTimer = null;
let demoState = null;

function key(r, c) { return `${r},${c}`; }
function fromKey(value) { return value.split(",").map(Number); }
function playMode() { return document.querySelector('input[name="playmode"]:checked')?.value || "solve"; }

function resizeBoard() {
  const nextRows = Number($("#rows-input")?.value || rows);
  const nextCols = Number($("#cols-input")?.value || cols);
  rows = Math.max(2, Math.min(7, nextRows));
  cols = Math.max(2, Math.min(7, nextCols));
  if ($("#rows-input")) $("#rows-input").value = rows;
  if ($("#cols-input")) $("#cols-input").value = cols;
  state = Array.from({ length: rows }, () => Array(cols).fill(0));
  holes = new Set();
  solution = null;
  demoState = null;
  stopPlayback();
  hideSolution();
  $("#status").textContent = "棋盘尺寸已更新";
  $("#move-count").textContent = "0 步";
  renderBoard();
}

function renderBoard() {
  board.style.setProperty("--cols", cols);
  board.innerHTML = "";
  const shownState = demoState || state;
  for (let r = 0; r < rows; r++) {
    for (let c = 0; c < cols; c++) {
      const cell = document.createElement("button");
      cell.type = "button";
      cell.className = "cell";
      cell.setAttribute("aria-label", `第 ${r + 1} 行，第 ${c + 1} 列`);
      if (holes.has(key(r, c))) {
        cell.classList.add("hole");
        cell.setAttribute("aria-label", "空洞");
      } else if (shownState[r][c] === 1) {
        cell.classList.add("on");
      }
      cell.dataset.row = r;
      cell.dataset.col = c;
      cell.addEventListener("click", onCellClick);
      board.appendChild(cell);
    }
  }
  if ($("#rows-value")) $("#rows-value").textContent = rows;
  if ($("#cols-value")) $("#cols-value").textContent = cols;
}

function onCellClick(event) {
  stopPlayback();
  demoState = null;
  solution = null;
  solutionStep = 0;
  hideSolution();
  const r = Number(event.currentTarget.dataset.row);
  const c = Number(event.currentTarget.dataset.col);
  if (playMode() === "play" && tool === "toggle" && !holes.has(key(r, c))) {
    const mode = document.querySelector('input[name="mode"]:checked').value;
    if (mode === "once" && state[r][c] === 1) {
      $("#status").textContent = "该开关已开启，不能再次点击";
      $("#move-count").textContent = "0 步";
      renderBoard();
      return;
    }
  }
  if (tool === "hole") {
    const id = key(r, c);
    if (holes.has(id)) holes.delete(id);
    else holes.add(id);
  } else if (!holes.has(key(r, c))) {
    state[r][c] ^= 1;
  }
  $("#status").textContent = "棋盘已修改";
  $("#move-count").textContent = "0 步";
  renderBoard();
  if (playMode() === "play") checkPlayOutcome();
}

function resize(delta) {
  const nextRows = Math.max(2, Math.min(7, rows + delta));
  rows = nextRows;
  state = Array.from({ length: rows }, () => Array(cols).fill(0));
  holes = new Set();
  solution = null;
  demoState = null;
  stopPlayback();
  hideSolution();
  $("#status").textContent = "点击方格可编辑棋盘";
  $("#move-count").textContent = "0 步";
  renderBoard();
}

function validPositions() {
  const positions = [];
  for (let r = 0; r < rows; r++) {
    for (let c = 0; c < cols; c++) {
      if (!holes.has(key(r, c))) positions.push([r, c]);
    }
  }
  return positions;
}

function clickMask(r, c, positions, posIndex) {
  let mask = 0n;
  for (const [nr, nc] of [[r,c],[r-1,c],[r+1,c],[r,c-1],[r,c+1]]) {
    if (nr >= 0 && nr < rows && nc >= 0 && nc < cols && !holes.has(key(nr,nc))) {
      mask |= 1n << BigInt(posIndex.get(key(nr,nc)));
    }
  }
  return mask;
}

function solveGauss(initialState) {
  const positions = validPositions();
  const posIndex = new Map(positions.map((p, i) => [key(p[0], p[1]), i]));
  const n = positions.length;
  const a = Array.from({ length: n }, () => Array(n + 1).fill(0));

  positions.forEach(([r, c], i) => {
    a[i][i] = 1;
    a[i][n] = 1 - initialState[r][c];
    for (const [nr, nc] of [[r-1,c],[r+1,c],[r,c-1],[r,c+1]]) {
      const id = key(nr, nc);
      if (posIndex.has(id)) a[i][posIndex.get(id)] ^= 1;
    }
  });

  const pivotCols = [];
  let pivotRow = 0;
  for (let col = 0; col < n && pivotRow < n; col++) {
    let found = -1;
    for (let r = pivotRow; r < n; r++) {
      if (a[r][col]) { found = r; break; }
    }
    if (found === -1) continue;
    [a[pivotRow], a[found]] = [a[found], a[pivotRow]];
    for (let r = 0; r < n; r++) {
      if (r !== pivotRow && a[r][col]) {
        for (let c = 0; c <= n; c++) a[r][c] ^= a[pivotRow][c];
      }
    }
    pivotCols.push(col);
    pivotRow++;
  }
  for (let r = pivotRow; r < n; r++) {
    if (a[r][n]) return null;
  }

  const x = Array(n).fill(0);
  pivotCols.forEach((col, i) => { x[col] = a[i][n]; });
  const result = positions.map((position, i) => x[i] ? position : null).filter(Boolean);
  return result;
}

function solveOnce(initialState) {
  const positions = validPositions();
  if (positions.length === 0) return null;
  const posIndex = new Map(positions.map((p, i) => [key(p[0], p[1]), i]));
  const goal = (1n << BigInt(positions.length)) - 1n;
  let start = 0n;
  positions.forEach(([r,c], i) => {
    if (initialState[r][c]) start |= 1n << BigInt(i);
  });
  if (start === goal) return [];

  const stateSpaceLimit = 1 << Math.min(20, positions.length);
  const masks = new Map();
  const posBits = new Map();
  positions.forEach(([r,c]) => {
    masks.set(key(r,c), clickMask(r,c,positions,posIndex));
  });
  positions.forEach(([r,c], i) => posBits.set(key(r,c), 1n << BigInt(i)));

  const queue = [start];
  let head = 0;
  const parent = new Map([[start, null]]);
  while (head < queue.length) {
    const current = queue[head++];
    if (queue.length > stateSpaceLimit * 50) return null;
    if (current === goal) {
      const path = [];
      let s = current;
      while (parent.get(s) !== null) {
        const [previous, position] = parent.get(s);
        path.push(position);
        s = previous;
      }
      return path.reverse();
    }
    for (const [r,c] of positions) {
      const id = key(r,c);
      if ((current & posBits.get(id)) === 0n) {
        const next = current ^ masks.get(id);
        if (!parent.has(next)) {
          parent.set(next, [current, [r,c]]);
          queue.push(next);
        }
      }
    }
  }
  return null;
}

function applyClick(grid, r, c) {
  const next = grid.map(row => row.slice());
  for (const [nr,nc] of [[r,c],[r-1,c],[r+1,c],[r,c-1],[r,c+1]]) {
    if (nr >= 0 && nr < rows && nc >= 0 && nc < cols && !holes.has(key(nr,nc))) {
      next[nr][nc] ^= 1;
    }
  }
  return next;
}

function verify(path) {
  let grid = state.map(row => row.slice());
  for (const [r,c] of path) {
    if (holes.has(key(r,c))) return false;
    if ($('input[name="mode"]:checked').value === "once" && grid[r][c] === 1) return false;
    grid = applyClick(grid,r,c);
  }

  function checkPlayOutcome() {
    const allOn = state.every((row, r) => row.every((value, c) =>
      holes.has(key(r, c)) || value === 1));
    hideSolution();
    if (allOn) {
      $("#status").textContent = "恭喜，所有灯已开启";
      $("#solve").hidden = true;
      return;
    }
    $("#solve").hidden = false;
    const mode = document.querySelector('input[name="mode"]:checked').value;
    const possible = mode === "repeat" ? solveGauss(state) : solveOnce(state);
    $("#status").textContent = possible ? "当前状态仍可解" : "当前状态已无解";
    if (!possible) $("#solve").disabled = true;
    else $("#solve").disabled = false;
  }
  return grid.every((row,r) => row.every((value,c) => holes.has(key(r,c)) || value === 1));
}

function solve() {
  stopPlayback();
  demoState = null;
  solutionStep = 0;
  if (playMode() === "play") return;
  const mode = $('input[name="mode"]:checked').value;
  $("#solve").disabled = true;
  $("#status").textContent = "正在搜索解...";

  setTimeout(() => {
    const found = mode === "repeat" ? solveGauss(state) : solveOnce(state);
    $("#solve").disabled = false;
    if (!found) {
      solution = null;
      $("#status").textContent = "此棋盘无解";
      hideSolution();
      return;
    }
    solution = found;
    $("#status").textContent = verify(solution) ? "找到合法解" : "未找到合法解";
    $("#move-count").textContent = `${solution.length} 步`;
    showSolution();
  }, 30);
}

function showSolution() {
  $("#solution-empty").hidden = true;
  $("#solution-list").hidden = false;
  $("#playback").hidden = false;
  $("#solution-list").innerHTML = solution.map(([r,c]) =>
    `<li>点击第 ${r + 1} 行，第 ${c + 1} 列</li>`
  ).join("");
  updateCurrentStep();
}

function hideSolution() {
  $("#solution-empty").hidden = false;
  $("#solution-list").hidden = true;
  $("#playback").hidden = true;
  $("#solution-list").innerHTML = "";
}

function updateCurrentStep() {
  const items = [...$("#solution-list").children];
  items.forEach((item, i) => item.classList.toggle("current", i === solutionStep - 1));
  if (items[solutionStep - 1]) items[solutionStep - 1].scrollIntoView({ block: "nearest" });
}

function setDemoStep(step) {
  if (!solution) return;
  stopTimerOnly();
  solutionStep = Math.max(0, Math.min(solution.length, step));
  demoState = state.map(row => row.slice());
  for (let i = 0; i < solutionStep; i++) {
    const [r,c] = solution[i];
    demoState = applyClick(demoState,r,c);
  }
  $("#move-count").textContent = `${solutionStep} / ${solution.length} 步`;
  renderBoard();
  updateCurrentStep();
}

function stopTimerOnly() {
  if (playbackTimer) clearInterval(playbackTimer);
  playbackTimer = null;
  $("#step-play").textContent = "演示";
}

function stopPlayback() {
  stopTimerOnly();
  if (solution) setDemoStep(0);
}

function startPlayback() {
  if (!solution || solution.length === 0) return;
  if (solutionStep >= solution.length) setDemoStep(0);
  $("#step-play").textContent = "暂停";
  playbackTimer = setInterval(() => {
    if (solutionStep >= solution.length) {
      stopPlayback();
      return;
    }
    setDemoStep(solutionStep + 1);
  }, 700);
}

if ($("#rows-down")) $("#rows-down").addEventListener("click", () => resize(-1));
if ($("#rows-up")) $("#rows-up").addEventListener("click", () => resize(1));
$("#reset").addEventListener("click", () => {
  state = Array.from({ length: rows }, () => Array(cols).fill(0));
  holes = new Set();
  demoState = null;
  solution = null;
  stopPlayback();
  hideSolution();
  $("#status").textContent = "棋盘已清空";
  $("#move-count").textContent = "0 步";
  renderBoard();
});
$("#solve").addEventListener("click", solve);
if ($("#rows-input")) $("#rows-input").addEventListener("change", resizeBoard);
if ($("#cols-input")) $("#cols-input").addEventListener("change", resizeBoard);
document.querySelectorAll('input[name="playmode"]').forEach(input => input.addEventListener("change", () => {
  solution = null;
  hideSolution();
  $("#solve").hidden = input.value === "play";
  $("#status").textContent = input.value === "play" ? "自己玩：每步会检测是否仍有解" : "求解模式";
  if (input.value === "play") checkPlayOutcome();
}));

document.querySelectorAll(".tool").forEach(button => {
  button.addEventListener("click", () => {
    tool = button.dataset.tool;
    document.querySelectorAll(".tool").forEach(item => item.classList.remove("active"));
    button.classList.add("active");
  });
});
$("#step-back").addEventListener("click", () => setDemoStep(solutionStep - 1));
$("#step-next").addEventListener("click", () => setDemoStep(solutionStep + 1));
$("#step-play").addEventListener("click", () => {
  if (playbackTimer) stopPlayback();
  else startPlayback();
});
$("#theme-toggle").addEventListener("click", () => document.body.classList.toggle("dark"));

renderBoard();
