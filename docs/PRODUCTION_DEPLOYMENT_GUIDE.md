# ResQ Web — Production Deployment Guide
**Next.js Frontend (Vercel) • FastAPI Backend (Render) • PostgreSQL Database (Supabase)**

---

## 1. Production Architecture Overview

ResQ Web operates as a full-stack, enterprise-grade process management and fault recovery system. In production, the system utilizes a modern, resilient cloud architecture:

```
+--------------------------------------------------------------------------+
|                            USER BROWSER / CLIENT                         |
+--------------------------------------------------------------------------+
                                    │
                                    │ HTTPS (Port 443)
                                    ▼
+--------------------------------------------------------------------------+
|                      VERCEL (Frontend Host / CDN)                        |
|   • Next.js 14 App Router, React, Tailwind CSS Light Theme               |
|   • Production URL: https://resq-web.vercel.app                          |
+--------------------------------------------------------------------------+
                     │                                   │
      REST API (HTTPS)                                   │ WebSockets (WSS)
                     ▼                                   ▼
+--------------------------------------------------------------------------+
|                       RENDER (Backend API Service)                       |
|   • FastAPI ASGI Server (Uvicorn), Background Daemons, REST & WS Routes  |
|   • Production URL: https://resq-web-backend.onrender.com                |
+--------------------------------------------------------------------------+
                                    │
                                    │ TCP / TLS (Port 6543 / 5432)
                                    ▼
+--------------------------------------------------------------------------+
|                  SUPABASE (Managed PostgreSQL Cloud Database)            |
|   • Connection Pooler (PgBouncer Transaction Mode)                       |
|   • Tables: applications, process_runs, recovery_attempts, events,       |
|             system_metrics                                               |
+--------------------------------------------------------------------------+
                                    ▲
                                    │ Hybrid Agent Sync (Optional)
+--------------------------------------------------------------------------+
|             LOCAL WINDOWS SUPERVISOR AGENT (Win32 Native Engine)         |
|   • Kernel handles (OpenProcess, WaitForSingleObject, Job Objects)       |
|   • Syncs process state and telemetry into the shared Supabase DB        |
+--------------------------------------------------------------------------+
```

---

## 2. Step 1: Database Setup on Supabase

Your Supabase PostgreSQL database is hosted on AWS Mumbai (`aws-0-ap-south-1`).

### 2.1 Connection String & URL Percent-Encoding
Your raw connection string contains the password `Nikhardh@25`. Because the `@` symbol is reserved in RFC 3986 URIs to separate credentials from the host, standard URL parsers (SQLAlchemy, psycopg2, Render) split at `@25` unless the `@` inside the password is URL-encoded as `%40`.

* **Raw Connection String:**
  ```text
  postgresql://postgres.zrujkuahfrdgwjhlojcy:Nikhardh@25@aws-0-ap-south-1.pooler.supabase.com:6543/postgres
  ```
* **Production RFC 3986 Encoded Connection String (USE THIS):**
  ```text
  postgresql://postgres.zrujkuahfrdgwjhlojcy:Nikhardh%4025@aws-0-ap-south-1.pooler.supabase.com:6543/postgres
  ```

> **Automatic Sanitization Built-in:** ResQ Web's backend code (`backend/app/database/session.py`) automatically sanitizes and encodes your database URL on boot, but setting the `%40` version directly in environment variables guarantees 100% compatibility across all deployment CLI tools.

### 2.2 Pooler Ports: 6543 vs 5432
* **Port `6543` (Recommended for Cloud Serverless / Free Tier):** Supabase PgBouncer Transaction Pooler. Ideal for high numbers of concurrent connections without exhausting PostgreSQL connection limits.
* **Port `5432`:** Supabase Session Pooler or Direct Connection. Use if you perform complex session-level transactions or DDL migrations.

### 2.3 Automatic Schema Creation
You do not need to run manual SQL migration scripts. ResQ Web's FastAPI startup hook executes `Base.metadata.create_all(bind=engine)` upon boot, automatically creating:
* `applications`
* `process_runs`
* `recovery_attempts`
* `events`
* `system_metrics`

---

## 3. Step 2: Backend Deployment on Render

Render hosts the FastAPI application using Ubuntu Linux with Python 3.11/3.12.

### Option A: 1-Click Blueprint (`render.yaml`)
A `render.yaml` configuration is included at the root of your repository.
1. Log in to [Render Dashboard](https://dashboard.render.com).
2. Click **New +** -> **Blueprint**.
3. Select your GitHub repository (`dhairyadesai26/ResQ`).
4. Render will detect `render.yaml` and configure the Web Service automatically.
5. Click **Apply**.

### Option B: Manual Setup via Render Dashboard
1. Go to [dashboard.render.com](https://dashboard.render.com) and click **New +** -> **Web Service**.
2. Connect your GitHub repository: `https://github.com/dhairyadesai26/ResQ.git`.
3. Configure the following fields:
   * **Name:** `resq-web-backend`
   * **Region:** `Singapore` (Lowest latency to Supabase Mumbai `ap-south-1`)
   * **Branch:** `main`
   * **Root Directory:** *(leave blank / repository root)*
   * **Runtime:** `Python 3`
   * **Build Command:**
     ```bash
     pip install -r backend/requirements.txt
     ```
   * **Start Command:**
     ```bash
     uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT
     ```
   * **Plan Type:** `Free`

4. Add **Environment Variables** under the **Environment** tab:

   | Key | Value | Description |
   | :--- | :--- | :--- |
   | `PYTHON_VERSION` | `3.11.10` | Enforces modern Python runtime |
   | `DATABASE_URL` | `postgresql://postgres.zrujkuahfrdgwjhlojcy:Nikhardh%4025@aws-0-ap-south-1.pooler.supabase.com:6543/postgres` | Your Supabase Pooler URL |
   | `ALLOWED_ORIGINS` | `*` *(or your Vercel URL)* | Configures CORS access |
   | `LOG_LEVEL` | `INFO` | FastAPI logging verbosity |
   | `HOST` | `0.0.0.0` | Binds to Render's public network interface |

5. Under **Advanced Settings**:
   * **Health Check Path:** `/api/v1/system/health`
   * **Auto-Deploy:** `Yes`
6. Click **Create Web Service**.
7. Wait 1-2 minutes for the build to finish. Once deployed, copy your Render URL:
   `https://resq-web-backend.onrender.com`

---

## 4. Step 3: Frontend Deployment on Vercel

Vercel hosts the Next.js 14 frontend with global edge caching and SSL.

### Step-by-Step Vercel Deployment:
1. Log in to [Vercel Dashboard](https://vercel.com).
2. Click **Add New...** -> **Project**.
3. Import your GitHub repository: `dhairyadesai26/ResQ`.
4. In the **Configure Project** screen:
   * **Project Name:** `resq-web`
   * **Framework Preset:** `Next.js`
   * **Root Directory:** Click **Edit** and select `frontend` (⚠️ **CRITICAL: Must be `frontend`**).
   * **Build Command:** `pnpm run build` (or leave default `next build`)
   * **Output Directory:** `.next`
   * **Install Command:** `pnpm install`
5. Expand the **Environment Variables** section and add:

   | Key | Value | Notes |
   | :--- | :--- | :--- |
   | `NEXT_PUBLIC_API_URL` | `https://resq-web-backend.onrender.com` | Replace with your exact Render service URL (no trailing slash) |
   | `NEXT_PUBLIC_WS_URL` | `wss://resq-web-backend.onrender.com/ws` | Must use secure WebSocket protocol `wss://` |

6. Click **Deploy**.
7. In ~60 seconds, your deployment will be live at:
   `https://resq-web.vercel.app`

---

## 5. Step 4: Hybrid Architecture & Process Supervision

### Operating Systems Context
ResQ Web is built to demonstrate genuine **Windows Process Management** using low-level Win32 APIs:
* `OpenProcess(PROCESS_QUERY_INFORMATION | SYNCHRONIZE | PROCESS_TERMINATE)`
* `WaitForSingleObject(hProcess, timeout)`
* `GetExitCodeProcess(hProcess, &exitCode)`
* `AssignProcessToJobObject`

Because Render and Vercel run on Linux cloud servers:
1. **Cloud Mode:** The FastAPI backend on Render operates as the central API, coordinating database records on Supabase, handling WebSocket broadcasting, and serving telemetry to Vercel.
2. **Hybrid Windows Supervisor Agent (Local Host):**
   To monitor real Windows applications (e.g. `calc.exe`, `notepad.exe`, Python crash test apps) and have them appear live on your Vercel dashboard:
   * Configure your local `.env` in `backend/` to point to your Supabase PostgreSQL database:
     ```env
     DATABASE_URL=postgresql://postgres.zrujkuahfrdgwjhlojcy:Nikhardh%4025@aws-0-ap-south-1.pooler.supabase.com:6543/postgres
     ```
   * Run the local supervisor on your Windows machine:
     ```powershell
     python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
     ```
   * Any process launched or recovered on your Windows machine will immediately sync to Supabase and stream live to your Vercel production dashboard!

---

## 6. Production Verification & Testing Checklist

Once deployed, verify all layers using this checklist:

### A. Backend Health & Database Check
Open your browser or terminal and test the Render endpoint:
```bash
curl https://resq-web-backend.onrender.com/api/v1/system/health
```
**Expected Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "database": "connected",
  "active_supervisors": 1
}
```

### B. Interactive Swagger Docs
Visit the interactive OpenAPI docs:
`https://resq-web-backend.onrender.com/docs`

### C. Frontend Dashboard Verification
1. Open your Vercel URL: `https://resq-web.vercel.app`.
2. Check the **System Status Pill** in the top navigation:
   * Should display a green badge: **"System Operational"** or **"Connected"**.
3. Navigate to **System Health**:
   * Inspect real-time CPU and Memory gauges.
4. Navigate to **Applications**:
   * Click **+ Register Application**.
   * Add a test application and verify that it appears instantly in the list.
5. Navigate to **OS Events**:
   * Verify all lifecycle transitions are timestamped with real Indian Standard Time (IST).

---

## 7. Troubleshooting Common Production Issues

### Issue 1: Supabase `getaddrinfo failed` or `password authentication failed`
* **Root Cause:** The unencoded `@` in `Nikhardh@25` caused the host to parse as `25@aws-0-ap-south-1...`.
* **Fix:** Ensure `DATABASE_URL` in Render environment variables uses `Nikhardh%4025`.

### Issue 2: Vercel displays `NetworkError when attempting to fetch resource`
* **Root Cause:** CORS rejection or Render free tier "spin down" after inactivity.
* **Fix:**
  1. Free-tier Render services sleep after 15 minutes of inactivity; allow 30 seconds for the first request to wake the service.
  2. Ensure Render environment variable `ALLOWED_ORIGINS` is set to `*` or your Vercel domain.

### Issue 3: WebSocket connection fails on Vercel (`Connection closed before receiving a handshake`)
* **Root Cause:** Insecure `ws://` used instead of `wss://`.
* **Fix:** Ensure `NEXT_PUBLIC_WS_URL` starts with `wss://` (e.g. `wss://resq-web-backend.onrender.com/ws`).

