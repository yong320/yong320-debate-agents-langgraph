from langgraph.graph import StateGraph, END
from debate_state import DebateState
from nodes.pro_debater_node import ProDebaterNode
from nodes.con_debater_node import ConDebaterNode
from nodes.debate_moderator_node import DebateModeratorNode
from nodes.fact_checker_node import FactCheckNode
from nodes.fact_check_router_node import FactCheckRouterNode
from nodes.judge_node import JudgeNode
from configurations.llm_config import llm_config_map

class DebateWorkflow:

    def _initialize_workflow(self) -> StateGraph:
        workflow = StateGraph(DebateState)
        # Nodes（generate_topic_node 已删除，议题由外部传入）
        workflow.add_node("pro_debater_node", ProDebaterNode(llm_config_map["gpt-4.1"]))
        workflow.add_node("con_debater_node", ConDebaterNode(llm_config_map["gpt-4.1"]))
        workflow.add_node("fact_check_node", FactCheckNode())
        workflow.add_node("fact_check_router_node", FactCheckRouterNode())
        workflow.add_node("debate_moderator_node", DebateModeratorNode())
        workflow.add_node("judge_node", JudgeNode(llm_config_map["gpt-4.1"]))

        # Entry point（原为 generate_topic_node，现由 pro 直接开局）
        workflow.set_entry_point("pro_debater_node")

        # Flow
        workflow.add_edge("pro_debater_node", "fact_check_node")
        workflow.add_edge("con_debater_node", "fact_check_node")
        workflow.add_edge("fact_check_node", "fact_check_router_node")
        workflow.add_edge("judge_node", END)
        return workflow

    async def run(self, topic: str):
        workflow = self._initialize_workflow()
        graph = workflow.compile()
        initial_state = {
            "debate_topic": topic,          # 键名是 debate_topic，不是 topic
            "positions": {
                "pro": "In favor of the topic",
                "con": "Against the topic"
            },
            "messages": [],
            "stage": "opening",             # 原 GenerateTopicNode 初始化的值
            "speaker": "pro",
            "times_pro_fact_checked": 0,
            "times_con_fact_checked": 0,
        }
        final_state = await graph.ainvoke(initial_state, config={"recursion_limit": 50})
        return final_state