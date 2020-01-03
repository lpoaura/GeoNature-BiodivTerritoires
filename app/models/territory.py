from app.utils import create_mat_view
from app import db
from app.models.synthese import CorAreaSynthese, Synthese
from app.models.ref_geo import LAreas
from sqlalchemy import func, distinct
from sqlalchemy.sql import select


class VMTerritoryGeneralStats(db.Model):
    __table_args__ = {"schema": "gn_biodivterritory"}
    __table__ = create_mat_view(
        "vm_territory_general_stats",
        select(
            [
                LAreas.area_code,
                func.count(distinct(Synthese.id_synthese)).label("count_occtax"),
                func.count(distinct(Synthese.cd_nom).label("count_taxa")),
            ]
        )
        .group_by(LAreas.id_area)
        .join(CorAreaSynthese, CorAreaSynthese.id_area == LAreas.id_area, isouter=True)
        .join(
            Synthese, CorAreaSynthese.id_synthese == Synthese.id_synthese, isouter=True
        ),
    )
