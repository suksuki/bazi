"""Migration-only tools for importing prior-version JSON into V40 contracts."""

from v40.migration.v30_export import V30ExportEnvelope, V30ToV40MigrationPlan
from v40.migration.v30_importer import (
    adapt_advice,
    adapt_signals,
    adapt_verdicts,
    build_product_projection,
    build_runtime_from_v30_export,
)
from v40.migration.admin_v30_profiles import (
    build_admin_account,
    convert_v30_profile_to_v40,
    select_v30_admin_profiles,
    sync_v30_admin_profiles_to_repository,
)

__all__ = [
    "V30ExportEnvelope",
    "V30ToV40MigrationPlan",
    "adapt_advice",
    "adapt_signals",
    "adapt_verdicts",
    "build_admin_account",
    "build_product_projection",
    "build_runtime_from_v30_export",
    "convert_v30_profile_to_v40",
    "select_v30_admin_profiles",
    "sync_v30_admin_profiles_to_repository",
]
