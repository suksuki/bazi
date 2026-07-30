from __future__ import annotations

from abu_v60.knowledge.bazi import (
    bazi_candidate_qualification_profile,
    bazi_foundation_profile,
)
from abu_v60.knowledge.contracts import (
    BaziCandidateQualificationProfile,
    BaziFoundationProfile,
    KnowledgeProfileSelection,
)
from abu_v60.knowledge.mechanism_bazi import bazi_mechanism_evidence_profile
from abu_v60.knowledge.mechanism_contracts import BaziMechanismEvidenceProfile
from abu_v60.knowledge.quant_bazi import bazi_quant_foundation_profile
from abu_v60.knowledge.quant_contracts import BaziQuantFoundationProfile
from abu_v60.knowledge.relation_effect_bazi import (
    bazi_relation_effect_admission_policy,
    bazi_zi_wu_automatic_damage_proposal,
)
from abu_v60.knowledge.relation_effect_contracts import (
    BaziRelationEffectAdmissionPolicy,
    BaziRelationEffectRuleProposal,
)
from abu_v60.knowledge.source_review_bazi import (
    bazi_source_coordinate_review_profile,
)
from abu_v60.knowledge.source_review_contracts import (
    BaziSourceCoordinateReviewProfile,
)
from abu_v60.knowledge.timing_bazi import bazi_timing_evidence_profile
from abu_v60.knowledge.timing_contracts import BaziTimingEvidenceProfile


class KnowledgeAuthorityError(ValueError):
    pass


class KnowledgeAuthority:
    """Resolve only exact, versioned and hash-locked knowledge profiles."""

    def __init__(
        self,
        profiles: tuple[BaziFoundationProfile, ...] | None = None,
        candidate_rule_profiles: tuple[BaziCandidateQualificationProfile, ...] | None = None,
        quant_foundation_profiles: tuple[BaziQuantFoundationProfile, ...] | None = None,
        source_review_profiles: tuple[BaziSourceCoordinateReviewProfile, ...] | None = None,
        mechanism_evidence_profiles: tuple[BaziMechanismEvidenceProfile, ...] | None = None,
        timing_evidence_profiles: tuple[BaziTimingEvidenceProfile, ...] | None = None,
        relation_effect_admission_policies: (
            tuple[BaziRelationEffectAdmissionPolicy, ...] | None
        ) = None,
        relation_effect_rule_proposals: (
            tuple[BaziRelationEffectRuleProposal, ...] | None
        ) = None,
        active_selection: KnowledgeProfileSelection | None = None,
    ) -> None:
        admitted = profiles or (bazi_foundation_profile(),)
        self._profiles = {
            (profile.profile_id, profile.profile_version): profile for profile in admitted
        }
        if len(self._profiles) != len(admitted):
            raise KnowledgeAuthorityError("knowledge_profile_identity_not_unique")
        admitted_rule_profiles = candidate_rule_profiles or (
            bazi_candidate_qualification_profile(),
        )
        self._candidate_rule_profiles = {
            (profile.profile_id, profile.profile_version): profile
            for profile in admitted_rule_profiles
        }
        if len(self._candidate_rule_profiles) != len(admitted_rule_profiles):
            raise KnowledgeAuthorityError("candidate_rule_profile_identity_not_unique")
        admitted_quant_profiles = quant_foundation_profiles or (bazi_quant_foundation_profile(),)
        self._quant_foundation_profiles = {
            (profile.profile_id, profile.profile_version): profile
            for profile in admitted_quant_profiles
        }
        if len(self._quant_foundation_profiles) != len(admitted_quant_profiles):
            raise KnowledgeAuthorityError("quant_foundation_profile_identity_not_unique")
        admitted_source_review_profiles = source_review_profiles or (
            bazi_source_coordinate_review_profile(),
        )
        self._source_review_profiles = {
            (profile.profile_id, profile.profile_version): profile
            for profile in admitted_source_review_profiles
        }
        if len(self._source_review_profiles) != len(admitted_source_review_profiles):
            raise KnowledgeAuthorityError("source_review_profile_identity_not_unique")
        admitted_mechanism_profiles = mechanism_evidence_profiles or (
            bazi_mechanism_evidence_profile(),
        )
        self._mechanism_evidence_profiles = {
            (profile.profile_id, profile.profile_version): profile
            for profile in admitted_mechanism_profiles
        }
        if len(self._mechanism_evidence_profiles) != len(admitted_mechanism_profiles):
            raise KnowledgeAuthorityError("mechanism_evidence_profile_identity_not_unique")
        admitted_timing_profiles = timing_evidence_profiles or (bazi_timing_evidence_profile(),)
        self._timing_evidence_profiles = {
            (profile.profile_id, profile.profile_version): profile
            for profile in admitted_timing_profiles
        }
        if len(self._timing_evidence_profiles) != len(admitted_timing_profiles):
            raise KnowledgeAuthorityError("timing_evidence_profile_identity_not_unique")
        requested_relation_effect_policies = (
            (bazi_relation_effect_admission_policy(),)
            if relation_effect_admission_policies is None
            else relation_effect_admission_policies
        )
        admitted_relation_effect_policies = tuple(
            BaziRelationEffectAdmissionPolicy.model_validate(
                policy.model_dump(mode="python")
            )
            for policy in requested_relation_effect_policies
        )
        self._relation_effect_admission_policies = {
            (policy.policy_ref, policy.policy_version): policy
            for policy in admitted_relation_effect_policies
        }
        if len(self._relation_effect_admission_policies) != len(
            admitted_relation_effect_policies
        ):
            raise KnowledgeAuthorityError(
                "relation_effect_admission_policy_identity_not_unique"
            )
        requested_relation_effect_proposals = (
            (bazi_zi_wu_automatic_damage_proposal(),)
            if relation_effect_rule_proposals is None
            else relation_effect_rule_proposals
        )
        admitted_relation_effect_proposals = tuple(
            BaziRelationEffectRuleProposal.model_validate(
                proposal.model_dump(mode="python")
            )
            for proposal in requested_relation_effect_proposals
        )
        self._relation_effect_rule_proposals = {
            (proposal.proposal_ref, proposal.proposal_version): proposal
            for proposal in admitted_relation_effect_proposals
        }
        if len(self._relation_effect_rule_proposals) != len(
            admitted_relation_effect_proposals
        ):
            raise KnowledgeAuthorityError(
                "relation_effect_rule_proposal_identity_not_unique"
            )
        self._active_selection = active_selection or KnowledgeProfileSelection.from_profiles(
            foundation=bazi_foundation_profile(),
            candidate_rules=bazi_candidate_qualification_profile(),
            quant_foundation=bazi_quant_foundation_profile(),
            source_review=bazi_source_coordinate_review_profile(),
            mechanism_evidence=bazi_mechanism_evidence_profile(),
            timing_evidence=bazi_timing_evidence_profile(),
        )
        self.active_foundation_profile()
        self.active_candidate_rule_profile()
        self.active_quant_foundation_profile()
        self.active_source_review_profile()
        self.active_mechanism_evidence_profile()
        self.active_timing_evidence_profile()

    def resolve(
        self,
        *,
        profile_id: str,
        profile_version: str,
        expected_hash: str | None = None,
    ) -> BaziFoundationProfile:
        profile = self._profiles.get((profile_id, profile_version))
        if profile is None:
            raise KnowledgeAuthorityError("knowledge_profile_not_admitted")
        if expected_hash is not None and expected_hash != profile.profile_hash:
            raise KnowledgeAuthorityError("knowledge_profile_hash_mismatch")
        return profile

    def public_manifest(self) -> list[dict[str, object]]:
        return [
            {
                "profile_id": profile.profile_id,
                "profile_version": profile.profile_version,
                "profile_hash": profile.profile_hash,
                "governance_status": profile.governance_status,
                "runtime_scope": profile.runtime_scope,
                "professionally_reviewed": profile.professionally_reviewed,
                "source_refs": list(profile.source_refs),
                "active": (
                    profile.profile_id == self._active_selection.foundation_profile_id
                    and profile.profile_version == self._active_selection.foundation_profile_version
                ),
            }
            for profile in sorted(
                self._profiles.values(),
                key=lambda item: (item.profile_id, item.profile_version),
            )
        ]

    def resolve_candidate_rule_profile(
        self,
        *,
        profile_id: str,
        profile_version: str,
        expected_hash: str | None = None,
    ) -> BaziCandidateQualificationProfile:
        profile = self._candidate_rule_profiles.get((profile_id, profile_version))
        if profile is None:
            raise KnowledgeAuthorityError("candidate_rule_profile_not_admitted")
        if expected_hash is not None and expected_hash != profile.profile_hash:
            raise KnowledgeAuthorityError("candidate_rule_profile_hash_mismatch")
        return profile

    def candidate_rule_manifest(self) -> list[dict[str, object]]:
        return [
            {
                "profile_id": profile.profile_id,
                "profile_version": profile.profile_version,
                "profile_hash": profile.profile_hash,
                "governance_status": profile.governance_status,
                "runtime_scope": profile.runtime_scope,
                "professionally_reviewed": profile.professionally_reviewed,
                "source_refs": list(profile.source_refs),
                "rule_refs": [rule.rule_ref for rule in profile.rules],
                "active": (
                    profile.profile_id == self._active_selection.candidate_rule_profile_id
                    and profile.profile_version
                    == self._active_selection.candidate_rule_profile_version
                ),
            }
            for profile in sorted(
                self._candidate_rule_profiles.values(),
                key=lambda item: (item.profile_id, item.profile_version),
            )
        ]

    def resolve_quant_foundation_profile(
        self,
        *,
        profile_id: str,
        profile_version: str,
        expected_hash: str | None = None,
    ) -> BaziQuantFoundationProfile:
        profile = self._quant_foundation_profiles.get((profile_id, profile_version))
        if profile is None:
            raise KnowledgeAuthorityError("quant_foundation_profile_not_admitted")
        if expected_hash is not None and expected_hash != profile.profile_hash:
            raise KnowledgeAuthorityError("quant_foundation_profile_hash_mismatch")
        return profile

    def quant_foundation_manifest(self) -> list[dict[str, object]]:
        return [
            {
                "profile_id": profile.profile_id,
                "profile_version": profile.profile_version,
                "profile_hash": profile.profile_hash,
                "governance_status": profile.governance_status,
                "runtime_scope": profile.runtime_scope,
                "professionally_reviewed": profile.professionally_reviewed,
                "source_refs": list(profile.source_refs),
                "calibration_status": profile.calibration_status,
                "active": (
                    profile.profile_id == self._active_selection.quant_foundation_profile_id
                    and profile.profile_version
                    == self._active_selection.quant_foundation_profile_version
                ),
            }
            for profile in sorted(
                self._quant_foundation_profiles.values(),
                key=lambda item: (item.profile_id, item.profile_version),
            )
        ]

    def resolve_source_review_profile(
        self,
        *,
        profile_id: str,
        profile_version: str,
        expected_hash: str | None = None,
    ) -> BaziSourceCoordinateReviewProfile:
        profile = self._source_review_profiles.get((profile_id, profile_version))
        if profile is None:
            raise KnowledgeAuthorityError("source_review_profile_not_admitted")
        if expected_hash is not None and expected_hash != profile.profile_hash:
            raise KnowledgeAuthorityError("source_review_profile_hash_mismatch")
        return profile

    def source_review_manifest(self) -> list[dict[str, object]]:
        return [
            {
                "profile_id": profile.profile_id,
                "profile_version": profile.profile_version,
                "profile_hash": profile.profile_hash,
                "governance_status": profile.governance_status,
                "runtime_scope": profile.runtime_scope,
                "professionally_reviewed": profile.professionally_reviewed,
                "source_refs": list(profile.source_refs),
                "rule_refs": [rule.rule_ref for rule in profile.rules],
                "active": (
                    profile.profile_id == self._active_selection.source_review_profile_id
                    and profile.profile_version
                    == self._active_selection.source_review_profile_version
                ),
            }
            for profile in sorted(
                self._source_review_profiles.values(),
                key=lambda item: (item.profile_id, item.profile_version),
            )
        ]

    def active_foundation_profile(self) -> BaziFoundationProfile:
        return self.resolve(
            profile_id=self._active_selection.foundation_profile_id,
            profile_version=self._active_selection.foundation_profile_version,
            expected_hash=self._active_selection.foundation_profile_hash,
        )

    def active_candidate_rule_profile(self) -> BaziCandidateQualificationProfile:
        return self.resolve_candidate_rule_profile(
            profile_id=self._active_selection.candidate_rule_profile_id,
            profile_version=self._active_selection.candidate_rule_profile_version,
            expected_hash=self._active_selection.candidate_rule_profile_hash,
        )

    def active_quant_foundation_profile(self) -> BaziQuantFoundationProfile:
        return self.resolve_quant_foundation_profile(
            profile_id=self._active_selection.quant_foundation_profile_id,
            profile_version=self._active_selection.quant_foundation_profile_version,
            expected_hash=self._active_selection.quant_foundation_profile_hash,
        )

    def active_source_review_profile(
        self,
    ) -> BaziSourceCoordinateReviewProfile:
        return self.resolve_source_review_profile(
            profile_id=self._active_selection.source_review_profile_id,
            profile_version=self._active_selection.source_review_profile_version,
            expected_hash=self._active_selection.source_review_profile_hash,
        )

    def resolve_mechanism_evidence_profile(
        self,
        *,
        profile_id: str,
        profile_version: str,
        expected_hash: str | None = None,
    ) -> BaziMechanismEvidenceProfile:
        profile = self._mechanism_evidence_profiles.get((profile_id, profile_version))
        if profile is None:
            raise KnowledgeAuthorityError("mechanism_evidence_profile_not_admitted")
        if expected_hash is not None and expected_hash != profile.profile_hash:
            raise KnowledgeAuthorityError("mechanism_evidence_profile_hash_mismatch")
        return profile

    def mechanism_evidence_manifest(self) -> list[dict[str, object]]:
        return [
            {
                "profile_id": profile.profile_id,
                "profile_version": profile.profile_version,
                "profile_hash": profile.profile_hash,
                "governance_status": profile.governance_status,
                "runtime_scope": profile.runtime_scope,
                "professionally_reviewed": profile.professionally_reviewed,
                "source_refs": list(profile.source_refs),
                "pattern_refs": [pattern.pattern_ref for pattern in profile.patterns],
                "active": (
                    profile.profile_id == self._active_selection.mechanism_evidence_profile_id
                    and profile.profile_version
                    == self._active_selection.mechanism_evidence_profile_version
                ),
            }
            for profile in sorted(
                self._mechanism_evidence_profiles.values(),
                key=lambda item: (item.profile_id, item.profile_version),
            )
        ]

    def active_mechanism_evidence_profile(
        self,
    ) -> BaziMechanismEvidenceProfile:
        return self.resolve_mechanism_evidence_profile(
            profile_id=self._active_selection.mechanism_evidence_profile_id,
            profile_version=(self._active_selection.mechanism_evidence_profile_version),
            expected_hash=(self._active_selection.mechanism_evidence_profile_hash),
        )

    def resolve_timing_evidence_profile(
        self,
        *,
        profile_id: str,
        profile_version: str,
        expected_hash: str | None = None,
    ) -> BaziTimingEvidenceProfile:
        profile = self._timing_evidence_profiles.get((profile_id, profile_version))
        if profile is None:
            raise KnowledgeAuthorityError("timing_evidence_profile_not_admitted")
        if expected_hash is not None and expected_hash != profile.profile_hash:
            raise KnowledgeAuthorityError("timing_evidence_profile_hash_mismatch")
        return profile

    def timing_evidence_manifest(self) -> list[dict[str, object]]:
        return [
            {
                "profile_id": profile.profile_id,
                "profile_version": profile.profile_version,
                "profile_hash": profile.profile_hash,
                "governance_status": profile.governance_status,
                "runtime_scope": profile.runtime_scope,
                "professionally_reviewed": profile.professionally_reviewed,
                "source_refs": list(profile.source_refs),
                "calendar_engine_version": profile.calendar_engine_version,
                "active": (
                    profile.profile_id == self._active_selection.timing_evidence_profile_id
                    and profile.profile_version
                    == self._active_selection.timing_evidence_profile_version
                ),
            }
            for profile in sorted(
                self._timing_evidence_profiles.values(),
                key=lambda item: (item.profile_id, item.profile_version),
            )
        ]

    def active_timing_evidence_profile(self) -> BaziTimingEvidenceProfile:
        return self.resolve_timing_evidence_profile(
            profile_id=self._active_selection.timing_evidence_profile_id,
            profile_version=self._active_selection.timing_evidence_profile_version,
            expected_hash=self._active_selection.timing_evidence_profile_hash,
        )

    def relation_effect_rule_admission_manifest(
        self,
    ) -> dict[str, object]:
        policy = bazi_relation_effect_admission_policy()
        proposal = bazi_zi_wu_automatic_damage_proposal()
        resolved_policy = self.resolve_relation_effect_admission_policy(
            policy_ref=policy.policy_ref,
            policy_version=policy.policy_version,
            expected_hash=policy.policy_hash,
        )
        resolved_proposal = self.resolve_relation_effect_rule_proposal(
            proposal_ref=proposal.proposal_ref,
            proposal_version=proposal.proposal_version,
            expected_hash=proposal.proposal_hash,
        )

        return {
            "policy": resolved_policy.model_dump(mode="json"),
            "proposal": resolved_proposal.model_dump(mode="json"),
            "admitted_effect_rule_profiles": [],
            "professional_rule_count": 0,
            "runtime_effect_authority": "NONE",
        }

    def resolve_relation_effect_admission_policy(
        self,
        *,
        policy_ref: str,
        policy_version: str,
        expected_hash: str | None = None,
    ) -> BaziRelationEffectAdmissionPolicy:
        policy = self._relation_effect_admission_policies.get(
            (policy_ref, policy_version)
        )
        if policy is None:
            raise KnowledgeAuthorityError(
                "relation_effect_admission_policy_not_registered"
            )
        policy = BaziRelationEffectAdmissionPolicy.model_validate(
            policy.model_dump(mode="python")
        )
        if expected_hash is not None and policy.policy_hash != expected_hash:
            raise KnowledgeAuthorityError(
                "relation_effect_admission_policy_hash_mismatch"
            )
        return policy

    def resolve_relation_effect_rule_proposal(
        self,
        *,
        proposal_ref: str,
        proposal_version: str,
        expected_hash: str | None = None,
    ) -> BaziRelationEffectRuleProposal:
        proposal = self._relation_effect_rule_proposals.get(
            (proposal_ref, proposal_version)
        )
        if proposal is None:
            raise KnowledgeAuthorityError(
                "relation_effect_rule_proposal_not_registered"
            )
        proposal = BaziRelationEffectRuleProposal.model_validate(
            proposal.model_dump(mode="python")
        )
        if (
            expected_hash is not None
            and proposal.proposal_hash != expected_hash
        ):
            raise KnowledgeAuthorityError(
                "relation_effect_rule_proposal_hash_mismatch"
            )
        return proposal

    def selection_manifest(self) -> dict[str, object]:
        return self._active_selection.public_manifest()
