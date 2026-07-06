import asyncio
import os
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, firestore
from google.antigravity import Agent

from agents.consultant import CONSULTANT_CONFIG
from agents.techlead import TECHLEAD_CONFIG
from agents.cko import CKO_CONFIG
from agents.jules import JULES_CONFIG
from agents.pmo import PMO_CONFIG
from agents.debugger import DEBUGGER_CONFIG

# --- Configuration & Initialization ---
# Initialize Firebase Admin SDK (Assumes GOOGLE_APPLICATION_CREDENTIALS is set)
# For local testing without a key, we'll mock the db if no credentials exist.
def initialize_firestore():
    try:
        firebase_admin.initialize_app()
        return firestore.client()
    except Exception as e:
        print(f"[WARN] Firestore initialization skipped (using mock mode): {e}")
        return None

db = initialize_firestore()

async def stream_agent_thoughts(agent_id: str, tenant_id: str, task_id: str, prompt: str, config):
    """
    Spawns an agent, feeds it the prompt, and streams its thoughts to Firestore.
    """
    print(f"[{agent_id}] Spawning agent for tenant {tenant_id}, task {task_id}...")
    
    # Spawn the agent
    async with Agent(config) as agent:
        response = await agent.chat(prompt)
        
        # Stream reasoning/thinking deltas to Firestore
        async for thought in response.thoughts:
            log_entry = {
                "tenant_id": tenant_id,
                "task_id": task_id,
                "agent_id": agent_id,
                "thought": thought,
                "timestamp": firestore.SERVER_TIMESTAMP if db else datetime.utcnow().isoformat()
            }
            if db:
                db.collection("global_context").add(log_entry)
            print(f"[{agent_id} THOUGHT] {thought.strip()}")
            
        print(f"[{agent_id}] Task completed.")

def on_task_snapshot(col_snapshot, changes, read_time):
    """
    Firestore listener callback for new tasks.
    """
    for change in changes:
        if change.type.name == 'ADDED':
            doc = change.document
            task_data = doc.to_dict()
            task_id = doc.id
            tenant_id = task_data.get("tenant_id", "unknown")
            prompt = task_data.get("prompt", "")
            agent_type = task_data.get("agent_type", "consultant")
            status = task_data.get("status", "pending")
            
            if status != "pending":
                continue
                
            print(f"[DAEMON] New task detected: {task_id} for tenant {tenant_id}")
            
            # Update status to processing
            if db:
                doc.reference.update({"status": "processing"})
            
            if agent_type == "consultant":
                config = CONSULTANT_CONFIG
            elif agent_type == "techlead":
                config = TECHLEAD_CONFIG
            elif agent_type == "cko" or agent_type == "alpha":
                config = CKO_CONFIG
            elif agent_type == "jules" or agent_type == "beta":
                config = JULES_CONFIG
            elif agent_type == "pmo":
                config = PMO_CONFIG
            elif agent_type == "debugger":
                config = DEBUGGER_CONFIG
            else:
                config = CONSULTANT_CONFIG # fallback
                
            agent_id = f"FDE-{agent_type.capitalize()}"
            
            # Fire and forget the async execution using the running event loop
            loop = asyncio.get_event_loop()
            loop.create_task(stream_agent_thoughts(agent_id, tenant_id, task_id, prompt, config))

async def health_check_handler(reader, writer):
    try:
        await reader.read(1024)
        response = b"HTTP/1.1 200 OK\r\nContent-Length: 2\r\n\r\nOK"
        writer.write(response)
        await writer.drain()
    except Exception:
        pass
    finally:
        writer.close()

async def main():
    print("========================================")
    print("🧠 Touchless-FDE V3: Python Daemon Core")
    print("========================================")
    
    if db:
        print("[DAEMON] Connecting to Firestore 'tasks' collection graph...")
        # Listen to a unified tasks collection for simplicity
        tasks_query = db.collection("tasks").where("status", "==", "pending")
        tasks_query.on_snapshot(on_task_snapshot)
    else:
        print("[DAEMON] Running in standalone mock mode (no Firestore connection).")
        print("[DAEMON] Simulating an incoming task...")
        # Simulate a task processing
        await stream_agent_thoughts(
            agent_id="FDE-Consultant",
            tenant_id="tenant_X",
            task_id="task_001",
            prompt="Client requires a new e-commerce migration strategy.",
            config=CONSULTANT_CONFIG
        )

    port = int(os.environ.get("PORT", 8080))
    print(f"[DAEMON] Starting health check server on port {port}...")
    server = await asyncio.start_server(health_check_handler, '0.0.0.0', port)

    print("[DAEMON] Event loop running. Waiting for events...")
    async with server:
        await server.serve_forever()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("[DAEMON] Shutdown signal received. Exiting.")
