import { useState, type FormEvent } from "react";

import {
  activateOwnerCase,
  createOwnerCase,
  type HomeSnapshot,
  type OwnerCaseInput,
} from "../homeApi";

const INITIAL_INPUT: OwnerCaseInput = {
  display_name: "",
  gender: "male",
  calendar_type: "solar",
  birth_date: "",
  birth_time: "12:00",
  birth_location: "",
  timezone: "Asia/Shanghai",
  lunar_leap_month: false,
  true_solar_time_policy: "not_applied",
};

export function MingliCaseManager({
  home,
  onChanged,
}: {
  home: HomeSnapshot;
  onChanged: () => Promise<void>;
}) {
  const [input, setInput] = useState<OwnerCaseInput>(INITIAL_INPUT);
  const [working, setWorking] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  const activate = async (caseRef: string) => {
    setWorking(true);
    setMessage(null);
    try {
      await activateOwnerCase(caseRef);
      await onChanged();
    } catch (error) {
      setMessage(error instanceof Error ? error.message : String(error));
    } finally {
      setWorking(false);
    }
  };

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setWorking(true);
    setMessage(null);
    try {
      await createOwnerCase(input);
      setInput(INITIAL_INPUT);
      await onChanged();
    } catch (error) {
      setMessage(error instanceof Error ? error.message : String(error));
    } finally {
      setWorking(false);
    }
  };

  return (
    <details className="mingli-case-manager">
      <summary>测算档案</summary>
      <div className="mingli-case-list">
        {home.case_options.map((item) => (
          <button
            data-active={item.active}
            disabled={working || item.active}
            key={item.case_ref}
            onClick={() => void activate(item.case_ref)}
            type="button"
          >
            <span>
              <strong>{item.display_name}</strong>
              <small>
                {Object.values(item.pillars).join(" · ")}
              </small>
            </span>
            <em>{item.active ? "当前" : "切换"}</em>
          </button>
        ))}
      </div>

      <form className="mingli-case-form" onSubmit={(event) => void submit(event)}>
        <h3>新建真实测算</h3>
        <div className="mingli-case-form-grid">
          <label>
            <span>姓名</span>
            <input
              required
              maxLength={80}
              value={input.display_name}
              onChange={(event) =>
                setInput((current) => ({
                  ...current,
                  display_name: event.target.value,
                }))
              }
            />
          </label>
          <label>
            <span>性别</span>
            <select
              value={input.gender}
              onChange={(event) =>
                setInput((current) => ({
                  ...current,
                  gender: event.target.value as OwnerCaseInput["gender"],
                }))
              }
            >
              <option value="male">男</option>
              <option value="female">女</option>
            </select>
          </label>
          <label>
            <span>历法</span>
            <select
              value={input.calendar_type}
              onChange={(event) =>
                setInput((current) => ({
                  ...current,
                  calendar_type: event.target.value as OwnerCaseInput["calendar_type"],
                }))
              }
            >
              <option value="solar">公历</option>
              <option value="lunar">农历</option>
            </select>
          </label>
          <label>
            <span>出生日期</span>
            <input
              required
              type="date"
              value={input.birth_date}
              onChange={(event) =>
                setInput((current) => ({
                  ...current,
                  birth_date: event.target.value,
                }))
              }
            />
          </label>
          <label>
            <span>出生时间</span>
            <input
              required
              type="time"
              value={input.birth_time}
              onChange={(event) =>
                setInput((current) => ({
                  ...current,
                  birth_time: event.target.value,
                }))
              }
            />
          </label>
          {input.calendar_type === "lunar" && (
            <label className="mingli-case-checkbox">
              <input
                checked={input.lunar_leap_month}
                type="checkbox"
                onChange={(event) =>
                  setInput((current) => ({
                    ...current,
                    lunar_leap_month: event.target.checked,
                  }))
                }
              />
              <span>该月为闰月</span>
            </label>
          )}
          <label>
            <span>出生地</span>
            <input
              required
              maxLength={160}
              value={input.birth_location}
              onChange={(event) =>
                setInput((current) => ({
                  ...current,
                  birth_location: event.target.value,
                }))
              }
            />
          </label>
          <label className="is-wide">
            <span>时区</span>
            <select
              value={input.timezone}
              onChange={(event) =>
                setInput((current) => ({
                  ...current,
                  timezone: event.target.value,
                }))
              }
            >
              <option value="Asia/Shanghai">中国标准时间</option>
              <option value="Asia/Seoul">韩国标准时间</option>
              <option value="Asia/Tokyo">日本标准时间</option>
              <option value="UTC">UTC</option>
            </select>
          </label>
        </div>
        <button className="rail-primary-command" disabled={working} type="submit">
          {working ? "正在建立正式命盘…" : "建立命盘并开始测算"}
          <span aria-hidden="true">→</span>
        </button>
        {message && <p role="alert">{message}</p>}
      </form>
    </details>
  );
}
