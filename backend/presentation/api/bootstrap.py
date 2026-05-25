from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from config import settings
from infrastructure.bootstrap.container_seed import seed_container_workspace
from infrastructure.persistence.database import get_db
from infrastructure.persistence.seed import seed_database
from presentation.schemas import BootstrapStatusSchema

router = APIRouter(prefix="/bootstrap", tags=["bootstrap"])


@router.get("/status", response_model=BootstrapStatusSchema)
def bootstrap_status(db: Session = Depends(get_db)):
    workspace = seed_container_workspace()
    seeded = seed_database(db) if settings.seed_on_startup else 0
    return BootstrapStatusSchema(database_seeded=seeded, container_workspace=workspace)
