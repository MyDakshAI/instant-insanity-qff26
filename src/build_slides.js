// Build slides.pptx from results/bonus.json. Run: node src/build_slides.js
const fs = require("fs");
const pptxgen = require("pptxgenjs");
const { applyTheme } = require("/root/.claude/skills/synced/6ab231db-ae75-468a-8a74-267ba486edad_c94e437e-6402-4416-8bea-bbd62b7570ac/pptx/scripts/apply_theme.js");

const R = JSON.parse(fs.readFileSync("results/bonus.json", "utf8"));
const four = R.find((r) => r.n === 4);
const pct = (x, d = 1) => (100 * x).toFixed(d) + "%";

const THEME = {
  name: "Instant Insanity",
  headFontFace: "Cambria",
  bodyFontFace: "Calibri",
  colors: {
    dk1: "17152B", lt1: "FFFFFF", dk2: "2B2745", lt2: "F3F1FA",
    accent1: "8B5CF6", accent2: "2FA95F", accent3: "E8B400",
    accent4: "3B82F6", accent5: "D64545", accent6: "7C7A94",
    hlink: "8B5CF6", folHlink: "7C7A94",
  },
};

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE";       // 13.3 x 7.5
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
pres.author = "UConn Fall Fest team";
pres.title = "Instant Insanity with a compact QAOA encoding";
const C = pres.SchemeColor;
const W = 13.3, H = 7.5;

// ---------------------------------------------------------------- layouts
pres.defineSlideMaster({
  title: "DARK",
  background: { color: THEME.colors.dk1 },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.9, y: 2.3, w: 11.5, h: 1.9,
        fontSize: 44, bold: true, color: C.background1, valign: "bottom" }, text: " " } },
    { placeholder: { options: { name: "body", type: "body", x: 0.9, y: 4.35, w: 11.5, h: 2.1,
        fontSize: 16, color: "C9C5DC", valign: "top" }, text: " " } },
  ],
});

pres.defineSlideMaster({
  title: "DARKCLOSE",
  background: { color: THEME.colors.dk1 },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.9, y: 0.9, w: 11.5, h: 1.2,
        fontSize: 40, bold: true, color: C.background1, valign: "middle" }, text: " " } },
    { placeholder: { options: { name: "body", type: "body", x: 0.9, y: 2.45, w: 11.5, h: 3.7,
        fontSize: 15, color: "C9C5DC", valign: "top" }, text: " " } },
  ],
});

pres.defineSlideMaster({
  title: "LIGHT",
  background: { color: C.background1 },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.75, y: 0.45, w: 11.8, h: 0.85,
        fontSize: 32, bold: true, color: C.text1, valign: "middle" }, text: " " } },
    { text: { text: "Instant Insanity · compact QAOA", options: { x: 0.75, y: 6.85, w: 7, h: 0.3,
        fontSize: 10, color: THEME.colors.accent6, isTextBox: true } } },
    { placeholder: { options: { name: "slideNumber", type: "sldNum", x: 12.4, y: 6.85, w: 0.5, h: 0.3,
        fontSize: 10, color: THEME.colors.accent6, align: "right" }, text: " " } },
  ],
});

// the four cube colours, used as the deck's repeating motif
const CUBE_COLS = ["D64545", "2FA95F", "3B82F6", "E8B400"];
function motif(slide, x, y, size = 0.17, gap = 0.055) {
  CUBE_COLS.forEach((c, i) => {
    slide.addShape(pres.ShapeType.roundRect, {
      x: x + i * (size + gap), y, w: size, h: size, fill: { color: c },
      rectRadius: 0.03, line: { color: c, width: 0 }, objectName: `motif${i}`,
    });
  });
}

function card(slide, o) {
  slide.addShape(pres.ShapeType.roundRect, {
    x: o.x, y: o.y, w: o.w, h: o.h, fill: { color: o.fill || THEME.colors.lt2 },
    rectRadius: 0.06, line: { color: o.fill || THEME.colors.lt2, width: 0 },
    objectName: o.name,
  });
}

function stat(slide, o) {
  slide.addText(o.value, { x: o.x, y: o.y, w: o.w, h: 0.85, fontSize: o.size || 46,
    bold: true, color: o.color || THEME.colors.accent1, align: "center",
    margin: 0, isTextBox: true, objectName: (o.name || "stat") + "v" });
  slide.addText(o.label, { x: o.x, y: o.y + 0.82, w: o.w, h: 0.6, fontSize: 12,
    color: THEME.colors.accent6, align: "center", margin: 0, isTextBox: true,
    objectName: (o.name || "stat") + "l" });
}

// ---------------------------------------------------------------- 1 title
pres.addSection({ title: "Opening" });
let s = pres.addSlide({ masterName: "DARK", sectionTitle: "Opening" });
motif(s, 0.9, 1.75, 0.3, 0.12);
s.addText("Instant Insanity on 12 qubits", { placeholder: "title" });
s.addText(
  [{ text: "Half the qubits, no penalty terms, and a " + pct(four.p_solved, 0) +
      " hit rate against a " + (100 * four.baseline).toFixed(3) + "% random baseline.",
    options: { breakLine: true } },
   { text: "Daksh Goswami  ·  Rueben  ·  Ishal",
    options: { fontSize: 14, color: "FFFFFF", breakLine: true } },
   { text: "Qiskit Fall Fest Connecticut 2026  ·  qBraid challenge  ·  UConn Quantum Computing",
    options: { fontSize: 13, color: THEME.colors.accent6 } }],
  { placeholder: "body" });
s.addNotes("Four cubes, four colours. Stack them so every colour shows once on each side. " +
  "We solve it with QAOA on an encoding that uses half the qubits of the starter's.");

// ---------------------------------------------------------------- 2 the puzzle
pres.addSection({ title: "Problem" });
s = pres.addSlide({ masterName: "LIGHT", sectionTitle: "Problem" });
s.addText("A tiny puzzle with a brutal search space", { placeholder: "title" });
[[0.75, "331,776", "ways to stack four cubes", THEME.colors.accent1],
 [4.95, "8", "that actually work", THEME.colors.accent2],
 [9.15, "< 1 s", "for classical brute force", THEME.colors.accent5]]
  .forEach(([x, v, l, c], i) => {
    card(s, { x, y: 1.6, w: 3.4, h: 1.9, name: "c" + i });
    stat(s, { x, y: 1.85, w: 3.4, value: v, label: l, color: c, name: "s" + i });
  });
s.addText("Every cube shows one of three opposite-face pairs on the front/back axis and a " +
  "different pair on left/right, so each cube has exactly 6 legal choices. A tower is solved " +
  "when all four sides show all four colours.",
  { x: 0.75, y: 3.9, w: 11.8, h: 0.9, fontSize: 15, color: C.text1, isTextBox: true,
    objectName: "explain" });
s.addText([
  { text: "Brute force already wins at N = 4.", options: { bold: true, breakLine: true } },
  { text: "We say so on every slide that reports a number. What the quantum route buys is a " +
      "method that never enumerates — and a cost curve we can measure as the puzzle grows." }],
  { x: 0.75, y: 4.85, w: 11.8, h: 1.2, fontSize: 14, color: C.text2, isTextBox: true,
    objectName: "honesty" });
motif(s, 0.75, 6.4);
s.addNotes("331,776 stackings, 8 solved orientations, which are one tower from eight angles.");

// ---------------------------------------------------------------- 3 the encoding
pres.addSection({ title: "Encoding" });
s = pres.addSlide({ masterName: "LIGHT", sectionTitle: "Encoding" });
s.addText("Make every bitstring legal, and the penalties disappear", { placeholder: "title" });

card(s, { x: 0.75, y: 1.5, w: 5.6, h: 3.5, fill: "F7E9E9", name: "onehot" });
s.addText("One-hot (starter)", { x: 1.05, y: 1.7, w: 5.0, h: 0.4, fontSize: 18, bold: true,
  color: THEME.colors.accent5, isTextBox: true, objectName: "oh" });
s.addText([
  { text: "6 qubits per cube → 24 for four cubes", options: { bullet: true, breakLine: true } },
  { text: "most bitstrings are illegal", options: { bullet: true, breakLine: true } },
  { text: "penalties for \"one pair per axis\"", options: { bullet: true, breakLine: true } },
  { text: "penalty for \"a pair cannot serve both axes\"", options: { bullet: true, breakLine: true } },
  { text: "XY mixer + W-state preparation", options: { bullet: true } }],
  { x: 1.05, y: 2.2, w: 5.0, h: 2.6, fontSize: 14, color: C.text1, paraSpaceAfter: 7,
    isTextBox: true, objectName: "ohlist" });

card(s, { x: 6.95, y: 1.5, w: 5.6, h: 3.5, fill: "ECE6FB", name: "compact" });
s.addText("Compact (ours)", { x: 7.25, y: 1.7, w: 5.0, h: 0.4, fontSize: 18, bold: true,
  color: THEME.colors.accent1, isTextBox: true, objectName: "cp" });
s.addText([
  { text: "3 qubits per cube → 12 for four cubes", options: { bullet: true, breakLine: true } },
  { text: "all 8 states map onto the 6 legal choices", options: { bullet: true, breakLine: true } },
  { text: "no bitstring is ever illegal", options: { bullet: true, breakLine: true } },
  { text: "no penalty terms, nothing to tune", options: { bullet: true, breakLine: true } },
  { text: "plain X mixer is enough", options: { bullet: true } }],
  { x: 7.25, y: 2.2, w: 5.0, h: 2.6, fontSize: 14, color: C.text1, paraSpaceAfter: 7,
    isTextBox: true, objectName: "cplist" });

s.addText("24  →  12 qubits", { x: 0.75, y: 5.25, w: 5.6, h: 0.7, fontSize: 30, bold: true,
  color: THEME.colors.accent1, align: "center", isTextBox: true, objectName: "big" });
s.addText([
  { text: "cost  =  Σ over axes and colours of  (dₖ − 2)²",
    options: { bold: true, fontSize: 15, breakLine: true } },
  { text: "zero exactly for a solved tower",
    options: { fontSize: 13, color: THEME.colors.accent6 } }],
  { x: 6.95, y: 5.2, w: 5.6, h: 0.85, color: C.text1, align: "center",
    isTextBox: true, objectName: "cost" });
motif(s, 0.75, 6.4);
s.addNotes("Six legal choices fit in three qubits, which hold eight states. Map all eight onto " +
  "the six. Then the structural rules are in the encoding, not in penalty weights.");

// ---------------------------------------------------------------- 4 checks
pres.addSection({ title: "Checks" });
s = pres.addSlide({ masterName: "LIGHT", sectionTitle: "Checks" });
s.addText("We checked the model before we trusted a single shot", { placeholder: "title" });
const checks = [
  ["Hamiltonian = cost", "On every one of the 4,096 bitstrings. Difference exactly 0.0, not a tolerance.", THEME.colors.accent1],
  ["Two cost implementations", "A vectorised one and a plain-Python one written straight from the definition.", THEME.colors.accent4],
  ["Decoder, both directions", "No zero-cost bitstring fails the starter's solves(); no positive-cost one passes it.", THEME.colors.accent2],
  ["Fast simulator = Qiskit", "The hand-written statevector used in the angle search agrees to 1e-15.", THEME.colors.accent3],
];
checks.forEach(([t, d, col], i) => {
  const y = 1.45 + i * 1.22;
  s.addShape(pres.ShapeType.ellipse, { x: 0.8, y: y + 0.12, w: 0.42, h: 0.42,
    fill: { color: col }, line: { color: col, width: 0 }, objectName: "dot" + i });
  s.addText(String(i + 1), { x: 0.8, y: y + 0.12, w: 0.42, h: 0.42, fontSize: 14, bold: true,
    color: "FFFFFF", align: "center", valign: "middle", margin: 0, isTextBox: true,
    objectName: "num" + i });
  s.addText(t, { x: 1.45, y: y, w: 4.0, h: 0.42, fontSize: 17, bold: true, color: C.text1,
    margin: 0, isTextBox: true, objectName: "ct" + i });
  s.addText(d, { x: 1.45, y: y + 0.44, w: 10.6, h: 0.6, fontSize: 13, color: C.text2,
    margin: 0, isTextBox: true, objectName: "cd" + i });
});
s.addText("Every success rate we report is the fraction of shots that pass the classical " +
  "checker — never the fraction below an energy threshold.",
  { x: 0.8, y: 6.3, w: 11.7, h: 0.5, fontSize: 14, bold: true, color: THEME.colors.accent1,
    isTextBox: true, objectName: "kicker" });
s.addNotes("A low energy is not proof. Each reported tower is rebuilt and handed to the " +
  "starter notebook's own solves().");

// ---------------------------------------------------------------- 5 alias search
pres.addSection({ title: "Results" });
s = pres.addSlide({ masterName: "LIGHT", sectionTitle: "Results" });
s.addText("The state-to-choice map is a free 2.6× saving", { placeholder: "title" });
s.addText("Two of the eight states are duplicates. Which ones is ours to choose, and it changes " +
  "the Walsh expansion of the cost — so it changes how many Z strings the Hamiltonian has and " +
  "how long they are. We searched all 720 × 36 maps and scored each by the CX gates one cost " +
  "layer needs. Same Hamiltonian, same answers, cheaper circuit.",
  { x: 0.75, y: 1.4, w: 6.4, h: 1.7, fontSize: 14, color: C.text1, isTextBox: true,
    objectName: "aliastext" });
[[0.75, "1216", "CX per layer, naive map", THEME.colors.accent5],
 [3.15, "460", "CX per layer, searched", THEME.colors.accent2],
 [5.55, "6 → 4", "longest Z string", THEME.colors.accent1]]
  .forEach(([x, v, l, c], i) => stat(s, { x, y: 3.35, w: 2.3, value: v, label: l, color: c,
    size: 34, name: "a" + i }));
s.addImage({ path: "figures/alias.png", x: 7.5, y: 1.5, w: 5.1, h: 3.3 });
s.addText("The search is pure classical preprocessing: it runs once, costs seconds, and the " +
  "circuit it produces is provably the same Hamiltonian.",
  { x: 0.75, y: 5.5, w: 11.8, h: 0.6, fontSize: 13, color: C.text2, isTextBox: true,
    objectName: "aliasnote" });
motif(s, 0.75, 6.4);
s.addNotes("This was free performance. We did not change the physics, only the labelling.");

// ---------------------------------------------------------------- 6 optimiser
s = pres.addSlide({ masterName: "LIGHT", sectionTitle: "Results" });
s.addText("How we optimised mattered more than the circuit", { placeholder: "title" });
s.addImage({ path: "figures/layers.png", x: 6.6, y: 1.5, w: 6.0, h: 3.3 });
s.addText([
  { text: "CVaR instead of the mean\n", options: { bold: true, fontSize: 17, breakLine: true } },
  { text: "Minimising the average cost is not the same as maximising P(solved): the average is " +
      "dominated by the bulk of bad bitstrings. CVaR averages only the best 30%, so the " +
      "optimiser chases the low-cost tail where the answers are.\n\n",
    options: { fontSize: 14, breakLine: true } },
  { text: "Layer-by-layer growth\n", options: { bold: true, fontSize: 17, breakLine: true } },
  { text: "Optimising 2p angles from a random start stalls. Instead solve p = 1, interpolate " +
      "those angles into a p + 1 schedule, re-optimise. Every layer starts from a good guess.",
    options: { fontSize: 14 } }],
  { x: 0.75, y: 1.5, w: 5.6, h: 3.4, color: C.text1, isTextBox: true, objectName: "opt" });
s.addText("Same Hamiltonian, same hardware:   ~2%   →   " + pct(four.p_solved),
  { x: 0.75, y: 5.3, w: 11.8, h: 0.8, fontSize: 28, bold: true, color: THEME.colors.accent1,
    isTextBox: true, objectName: "jump" });
motif(s, 0.75, 6.4);
s.addNotes("Random-restart COBYLA on the mean stalled near 2 percent. CVaR plus layerwise " +
  "growth reached 45 on the identical Hamiltonian.");

// ---------------------------------------------------------------- 7 results
s = pres.addSlide({ masterName: "LIGHT", sectionTitle: "Results" });
s.addText("Results, and how they scale with N", { placeholder: "title" });
const rows = [[
  { text: "N", options: { bold: true } }, { text: "Qubits", options: { bold: true } },
  { text: "CX/layer", options: { bold: true } }, { text: "p", options: { bold: true } },
  { text: "P(solved)", options: { bold: true } }, { text: "Random", options: { bold: true } },
  { text: "Lift", options: { bold: true } }]];
R.forEach((r) => rows.push([
  String(r.n), String(r.qubits), String(r.cx_per_layer), String(r.best_p),
  pct(r.p_solved, 2), (100 * r.baseline).toFixed(4) + "%", "×" + Math.round(r.lift)]));
s.addTable(rows, {
  x: 0.75, y: 1.45, w: 6.1, colW: [0.5, 0.8, 1.0, 0.45, 1.2, 1.2, 0.95],
  fontSize: 12, color: THEME.colors.dk1, border: { type: "solid", color: "DDDAE8", pt: 1 },
  fill: { color: "FFFFFF" }, align: "center", valign: "middle", rowH: 0.34,
  objectName: "restable",
});
s.addImage({ path: "figures/scaling.png", x: 7.1, y: 1.45, w: 5.4, h: 3.2 });
s.addText([
  { text: "The lift over random grows with N — but the absolute success rate falls, because " +
      "the solution fraction shrinks faster than the algorithm gains. ",
    options: { breakLine: false } },
  { text: "We report both, not only the flattering one.", options: { bold: true } }],
  { x: 0.75, y: 5.0, w: 11.8, h: 0.8, fontSize: 14, color: C.text1, isTextBox: true,
    objectName: "scalenote" });
const SEEDS = { 5: 16, 6: 86, 7: 68 };
const seedNote = R.filter((r) => r.n > 4).map((r) => `N=${r.n} seed ${SEEDS[r.n]}`).join(", ");
s.addText("Puzzles with N > 4 from the starter's make_puzzle(n, seed): " + seedNote +
  ". Every N re-verified against the classical cost, and its alias map re-searched, before any angle search.",
  { x: 0.75, y: 5.78, w: 11.8, h: 0.5, fontSize: 11, color: THEME.colors.accent6,
    isTextBox: true, objectName: "seeds" });
motif(s, 0.75, 6.4);
s.addNotes("Four cubes on SV1, the larger ones on the local simulator.");

// ---------------------------------------------------------------- 8 close
pres.addSection({ title: "Closing" });
s = pres.addSlide({ masterName: "DARKCLOSE", sectionTitle: "Closing" });
s.addText("What we are not claiming", { placeholder: "title" });
s.addText([
  { text: "No quantum speedup. ", options: { bold: true, color: "FFFFFF" } },
  { text: "Brute force solves the four-cube puzzle in a fraction of a second, far faster than " +
      "building, optimising and sampling these circuits. The honest comparison is against " +
      "random guessing inside the same encoding, and that is what every table reports. The " +
      "general N-cube problem is NP-complete, and nothing here changes that.\n\n",
    options: { breakLine: true } },
  { text: "Next. ", options: { bold: true, color: "FFFFFF" } },
  { text: "The cost layer is the bottleneck, and most of it is weight-3 and weight-4 Z strings. " +
      "Order them to share CX ladders between neighbouring terms, and warm-start the angles for " +
      "N + 1 from the optimised schedule at N — the layerwise growth already hints it transfers." }],
  { placeholder: "body" });
motif(s, 0.9, 6.5, 0.3, 0.12);
s.addNotes("The thing we would try next is CX-ladder sharing across neighbouring Z terms.");

(async () => {
  await pres.writeFile({ fileName: "slides.pptx" });
  await applyTheme("slides.pptx", THEME);
  console.log("wrote slides.pptx");
})();
