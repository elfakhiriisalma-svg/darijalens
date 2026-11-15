import { describe, expect, it } from "vitest";
import { coreOf, highlight, intensity, wholeWordWeights } from "./highlight";

describe("coreOf", () => {
  it("retire la ponctuation autour d'un mot", () => {
    expect(coreOf("بزاف،")).toBe("بزاف");
    expect(coreOf("(mzyan)!")).toBe("mzyan");
    expect(coreOf("3jebni")).toBe("3jebni");
  });
});

describe("wholeWordWeights", () => {
  it("garde les mots entiers, avec ou sans espaces de chaque côté", () => {
    const weights = wholeWordWeights([
      { feature: "عجبني", weight: 0.4 },
      { feature: " هاد ", weight: -0.1 },
    ]);
    expect(weights.get("عجبني")).toBe(0.4);
    expect(weights.get("هاد")).toBe(-0.1);
  });

  it("ignore les débuts, fins et paires de mots", () => {
    const weights = wholeWordWeights([
      { feature: " ه", weight: 0.3 },
      { feature: "ش ", weight: 0.3 },
      { feature: "هاد الفيلم", weight: 0.3 },
      { feature: "", weight: 0.3 },
    ]);
    expect(weights.size).toBe(0);
  });

  it("additionne les poids d'un même mot", () => {
    const weights = wholeWordWeights([
      { feature: "زوين", weight: 0.1 },
      { feature: " زوين ", weight: 0.05 },
    ]);
    expect(weights.get("زوين")).toBeCloseTo(0.15);
  });
});

describe("highlight", () => {
  it("marque les mots qui ont pesé, même suivis de ponctuation", () => {
    const pieces = highlight("هاد الفيلم زوين بزاف، عجبني", [
      { feature: "عجبني", weight: 0.4 },
      { feature: "بزاف", weight: 0.2 },
      { feature: "هاد", weight: -0.1 },
    ]);
    const weighted = pieces.filter((piece) => piece.weight !== null).map((piece) => piece.text);
    expect(weighted).toEqual(["هاد", "بزاف،", "عجبني"]);
  });

  it("rend exactement le texte d'origine une fois recollé", () => {
    const text = "wach  nta mzyan?";
    expect(highlight(text, []).map((piece) => piece.text).join("")).toBe(text);
  });
});

describe("intensity", () => {
  it("donne 1 au plus grand poids et au moins 0,25 aux autres", () => {
    const pieces = highlight("a b", [
      { feature: "a", weight: 0.4 },
      { feature: "b", weight: -0.1 },
    ]);
    expect(intensity(0.4, pieces)).toBeCloseTo(1);
    expect(intensity(-0.1, pieces)).toBeCloseTo(0.25 + 0.75 * 0.25);
  });
});
