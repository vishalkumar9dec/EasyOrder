# EasyOrder (Swiggy Builder Program Project)

EasyOrder is a WhatsApp-first agentic food coordination system linked with a collaborative visual PWA canvas. Groups can plan their food orders (Swiggy Food) and supplies (Swiggy Instamart) in real-time, enforcing budgets and executing checkouts sequentially via Swiggy OAuth.

---

## 1. Project Directory Structure

```text
/Users/vishalkumar/projects/swiggy_builder_prog/
├── docs/                        # Specifications & architectural designs
│   ├── easyorder-prd.md         # Product Requirements Document
│   ├── hld.md                   # High-Level Design (Architecture & Flows)
│   ├── lld.md                   # Low-Level Design (APIs & Interfaces)
│   ├── decision-map.md          # Log of resolved design decisions
│   └── easyorder-visual-guide.md# Mockups and user journey flows
├── CONTEXT.md                   # Project Domain Glossary
└── README.md                    # This file (Setup & Debugging Guide)
```

---

## 2. Local-First & Freemium Setup

This project is designed to be fully testable and debuggable locally for **₹0** before deploying to cloud hosting.

### 2.1 Backend Local Setup (Python FastAPI)
1. Navigate to the backend directory (once created) and create a virtual environment:
   ```bash
   cd src/backend
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
2. Start the FastAPI server locally:
   ```bash
   uvicorn main:app --reload --port 8000
   ```
3. Expose port 8000 for Meta WhatsApp Webhooks using **localtunnel** (Free):
   ```bash
   npx localtunnel --port 8000
   ```
4. Copy the secure HTTPS URL provided and paste it into the Webhook settings on the Meta App Dashboard under the WhatsApp Cloud API section.

### 2.2 Frontend Local Setup (React PWA)
1. Navigate to the frontend directory:
   ```bash
   cd src/frontend
   npm install
   ```
2. Start the local Vite server:
   ```bash
   npm run dev
   ```

### 2.3 Database Emulator Setup (Firestore)
We use the **Firebase Local Emulator Suite** during development to avoid read/write cloud costs:
1. Ensure the Firebase CLI is installed:
   ```bash
   npm install -g firebase-tools
   ```
2. Start the emulators:
   ```bash
   firebase emulators:start --only firestore
   ```
3. Set the environment variable in your local shell running FastAPI or React:
   ```bash
   export FIRESTORE_EMULATOR_HOST="localhost:8080"
   ```
   All database writes will route to the emulator interface (`http://localhost:4000/firestore`).

---

## 3. Authentication & Access Scopes

* **Guest Token:** Delivered publicly in the group URL (`/session/{id}?token=guest_abc`). Restricts modifications to cart items only.
* **Host Token:** Delivered privately to the host's WhatsApp phone. Enables administrative functions and the **Swiggy OAuth Handoff** flow.
* **Swiggy OAuth Callback:** Swiggy returns authorization codes to `https://easyorder.app/oauth/callback?code=xxx`. The backend exchanges this for an access token to create carts on Swiggy MCP.
