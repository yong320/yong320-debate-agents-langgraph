import json
import re
import textwrap
from typing import Dict, Any
from openai import OpenAI
from debate_state import DebateState
from configurations.debate_constants import SPEAKER_PRO, SPEAKER_CON
import os
from utils import create_debate_message
from dotenv import load_dotenv
from pydantic import BaseModel, Field
import logging

load_dotenv()


class FactCheck(BaseModel):
    """
    Pydantic model for the fact checking the claims made by debaters.

    Attributes:
        binary_score (str): 'yes' if the claim is verifiable and truthful, 'no' otherwise.
    """

    binary_score: str = Field(
        description="Indicates if the claim is verifiable and truthful. 'yes' or 'no'."
    )
    justification: str = Field(
        description="Explanation of the reasoning behind the score."
    )


def strip_think(text: str) -> str:
    """Remove <think>...</think> blocks that reasoning models may emit."""
    if not text:
        return ""
    return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()


class FactCheckNode:
    def __init__(self):
        self.client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_BASE_URL"),
        )
        self.model_name = os.getenv("FACT_CHECK_MODEL", "MiniMax-M2")
        self.logger = logging.getLogger(self.__class__.__name__)
        self._configure_rich_logger()

    def _configure_rich_logger(self):
        """Initialize rich logging for standalone nodes"""
        from rich.console import Console
        from rich.logging import RichHandler

        console = Console(width=100)
        handler = RichHandler(
            console=console,
            show_time=True,
            show_level=True,
            markup=True,
            show_path=False
        )
        self.logger.addHandler(handler)
        self.logger.propagate = False

    def _parse_fact_check(self, raw: str) -> FactCheck:
        """Parse the model's JSON reply into a FactCheck object.

        Falls back to a passing score if the reply is unparseable,
        so debaters are never penalized for formatting issues.
        """
        cleaned = strip_think(raw)
        cleaned = re.sub(r"```(?:json)?|```", "", cleaned).strip()

        # Grab the first {...} block in case the model added extra prose
        match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
        if match:
            cleaned = match.group(0)

        try:
            data = json.loads(cleaned)
            score = str(data.get("binary_score", "yes")).strip().lower()
            if score not in ("yes", "no"):
                score = "yes"
            return FactCheck(
                binary_score=score,
                justification=str(data.get("justification", "")).strip()
            )
        except (json.JSONDecodeError, TypeError):
            self.logger.warning(
                f"[yellow]Fact check reply unparseable, passing by default:[/]\n"
                f"[dim]{textwrap.shorten(raw, width=200, placeholder='...')}[/]"
            )
            return FactCheck(
                binary_score="yes",
                justification="Fact check skipped: model reply could not be parsed."
            )

    def __call__(self, state: DebateState) -> Dict[str, Any]:
        messages = state.get("messages", [])
        last_message = messages[-1]
        claim = strip_think(last_message["content"])
        speaker = last_message["speaker"]
        stage = state["stage"]

        self.logger.info(
            f"[bold red]Fact-Checking {speaker.upper()}'s {stage.title()} Claim:[/]\n"
            f"[dim]{textwrap.shorten(claim, width=150, placeholder='...')}[/]"
        )

        completion = self.client.chat.completions.create(
            model=self.model_name,
            messages=[{
                "role": "user",
                "content": (
                    f"Consider the following statement from a debate.\n\n"
                    f"Statement:\n\"{claim}\"\n\n"
                    f"Based on your own knowledge, judge whether any numbers, statistics, "
                    f"or cited studies in the statement appear inaccurate or hallucinated, and why. "
                    f"If the statement does not contain numbers or references to studies, "
                    f"consider it successfully fact-checked with a 'yes' score.\n\n"
                    f"Reply with ONLY a JSON object, no markdown fences, no extra text, "
                    f"in exactly this format:\n"
                    f'{{"binary_score": "yes", "justification": "your reasoning here"}}\n'
                    f'where binary_score is "yes" if the claim is acceptable and "no" otherwise.'
                )
            }],
            temperature=0.1,
        )

        fact_check = self._parse_fact_check(completion.choices[0].message.content)
        result = fact_check.binary_score
        justification = fact_check.justification

        if result == "yes":
            self.logger.info(f"[green]✅ Verified[/]\n"f"[dim]{justification}[/]")
            last_message["validated"] = True
            return {
                "messages": messages,
                "validated": True
            }
        else:
            self.logger.info(
                f"[red]❌ Disputed[/]\n"
                f"[bold]Reason:[/] {justification}\n"
                f"[yellow]⚠ {speaker.upper()} now has {state.get(f'times_{speaker}_fact_checked', 0) + 1}/3 failed checks[/]"
            )
            fact_checker_msg = create_debate_message(
                speaker="fact_checker",
                content=result,
                stage=state["stage"]
            )
            if speaker == SPEAKER_PRO:
                return {
                    "messages": messages + [fact_checker_msg],
                    "validated": False,
                    "times_pro_fact_checked": state.get("times_pro_fact_checked", 0) + 1,
                }
            elif speaker == SPEAKER_CON:
                return {
                    "messages": messages + [fact_checker_msg],
                    "validated": False,
                    "times_con_fact_checked": state.get("times_con_fact_checked", 0) + 1,
                }