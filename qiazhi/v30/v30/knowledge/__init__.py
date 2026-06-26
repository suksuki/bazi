"""V30 knowledge pack loading."""

from v30.knowledge.library import (
    KRP_LIBRARY_PACK_ID,
    KRP_LIBRARY_PACK_VERSION,
    KRP_LIBRARY_UNITS,
    KnowledgeRulePortraitUnit,
    match_krp_library_units,
    summarize_krp_library_units,
)
from v30.knowledge.loaders import (
    CORE_MACRO_PACK_ID,
    CORE_MACRO_PACK_VERSION,
    MacroKnowledgePack,
    MacroKnowledgePackItem,
    MacroDimensionSignal,
    build_macro_dimension_signals,
    load_core_macro_pack,
    summarize_core_macro_pack,
)
from v30.knowledge.seed_registry import (
    KnowledgeRulePortraitSignal,
    build_knowledge_rule_portrait_signals,
)
from v30.knowledge.source_registry import (
    SOURCE_REGISTRY_VERSION,
    KnowledgeSourceFamily,
    list_source_families,
    summarize_source_registry,
)
from v30.knowledge.v20_reference_registry import (
    V20_REFERENCE_REGISTRY_VERSION,
    V20ReferenceAsset,
    list_v20_reference_assets,
    summarize_v20_reference_registry,
)

__all__ = [
    "KRP_LIBRARY_UNITS",
    "KRP_LIBRARY_PACK_ID",
    "KRP_LIBRARY_PACK_VERSION",
    "CORE_MACRO_PACK_ID",
    "CORE_MACRO_PACK_VERSION",
    "KnowledgeRulePortraitSignal",
    "KnowledgeRulePortraitUnit",
    "KnowledgeSourceFamily",
    "MacroKnowledgePack",
    "MacroKnowledgePackItem",
    "MacroDimensionSignal",
    "SOURCE_REGISTRY_VERSION",
    "V20_REFERENCE_REGISTRY_VERSION",
    "V20ReferenceAsset",
    "build_macro_dimension_signals",
    "build_knowledge_rule_portrait_signals",
    "list_source_families",
    "list_v20_reference_assets",
    "load_core_macro_pack",
    "match_krp_library_units",
    "summarize_core_macro_pack",
    "summarize_krp_library_units",
    "summarize_source_registry",
    "summarize_v20_reference_registry",
]
