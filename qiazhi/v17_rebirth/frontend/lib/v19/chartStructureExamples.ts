import { evaluateChartStructure } from "./chartStructureEngine";
import type { BirthInput } from "./chartStructureTypes";

export const exampleSolarBirthInput: BirthInput = {
  year: 1990,
  month: 5,
  day: 12,
  hour: 10,
  calendar_type: "solar",
  gender: "male",
};

export const exampleLunarBirthInput: BirthInput = {
  year: 1990,
  month: 4,
  day: 18,
  hour: 10,
  calendar_type: "lunar",
  gender: "female",
};

export const exampleSolarChartStructure = evaluateChartStructure(exampleSolarBirthInput);

