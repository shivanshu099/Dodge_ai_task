# Chat Export — SAP O2C Database & Graph Visualization
**Date:** 2026-03-23

---

## 1. Data Ingestion — JSONL to SQLite

**User:** Read the document and help store the data in a sql lite databse by making the python script.

**Assistant:** Analyzed the `sap-order-to-cash-dataset` folder containing JSONL files across 19 subdirectories (billing documents, sales orders, business partners, products, etc.). Created `import_data.py` to dynamically:
- Iterate all subdirectories inside `sap-o2c-data`
- Infer schema columns from JSON keys
- Serialize nested objects (e.g., `creationTime`) to JSON strings
- Bulk-insert into SQLite using `executemany`

**Files created:**
- `import_data.py` — Main ingestion script
- `sap_o2c.db` — SQLite database (~983 KB, 19 tables)

**Tables created:** `billing_document_cancellations`, `billing_document_headers`, `billing_document_items`, `business_partners`, `business_partner_addresses`, `customer_company_assignments`, `customer_sales_area_assignments`, `journal_entry_items_accounts_receivable`, `outbound_delivery_headers`, `outbound_delivery_items`, `payments_accounts_receivable`, `plants`, `products`, `product_descriptions`, `product_plants`, `product_storage_locations`, `sales_order_headers`, `sales_order_items`, `sales_order_schedule_lines`

---

## 2. React Graph Frontend with Force-Directed Visualization

**User:** Make a backend server that can give graph in endpoint /api/graph also make a frontend that can display data in graphs, nodes, and edges using React.

**Assistant:** Built a full-stack application:

### Backend — FastAPI (`backend/main.py`)
- Runs on `http://127.0.0.1:8000`
- Endpoint: `GET /api/graph?limit=100`
- Queries `sap_o2c.db` and returns graph JSON:
  - **Nodes:** Sales Orders (Group 1), Billing Documents (Group 2), Business Partners (Group 3)
  - **Edges:** SO→BP (soldToParty), Bill→BP (soldToParty), Bill→SO (via billing_document_items.referenceSdDocument)

### Frontend — React + Vite (`frontend/`)
- Runs on `http://localhost:5173`
- Uses `react-force-graph-2d` for interactive force-directed graph
- Premium dark-mode UI with glassmorphism, gradient accents, Inter font
- Sidebar with Legend (color-coded node types), Statistics (354 nodes, 445 edges), and node selection detail

**Files created:**
- `backend/main.py` — FastAPI server
- `backend/requirements.txt` — `fastapi`, `uvicorn`
- `frontend/vite.config.js` — Vite config with React plugin
- `frontend/index.html` — HTML entry with Google Fonts
- `frontend/src/main.jsx` — React entry point
- `frontend/src/App.jsx` — Main graph component
- `frontend/src/index.css` — Full CSS design system

**Verification:** 354 nodes and 445 edges rendered successfully (183 Sales Orders, 163 Billing Documents, 8 Business Partners). No console errors.

---

## 3. Chatbot Interface in Sidebar

**User:** In the right panel, create a chatbot-like interface that can call port 8969 and print output from the endpoint.

**Assistant:** Added a **💬 AI Assistant** chat panel to the sidebar:
- Sends `POST` requests to `http://127.0.0.1:8969` with `{ "message": "user text" }`
- Parses response JSON for fields: `response`, `answer`, `result`, `output`
- Chat bubble UI with:
  - User messages (blue/purple gradient, right-aligned)
  - Assistant messages (dark card, left-aligned with 🤖 avatar)
  - Typing indicator animation (bouncing dots)
  - Auto-scroll to latest message
  - Enter key to send

**Files modified:**
- `frontend/src/App.jsx` — Added chatbot state, API call logic, and JSX
- `frontend/src/index.css` — Added chatbot styles with animations

---

## 4. Sidebar Always Visible Fix

**User:** Do not make the right panel disappear, make it always stay in the frontend.

**Assistant:** Updated CSS to ensure the sidebar never collapses:
- Added `min-width: 320px` and `max-width: 320px` to `.sidebar`
- Added `flex-grow: 0` to prevent expansion
- Added `min-width: 0` and `overflow: hidden` to `.graph-container` so flex distributes space correctly

**Files modified:**
- `frontend/src/index.css` — Sidebar and graph container CSS fixes

---

## 5. LangChain Database Tools

**User:** In Python, make tools that can query the database — tools that a LangChain LLM model can use. Create `backend/tools.py` capable of performing all operations.

**Assistant:** Created `backend/tools.py` with **14 LangChain `@tool` functions**:

| Category | Tools |
|---|---|
| **Schema Discovery** | `list_tables`, `get_table_schema`, `get_all_table_schemas` |
| **Read / Query** | `run_sql_query`, `get_sample_rows`, `count_rows`, `get_distinct_values`, `search_table` |
| **Aggregation** | `aggregate_column`, `group_by_count` |
| **Write / Modify** | `run_sql_write`, `insert_row`, `delete_rows` |
| **Joins** | `join_tables` |

**Usage:**
```python
from tools import get_all_tools
tools = get_all_tools()
# Pass tools to any LangChain agent
```

**Safety features:**
- `run_sql_query` only allows SELECT statements
- `run_sql_write` blocks DROP and ALTER operations
- All query results are capped (500 rows for queries, 100 for search, etc.)

**Files created:**
- `backend/tools.py` — 14 LangChain-compatible tools

**Verification:** All 14 tools imported and loaded successfully.

---

## Project Structure (Final)

```
doge_ai_assment/
├── import_data.py              # JSONL → SQLite ingestion script
├── schema.py                   # Schema inspection utility
├── sap_o2c.db                  # SQLite database (~983 KB)
├── sap-order-to-cash-dataset/  # Source JSONL data
│   └── sap-o2c-data/
│       ├── billing_document_headers/
│       ├── sales_order_headers/
│       ├── business_partners/
│       └── ... (19 subdirectories)
├── backend/
│   ├── main.py                 # FastAPI server (port 8000)
│   ├── tools.py                # 14 LangChain database tools
│   └── requirements.txt        # fastapi, uvicorn
└── frontend/
    ├── vite.config.js           # Vite + React plugin
    ├── index.html               # HTML entry
    ├── package.json
    └── src/
        ├── main.jsx             # React entry
        ├── App.jsx              # Graph + Chatbot component
        └── index.css            # Premium dark-mode CSS
```

## How to Run

```bash
# Terminal 1 — Backend
cd backend
python main.py
# → http://127.0.0.1:8000

# Terminal 2 — Frontend
cd frontend
npm run dev
# → http://localhost:5173

# Terminal 3 — Your chatbot service (optional)
# Start your service on port 8969
```
