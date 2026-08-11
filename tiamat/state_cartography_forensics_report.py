"""Run the State Cartography divergence-forensics experiment."""
from __future__ import annotations

from .state_cartography_worlds import build_forensic_episodes
from tools.divergence_forensics import analyze, candidate_pre_divergence_differences, summarize


def run() -> list[dict]:
    rows: list[dict] = []
    for episode in build_forensic_episodes():
        findings = analyze(
            episode.left,
            episode.right,
            similarity_threshold=0.2,
            divergence_threshold=0.5,
        )
        summary = summarize(findings)
        candidate_scores: dict[str, list[float]] = {}
        for finding in findings:
            if finding.divergence_horizon is None:
                continue
            for name, score in candidate_pre_divergence_differences(
                episode.dimensions_left,
                episode.dimensions_right,
                left=finding.left,
                right=finding.right,
            ):
                candidate_scores.setdefault(name, []).append(score)
        ranked = sorted(
            ((name, sum(values) / len(values)) for name, values in candidate_scores.items()),
            key=lambda item: item[1],
            reverse=True,
        )
        rows.append(
            {
                "world": episode.world,
                "similar_state_pairs": summary["similar_state_pairs"],
                "consistent_futures": summary["consistent_futures"],
                "divergent_futures": summary["divergent_futures"],
                "horizons": summary["divergence_horizon_distribution"],
                "top_pre_divergence_dimensions": ranked,
                "expected_missing_dimension": episode.expected_missing,
            }
        )
    return rows


def main() -> None:
    print("STATE CARTOGRAPHY DIVERGENCE FORENSICS")
    for row in run():
        print(f"WORLD {row['world']}")
        print(
            f"  similar={row['similar_state_pairs']} "
            f"consistent={row['consistent_futures']} "
            f"divergent={row['divergent_futures']} "
            f"horizons={row['horizons']}"
        )
        print(f"  candidates={row['top_pre_divergence_dimensions']}")
        print(f"  expected_missing={row['expected_missing_dimension']}")


if __name__ == "__main__":
    main()
