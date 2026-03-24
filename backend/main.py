import sqlite3
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from llm import llm_response
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all origins for dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# DB_PATH = os.path.join(os.path.dirname(__file__), "..", "sap_o2c.db")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "sap_o2c.db")

@app.get("/api/graph")
def get_graph_data(limit: int = 100):
    """
    Returns nodes and links for Force Graph visualization.
    Extracts Sales Orders, Billing Documents and Business Partners.
    """
    if not os.path.exists(DB_PATH):
        return {"nodes": [], "links": []}

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    nodes_dict = {}
    links = []

    def add_node(node_id, label, group):
        if not node_id: return
        if node_id not in nodes_dict:
            nodes_dict[node_id] = {"id": node_id, "label": label, "group": group}

    def add_link(source, target):
        if not source or not target: return
        links.append({"source": source, "target": target})

    # 1. Fetch Sales Orders (Group 1) and link to Business Partners (soldToParty)
    try:
        cursor.execute("SELECT salesOrder, soldToParty FROM sales_order_headers LIMIT ?", (limit,))
        so_data = cursor.fetchall()
        for so, bp in so_data:
            add_node(so, f"SO: {so}", 1)
            if bp:
                add_node(bp, f"BP: {bp}", 3)
                add_link(so, bp)
    except Exception as e:
        print(f"Error fetching Sales Orders: {e}")

    # 2. Fetch Billing Documents (Group 2), link to BP (soldToParty)
    #    and link to Sales Order via billing_document_items
    try:
        cursor.execute("SELECT billingDocument, soldToParty FROM billing_document_headers LIMIT ?", (limit,))
        bill_data = cursor.fetchall()
        for bill, bp in bill_data:
            add_node(bill, f"Bill: {bill}", 2)
            if bp:
                add_node(bp, f"BP: {bp}", 3)
                add_link(bill, bp)
    except Exception as e:
        print(f"Error fetching Billing Docs: {e}")

    try:
        cursor.execute("SELECT billingDocument, referenceSdDocument FROM billing_document_items LIMIT ?", (limit * 5,))
        bill_items = cursor.fetchall()
        for bill, ref_so in bill_items:
            # referenceSdDocument is usually the sales order
            if ref_so:
                # We check if ref_so is actually in our nodes, or just add it anyway 
                # (might create dangling SO nodes without soldToParty)
                add_node(ref_so, f"SO: {ref_so}", 1) 
                add_node(bill, f"Bill: {bill}", 2)
                add_link(bill, ref_so)
    except Exception as e:
        print(f"Error fetching Billing Items: {e}")

    # 3. Fetch independent Business Partners (Group 3)
    try:
        cursor.execute("SELECT businessPartner, businessPartnerFullName FROM business_partners LIMIT ?", (limit,))
        bp_data = cursor.fetchall()
        for bp, name in bp_data:
            add_node(bp, f"BP: {name or bp}", 3)
    except Exception as e:
        print(f"Error fetching Business Partners: {e}")

    conn.close()

    return {
        "nodes": list(nodes_dict.values()),
        "links": links
    }

@app.get("/ask")
def llm_ask(question:str)->str:
    return llm_response(question)




if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)

























































































