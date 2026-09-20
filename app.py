import os
import json
from flask import Flask, render_template, request, jsonify

from dotenv import load_dotenv
from google import genai

from rag import search_knowledge_base
from database import (
    init_database,
    create_ticket,
    add_audit_log,
    get_all_tickets,
    get_audit_logs
)

load_dotenv()

app = Flask(__name__)

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)

init_database()


SYSTEM_PROMPT = """
You are the Veridian Corp Internal IT Service Agent.

IMPORTANT:
You may ONLY use information provided in the Veridian Corp knowledge
base and employee/ticket information supplied to you.

Never invent company policies, approvals, timelines, permissions,
technical facts, or employee information.

Your job is to:
1. Understand the employee's IT issue.
2. Use the supplied knowledge-base information.
3. Ask a sensible follow-up question if essential information is missing.
4. Resolve simple requests when the supplied policy clearly allows it.
5. Escalate risky, unclear, security-related, or unauthorized requests.
6. Provide the policy/source used for the answer.
7. Never claim an action was completed if the supplied information
   does not establish that it was completed.

Return ONLY valid JSON using this structure:

{
    "decision": "RESOLVE | FOLLOW_UP | ESCALATE",
    "response": "Clear response to the employee",
    "source": "KB-XX or policy name",
    "category": "Short issue category",
    "priority": "Low | Medium | High",
    "resolution": "Resolution or next step",
    "follow_up_question": ""
}

Decision rules:

RESOLVE:
Use when the supplied policy clearly provides the answer or
the request can be handled using the supplied information.

FOLLOW_UP:
Use when important information is missing and you need to ask
the employee a necessary question before deciding.

ESCALATE:
Use when the request is risky, unclear, outside policy,
requires another team/approval, or requires human handling.

For security incidents such as suspected phishing, malware,
or unauthorized access, follow KB-09 exactly.

Do not create or invent a policy.
"""


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/chat", methods=["POST"])
def chat():

    data = request.get_json()

    message = data.get("message", "").strip()
    employee_name = data.get("employee_name", "").strip()

    if not message:
        return jsonify({
            "response": "Please describe your IT issue.",
            "decision": "FOLLOW_UP"
        })

    knowledge = search_knowledge_base(message)

    prompt = f"""
{SYSTEM_PROMPT}

EMPLOYEE:
{employee_name if employee_name else "Unknown"}

EMPLOYEE REQUEST:
{message}

RELEVANT VERIDIAN KNOWLEDGE:
{knowledge}
"""

    try:

        interaction = client.interactions.create(
            model="gemini-3.8-flash",
            input=prompt
        )

        raw_response = interaction.output_text.strip()

        if raw_response.startswith("```"):
            raw_response = raw_response.replace("```json", "")
            raw_response = raw_response.replace("```", "")
            raw_response = raw_response.strip()

        result = json.loads(raw_response)

        decision = result.get("decision", "FOLLOW_UP")

        answer = result.get(
            "response",
            "I need more information to process this request."
        )

        source = result.get(
            "source",
            "Veridian IT Knowledge Base"
        )

        category = result.get(
            "category",
            "IT Support"
        )

        priority = result.get(
            "priority",
            "Medium"
        )

        resolution = result.get(
            "resolution",
            ""
        )

        follow_up = result.get(
            "follow_up_question",
            ""
        )

        if decision == "FOLLOW_UP":

            add_audit_log(
                employee_name or "Unknown",
                "FOLLOW_UP",
                f"Issue: {message} | Question: {follow_up}"
            )

            return jsonify({
                "response": answer,
                "decision": "FOLLOW_UP",
                "source": source,
                "follow_up_question": follow_up
            })

        if decision == "ESCALATE":

            ticket_id = create_ticket(
                employee_name=employee_name or "Unknown",
                issue=message,
                category=category,
                priority=priority,
                status="Escalated",
                resolution=resolution,
                source=source
            )

            add_audit_log(
                employee_name or "Unknown",
                "TICKET_CREATED",
                f"Ticket TK-{ticket_id}: {message}"
            )

            return jsonify({
                "response": answer,
                "decision": "ESCALATE",
                "source": source,
                "ticket_id": f"TK-{ticket_id}"
            })

        add_audit_log(
            employee_name or "Unknown",
            "RESOLVED",
            f"Issue: {message} | Resolution: {resolution}"
        )

        return jsonify({
            "response": answer,
            "decision": "RESOLVE",
            "source": source,
            "resolution": resolution
        })

    except Exception as error:

        print("Agent Error:", error)

        return jsonify({
            "response": (
                "I couldn't safely process this request. "
                "Please provide more details or contact the IT team."
            ),
            "decision": "FOLLOW_UP",
            "source": "Veridian IT Knowledge Base"
        })


@app.route("/tickets")
def tickets():

    all_tickets = get_all_tickets()

    return render_template(
        "tickets.html",
        tickets=all_tickets
    )


@app.route("/audit")
def audit():

    logs = get_audit_logs()

    return render_template(
        "audit.html",
        logs=logs
    )


if __name__ == "__main__":
    app.run(debug=True)