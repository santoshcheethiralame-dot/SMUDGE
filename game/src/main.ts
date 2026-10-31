import Phaser from "phaser";
import { W, H, Z } from "./consts";
import { Boot } from "./scenes/Boot";
import { Title } from "./scenes/Title";
import { Prologue } from "./scenes/Prologue";
import { HQ, EndCard } from "./scenes/HQ";
import { District } from "./systems/district";
import { CaseMap } from "./scenes/Map";
import { CaseLab } from "./scenes/CaseLab";
import { Bench } from "./scenes/Bench";
import { Lab } from "./scenes/Lab";
import { LabMotion } from "./scenes/LabMotion";
import { CrossExam } from "./scenes/CrossExam";
import { Restore, CaseSolved } from "./scenes/Restore";
import { installInside } from "./systems/inside";
import { installAudio } from "./audio";

const game = new Phaser.Game({
  type: Phaser.AUTO,
  parent: "game",
  width: W * Z,
  height: H * Z,
  backgroundColor: "#05060F",
  pixelArt: true,
  roundPixels: true,
  scale: { mode: Phaser.Scale.FIT, autoCenter: Phaser.Scale.CENTER_BOTH },
  input: { activePointers: 2 },
  scene: [Boot, Title, Prologue, HQ, EndCard, CaseMap, District, Lab, LabMotion, CaseLab, CrossExam, Restore, CaseSolved, Bench],
});

// text draws its texture at Z, so through the zoomed camera every glyph pixel is a screen pixel
const factory = Phaser.GameObjects.GameObjectFactory.prototype as unknown as { text: (...a: unknown[]) => Phaser.GameObjects.Text };
const makeText = factory.text;
factory.text = function (this: unknown, ...a: unknown[]) { return makeText.apply(this, a).setResolution(Z); };

// every scene sees a 480x270 world: its main camera zooms Z from the top-left corner
game.events.once(Phaser.Core.Events.READY, () => {
  for (const s of game.scene.scenes) {
    s.sys.events.on(Phaser.Scenes.Events.START, () => s.cameras.main.setOrigin(0, 0).setZoom(Z));
    if (s.sys.isActive()) s.cameras.main.setOrigin(0, 0).setZoom(Z);      // Boot is already running
  }
});

(window as any).game = game;
installInside(game);
installAudio(() => game.canvas);
