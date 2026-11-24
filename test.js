const fs = require("fs");
const vm = require("vm");

// Basic static build and source sanity checks.
const required = ["index.html", "light.html", "slide.html", "styles.css", "game.js", "slide.js"];
for (const file of required) {
  if (!fs.existsSync(file) || fs.statSync(file).size === 0) {
    throw new Error(`Missing static asset: ${file}`);
  }
}
const htmlAssets = {
  "index.html": ["./styles.css"],
  "light.html": ["./styles.css", "./game.js"],
  "slide.html": ["./styles.css", "./slide.js"]
};
for (const [file, assets] of Object.entries(htmlAssets)) {
  const html = fs.readFileSync(file, "utf8");
  for (const asset of assets) {
    if (!html.includes(asset)) throw new Error(`${file} does not include ${asset}`);
  }
}
console.log("Static asset checks passed.");
