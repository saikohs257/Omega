from atlas.hypercube import HypercubeAtlas


def test_hypercube_projection_is_deterministic() -> None:
    atlas = HypercubeAtlas(dimensions=4)
    left = atlas.project({"axis_0": 1, "axis_2": 1})
    right = atlas.project({"axis_2": 1, "axis_0": 1})
    assert left == right == (1, 0, 1, 0)


def test_hypercube_neighbors_flip_single_axes() -> None:
    atlas = HypercubeAtlas(dimensions=3)
    coordinate = (0, 1, 0)
    neighbors = atlas.get_neighbors(coordinate)
    assert len(neighbors) == 3
    assert set(neighbors) == {(1, 1, 0), (0, 0, 0), (0, 1, 1)}
    chart = atlas.local_chart(coordinate)
    assert chart.origin == coordinate
    assert chart.neighbors == neighbors


def test_hypercube_distance_is_manhattan() -> None:
    atlas = HypercubeAtlas(dimensions=3)
    assert atlas.distance((0, 1, 0), (1, 0, 1)) == 3
