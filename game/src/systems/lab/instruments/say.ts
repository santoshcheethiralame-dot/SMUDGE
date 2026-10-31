import type { LabCtx, SayStep } from "../types";

export const kind = "say";

export async function run(ctx: LabCtx, step: SayStep) {
  await ctx.dlg.play(step.lines);
  ctx.dlg.hide();
}
