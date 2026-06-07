from discount_analyst.agents.common_prompts.structured_output import (
    final_result_user_step,
)
from discount_analyst.agents.surveyor.schema import SurveyorOutput

USER_PROMPT = f"""
Execute the four-step screening plan in your system prompt now.

Step 1: launch the three screener calls in parallel — NYSE, NASDAQ, and LSE.
Step 2: pull financial scores for your shortlist in parallel.
Step 3: run the registered web search tool (web_search or duckduckgo_search; use whichever is available) and web_fetch only where the snippet is insufficient, sequentially per candidate.
Step 4: {final_result_user_step(output_type_name=SurveyorOutput.__name__)}

Do not produce any reasoning about which tools to use or in what order — the plan is fixed.
Your first action must be the parallel batch from Step 1.
""".strip()
