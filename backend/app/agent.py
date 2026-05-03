from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI

from app.config import settings
from app.memory import get_memory, is_paused, save_memory, set_paused
from app.prompts import SYSTEM_PROMPT
from app.tools.bitrix import check_handover_needed, create_bitrix_lead
from app.tools.entity_extractor import extract_entities
from app.tools.svoydom import search_apartments

llm = ChatOpenAI(model="gpt-4o", temperature=0.3, openai_api_key=settings.OPENAI_API_KEY)
tools = [search_apartments]

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", SYSTEM_PROMPT),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
        MessagesPlaceholder("agent_scratchpad"),
    ]
)

agent = create_openai_tools_agent(llm, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=False)


def _get_missing_entity_question(entities: dict) -> str | None:
    if not entities.get("contact_name"):
        return "Как я могу к вам обращаться?"
    if entities.get("budget_min") is None and entities.get("budget_max") is None:
        return "Подскажите, пожалуйста, ваш бюджет в тенге?"
    if entities.get("rooms") is None:
        return "Сколько комнат рассматриваете?"
    if entities.get("purpose") not in {"investment", "living"}:
        return "Покупаете для инвестиции или для собственного проживания?"
    return None


async def process_message(phone: str, text: str) -> str | None:
    if await is_paused(phone):
        return None

    memory = await get_memory(phone)
    memory.setdefault("entities", {})
    memory["entities"]["contact_phone"] = memory["entities"].get("contact_phone") or phone
    memory["entities"] = await extract_entities(text, memory.get("entities", {}))
    next_question = _get_missing_entity_question(memory["entities"])

    chat_history = []
    for m in memory["messages"]:
        if m["role"] == "user":
            chat_history.append(HumanMessage(content=m["content"]))
        elif m["role"] == "assistant":
            chat_history.append(AIMessage(content=m["content"]))

    try:
        result = await agent_executor.ainvoke({"input": text, "chat_history": chat_history})
        response = result["output"]
    except Exception as e:
        print(f"[Agent] Error: {e}")
        response = "Извините, произошла ошибка. Попробуйте ещё раз."

    
    if next_question:
        response = f"{response}\n\n{next_question}"

    handover_needed, reason = await check_handover_needed(text, memory["messages"])
    if handover_needed:
        await create_bitrix_lead(memory["entities"], memory["messages"], reason)
        await set_paused(phone)
        if reason == "purchase_ready":
            response += "\n\nОтлично! Передаю ваши данные менеджеру, скоро к вам вернутся! 🏠"
        else:
            response = "Понимаю вас. Сейчас соединю с менеджером — он ответит в течение нескольких минут."

    memory["messages"].append({"role": "user", "content": text})
    memory["messages"].append({"role": "assistant", "content": response})
    await save_memory(phone, memory)
    return response
