import streamlit as st

from tools.input_guard import check_user_input, get_error_fallback_message

st.set_page_config(
    page_title="ShopSphere Assistant",
    page_icon="🛍️",
    layout="centered",
)

st.sidebar.title("🛍️ ShopSphere")
st.sidebar.markdown("Intelligent Retail Assistant")
st.sidebar.divider()

mode = st.sidebar.radio(
    "Agent Mode",
    options=["Part A - Basic Agent", "Part B - Deep Agent (Web)", "Part C - Multi-Agent"],
    index=2,
)

st.sidebar.divider()
st.sidebar.caption("LLM: gemma4:e4b via Ollama")
st.sidebar.caption("Web Search: Tavily API")


@st.cache_resource
def load_basic_agent():
    """Load and cache the Part A basic agent."""
    from part_a_basic_agent import agent

    return agent


@st.cache_resource
def load_deep_agent():
    """Load and cache the Part B deep agent."""
    from part_b_deep_agent import deep_agent

    return deep_agent


@st.cache_resource
def load_orchestrator():
    """Load and cache Part C orchestrator helpers."""
    from part_c_multi_agent import keyword_router, orchestrate

    return orchestrate, keyword_router


st.title("🛍️ ShopSphere Assistant")
st.caption(f"Running in: **{mode}**")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])
        if message.get("route"):
            st.caption(f"🔀 Routed to: {message['route']}")


if user_input := st.chat_input("Ask ShopBot anything..."):
    st.session_state.messages.append({"role": "user", "content": user_input})

    with st.chat_message("user"):
        st.write(user_input)

    with st.chat_message("assistant"):
        response = ""
        route_label = None
        blocked = False
        guard = check_user_input(user_input)

        if not guard.allowed:
            response = guard.message
            blocked = True
        else:
            with st.spinner("ShopBot is thinking..."):
                try:
                    if mode == "Part A - Basic Agent":
                        basic_agent = load_basic_agent()
                        result = basic_agent.invoke({"input": user_input})
                        response = result["output"]
                    elif mode == "Part B - Deep Agent (Web)":
                        deep = load_deep_agent()
                        result = deep.invoke({"input": user_input})
                        response = result["output"]
                    else:
                        orchestrate, keyword_router = load_orchestrator()
                        route_label = f"{keyword_router(user_input).upper()} AGENT"
                        response = orchestrate(user_input)
                except Exception as exc:  # pragma: no cover - runtime UI safeguard
                    response = (
                        f"{get_error_fallback_message()}\n\n"
                        f"Details: {exc}"
                    )

        st.write(response)
        if blocked:
            st.caption("Input blocked by safety check")
        if route_label:
            st.caption(f"🔀 Routed to: {route_label}")

    st.session_state.messages.append(
        {"role": "assistant", "content": response, "route": route_label}
    )


if st.session_state.messages and st.sidebar.button("🗑️ Clear Chat"):
    st.session_state.messages = []
    st.rerun()
