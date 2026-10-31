/** A calculator that only understands numbers, + - * / ^, brackets and square roots ("√" or "sqrt"). */
export function calc(src: string): number {
  const s = src.replace(/,/g, ".").replace(/×/g, "*").replace(/÷/g, "/").replace(/sqrt/gi, "√").replace(/\s+/g, "");
  if (!s || /[^0-9.+\-*/^()√]/.test(s)) return NaN;
  let i = 0;
  const peek = () => s[i];
  const num = (): number => {
    if (peek() === "(") { i++; const v = expr(); if (peek() === ")") i++; return v; }
    if (peek() === "√") { i++; return Math.sqrt(unary()); }
    const m = /^\d*\.?\d+/.exec(s.slice(i));
    if (!m) return NaN;
    i += m[0].length;
    return parseFloat(m[0]);
  };
  const unary = (): number => (peek() === "-" ? (i++, -unary()) : num());
  const pow = (): number => { const b = unary(); return peek() === "^" ? (i++, b ** pow()) : b; };
  const term = (): number => { let v = pow(); while (peek() === "*" || peek() === "/") v = s[i++] === "*" ? v * pow() : v / pow(); return v; };
  const expr = (): number => { let v = term(); while (peek() === "+" || peek() === "-") v = s[i++] === "+" ? v + term() : v - term(); return v; };
  const v = expr();
  return i === s.length ? v : NaN;
}
