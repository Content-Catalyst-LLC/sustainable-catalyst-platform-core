from app.database import Database
from app.migrations import run_migrations,migration_status
from app.services.cross_product_visual_runtime_integration import CONTRACT,boundaries,PRODUCTS
import os
db=Database(os.environ["SC_CORE_DATABASE_URL"]);run_migrations(db);s=migration_status(db);b=boundaries();assert "0075" in s["applied"] and not s["pending"];assert CONTRACT=="sc.visual-runtime.cross-product-integration.v1";assert len(PRODUCTS)==7;assert b["product_integration_registry_by_core"] and b["render_by_core"] is False and b["compute_by_core"] is False and b["automatic_cross_product_sync"] is False
print("PASS - Platform Core v2.71.0 Cross-Product Visual Runtime Integration invariants")
