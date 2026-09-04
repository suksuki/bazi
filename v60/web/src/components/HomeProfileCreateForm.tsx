import { useState, type FormEvent } from "react";

import type { OwnerCaseInput } from "../publicHomeApi";

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

export function HomeProfileCreateForm({
  saving,
  onCancel,
  onSubmit,
}: {
  saving: boolean;
  onCancel: () => void;
  onSubmit: (input: OwnerCaseInput) => Promise<void>;
}) {
  const [input, setInput] = useState<OwnerCaseInput>(INITIAL_INPUT);

  const submit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    void onSubmit(input);
  };

  return (
    <form className="profile-editor" onSubmit={submit}>
      <header>
        <span>
          <small>NEW LIFECASE</small>
          <strong>新增八字档案</strong>
        </span>
        <button disabled={saving} onClick={onCancel} type="button">
          取消
        </button>
      </header>

      <label>
        <span>档案称呼</span>
        <input
          autoFocus
          maxLength={80}
          placeholder="例如：妈妈、客户 A"
          required
          value={input.display_name}
          onChange={(event) =>
            setInput((current) => ({ ...current, display_name: event.target.value }))
          }
        />
      </label>

      <fieldset>
        <legend>性别</legend>
        {(["male", "female"] as const).map((gender) => (
          <button
            aria-pressed={input.gender === gender}
            className={input.gender === gender ? "is-selected" : ""}
            key={gender}
            onClick={() => setInput((current) => ({ ...current, gender }))}
            type="button"
          >
            {gender === "male" ? "男" : "女"}
          </button>
        ))}
      </fieldset>

      <div className="profile-editor-grid">
        <label>
          <span>历法</span>
          <select
            value={input.calendar_type}
            onChange={(event) =>
              setInput((current) => ({
                ...current,
                calendar_type: event.target.value as OwnerCaseInput["calendar_type"],
                lunar_leap_month:
                  event.target.value === "lunar" ? current.lunar_leap_month : false,
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
              setInput((current) => ({ ...current, birth_date: event.target.value }))
            }
          />
        </label>
      </div>

      <div className="profile-editor-grid">
        <label>
          <span>出生时间</span>
          <input
            required
            type="time"
            value={input.birth_time}
            onChange={(event) =>
              setInput((current) => ({ ...current, birth_time: event.target.value }))
            }
          />
        </label>
        <label>
          <span>出生地</span>
          <input
            maxLength={160}
            placeholder="城市或地区"
            required
            value={input.birth_location}
            onChange={(event) =>
              setInput((current) => ({ ...current, birth_location: event.target.value }))
            }
          />
        </label>
      </div>

      <label>
        <span>时区</span>
        <input
          list="profile-timezones"
          placeholder="例如 Asia/Shanghai"
          required
          value={input.timezone}
          onChange={(event) =>
            setInput((current) => ({ ...current, timezone: event.target.value }))
          }
        />
        <datalist id="profile-timezones">
          <option value="Asia/Shanghai">中国标准时间</option>
          <option value="Asia/Hong_Kong">香港时间</option>
          <option value="Asia/Taipei">台北时间</option>
          <option value="Asia/Seoul">韩国标准时间</option>
          <option value="Asia/Tokyo">日本标准时间</option>
          <option value="UTC">UTC</option>
        </datalist>
      </label>

      {input.calendar_type === "lunar" && (
        <label className="profile-editor-check">
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

      <p className="profile-editor-boundary">
        保存后会先建立真实 Profile、四柱、Case 与 LifeCase，再从同一事实链读取 Reading；系统不会用示例命盘代替你的出生资料。当前使用民用钟表时间，不自动换算真太阳时。
      </p>

      <button className="profile-editor-save" disabled={saving} type="submit">
        {saving ? "正在生长生命叶…" : "保存并生成命理枝"}
      </button>
    </form>
  );
}
