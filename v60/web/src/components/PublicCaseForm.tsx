import { useMemo, useState, type FormEvent } from "react";

import type { OwnerCaseInput } from "../publicHomeApi";

function initialInput(): OwnerCaseInput {
  const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone || "Asia/Shanghai";
  return {
    display_name: "",
    gender: "male",
    calendar_type: "solar",
    birth_date: "",
    birth_time: "12:00",
    birth_location: "",
    timezone,
    lunar_leap_month: false,
    true_solar_time_policy: "not_applied",
  };
}

export function PublicCaseForm({
  saving,
  error,
  canClose,
  onClose,
  onSubmit,
}: {
  saving: boolean;
  error: string | null;
  canClose: boolean;
  onClose: () => void;
  onSubmit: (input: OwnerCaseInput) => Promise<void>;
}) {
  const [input, setInput] = useState<OwnerCaseInput>(initialInput);
  const today = useMemo(() => new Date().toISOString().slice(0, 10), []);

  const submit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    void onSubmit({
      ...input,
      display_name: input.display_name.trim(),
      birth_location: input.birth_location.trim(),
      timezone: input.timezone.trim(),
    });
  };

  return (
    <div className="public-modal-backdrop" role="presentation" onMouseDown={canClose ? onClose : undefined}>
      <section
        aria-labelledby="new-chart-title"
        aria-modal="true"
        className="public-case-modal"
        role="dialog"
        onMouseDown={(event) => event.stopPropagation()}
      >
        <header>
          <div>
            <p className="public-kicker">新命盘</p>
            <h2 id="new-chart-title">填写出生资料</h2>
          </div>
          {canClose && (
            <button aria-label="关闭" className="public-icon-button" onClick={onClose} type="button">
              ×
            </button>
          )}
        </header>

        <form className="public-case-form" onSubmit={submit}>
          <label className="public-field-wide">
            <span>怎么称呼这份命盘</span>
            <input
              autoFocus
              maxLength={80}
              placeholder="例如：我、妈妈、朋友 A"
              required
              value={input.display_name}
              onChange={(event) => setInput((current) => ({ ...current, display_name: event.target.value }))}
            />
          </label>

          <fieldset>
            <legend>性别</legend>
            <div className="public-segmented-field">
              {(["male", "female"] as const).map((gender) => (
                <button
                  aria-pressed={input.gender === gender}
                  className={input.gender === gender ? "is-active" : ""}
                  key={gender}
                  onClick={() => setInput((current) => ({ ...current, gender }))}
                  type="button"
                >
                  {gender === "male" ? "男" : "女"}
                </button>
              ))}
            </div>
          </fieldset>

          <label>
            <span>历法</span>
            <select
              value={input.calendar_type}
              onChange={(event) => setInput((current) => ({
                ...current,
                calendar_type: event.target.value as OwnerCaseInput["calendar_type"],
                lunar_leap_month: event.target.value === "lunar" && current.lunar_leap_month,
              }))}
            >
              <option value="solar">公历</option>
              <option value="lunar">农历</option>
            </select>
          </label>

          <label>
            <span>出生日期</span>
            <input
              max={today}
              required
              type="date"
              value={input.birth_date}
              onChange={(event) => setInput((current) => ({ ...current, birth_date: event.target.value }))}
            />
          </label>

          <label>
            <span>出生时间</span>
            <input
              required
              type="time"
              value={input.birth_time}
              onChange={(event) => setInput((current) => ({ ...current, birth_time: event.target.value }))}
            />
          </label>

          <label>
            <span>出生地</span>
            <input
              maxLength={160}
              placeholder="城市或地区"
              required
              value={input.birth_location}
              onChange={(event) => setInput((current) => ({ ...current, birth_location: event.target.value }))}
            />
          </label>

          <label className="public-field-wide">
            <span>出生地时区</span>
            <input
              list="public-timezones"
              required
              value={input.timezone}
              onChange={(event) => setInput((current) => ({ ...current, timezone: event.target.value }))}
            />
            <datalist id="public-timezones">
              <option value="Asia/Shanghai">中国标准时间</option>
              <option value="Asia/Hong_Kong">香港时间</option>
              <option value="Asia/Taipei">台北时间</option>
              <option value="Asia/Seoul">韩国标准时间</option>
              <option value="Asia/Tokyo">日本标准时间</option>
              <option value="UTC">UTC</option>
            </datalist>
          </label>

          {input.calendar_type === "lunar" && (
            <label className="public-field-wide public-check-field">
              <input
                checked={input.lunar_leap_month}
                type="checkbox"
                onChange={(event) => setInput((current) => ({ ...current, lunar_leap_month: event.target.checked }))}
              />
              <span>这个农历月份是闰月</span>
            </label>
          )}

          <p className="public-form-note public-field-wide">
            系统会据此确定四柱。当前按民用钟表时间计算，不自动换算真太阳时。
          </p>
          {error && <p className="public-form-error public-field-wide" role="alert">{error}</p>}
          <button className="public-primary-button public-field-wide" disabled={saving} type="submit">
            {saving ? "正在建立命盘…" : "生成命盘并开始断命"}
          </button>
        </form>
      </section>
    </div>
  );
}
