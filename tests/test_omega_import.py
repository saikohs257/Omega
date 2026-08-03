def test_omega_package_exports_core_symbols() -> None:
    import omega

    assert hasattr(omega, "BentAxisStore")
    assert hasattr(omega, "ColonyScheduler")
    assert hasattr(omega, "HypercubeAtlas")
    assert hasattr(omega, "Hypergraph")
    assert hasattr(omega, "SimplicialComplex")
    assert hasattr(omega, "Sheaf")
    assert hasattr(omega, "TiamatEngine")
    assert hasattr(omega, "Court")
    assert hasattr(omega, "Oracle")
