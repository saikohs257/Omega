from tools.dvqt_ten_tests import run


def test_ten_directional_battery_executes():
    results = run()
    assert len(results) == 10
    assert all(len(row) == 3 for row in results)
