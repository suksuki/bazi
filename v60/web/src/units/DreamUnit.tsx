import type { DreamSnapshot } from "../api";

export function DreamUnit({ snapshot }: { snapshot: DreamSnapshot }) {
  const observed = snapshot.encounter.state.observed_organs.length;
  const activeStep = snapshot.encounter.state.revealed
    ? 3
    : snapshot.encounter.state.answer_sealed
      ? 2
      : snapshot.question
        ? 1
        : 0;

  return (
    <>
      <p className="rail-kicker">阿布</p>
      <blockquote>{snapshot.projections.abu.line}</blockquote>
      <div className="journey-list">
        {[
          ["读树", `${Math.min(observed, 3)} / 3 条线索已看见`],
          ["封存", snapshot.human_seal ? "你的判断已经留下" : "等待你的独立判断"],
          [
            "等世界",
            snapshot.encounter.state.world_settled
              ? "后来发生的事已抵达"
              : "让真实时间给出新证据",
          ],
          [
            "收果",
            snapshot.encounter.state.reconciled
              ? "复盘已经收入观察记录"
              : "事实抵达后再打开果实",
          ],
        ].map(([title, detail], index) => (
          <div
            className="journey-step"
            data-active={activeStep === index}
            data-complete={activeStep > index}
            key={title}
          >
            <span>{index + 1}</span>
            <p>
              <strong>{title}</strong>
              <small>{detail}</small>
            </p>
          </div>
        ))}
      </div>
    </>
  );
}
