import { useEffect, useMemo, useRef, useState } from "react";

import { AbuIdle } from "../AbuIdle";
import type { MingliFocusedPassRecord, MingliStageProjection } from "../mingliStageTypes";
import type { PublicReadingCopy } from "../publicReadingPresentation";
import type { RuntimeMediaCue } from "../publicRuntimeTypes";
import { loadFocusedPassSpeech } from "../publicSpeechApi";

type SpeechState = "IDLE" | "PREPARING" | "PLAYING" | "PAUSED" | "FALLBACK" | "ERROR";

export function PublicAbuSays({
  cue,
  stage,
  record,
  copy,
  topicLabel,
  generating,
}: {
  cue: RuntimeMediaCue;
  stage: MingliStageProjection;
  record: MingliFocusedPassRecord | null;
  copy: PublicReadingCopy;
  topicLabel: string;
  generating: boolean;
}) {
  const [speechState, setSpeechState] = useState<SpeechState>("IDLE");
  const [speechNote, setSpeechNote] = useState<string | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const objectUrlRef = useRef<string | null>(null);
  const speechText = useMemo(
    () => [copy.lead, ...copy.paragraphs].filter(Boolean).join("\n"),
    [copy.lead, copy.paragraphs],
  );

  useEffect(() => {
    return () => {
      audioRef.current?.pause();
      audioRef.current = null;
      if (objectUrlRef.current) URL.revokeObjectURL(objectUrlRef.current);
      objectUrlRef.current = null;
      window.speechSynthesis?.cancel();
    };
  }, [speechText, record?.record_ref]);

  const speakWithBrowser = () => {
    if (!("speechSynthesis" in window)) {
      setSpeechState("ERROR");
      setSpeechNote("声音暂时不可用，文字仍可正常阅读。");
      return;
    }
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(speechText);
    utterance.lang = "zh-CN";
    utterance.rate = 0.92;
    utterance.pitch = 1.03;
    utterance.onstart = () => setSpeechState("FALLBACK");
    utterance.onend = () => setSpeechState("IDLE");
    utterance.onerror = () => {
      setSpeechState("ERROR");
      setSpeechNote("声音暂时不可用，文字仍可正常阅读。");
    };
    setSpeechNote("专属声音暂时没有接通，已改用设备中文语音。");
    window.speechSynthesis.speak(utterance);
  };

  const toggleSpeech = async () => {
    const current = audioRef.current;
    if (current) {
      if (current.paused) {
        await current.play();
        setSpeechState("PLAYING");
      } else {
        current.pause();
        setSpeechState("PAUSED");
      }
      return;
    }
    if (speechState === "FALLBACK") {
      window.speechSynthesis.cancel();
      setSpeechState("IDLE");
      return;
    }
    if (!record) {
      speakWithBrowser();
      return;
    }

    setSpeechState("PREPARING");
    setSpeechNote("阿布正在准备声音，文字不用等。");
    try {
      const speech = await loadFocusedPassSpeech(stage, record);
      const objectUrl = URL.createObjectURL(speech.blob);
      objectUrlRef.current = objectUrl;
      const audio = new Audio(objectUrl);
      audioRef.current = audio;
      audio.onplay = () => setSpeechState("PLAYING");
      audio.onpause = () => {
        if (!audio.ended) setSpeechState("PAUSED");
      };
      audio.onended = () => setSpeechState("IDLE");
      audio.onerror = () => speakWithBrowser();
      setSpeechNote(null);
      await audio.play();
    } catch {
      audioRef.current = null;
      speakWithBrowser();
    }
  };

  const controlLabel = speechState === "PREPARING"
    ? "准备声音…"
    : speechState === "PLAYING" || speechState === "FALLBACK"
      ? "暂停"
      : speechState === "PAUSED"
        ? "继续"
        : "听阿布说";

  return (
    <section className="public-abu-stage" aria-label={`阿布说：${topicLabel}`}>
      <div className="public-abu-visual" aria-hidden="true">
        <span className="public-abu-orbit public-abu-orbit-one" />
        <span className="public-abu-orbit public-abu-orbit-two" />
        <AbuIdle className="public-abu-character" cue={cue} label="阿布" />
        <div className="public-abu-nameplate">
          <strong>阿布</strong>
          <span>陪你把命盘读明白</span>
        </div>
      </div>

      <div className="public-abu-dialogue">
        <header>
          <div>
            <p className="public-kicker">阿布说 · {topicLabel}</p>
            <h2>{generating ? "我正在细看这一层…" : "我先说最重要的。"}</h2>
          </div>
          <button
            className="public-audio-button"
            disabled={generating || speechState === "PREPARING"}
            onClick={() => void toggleSpeech()}
            type="button"
          >
            <span aria-hidden="true">{speechState === "PLAYING" || speechState === "FALLBACK" ? "Ⅱ" : "▶"}</span>
            {controlLabel}
          </button>
        </header>

        <div className="public-speech-bubble" aria-live="polite">
          <strong>{generating ? "命局的基础结论已经可看，细断正在补全。" : copy.lead}</strong>
          {!generating && copy.paragraphs.map((paragraph) => <p key={paragraph}>{paragraph}</p>)}
          {generating && <p>你可以留在这里，新的断语出来后会自动替换，不需要反复点击。</p>}
        </div>
        {speechNote && <p className="public-speech-note" role="status">{speechNote}</p>}
      </div>
    </section>
  );
}
