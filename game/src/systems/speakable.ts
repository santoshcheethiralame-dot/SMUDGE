// Turns what is on the screen into what a voice should say: formulas, units and a few noises. The text on screen
// is never changed; this only feeds speech (Sarvam and the browser voice alike).
const SQ: Record<string, string> = { "²": " squared", "³": " cubed" };

export function speakable(text: string): string {
  const formula = /[=×÷]/.test(text);
  let t = text
    .replace(/\bhr+m+\b/gi, (m) => (m[0] === "H" ? "Hmm" : "hmm"))                       // the noises: Hrrm. is a hum, not a spelling
    .replace(/\bp+s+t+\b/gi, (m) => (m[0] === "P" ? "Psst" : "psst"))
    .replace(/\b([ckm])m([²³])/g, (_, k, p) => `${p === "²" ? "square" : "cubic"} ${k === "c" ? "centi" : k === "m" ? "milli" : "kilo"}metres`)
    .replace(/\b([a-z])([a-z]{1,2})(?=[²³])/g, (_, a, b) => `${a} ${[...b].join(" ")}`)  // "gt²" is g t squared, not "gt"
    .replace(/(\d)([a-z])([a-z])\b/g, "$1 $2 $3")                                         // "2as" is 2 a s
    .replace(/[²³]/g, (m) => SQ[m])
    .replace(/\s·\s/g, ", ")
    .replace(/½/g, " half ")
    .replace(/¼/g, " a quarter ")
    .replace(/√/g, " square root of ")
    .replace(/Δ/g, " delta ")
    .replace(/°\s?C\b/g, " degrees Celsius")
    .replace(/°/g, " degrees")
    .replace(/(\d)\s*Ω/g, "$1 ohms")
    .replace(/Ω/g, " ohms")
    .replace(/\s×\s|×/g, " times ")
    .replace(/\s÷\s|÷/g, " divided by ")
    .replace(/\s=\s|=/g, " equals ")
    .replace(/\s\/\s/g, " over ")
    .replace(/(?<=[A-Za-z])\/(?=[A-Za-z])/g, " per ");                                    // N/kg, g/cm³
  if (formula) t = t.replace(/\s[-−]\s/g, " minus ").replace(/\s\+\s/g, " plus ");
  return t.replace(/\s{2,}/g, " ").replace(/\s+([.,!?;:])/g, "$1").trim();
}
