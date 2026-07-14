import pytest

from osm2terrn.domain.entities.bbox import BBox


def test_bbox_sequence_requires_numeric_values():
    with pytest.raises(ValueError, match="must be numeric"):
        BBox((0, "a", 1, 2))


def test_bbox_rejects_invalid_coordinate_order():
    with pytest.raises(ValueError, match="west < east"):
        BBox((2, 0, 1, 3))


def test_bbox_dict_supports_alternative_keys():
    b = BBox({"left": -10, "bottom": -5, "right": 10, "top": 5})
    assert b.to_tuple() == (-10.0, -5.0, 10.0, 5.0)
    assert b.is_projected is False
