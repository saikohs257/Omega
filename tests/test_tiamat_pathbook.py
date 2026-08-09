import pytest

from tiamat import PathbookExtractionError, extract_pathbook_routes


def row(ts, episode, mode, burden, **extra):
    return {
        "timestamp": ts,
        "episode_id": episode,
        "mode": mode,
        "ActiveBurden": burden,
        **extra,
    }


def test_pathbook_preserves_path_seats_and_timing_seats():
    rows = [
        row("2026-01-01T00:00:00Z", "e1", "P", 0.20, start_transition_path="2_to_4", topology_path="2_to_4"),
        row("2026-01-01T00:01:00Z", "e1", "H", 0.40, next_trigger_6h=1.0, next_trigger_24h=0.0, next_trigger_48h=0.0),
        row("2026-01-01T01:00:00Z", "e2", "P", 0.30, start_transition_path="3_to_4", topology_path="3_to_4"),
        row("2026-01-01T01:01:00Z", "e2", "H", 0.50),
    ]

    routes = extract_pathbook_routes(rows)

    assert routes[0].start_transition_path == "2_to_4"
    assert routes[0].topology_path == "2_to_4"
    assert routes[0].active_burden == 0.20
    assert routes[0].exit_bridge_deficit == 0.40
    assert routes[0].prior_carry_deficit is None
    assert routes[1].prior_carry_deficit == 0.40
    assert routes[1].exit_bridge_deficit == 0.50


def test_h4_establishes_topology_4_to_4_without_faking_start_path():
    rows = [
        row("2026-01-01T00:00:00Z", "e1", "H", 0.80, head_id="H4"),
    ]
    route = extract_pathbook_routes(rows)[0]
    assert route.topology_path == "4_to_4"
    assert route.start_transition_path is None


def test_4_to_4_cannot_be_fabricated_as_legacy_start_transition():
    rows = [
        row(
            "2026-01-01T00:00:00Z",
            "e1",
            "H",
            0.80,
            head_id="H4",
            start_transition_path="4_to_4",
        )
    ]
    with pytest.raises(PathbookExtractionError, match="legacy start-transition"):
        extract_pathbook_routes(rows)


def test_missing_episode_id_is_rejected_instead_of_inferred():
    with pytest.raises(PathbookExtractionError, match="episode_id"):
        extract_pathbook_routes([
            {"timestamp": "2026-01-01T00:00:00Z", "mode": "H", "ActiveBurden": 0.4}
        ])


def test_unsorted_rows_are_rejected():
    rows = [
        row("2026-01-01T00:01:00Z", "e1", "H", 0.4),
        row("2026-01-01T00:00:00Z", "e1", "P", 0.2),
    ]
    with pytest.raises(PathbookExtractionError, match="timestamp order"):
        extract_pathbook_routes(rows)
