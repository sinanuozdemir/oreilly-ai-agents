import streamlit as st
import os
import subprocess
import sys

# Install necessary packages
def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package, "--upgrade", "--quiet"])
# install('crewai_tools')
# install('crewai')
try:
    from crewai_tools import ScrapeWebsiteTool
    from crewai import Agent, Task, Crew, Process
except ImportError:
    st.write("Installing necessary packages...")
    install('crewai_tools')
    install('crewai')
    from crewai_tools import ScrapeWebsiteTool
    from crewai import Agent, Task, Crew, Process

# Set up the app title and description
st.title("CrewAI Streamlit App")
st.write("Welcome to the CrewAI Streamlit App! Define agents, tasks, and run a crew.")

# Handle OpenAI API key
if 'OPENAI_API_KEY' in st.secrets:
    os.environ['OPENAI_API_KEY'] = st.secrets["OPENAI_API_KEY"]
else:
    api_key = st.text_input("Enter your OpenAI API Key", type="password")
    if api_key:
        os.environ['OPENAI_API_KEY'] = api_key
    else:
        st.warning("Please provide your OpenAI API Key.")

# Initialize session state for agents and tasks
if 'agents' not in st.session_state:
    st.session_state.agents = []

if 'tasks' not in st.session_state:
    st.session_state.tasks = []

# Agents Section
st.header("Agents")

with st.expander("Create a new Agent"):
    with st.form(key='agent_form'):
        agent_name = st.text_input("Agent Name")
        agent_role = st.text_input("Agent Role")
        agent_goal = st.text_area("Agent Goal")
        agent_backstory = st.text_area("Agent Backstory")
        agent_allow_delegation = st.checkbox("Allow Delegation", value=False)
        agent_verbose = st.checkbox("Verbose", value=True)
        # Tools selection
        tools_available = ['ScrapeWebsiteTool']
        agent_tools_selected = st.multiselect("Select Tools", tools_available)

        submit_agent = st.form_submit_button("Create Agent")

        if submit_agent:
            # Map selected tools to actual tool instances
            tools_mapping = {
                'ScrapeWebsiteTool': ScrapeWebsiteTool(),
            }
            agent_tools = [tools_mapping[tool_name] for tool_name in agent_tools_selected]

            new_agent = Agent(
                role=agent_role,
                goal=agent_goal,
                backstory=agent_backstory,
                verbose=agent_verbose,
                allow_delegation=agent_allow_delegation,
                tools=agent_tools
            )

            # Store the agent in session state
            st.session_state.agents.append((agent_name, new_agent))
            st.success(f"Agent '{agent_name}' created successfully.")

# Display existing agents
st.subheader("Existing Agents")
if st.session_state.agents:
    for idx, (agent_name, agent) in enumerate(st.session_state.agents):
        st.write(f"**{agent_name}**: {agent.role}")
else:
    st.write("No agents created yet.")

# Tasks Section
st.header("Tasks")

with st.expander("Create a new Task"):
    with st.form(key='task_form'):
        task_description = st.text_area("Task Description")
        task_expected_output = st.text_area("Expected Output")
        # Assign to an agent
        agent_options = [name for name, _ in st.session_state.agents]
        if agent_options:
            task_agent_name = st.selectbox("Assign to Agent", agent_options)
            submit_task = st.form_submit_button("Create Task")

            if submit_task:
                # Get the agent instance
                agent_dict = dict(st.session_state.agents)
                task_agent = agent_dict[task_agent_name]
                new_task = Task(
                    description=task_description,
                    agent=task_agent,
                    expected_output=task_expected_output
                )
                # Store the task
                st.session_state.tasks.append(new_task)
                st.success("Task created successfully.")
        else:
            st.warning("Please create at least one agent before adding tasks.")

# Display existing tasks
st.subheader("Existing Tasks")
if st.session_state.tasks:
    for idx, task in enumerate(st.session_state.tasks):
        st.write(f"**Task {idx+1}**: {task.description}")
else:
    st.write("No tasks created yet.")

# Run Crew Section
st.header("Run the Crew")

process_options = {
    'Sequential': Process.sequential,
    'Hierarchical': Process.hierarchical
}

selected_process = st.selectbox("Select Process", list(process_options.keys()))

if st.button("Run Crew"):
    if st.session_state.tasks:
        # Get the process
        process = process_options[selected_process]
        print(process)

        crew = Crew(
            tasks=st.session_state.tasks,
            process=process,
            verbose=True
        )

        output = crew.kickoff()

        st.subheader("Crew Output")
        st.write(output.raw)
    else:
        st.warning("Please create at least one task before running the crew.")
