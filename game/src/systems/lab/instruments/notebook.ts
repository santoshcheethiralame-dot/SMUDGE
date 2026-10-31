// The notebook: measurements carried over from the instruments, and boxes for the player's working.
// The server's kit checks it step by step; a wrong step gets Footnote's hint, a right one the evidence.
import { sfx } from "../../../audio";
import { api } from "../../../api";
import { overlay, replay } from "../../ui";
import { calc } from "../calc";
import type { LabCtx, NotebookStep } from "../types";

export const kind = "notebook";

export function run(ctx: LabCtx, step: NotebookStep): Promise<void> {
  const { scene, dlg } = ctx;
  const fields = step.fields(ctx.c, ctx.measured);
  return new Promise((resolve) => {
    dlg.say({ who: "foot", expr: "neutral", text: step.hint });
    const wrap = document.createElement("form");
    wrap.setAttribute("aria-label", "Notebook");
    wrap.style.cssText = `font-family:"Smudge Digits","Pixelify Sans",monospace;background:#F2E9CF;border:2px solid #0E1938;border-radius:4px;
      padding:8px 10px;box-sizing:border-box;display:flex;flex-direction:column;gap:5px;color:#0E1938;overflow:auto;
      background-image:repeating-linear-gradient(#F2E9CF 0 15px,#9cb8dc 15px 16px);`;
    const box = (f: (typeof fields)[number]) =>
      `<input id="nb-${f.key}" value="${f.given ?? ""}" ${f.given !== undefined ? "readonly tabindex=-1" : ""} inputmode="decimal" autocomplete="off"
        style="width:5.4em;font:inherit;padding:1px 4px;border:1.5px solid #0E1938;background:${f.given !== undefined ? "#E6DCC0" : "#FFFBEF"};color:#0E1938;border-radius:3px">`;
    wrap.innerHTML = `<div style="font-weight:700;color:#C9302A;display:flex;justify-content:space-between;gap:8px"><span>Working</span><span style="font-weight:400;color:#46506E">sums like 8.7/5 work too</span></div>
      ${step.note ? `<div style="background:#E6DCC0;border:1px solid #0E1938;border-radius:3px;padding:2px 5px;color:#0E1938">${step.note}</div>` : ""}
      ${fields.map((f) => `<label style="display:flex;justify-content:space-between;align-items:center;gap:6px"><span>${f.label}${f.unit ? ` (${f.unit})` : ""}</span>${box(f)}</label>`).join("")}
      <button type="submit" style="font:inherit;margin-top:3px;padding:4px;border:2px solid #0E1938;background:#C9302A;color:#fff;border-radius:4px;cursor:pointer">Check working</button>`;
    ["pointerdown", "keydown", "keyup"].forEach((ev) => wrap.addEventListener(ev, (e) => e.stopPropagation()));
    sfx("open");
    const remove = overlay(scene, wrap, 270, 84, 202, Math.min(180, 50 + (step.note ? 22 : 0) + fields.length * 22));
    scene.input.keyboard!.enabled = false;
    const mark = (key: string, bad: boolean) => { (document.getElementById(`nb-${key}`) as HTMLInputElement).style.borderColor = bad ? "#C9302A" : "#0E1938"; };
    wrap.onsubmit = async (e) => {
      e.preventDefault();
      const working: Record<string, number> = {};
      for (const f of fields) working[f.key] = f.given ?? calc((document.getElementById(`nb-${f.key}`) as HTMLInputElement).value);
      if (Object.values(working).some((x) => Number.isNaN(x))) {
        dlg.say({ who: "foot", expr: "neutral", text: "*Fill in every empty box first. Numbers, or a sum." });
        return;
      }
      const btn = wrap.querySelector("button[type=submit]") as HTMLButtonElement;
      btn.disabled = true;
      btn.textContent = "Checking...";
      const r = await api.labCheck(working);
      btn.disabled = false;
      btn.textContent = "Check working";
      if (!r) {
        dlg.say({ who: "foot", expr: "worried", text: "*The agent server didn't answer. Give it a moment, then press Check working again." });
        return;
      }
      const bad = new Set(r.bad ?? []);
      for (const f of fields) if (f.given === undefined) mark(f.key, bad.has(f.key));
      if (r.ok && r.evidence && r.card) {
        // a red ink stamp lands on the page before it closes
        const stamp = document.createElement("div");
        stamp.textContent = "CORRECT";
        stamp.className = "sm-stamp";
        stamp.style.cssText += "position:absolute;right:14px;top:30%;padding:2px 8px;border:3px solid #C9302A;color:#C9302A;" +
          "font-weight:700;letter-spacing:2px;border-radius:4px;pointer-events:none;background:rgba(242,233,207,.6)";
        wrap.style.position = "fixed";
        wrap.appendChild(stamp);
        sfx("stamp");
        sfx("chime");
        btn.disabled = true;
        await new Promise((res) => setTimeout(res, 650));
        remove();
        scene.input.keyboard!.enabled = true;
        dlg.hide();
        ctx.result = r;
        resolve();
      } else {
        replay(wrap, "sm-shake");
        sfx("wrong");
        dlg.say({ who: "foot", expr: "worried", text: r.hint ?? "*Check each number again, one at a time." });
      }
    };
  });
}
