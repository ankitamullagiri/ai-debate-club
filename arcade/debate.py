from arcade.llm import ask_llm


def debater_turn(side: str, topic: str, transcript: list[str], model: str) -> str:
    stance = "FOR" if side == "PRO" else "AGAINST"
    system_prompt = (
        f"You are the {side} debater. You argue {stance} the topic. "
        "Be persuasive and concise: at most 4 sentences. "
        "Directly rebut your opponent's latest points when there are any."
    )

    history = "\n\n".join(transcript) if transcript else "(No arguments yet. You go first.)"
    user_prompt = f"Topic: {topic}\n\nDebate so far:\n{history}\n\nGive your next argument."

    return ask_llm(system_prompt, user_prompt, model=model)


def run_debate(topic: str, pro_model: str, con_model: str, rounds: int = 3) -> list[str]:
    transcript = []
    for round_num in range(1, rounds + 1):
        for side, model in [("PRO", pro_model), ("CON", con_model)]:
            argument = debater_turn(side, topic, transcript, model)
            transcript.append(f"{side} (round {round_num}): {argument}")
            print(transcript[-1], "\n")
    return transcript
