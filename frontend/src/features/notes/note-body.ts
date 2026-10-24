import type { AnswerItem, CopilotAnswer } from "@/features/copilot/schemas";

const cited = (item: AnswerItem) =>
  item.citations.length
    ? `${item.text} [${item.citations.join(", ")}]`
    : item.text;

/**
 * A copilot answer as editable note text: the four sections as headings, each item on its own
 * line with its citations in square brackets (the server re-validates every cited ID).
 */
export function answerToNoteBody(answer: CopilotAnswer): string {
  const sections: [string, string[]][] = [
    ["What the records show", answer.records.map(cited)],
    ["Calculated", answer.calculated.map(cited)],
    ["Not established", answer.notEstablished],
    ["Next checks", answer.nextChecks],
  ];
  return sections
    .filter(([, lines]) => lines.length > 0)
    .map(([title, lines]) => [title, ...lines.map((l) => `- ${l}`)].join("\n"))
    .join("\n\n");
}
