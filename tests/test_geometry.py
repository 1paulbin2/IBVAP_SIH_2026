from analytics.geometry import point_inside_polygon


def test_point_inside_polygon():
    polygon = [
        (0, 0),
        (100, 0),
        (100, 100),
        (0, 100)
    ]

    assert point_inside_polygon((50, 50), polygon) is True
    assert point_inside_polygon((150, 50), polygon) is False
def test_point_on_polygon_boundary():
    polygon = [
        (0, 0),
        (100, 0),
        (100, 100),
        (0, 100)
    ]

    result = point_inside_polygon((0, 50), polygon)

    assert isinstance(result, bool)