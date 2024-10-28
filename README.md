![oreilly-logo](images/oreilly.png)

# AI Agents A-Z

This repository contains code for the [O'Reilly Live Online Training for AI Agents A-Z](https://learning.oreilly.com/live-events/ai-agents-a-z/0642572007604)

This course provides a comprehensive guide to understanding, implementing, and managing AI agents both at the prototype stage and in production. Attendees will start with foundational concepts and progressively delve into more advanced topics, including various frameworks like CrewAI, LangChain, and AutoGen as well as building agents from scratch using powerful prompt engineering techniques. The course emphasizes practical application, guiding participants through hands-on exercises to implement and deploy AI agents, evaluate their performance, and iterate on their designs. We will go over key aspects like cost projections, open versus closed source options, and best practices are thoroughly covered to equip attendees with the knowledge to make informed decisions in their AI projects.


## Setup Instructions

1. **Create and Activate Virtual Environment**

   Create a virtual environment using Python 3.10:

   ```bash
   python3.10 -m venv venv
   ```

   Activate the virtual environment:

   - **macOS/Linux**:

     ```bash
     source venv/bin/activate
     ```

   - **Windows**:

     ```bash
     venv\Scripts\activate
     ```

2. **Install Dependencies**

   With the virtual environment activated, install dependencies from `requirements.txt`:

   ```bash
   pip install -r requirements.txt
   ```
   
   You might need to do:
   
	```bash
	python3 -m pip install -r requirements.txt
	```


## Notebooks

In the activated environment, run

```bash
python3 -m jupyter notebook
```

- **Using 3rd party agent frameworks**
	
	- **[Intro to CrewAI](notebooks/CrewAI_Hello_World.ipynb)** - An introductory notebook for CrewAI
	
	- **[Intro to OpenAI Swarm](notebooks/Swarm_Hello_World.ipynb)** - An introductory notebook for OpenAI's Swarm
	
	
	- See **[the streamlit directory](./streamlit)** for an example of deploying crew on a streamlit app


- **Evaluating Agents**

	- **[Evaluating LLMs with Rubrics](https://colab.research.google.com/drive/1DeVYrdNb3FlQQLeBqGPFkx6roZaPwVRy?usp=sharing)** - Exploring a rubric prompt to evaluate generative output

	- **[Evaluating Alignment](notebooks/evaluating_alignment.ipynb)** - Seeing how an LLM can judge agent's responses

- **Building our own agents**
	
	- **[First Steps with our own Agent](https://colab.research.google.com/drive/14jAlW2E7ya_aS1M6eUsuHciC1WvLfIif?usp=sharing)** - Working towards building our own agent framework
	
	- See **[Squad Goals](https://github.com/sinanuozdemir/squad-goals)** for a very simple example of my own agent framework
	
		- **[Intro to Squad Goals](notebooks/SquadGoals_Hello_World.ipynb)** - using my own framework to do some basic tasks
	

## Instructor

**Sinan Ozdemir** is the Founder and CTO of LoopGenius where he uses State of the art AI to help people run digital ads on Meta, Google, and more. Sinan is a former lecturer of Data Science at Johns Hopkins University and the author of multiple textbooks on data science and machine learning. Additionally, he is the founder of the recently acquired Kylie.ai, an enterprise-grade conversational AI platform with RPA capabilities. He holds a master’s degree in Pure Mathematics from Johns Hopkins University and is based in San Francisco, CA.

