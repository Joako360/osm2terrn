from __future__ import annotations

from osm2terrn.processing.domain_bridge import road_to_domain_model
from osm2terrn.processing.roads.road_model import Road


def test_road_to_domain_model_converts_processing_road() -> None:
    processing_road = Road(
        points_m=[(0.0, 0.0, 0.0), (10.0, 0.0, 1.0)],
        width=7.0,
        border_width=0.5,
        border_height=0.2,
        type="flat",
        name="Main Street",
        is_bridge=False,
    )

    domain_road = road_to_domain_model(processing_road)

    assert domain_road.width == 7.0
    assert domain_road.metadata["name"] == "Main Street"
    assert domain_road.geometry.points[0].x == 0.0
