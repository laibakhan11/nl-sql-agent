# NL-to-SQL Agent

A conversational AI agent that lets non-technical users query a PostgreSQL database using plain English.

## How it works
1. User asks a question in natural language
2. LLM reads the database schema and writes a SQL query
3. Query runs on a live PostgreSQL database (hosted on Neon)
4. LLM converts the raw results into a human-friendly answer

## Tech Stack
- LLM: Llama 3.3 70B via Groq API
- Database: PostgreSQL on Neon
- Framework: LangChain (tool calling)
- Data: FakeStore API mock e-commerce data (users, orders, products)

## Setup
1. Clone the repo
2. Install dependencies: pip install psycopg2 langchain langchain-groq python-dotenv
3. Create a .env file:
   GROQ_API_KEY=your_key_here
   DATABASE_URL=your_neon_connection_string
4. Run: python main.py

## Example
You: how many orders were cancelled?
Agent: There were 3 orders that were cancelled.

You: by whom?
Agent: The cancelled orders were made by the following customers:
- David Morrison (order ID: 3)
- Don Romer (order ID: 6)
- William Hopkins (order ID: 7)

Note: handles typos and remembers context from previous questions.
