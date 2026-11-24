const $ = (s) => document.querySelector(s);
const board = $("#slide-board");
let size = 4;
let extra = false;
let tiles = [];
let goal = [];
let imageUrl = null;
let targetImageUrl = null;
let solution = null;
let timer = null;
let targetCanvas = null;
let stateCanvas = null;

function initTiles() {
  extra = document.querySelector('input[name="extra"]:checked').value === "edge";
  const count = extra ? size * size + 1 : size * size;
  tiles = Array.from({ length: count }, (_, i) => i === count - 1 ? 0 : i + 1);
  goal = tiles.slice();
  render();
}

function render() {
  board.innerHTML = "";
  board.style.setProperty("--slide-cols", extra ? size + 1 : size);
  const mode = document.querySelector('input[name="slide-mode"]:checked').value;
  const cols = extra ? size + 1 : size;
  tiles.forEach((tile, index) => {
    const cell = document.createElement("button");
    cell.type = "button";
    cell.className = "slide-cell";
    cell.dataset.index = index;
    cell.draggable = tile !== 0;
    if (tile === 0) {
      cell.classList.add("empty");
      cell.setAttribute("aria-label", "空格");
    } else {
      if (mode === "image" && (imageUrl || targetImageUrl)) {
        cell.style.backgroundImage = `url("${(imageUrl || targetImageUrl)}")`;
        const tileId = tile;
        const pos = tileId - 1;
        const r = Math.floor(pos / size);
        const c = pos % size;
        cell.style.backgroundSize = `${size * 100}% ${size * 100}%`;
        cell.style.backgroundPosition = `${c * 100 / (size - 1)}% ${r * 100 / (size - 1)}%`;
      } else {
        cell.textContent = tile;
      }
    }
    cell.addEventListener("click", () => moveByIndex(index));
    cell.addEventListener("dragstart", (event) => {
      event.dataTransfer.setData("text/plain", String(index));
    });
    cell.addEventListener("dragover", (event) => event.preventDefault());
    cell.addEventListener("drop", (event) => {
      event.preventDefault();
      const from = Number(event.dataTransfer.getData("text/plain"));
      if (Number.isInteger(from) && from !== index) swapTiles(from, index);
    });
    board.appendChild(cell);
  });
  if (!extra && tiles.length !== size * size) initTiles();
  if (board.children.length === 0) return;
}

function swapTiles(from, to) {
  [tiles[from], tiles[to]] = [tiles[to], tiles[from]];
  solution = null;
  $("#slide-empty").hidden = false;
  $("#slide-list").hidden = true;
  $("#slide-play").hidden = true;
  $("#slide-count").textContent = "0 步";
  $("#slide-status").textContent = "状态已编辑";
  render();
  checkSolvable();
}

function neighbors(index) {
  const cols = extra ? size + 1 : size;
  const r = Math.floor(index / cols);
  const c = index % cols;
  const result = [];
  for (const [dr, dc] of [[-1,0],[1,0],[0,-1],[0,1]]) {
    const nr = r + dr, nc = c + dc;
    if (nr >= 0 && nr < (extra ? size : size) && nc >= 0 && nc < cols) result.push(nr * cols + nc);
  }
  if (extra) {
    const edgeIndex = size * size;
    if (index === edgeIndex) result.push(size * size - 1);
    if (index === size * size - 1) result.push(edgeIndex);
  }
  return result;
}

function moveByIndex(index) {
  if (timer) return;
  let empty = tiles.indexOf(0);
  if (neighbors(empty).includes(index)) {
    [tiles[empty], tiles[index]] = [tiles[index], tiles[empty]];
    solution = null;
    $("#slide-count").textContent = "0 步";
    $("#slide-status").textContent = "棋盘已移动";
    render();
    checkSolvable();
  }
}

function inversionCount(arr) {
  const values = arr.filter(Boolean);
  let count = 0;
  for (let i = 0; i < values.length; i++) {
    for (let j = i + 1; j < values.length; j++) if (values[i] > values[j]) count++;
  }
  return count;
}

function isSolvable(arr) {
  if (extra) return true;
  const inv = inversionCount(arr);
  if (size % 2 === 1) return inv % 2 === 0;
  const blankFromBottom = size - Math.floor(arr.indexOf(0) / size);
  return size % 2 === 0 ? ((inv + blankFromBottom) % 2 === 1) : false;
}

function checkSolvable() {
  if (inversionCount(tiles) !== 0 && !isSolvable(tiles)) {
    $("#slide-status").textContent = "当前状态无解";
    $("#slide-solve").disabled = true;
  } else {
    $("#slide-status").textContent = "当前状态可解";
    $("#slide-solve").disabled = false;
  }
}

function heuristic(arr) {
  const cols = extra ? size + 1 : size;
  let h = 0;
  arr.forEach((tile, index) => {
    if (!tile) return;
    const target = tile - 1;
    h += Math.abs(Math.floor(index / cols) - Math.floor(target / cols)) +
      Math.abs(index % cols - target % cols);
  });
  return h;
}

function astar() {
  const start = tiles.slice();
  const startKey = start.join(",");
  const goalKey = goal.join(",");
  if (startKey === goalKey) return [];
  if (!isSolvable(start)) return null;
  if (size >= 5) return null;

  let counter = 0;
  const open = [{ arr: start, g: 0, f: heuristic(start), id: counter++ }];
  const gScore = new Map([[startKey, 0]]);
  const parent = new Map([[startKey, null]]);
  let processed = 0;

  while (open.length && processed < 100000) {
    open.sort((a,b) => a.f - b.f || a.id - b.id);
    const current = open.shift();
    const key = current.arr.join(",");
    processed++;
    if (key === goalKey) {
      const path = [];
      let node = key;
      while (parent.get(node)) {
        const item = parent.get(node);
        path.push(item.move);
        node = item.parent;
      }
      return path.reverse();
    }
    const empty = current.arr.indexOf(0);
    for (const index of neighbors(empty)) {
      const next = current.arr.slice();
      [next[empty], next[index]] = [next[index], next[empty]];
      const nextKey = next.join(",");
      const ng = current.g + 1;
      if (!gScore.has(nextKey) || ng < gScore.get(nextKey)) {
        gScore.set(nextKey, ng);
        parent.set(nextKey, { parent: key, move: index });
        open.push({ arr: next, g: ng, f: ng + heuristic(next), id: counter++ });
      }
    }
  }
  return null;
}

async function solve() {
  $("#slide-status").textContent = "正在求解...";
  $("#slide-solve").disabled = true;
  await new Promise(resolve => setTimeout(resolve, 30));
  solution = astar();
  $("#slide-solve").disabled = false;
  if (!solution) {
    $("#slide-status").textContent = size >= 5 ? "此尺寸需要更大的求解引擎（暂不支持实时求解）" : "当前状态无解";
    return;
  }
  $("#slide-status").textContent = `找到解：${solution.length} 步`;
  $("#slide-count").textContent = `${solution.length} 步`;
  $("#slide-empty").hidden = true;
  $("#slide-list").hidden = false;
  $("#slide-play").hidden = false;
  $("#slide-list").innerHTML = solution.map((index, i) =>
    `<li>移动格子到位置 ${index + 1}</li>`).join("");
}

function playSolution() {
  if (!solution) return;
  let i = 0;
  timer = setInterval(() => {
    if (i >= solution.length) {
      clearInterval(timer);
      timer = null;
      $("#slide-status").textContent = "已还原";
      return;
    }
    moveByIndex(solution[i++]);
  }, 180);
}

document.querySelectorAll("#size-options button").forEach(button => {
  button.addEventListener("click", () => {
    size = Number(button.dataset.size);
    document.querySelectorAll("#size-options button").forEach(b => b.classList.remove("active"));
    button.classList.add("active");
    solution = null;
    initTiles();
  });
});
document.querySelectorAll('input[name="extra"]').forEach(input => input.addEventListener("change", initTiles));
document.querySelectorAll('input[name="slide-mode"]').forEach(input => input.addEventListener("change", render));

$("#shuffle").addEventListener("click", () => {
  for (let i = 0; i < size * size * 20; i++) {
    const empty = tiles.indexOf(0);
    const options = neighbors(empty).filter(index => index < tiles.length);
    if (options.length) {
      const index = options[Math.floor(Math.random() * options.length)];
      [tiles[empty], tiles[index]] = [tiles[index], tiles[empty]];
    }
  }
  solution = null;
  $("#slide-count").textContent = "0 步";
  $("#slide-status").textContent = "棋盘已打乱";
  render();
  checkSolvable();
});

$("#slide-solve").addEventListener("click", solve);
$("#slide-play").addEventListener("click", playSolution);
$("#theme-toggle").addEventListener("click", () => document.body.classList.toggle("dark"));

function loadImage(file, target) {
  if (!file) return;
  const reader = new FileReader();
  reader.onload = () => {
    const url = reader.result;
    const img = new Image();
    img.onload = () => {
      const cropped = cropWithEdgeDetection(img);
      const cropUrl = cropped.toDataURL("image/jpeg", 0.92);
      if (target) {
        targetImageUrl = cropUrl;
        const count = extra ? size * (size + 1) : size * size;
        goal = Array.from({ length: count }, (_, i) => i === count - 1 ? 0 : i + 1);
        $("#slide-status").textContent = "目标图已裁切并按棋盘分割";
      } else {
        imageUrl = cropUrl;
        stateCanvas = cropped;
        $("#slide-status").textContent = "当前图已裁切；可拖拽格子调整识别状态";
      }
      document.querySelector('input[name="slide-mode"][value="image"]').checked = true;
      render();
    };
    img.src = url;
  };
  reader.readAsDataURL(file);
}

function cropWithEdgeDetection(img) {
  const canvas = document.createElement("canvas");
  const maxSide = 1200;
  const scale = Math.min(1, maxSide / Math.max(img.naturalWidth, img.naturalHeight));
  canvas.width = Math.max(1, Math.round(img.naturalWidth * scale));
  canvas.height = Math.max(1, Math.round(img.naturalHeight * scale));
  const ctx = canvas.getContext("2d", { willReadFrequently: true });
  ctx.drawImage(img, 0, 0, canvas.width, canvas.height);

  const pixels = ctx.getImageData(0, 0, canvas.width, canvas.height).data;
  let top = canvas.height, left = canvas.width, right = 0, bottom = 0;
  const threshold = 12;
  for (let y = 0; y < canvas.height; y++) {
    for (let x = 0; x < canvas.width; x++) {
      const i = (y * canvas.width + x) * 4;
      const alpha = pixels[i + 3];
      if (alpha < 240) continue;
      if (y > 0 && y < canvas.height - 1 && x > 0 && x < canvas.width - 1) {
        const prev = (y * canvas.width + (x - 1)) * 4;
        const next = ((y + 1) * canvas.width + x) * 4;
        const edge = Math.abs(pixels[i] - pixels[prev]) + Math.abs(pixels[i + 1] - pixels[prev + 1]) +
          Math.abs(pixels[i] - pixels[next]) + Math.abs(pixels[i + 1] - pixels[next + 1]);
        if (edge > threshold) {
          left = Math.min(left, x); right = Math.max(right, x);
          top = Math.min(top, y); bottom = Math.max(bottom, y);
        }
      }
    }
  }

  if (right <= left || bottom <= top) {
    left = 0; top = 0; right = canvas.width; bottom = canvas.height;
  }
  const cols = extra ? size + 1 : size;
  const cropWidth = right - left;
  const cropHeight = bottom - top;
  const cellWidth = cropWidth / cols;
  const cellHeight = cropHeight / size;
  const outSize = 900;
  const result = document.createElement("canvas");
  result.width = outSize;
  result.height = outSize * (size / cols);
  const out = result.getContext("2d");
  out.drawImage(canvas, left, top, cropWidth, cropHeight, 0, 0, result.width, result.height);
  return result;
}

$("#target-upload").addEventListener("click", () => {
  $("#image-upload").dataset.kind = "target";
  $("#image-upload").click();
});
$("#state-upload").addEventListener("click", () => {
  $("#image-upload").dataset.kind = "state";
  $("#image-upload").click();
});
$("#image-upload").addEventListener("change", event => loadImage(event.target.files[0], event.target.dataset.kind === "target"));
window.addEventListener("paste", event => {
  const item = [...event.clipboardData.items].find(item => item.type.startsWith("image/"));
  if (item) loadImage(item.getAsFile(), false);
});

initTiles();
