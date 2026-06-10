"""関節可動域検査のテスト（bpy 不要）。"""
from scripts.lib.anatomy import PARAM_TO_JOINT, check_pose, load_anatomy


def test_valid_human_pose_passes():
    pose = {"lean_deg": 14, "hip_pitch_deg": 12, "knee_bend_deg": 20,
            "shoulder_pitch_deg": 20, "elbow_bend_deg": 55}
    assert check_pose(pose, species="human") == []


def test_knee_hyperextension_is_violation():
    violations = check_pose({"knee_bend_deg": -10}, species="human")
    assert len(violations) == 1
    v = violations[0]
    assert v["joint"] == "knee" and v["bound"] == "min" and v["limit"] == 0


def test_elbow_over_flexion_is_violation():
    violations = check_pose({"elbow_bend_deg": 160}, species="human")
    assert violations[0]["bound"] == "max" and violations[0]["limit"] == 145


def test_quadruped_uses_canine_mapping():
    # stifle は常に屈曲位（min 20°）— 0° は違反
    violations = check_pose({"stifle_deg": 0}, species="quadruped_canine")
    assert violations[0]["joint"] == "stifle" and violations[0]["bound"] == "min"


def test_all_mapped_joints_exist_in_knowledge_base():
    anatomy = load_anatomy()
    for species, mapping in PARAM_TO_JOINT.items():
        joints = anatomy[species]["joints"]
        for param, joint in mapping.items():
            assert joint in joints, f"{species}.{joint} ({param}) が anatomy.yaml にない"
            j = joints[joint]
            assert j["min_deg"] < j["max_deg"]
