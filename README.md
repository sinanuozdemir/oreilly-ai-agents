![oreilly-logo](images/oreilly.png)

# AI Agents A-Z

This repository contains code for both my live course: [O'Reilly Live Online Training for AI Agents A-Z](https://learning.oreilly.com/live-events/ai-agents-a-z/0642572007604) and my video series: [Modern Automated AI Agents: Building Agentic AI to Perform Complex Tasks
](https://learning.oreilly.com/course/modern-automated-ai/9780135414965/)

This course provides a comprehensive guide to understanding, implementing, and managing AI agents both at the prototype stage and in production. Attendees will start with foundational concepts and progressively delve into more advanced topics, including various frameworks like CrewAI, LangChain, and AutoGen as well as building agents from scratch using powerful prompt engineering techniques. The course emphasizes practical application, guiding participants through hands-on exercises to implement and deploy AI agents, evaluate their performance, and iterate on their designs. We will go over key aspects like cost projections, open versus closed source options, and best practices are thoroughly covered to equip attendees with the knowledge to make informed decisions in their AI projects.


## Setup Instructions


### Using Python 3.11 Virtual Environment

At the time of writing, we need a Python virtual environment with Python 3.11.

#### Option 1: Python 3.11 is Already Installed

##### Step 1: Verify Python 3.11 Installation

```bash
python3.11 --version
```

##### Step 2: Create a Virtual Environment

```bash
python3.11 -m venv .venv
```

This creates a `.venv` folder in your current directory.

##### Step 3: Activate the Virtual Environment

- **macOS/Linux:**
  
  ```bash
  source .venv/bin/activate
  ```

- **Windows:**
  
  ```cmd
  .venv\Scripts\activate
  ```

You should see `(.venv)` in your terminal prompt.

##### Step 4: Verify the Python Version

```bash
python --version
```

##### Step 5: Install Packages

```bash
pip install -r requirements.txt
```

##### Step 6: Deactivate the Virtual Environment

```bash
deactivate
```

---

#### Option 2: Install Python 3.11

If you don’t have Python 3.11, follow the steps below for your OS.

##### **macOS (Using Homebrew)**

```bash
brew install python@3.11
```

##### **Ubuntu/Debian**

```bash
sudo apt update
sudo apt install python3.11 python3.11-venv
```

##### **Windows (Using Windows Installer)**

1. Go to [Python Downloads](https://www.python.org/downloads/release/python-3110/).
2. Download the installer for Python 3.11.
3. Run the installer and ensure **"Add Python 3.11 to PATH"** is checked.

### Verify Installation

```bash
python3.11 --version
```

## Notebooks

In the activated environment, run

```bash
python3 -m jupyter notebook
```

- **Using 3rd party agent frameworks**
	
	- **[Intro to CrewAI](notebooks/CrewAI_Hello_World.ipynb)** - An introductory notebook for CrewAI

		- See **[the streamlit directory](./streamlit)** for an example of deploying crew on a streamlit app
	
	- **[Intro to Autogen](notebooks/Autogen_HelloWorld.ipynb)** - An introductory notebook for Microsoft's Autogen
	
	- **[Intro to OpenAI Swarm](notebooks/Swarm_Hello_World.ipynb)** - An introductory notebook for OpenAI's Swarm
	
	
	- **[Intro to LangGraph](notebooks/LangGraph_Hello_World.ipynb)** - An introductory notebook for LangGraph

		- **[Agents playing Chess](https://colab.research.google.com/drive/1NMb4H8q-N0ZgEdaiDd6qUaBLD21yLejD?usp=sharing)** - An implementation of two ReAct Agents playing Chess with each other

- **Evaluating Agents**

	- **[Evaluating Agent Output with Rubrics](notebooks/Evaluating_LLMs_with_Rubrics.ipynb)** - Exploring a rubric prompt to evaluate generative output. This notebook also notes positional biases when choosing between agent responses.

		- **[Advanced - Evaluating Alignment](notebooks/evaluating_alignment.ipynb)** - A longer notebook doing a much more in depth analysis on how an LLM can judge agent's responses

 	- **[Evaluating Tool Selection](notebooks/agent_positional_bias_tools.ipynb)** - Calculating the accuracy of tool selection between different LLMs and quantifying the positional bias present in auto-regressive LLMs. See the additions [here for V3 + DeepSeek Distilled Models](notebooks/agent_positional_bias_tools%20-%20DEEPSEEK%20edition.ipynb) and [here for DeepSeek R1](notebooks/agent_positional_bias_tools%20-%20DEEPSEEK%20R1.ipynb)

- **Building our own agents**
	
	- **[First Steps with our own Agent](https://colab.research.google.com/drive/14jAlW2E7ya_aS1M6eUsuHciC1WvLfIif?usp=sharing)** - Working towards building our own agent framework
	
	- See **[Squad Goals](https://github.com/sinanuozdemir/squad-goals)** for a very simple example of my own agent framework
	
		- **[Intro to Squad Goals](notebooks/SquadGoals_Hello_World.ipynb)** - using my own framework to do some basic tasks
		- **[Multimodal Agents](notebooks/squad_visual_agent.ipynb)** - Incorporating Dalle-3 to allow our squad to generate images


- **Modern Agent Paradigms**
	
	-  **[Plan & Execute Agents](notebooks/LangGraph_Plan_Execute.ipynb)** - Plan & Execute Agents use a planner to create multi-step plans with an LLM and an executor to complete each step by invoking tools.

	-  **[Reflection Agents](notebooks/LangGraph_Reflect.ipynb)** - Reflection Agents combine a generator to perform tasks and a reflector to provide feedback and guide improvements.
  
 	-  Using open source [Qwen VL 72B](https://colab.research.google.com/drive/1TYqAtnk1m_gLpCF5KY8WaNNOkfcYuBsy?usp=sharing) to grab bounding boxes of elements
  
  	-  Amazon's Nova Act for Browser Use in Action
  		-   run `python nova_apt.py --caltrain_city "Dogpatch" --bedrooms 2 --baths 2` in the notebooks directory

## Instructor

**Sinan Ozdemir** is the Founder and CTO of LoopGenius where he uses State of the art AI to help people run digital ads on Meta, Google, and more. Sinan is a former lecturer of Data Science at Johns Hopkins University and the author of multiple textbooks on data science and machine learning. Additionally, he is the founder of the recently acquired Kylie.ai, an enterprise-grade conversational AI platform with RPA capabilities. He holds a master’s degree in Pure Mathematics from Johns Hopkins University and is based in San Francisco, CA.

