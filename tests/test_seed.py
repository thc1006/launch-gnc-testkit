from launch_gnc_testkit.seed import SeedTree


def test_named_derivation_is_stable_and_order_independent():
    tree = SeedTree(12345)
    first = tree.derive("sensor", "gyro")
    tree.derive("unrelated")
    assert tree.derive("sensor", "gyro") == first
    assert tree.derive("sensor", "gyro") != tree.derive("sensor", "gnss")


def test_numpy_seed_sequence_reconstructs_stream():
    import numpy as np

    tree = SeedTree("run")
    left = np.random.default_rng(tree.numpy_seed_sequence("wind")).normal(size=5)
    right = np.random.default_rng(tree.numpy_seed_sequence("wind")).normal(size=5)
    assert np.array_equal(left, right)


def test_seed_root_types_are_domain_separated():
    assert SeedTree(65).derive("x") != SeedTree("A").derive("x")
    assert SeedTree("A").derive("x") != SeedTree(b"A").derive("x")


def test_seed_path_types_are_domain_separated():
    tree = SeedTree(1)
    assert tree.derive(1) != tree.derive("1")
