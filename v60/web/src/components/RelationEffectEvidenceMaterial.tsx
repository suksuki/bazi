import { useState, type FormEvent } from "react";

import type { HomeSnapshot } from "../homeApi";
import { isRelationEffectEvidenceMaterialStateDisplayable } from "../homeRelationEffectEvidenceMaterialGuard";
import type {
  HomeRelationEffectEvidenceMaterial,
  RelationEffectEvidenceMaterialBibliography,
} from "../homeRelationEffectEvidenceMaterialTypes";
import type {
  HomeRelationEffectEvidenceRequestedSlot,
  HomeRelationEffectEvidenceRequestItem,
  HomeRelationEffectEvidenceRequestReceipt,
} from "../homeRelationEffectEvidenceRequestTypes";
import { createRelationEffectEvidenceMaterial } from "../relationEffectEvidenceMaterialApi";
import { isRelationEffectMaterialBibliographyValid } from "../relationEffectEvidenceMaterialValidation";

const EMPTY_BIBLIOGRAPHY: RelationEffectEvidenceMaterialBibliography = {
  title: "",
  responsible_party: "",
  edition_or_publication_identity: "",
  locator: "",
};

export function RelationEffectEvidenceMaterialControl({
  home,
  onChanged,
}: {
  home: HomeSnapshot;
  onChanged: () => Promise<void>;
}) {
  const packet = home.mingli.relation_effect_evidence_packet;
  const receipt =
    home.mingli.relation_effect_evidence_request_receipt;
  const materials =
    home.mingli.relation_effect_evidence_materials;
  const safe = isRelationEffectEvidenceMaterialStateDisplayable(
    materials,
    { packet, receipt, lab: home.lab },
  );
  if (!safe) return <Withheld />;
  if (!receipt) return null;

  const targets = receipt.request_items.flatMap((requestItem) =>
    requestItem.dimension_slots
      .filter(
        (slot) => slot.dimension_id === "PROFESSIONAL_PROVENANCE",
      )
      .map((slot) => ({ requestItem, slot })),
  );

  return (
    <section
      aria-label="关系作用候选书目元数据"
      className="relation-effect-evidence-material"
      data-candidate-material-count={materials.length}
      data-effect-decision-status="WITHHELD"
      data-evidence-role="NOT_EVIDENCE"
      data-professional-evidence-count="0"
      data-professional-material-count="0"
      data-ready-dimension-slot-count="0"
    >
      <header>
        <span>
          <small>专业依据维 · 结构化候选登记</small>
          <strong>未核验候选书目元数据</strong>
        </span>
        <em>不是 requested artifact</em>
      </header>

      <div className="relation-effect-evidence-material-counts">
        <span>
          <b>{materials.length}</b>
          候选元数据
        </span>
        <span>
          <b>0</b>
          专业材料
        </span>
        <span>
          <b>0 / {receipt.requested_dimension_slot_count}</b>
          专业证据就绪
        </span>
      </div>

      {materials.length > 0 && (
        <MaterialList materials={materials} />
      )}

      {targets.map(({ requestItem, slot }) => (
        <MaterialForm
          key={`${requestItem.request_item_ref}:${slot.slot_ref}`}
          onChanged={onChanged}
          receipt={receipt}
          requestItem={requestItem}
          slot={slot}
        />
      ))}

      <p className="relation-effect-evidence-material-boundary">
        这里只登记书目坐标候选；不接收文件、URL、引文正文、非结构化备注或专业结论。
        候选尚未核验来源真实性，也不满足
        PROFESSIONAL_SOURCE_MANIFEST；作用 Decision 继续 WITHHELD。
      </p>
    </section>
  );
}

function MaterialForm({
  onChanged,
  receipt,
  requestItem,
  slot,
}: {
  onChanged: () => Promise<void>;
  receipt: HomeRelationEffectEvidenceRequestReceipt;
  requestItem: HomeRelationEffectEvidenceRequestItem;
  slot: HomeRelationEffectEvidenceRequestedSlot;
}) {
  const [bibliography, setBibliography] = useState(
    EMPTY_BIBLIOGRAPHY,
  );
  const [working, setWorking] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const valid =
    isRelationEffectMaterialBibliographyValid(bibliography);

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!valid || working) return;
    setWorking(true);
    setError(null);
    try {
      await createRelationEffectEvidenceMaterial(
        receipt,
        requestItem,
        slot,
        bibliography,
      );
      setBibliography(EMPTY_BIBLIOGRAPHY);
      await onChanged();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : String(cause));
    } finally {
      setWorking(false);
    }
  };

  const update = (
    field: keyof RelationEffectEvidenceMaterialBibliography,
    value: string,
  ) => {
    setBibliography((current) => ({
      ...current,
      [field]: value,
    }));
  };

  return (
    <form
      aria-label="登记未核验候选书目元数据"
      data-candidate-kind="BIBLIOGRAPHIC_COORDINATE_CANDIDATE"
      data-material-command="CREATE"
      data-request-item-ref={requestItem.request_item_ref}
      data-slot-ref={slot.slot_ref}
      data-target-artifact-kind="PROFESSIONAL_SOURCE_MANIFEST"
      onSubmit={(event) => void submit(event)}
    >
      <header>
        <span>
          <small>目标证据维</small>
          <strong>专业依据 · 当前 0 证据</strong>
        </span>
        <em>结构化字段限定</em>
      </header>

      <div>
        <MetadataInput
          label="题名"
          maxLength={240}
          name="title"
          onChange={(value) => update("title", value)}
          placeholder="资料或书目的完整题名"
          value={bibliography.title}
        />
        <MetadataInput
          label="责任者"
          maxLength={180}
          name="responsible_party"
          onChange={(value) => update("responsible_party", value)}
          placeholder="作者、编者或责任机构"
          value={bibliography.responsible_party}
        />
        <MetadataInput
          label="版本／出版身份"
          maxLength={180}
          name="edition_or_publication_identity"
          onChange={(value) =>
            update("edition_or_publication_identity", value)
          }
          placeholder="版次、出版方与可区分身份"
          value={bibliography.edition_or_publication_identity}
        />
        <MetadataInput
          label="定位"
          maxLength={180}
          name="locator"
          onChange={(value) => update("locator", value)}
          placeholder="卷、章、节或页码坐标"
          value={bibliography.locator}
        />
      </div>

      <p>
        目标产物类型为 PROFESSIONAL_SOURCE_MANIFEST；本次登记只产生候选元数据回执，
        不产生该产物。
      </p>
      <button disabled={!valid || working} type="submit">
        {working ? "正在登记…" : "登记候选书目元数据"}
      </button>
      {error && <p role="alert">{error}</p>}
    </form>
  );
}

function MetadataInput({
  label,
  maxLength,
  name,
  onChange,
  placeholder,
  value,
}: {
  label: string;
  maxLength: number;
  name: keyof RelationEffectEvidenceMaterialBibliography;
  onChange: (value: string) => void;
  placeholder: string;
  value: string;
}) {
  return (
    <label>
      <span>{label}</span>
      <input
        autoComplete="off"
        maxLength={maxLength}
        name={name}
        onChange={(event) => onChange(event.target.value)}
        placeholder={placeholder}
        required
        type="text"
        value={value}
      />
    </label>
  );
}

function MaterialList({
  materials,
}: {
  materials: HomeRelationEffectEvidenceMaterial[];
}) {
  return (
    <div
      aria-label="已登记的未核验候选书目元数据"
      className="relation-effect-evidence-material-list"
    >
      {materials.map((material) => (
        <article
          data-material-hash={material.material_hash}
          data-material-ref={material.material_ref}
          data-material-status={material.status}
          key={material.material_ref}
        >
          <header>
            <strong>{material.bibliography.title}</strong>
            <em>未核验候选</em>
          </header>
          <dl>
            <MetadataRow
              label="责任者"
              value={material.bibliography.responsible_party}
            />
            <MetadataRow
              label="版本／出版身份"
              value={
                material.bibliography
                  .edition_or_publication_identity
              }
            />
            <MetadataRow
              label="定位"
              value={material.bibliography.locator}
            />
          </dl>
          <small>
            NOT_EVIDENCE · 未满足 PROFESSIONAL_SOURCE_MANIFEST
          </small>
        </article>
      ))}
    </div>
  );
}

function MetadataRow({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <div>
      <dt>{label}</dt>
      <dd>{value}</dd>
    </div>
  );
}

function Withheld() {
  return (
    <section
      aria-label="候选书目元数据暂不可登记"
      className="relation-effect-evidence-material is-withheld"
      data-material-state="WITHHELD"
    >
      <strong>候选书目元数据暂不展示</strong>
      <p>回执、需求、证据维或材料谱系不完整，页面不会显示或提交元数据。</p>
    </section>
  );
}
