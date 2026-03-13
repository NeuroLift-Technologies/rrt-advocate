from rrt_advocate import ActivationStage, DistressInput, RRTAdvocate


def test_entry_prompt_requires_consent() -> None:
    advocate = RRTAdvocate("user-1")
    response = advocate.assess_interaction(
        user_message="everything is too much",
        distress_input=DistressInput.EVERYTHING_HURTS_MELTDOWN,
        toi_config={"tone": "minimal"},
        consent_granted=False,
    )
    assert response.stage == ActivationStage.STAGE_1_ENTRY
    assert response.consent_required is True
    assert "support" in response.message.lower() or "rrt" in response.message.lower()


def test_meltdown_weights_ash_and_myra() -> None:
    advocate = RRTAdvocate("user-2")
    response = advocate.assess_interaction(
        user_message="everything hurts and I am overwhelmed",
        distress_input=DistressInput.EVERYTHING_HURTS_MELTDOWN,
        toi_config={"tone": "supportive_default"},
        recent_user_messages=["too much", "meltdown"],
        response_latency_seconds=75,
        consent_granted=True,
    )
    assert response.stage == ActivationStage.STAGE_3_REGULATION
    assert response.persona_weights["ash"] > response.persona_weights.get("sol", 0)
    assert response.persona_weights["myra"] > response.persona_weights.get("echo", 0)
    assert "overwhelm" in response.metadata["assessment"]["semantic_hits"]


def test_shutdown_activates_silent_mode() -> None:
    advocate = RRTAdvocate("user-3")
    response = advocate.assess_interaction(
        user_message="don't know blank",
        distress_input=DistressInput.DONT_KNOW_SHUT_DOWN,
        toi_config={"tone": "minimal", "pacing": "minimal"},
        recent_user_messages=["don't know", "don't know"],
        response_latency_seconds=600,
        consent_granted=True,
    )
    assert response.silent_mode is True
    assert response.active_personas[0] == "myra"
    assert len(response.active_personas) <= 2
    assert "Silent mode" in response.message


def test_negative_self_talk_boosts_echo_and_reports_layers() -> None:
    advocate = RRTAdvocate("user-4")
    response = advocate.assess_interaction(
        user_message="I am useless and failing and I hate myself",
        distress_input=DistressInput.CANT_STOP_SELF_BLAME,
        toi_config={"tone": "therapeutic_reflective"},
        recent_user_messages=["I messed up", "I am failing"],
        response_latency_seconds=140,
        consent_granted=True,
    )
    assessment = response.metadata["assessment"]
    assert set(assessment["layer_scores"]) == {"semantic", "sentiment", "behavioral"}
    assert "negative_self_talk" in assessment["semantic_hits"]
    assert response.persona_weights["echo"] == max(response.persona_weights.values())


def test_toi_blocks_kai_even_for_hyperfocus_loop() -> None:
    advocate = RRTAdvocate("user-5")
    response = advocate.assess_interaction(
        user_message="I can't stop the loop and I can't switch away",
        distress_input=DistressInput.STUCK_IN_HYPERFOCUS_LOOP,
        toi_config={
            "tone": "directive",
            "safety_boundaries": {"blocked_personas": ["kai"], "max_active_personas": 2},
        },
        recent_user_messages=["loop", "loop", "loop"],
        response_latency_seconds=45,
        consent_granted=True,
    )
    assert "kai" not in response.active_personas
    assert len(response.active_personas) <= 2
