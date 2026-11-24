const fs = require("fs");
const path = require("path");

const root = __dirname;
const out = path.join(root, "dist");
const files = ["index.html", "light.html", "slide.html", "styles.css", "game.js", "slide.js"];

fs.rmSync(out, { recursive: true, force: true });
fs.mkdirSync(out, { recursive: true });
for (const file of files) {
  fs.copyFileSync(path.join(root, file), path.join(out, file));
}
console.log(`Static site built in ${path.relative(root, out)}/`);
