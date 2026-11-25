# Mini Puzzle Resolvers

常见小游戏解：一个包含点灯游戏、数字华容道及概率模拟的小型谜题项目。

## 项目特色

- **点灯游戏（Lights Out）**：支持随机棋盘、空洞、不可重复点击等规则，并提供可视化求解过程。
- **数字华容道（Sliding Puzzle）**：支持常见滑块拼图操作与求解逻辑。
- **Python 求解器**：使用高斯消元、BFS、A* 与优化搜索求解点灯类问题。
- **概率模拟**：包含抛硬币与轮盘游戏资金变化的 NumPy / Matplotlib 模拟。
- **纯静态构建**：无需前端框架，可直接构建为可部署的静态站点。

## 在线演示

项目已配置 GitHub Pages，可通过仓库的 Pages 地址访问静态版本。

## 项目结构

```text
.
├── index.html       # 游戏入口页面
├── light.html       # 点灯游戏页面
├── slide.html       # 数字华容道页面
├── styles.css       # 页面与主题样式
├── game.js          # 点灯游戏交互逻辑
├── slide.js         # 数字华容道交互逻辑
├── light-game.py    # 点灯游戏求解器
├── gemble.py        # 抛硬币与轮盘概率模拟
├── build.js         # 静态站点构建脚本
├── dev-server.js    # 本地开发服务器
├── test.js          # Node.js 测试脚本
├── package.json     # 项目脚本与元数据
└── dist/            # 构建后生成的静态文件（构建时生成）
```

## 本地运行

项目不需要安装第三方 Node.js 依赖。

```bash
# 启动本地开发服务器
npm run dev
```

默认访问：<http://127.0.0.1:4173>

也可以直接使用浏览器打开 `index.html`。

## 构建静态站点

```bash
npm run build
```

构建结果会生成在 `dist/`目录，其中包含可部署的 HTML、CSS 和 JavaScript 文件。

## 测试

```bash
npm test
```

## Python 求解器

`light-game.py` 提供了 `LightPuzzle` 类，可求解标准点灯游戏及带空洞、不可重复点击等限制的变种。

```python
from light_game import LightPuzzle

puzzle = LightPuzzle.simple(3)
solution = puzzle.resolve()
print(puzzle.verify_solution(solution))
```

运行内置示例：

```bash
python light-game.py
```

支持的求解算法：

- `BFS`：适合通用状态空间搜索
- `A*`：使用启发式信息加速搜索
- `Optimized`：先使用高斯消元缩小解空间，再进行合法顺序搜索

## 概率模拟

`gemble.py` 使用 Matplotlib 展示：

- 10 位玩家在公平抛硬币游戏中的资金变化
- 0 至 48 的轮盘不同投注方式的资金变化
- 庄家总净资金变化

运行方式：

```bash
pip install numpy matplotlib
python gemble.py
```

> 本脚本仅用于概率与统计演示，不构成赌博建议。

## 技术栈

- HTML5 / CSS3 / JavaScript
- Node.js（本地服务与静态构建）
- Python
- NumPy / Matplotlib

## 许可证

本项目采用 [MIT License](./LICENSE)。
