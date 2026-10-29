from qiqi_town.world.nav import NavGrid


def _grid(rows: list[str]) -> NavGrid:
    walkable = [[ch == "." for ch in row] for row in rows]
    return NavGrid(walkable, origin=(0.0, 0.0), cell_size=1.0)


def test_path_on_open_grid() -> None:
    nav = _grid([".....", ".....", "....."])
    path = nav.find_path((0.5, 0.5), (4.5, 2.5))
    assert path
    assert path[0] == (0.5, 0.5)
    assert path[-1] == (4.5, 2.5)


def test_path_goes_around_wall() -> None:
    nav = _grid(
        [
            ".....",
            "..#..",
            "..#..",
            "..#..",
            ".....",
        ]
    )
    path = nav.find_path((0.5, 2.5), (4.5, 2.5))
    assert path
    assert all(nav.is_walkable(point) for point in path)
    assert not any(1.9 < x < 3.1 and y == 2.5 for x, y in path)


def test_unreachable_goal_returns_nearest() -> None:
    nav = _grid([".....", "..#..", "....."])
    path = nav.find_path((0.5, 0.5), (2.5, 1.5))
    assert path
    # 目标格是墙，最近可走点会落到旁边。
    assert nav.is_walkable(path[-1])


def test_nearest_walkable() -> None:
    nav = _grid(["##.", "#.."])
    point = nav.nearest_walkable((0.5, 0.5))
    assert point is not None
    assert nav.is_walkable(point)
    assert nav.nearest_walkable((1.5, 1.5)) == (1.5, 1.5)


def test_no_path_between_separate_areas() -> None:
    nav = _grid(
        [
            "###....",
            "#.#....",
            "###....",
        ]
    )
    assert nav.find_path((1.5, 1.5), (5.5, 1.5)) == []
