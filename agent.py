import psycopg2
from dotenv import load_dotenv, find_dotenv
import os
from langchain_core.tools import tool
from langchain_groq import ChatGroq

load_dotenv(find_dotenv())

model = ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key=os.environ["GROQ_API_KEY"]
)

def get_schema() -> str:
    conn = psycopg2.connect(os.environ["DATABASE_URL"])
    cur = conn.cursor()
    cur.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
    """)
    tables = [row[0] for row in cur.fetchall()]
    schema = ""
    for table in tables:
        cur.execute(f"""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = '{table}'
        """)
        columns = cur.fetchall()
        schema += f"\nTable: {table}\n"
        for col_name, col_type in columns:
            schema += f"  - {col_name}: {col_type}\n"
    cur.close()
    conn.close()
    return schema

@tool
def execute_sql(query: str) -> str:
    """Executes a SQL query on the PostgreSQL database and returns the results."""
    conn = psycopg2.connect(os.environ["DATABASE_URL"])
    cur = conn.cursor()
    try:
        cur.execute(query)
        results = cur.fetchall()
        columns = [desc[0] for desc in cur.description]
        formatted = [dict(zip(columns, row)) for row in results[:2]]
        return str(formatted)
    except Exception as e:
        return f"Error executing query: {str(e)}"
    finally:
        cur.close()
        conn.close()

model_with_tools = model.bind_tools([execute_sql])

schema = get_schema()

system_prompt = f"""You are an expert SQL assistant.
The user will ask questions about an e-commerce database.
Convert their question into a PostgreSQL query and use the execute_sql tool to run it.

Here is the database schema:
{schema}

Rules:
-This schema has all coloumns and two rows of data in each table, so you can use that to figure out what type of values exist in the database write sql queries accordingly.
- Only write SELECT statements, never INSERT, UPDATE or DELETE
- Always use correct table and column names from the schema above
- For joins use: orders.customer_id, order_items.order_id, order_items.product_id
- Before filtering by any text value (status, category, city), first check what values exist using SELECT DISTINCT
- If the user makes a spelling mistake, figure out what they meant and query accordingly
- If the question has nothing to do with the database, politely say you can only answer questions about the e-commerce data
"""

chat_history = [{"role": "system", "content": system_prompt}]

def ask(user_question: str):
    chat_history.append({"role": "user", "content": user_question})

    # LLM Call 1 — generate SQL
    response = model_with_tools.invoke(chat_history)

    # No tool call — LLM answered directly
    if not response.tool_calls:
        chat_history.append({"role": "assistant", "content": response.content})
        return response.content

    # Execute tool call
    tool_call = response.tool_calls[0]
    query = tool_call["args"]["query"]
    print(f"SQL Generated: {query}")
    result = execute_sql.invoke({"query": query})
    print(f"Raw Result: {result}")

    # Append tool call and result to history
    chat_history.append({
        "role": "assistant",
        "content": response.content,
        "tool_calls": response.additional_kwargs["tool_calls"]
    })
    chat_history.append({
        "role": "tool",
        "tool_call_id": tool_call["id"],
        "content": result
    })

    # LLM Call 2 — convert result to human answer
    final_response = model_with_tools.invoke(chat_history)
    chat_history.append({"role": "assistant", "content": final_response.content})
    return final_response.content

print("E-commerce SQL Agent ready! Type 'exit' to quit.\n")
while True:
    question = input("You: ")
    if question.lower() in ["exit", "quit"]:
        break
    answer = ask(question)
    print(f"Agent: {answer}\n")