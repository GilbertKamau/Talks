# Live demo walkthrough — beginners, AWS Console

**Audience:** first-time AWS builders  
**Rule:** the laptop is for *your code*. The **AWS Management Console** (the website) is for *every AWS service*.  
**On Windows:** use `curl.exe`, never `curl`.

Zoom the browser to **125%**. Stay in region **N. Virginia (`us-east-1`)** unless the room agrees otherwise. The region is the orange/white menu at the **top right**.

---

## Picture of the journey (draw this, then keep it on screen)

```mermaid
flowchart LR
  subgraph laptop [Your laptop]
    Code[Python API]
    Box[Docker box]
  end
  subgraph aws [AWS Console]
    ECR[ECR\nimage warehouse]
    SM[Secrets Manager\nlocked drawer]
    ECS[ECS Express Mode\nruns the box]
    ALB[Load balancer\nfront door]
    RDS[RDS Postgres\nfiling cabinet]
    CW[CloudWatch\nCCTV logs]
  end
  User[Browser / curl]
  Code --> Box --> ECR --> ECS
  SM -.-> ECS
  ECS --> ALB
  ECS --> RDS
  ECS --> CW
  User --> ALB
```

**Say in one breath:** We write an API, pack it in a Docker box, store the box in ECR, tell ECS to run it, visitors knock on the load balancer, RDS holds data that survives restarts, and CloudWatch is the camera that records what happened.

---

## What each service *looks like* (use these analogies)

| Orange console name | Picture for beginners | Why we open it tonight |
|---|---|---|
| **IAM** | Staff badges. A *role* is a job badge a service wears, not a person. | ECS needs two badges: “pull images / write logs” and “build the load balancer”. The console can create them. |
| **ECR** | A locked warehouse for Docker boxes. | So AWS has *your* image, not a file on your USB. |
| **Secrets Manager** | A hotel safe. You store the key; you do not tape it to the door (Git). | Show that passwords do not live in the Dockerfile. |
| **ECS** | The factory manager. **Fargate** = AWS owns the factory floor. | Runs the container 24/7 without you SSH-ing into a server. |
| **Express Mode** | A “deploy my website” wizard *inside* ECS. | One Create button builds ECS + load balancer + HTTPS + logs. |
| **ELB / ALB** | The building’s front door and receptionist. | Public HTTPS URL, health checks (`/health`). |
| **VPC + security groups** | Neighbourhood fence + bouncer. | Default VPC is fine. Bouncer only lets web traffic in. |
| **CloudWatch** | CCTV + guestbook. | We *see* the same curls that hit the live URL. |
| **ACM** | Free HTTPS name tag on `*.on.aws`. | Padlock in the browser without buying a domain. |
| **RDS** | A managed PostgreSQL filing cabinet. AWS patches and backs it up. | Beat 7. Tasks can be replaced; student data should not vanish. |

App Runner was on the old architecture slide. **New AWS accounts cannot start App Runner.** Express Mode is the replacement — same story, different wizard.

---

## Before the session (you only)

1. Open [https://console.aws.amazon.com/](https://console.aws.amazon.com/) and sign in.
2. Top right region = **N. Virginia**.
3. Docker Desktop whale is steady (**Engine running**).
4. Folder ready:

```powershell
cd C:\Users\user\Talks\talks\2026-08-19-backend-to-cloud\demo
```

Split the screen: **left = PowerShell**, **right = AWS Console**. Beginners follow the console; you type the few local commands.

---

## Beat 1 — Laptop (PowerShell only)

**Show:** code answering on your machine. No AWS yet.

```powershell
python -m pip install -r requirements.txt
python -m uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

New PowerShell window:

```powershell
curl.exe http://localhost:8000/health
curl.exe http://localhost:8000/
curl.exe -X POST http://localhost:8000/echo -H "Content-Type: application/json" -d "{\"message\":\"JKUAT to the cloud\"}"
```

Point at `"stage":"local"`. **Say:** when this is in the cloud, that word must become `cloud`.

---

## Beat 2 — Docker box (PowerShell only)

**Show:** same API, now inside a container. Still not AWS.

Stop uvicorn (Ctrl+C), then:

```powershell
docker build -t workshop-api .
docker run --rm -p 8000:8000 workshop-api
```

Same three `curl.exe` lines. Stop the container (Ctrl+C).

If Docker says `_ping` 500: start Docker Desktop, wait, new PowerShell. Do not lose the room here.

---

## Beat 3 — ECR in the Console (warehouse)

**Search bar at the top:** type `ECR` → **Elastic Container Registry**.

1. **Repositories** → **Create repository**.
2. Visibility: **Private**.
3. Repository name: `workshop-api`.
4. Leave scanning defaults → **Create**.

You now have an empty warehouse. **Say:** ECS cannot run what we have not stored.

### Put the box in the warehouse

On the repository page click **View push commands**. Choose the **Windows** tab. AWS shows four commands. Run them **in this order** in PowerShell from the `demo` folder.

They look like this (your account number will differ):

```powershell
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 123456789012.dkr.ecr.us-east-1.amazonaws.com
docker build -t workshop-api .
docker tag workshop-api:latest 123456789012.dkr.ecr.us-east-1.amazonaws.com/workshop-api:latest
docker push 123456789012.dkr.ecr.us-east-1.amazonaws.com/workshop-api:latest
```

**Say:** the first line is a short-lived badge to the warehouse (not a password you save). Refresh ECR — you should see image tag `latest`.

If `aws` is missing, the push-commands page still works if AWS CLI is installed; install from [AWS CLI Windows](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html) before the talk if needed. That is the only CLI beginners need, and only because Docker must talk to ECR.

---

## Beat 4 — Secrets Manager in the Console (the safe)

**Search:** `Secrets Manager` → **Secrets** → **Store a new secret**.

1. Secret type: **Other type of secret**.
2. Key/value: key `workshop` value `do-not-put-this-in-git` (do **not** zoom this value on the projector — type it, then click away).
3. Secret name: `workshop/api`.
4. Next, next, **Store**.

Open the secret. Show **Secret name** and **ARN** only. **Do not** click Retrieve secret value on the big screen.

**Say:** Git is a postcard. This is a safe. The app should read from here, never from a committed `.env`.

---

## Beat 5 — ECS Express Mode in the Console (run it)

**Search:** `ECS` → **Elastic Container Service**.

Left sidebar: **Express mode** → **Create**.

Fill the wizard slowly, and name each box:

| Field | What to enter | What you say |
|---|---|---|
| **Image URI** | **Browse ECR images** → `workshop-api` → tag `latest` | “This is the box we just pushed.” |
| **Task execution role** | **Create new role** if empty | “Badge to pull ECR and write CloudWatch logs.” |
| **Infrastructure role** | **Create new role** if empty | “Badge to build the front door (load balancer) for us.” |
| **Additional configurations** | Open this section | “We customise port and health so the receptionist knows we are alive.” |
| **Name** | `workshop-api` | Becomes part of the public URL. |
| **Container port** | `8000` | Matches Dockerfile / uvicorn. Default 80 would fail. |
| **Health check path** | `/health` | ALB asks this path; our API returns JSON 200. |
| **Environment variables** | Key `APP_STAGE` Value type **Environment variable** Value `cloud` | This is how `/health` flips from local to cloud. |
| | Key `PORT` Value `8000` | Same port inside Fargate. |
| **CPU / Memory** | 1 vCPU / 2 GB (defaults OK) | “We rent a small worker, not a whole server.” |
| **Min / max tasks** | Min `1` Max `2` | “Autoscaling ceiling so a typo cannot spawn 20 machines.” |

**Create.** Stay on the page.

**While it spins (3–5 minutes), click Resources / Timeline and narrate:**

1. Cluster (folder of apps)
2. Task definition (recipe)
3. Fargate task (the actual running box)
4. Application Load Balancer (front door + HTTPS)
5. Target group + health check
6. Security groups (bouncers)
7. CloudWatch log group
8. Autoscaling policy

If you see **Unable to assume the service linked role**, wait 15 seconds and click Create again.

When status is **Active**, copy **Application URL** (`https://workshop-api.ecs.us-east-1.on.aws` or similar). Open it in the browser, then:

```powershell
$App = "https://PASTE-YOUR-URL-HERE"
curl.exe "$App/health"
curl.exe "$App/"
curl.exe -X POST "$App/echo" -H "Content-Type: application/json" -d "{\"message\":\"JKUAT to the cloud\"}"
```

**Circle `"stage":"cloud"` on screen.** Same three routes as localhost.

---

## Beat 6 — CloudWatch in the Console (the camera)

**Search:** `CloudWatch` → **Logs** → **Log groups**.

Open the group that contains `workshop-api` or `ecs` / your cluster name. Open the newest **log stream**. You should see lines like `GET /health stage=cloud`.

Hit `$App/health` again and click **Refresh** on the stream.

**Say:** this is how you debug without asking “did it work?” in the chat.

Optional visual: CloudWatch → **Metrics** → `AWS/ApplicationELB` or `AWS/ECS` — request count going up.

---

## Beat 7 — RDS in the Console (filing cabinet)

**Say:** ECS tasks are disposable. If the box restarts, memory is gone. **RDS** is a managed PostgreSQL database: AWS installs it, patches it, and can take backups. We prove it works with `GET /db`, which runs `SELECT 1` inside Postgres.

Start this create while Express Mode is still provisioning if you can — RDS often takes **8–12 minutes**.

### 7a. Create the database

**Search:** `RDS` → **Amazon RDS** → **Databases** → **Create database**.

| Click | Choose | Why |
|---|---|---|
| Creation method | **Standard create** | Easy create hides the network story. |
| Engine | **PostgreSQL** (leave default version) | Matches the `/db` check in our API. |
| Templates | **Free tier** if you see it, else **Dev/Test** | Classroom size. |
| DB instance identifier | `workshop-db` | Name on the list. |
| Master username | `workshop` | The app login. |
| Credentials | **Self managed** → type a password once, write it on paper off-screen | This password goes into Secrets Manager, never into Git. |
| Instance | `db.t4g.micro` or `db.t3.micro` | Smallest that still boots. |
| Storage | 20 GiB, uncheck autoscaling if shown | Stops surprise bills. |
| Connectivity / VPC | **default VPC** | Same neighbourhood as ECS. |
| Public access | **No** | The internet must not open Postgres. ECS in the same VPC still reaches it. |
| VPC security group | **Create new** named `workshop-db-sg` | We will unlock port 5432 only for ECS. |
| DB name (Additional config) | `workshop` | `/db` will report this name. |

**Create database.** Status goes **Creating** → wait until **Available**. Do not continue until it is Available.

Open the database. On **Connectivity & security** copy **Endpoint** (looks like `workshop-db.xxxx.us-east-1.rds.amazonaws.com`). Port is **5432**.

### 7b. Let ECS reach Postgres (the bouncer)

**Say:** a security group is a bouncer. RDS should only admit our API boxes, never the whole internet.

1. **ECS** → **Clusters** → `default` → service `workshop-api` → **Tasks** (or **Configuration** / **Networking**) → open a running task → **ENI** / **Network** → copy the **security group** id (`sg-...`). That is the task’s badge.
2. **EC2** → **Security Groups** → `workshop-db-sg` → **Edit inbound rules** → **Add rule**:
   - Type: **PostgreSQL**
   - Port: **5432**
   - Source: **Custom** → paste the ECS task security group (not `0.0.0.0/0`)
   - Save

Outbound on the ECS task group is usually already **All traffic**. Leave it.

### 7c. Put the connection string in Secrets Manager

**Search:** Secrets Manager → **Store a new secret** → **Other type of secret**.

Plaintext (or one key `url`) — build this off the projector, then paste:

```text
postgresql://workshop:YOUR_PASSWORD@YOUR_ENDPOINT:5432/workshop
```

Secret name: `workshop/database-url` → **Store**.

**Say:** the URL is the key to the filing cabinet. The container will read `DATABASE_URL` from this secret.

### 7d. Point the running API at RDS

You must be on the **new image** that includes `GET /db` (rebuild + ECR **View push commands** if this laptop still has the old image).

**ECS** → **Express mode** → `workshop-api` → **Update** / **Edit**.

**Additional configurations → Environment variables → Add:**

| Key | Value type | Value |
|---|---|---|
| `DATABASE_URL` | **Secret** | Choose `workshop/database-url` (or paste its ARN) |

Keep `APP_STAGE=cloud` and `PORT=8000`. Save / deploy. Wait until the service is **Active** again (new task).

---

## How we test that RDS is working

Do these **in order**. If a later check fails, do not skip ahead.

### Test 1 — RDS itself is up (Console)

**RDS** → `workshop-db`

- Status badge is **Available** (not Creating / Backing-up only).
- Endpoint is visible.
- **Monitoring** tab: after Test 3, **DatabaseConnections** should leave 0.

If status is not Available, `/db` cannot work yet.

### Test 2 — the API sees a URL (`/health`)

```powershell
curl.exe "$App/health"
```

**Working:** `"database":"connected"`  
**Not wired yet:** `"database":"not-attached"` → secret / env var missing, or old task still running.  
**Reachable URL but login/network fail:** `"database":"error"` → go to Test 3 for the reason.

### Test 3 — Postgres answers `SELECT 1` (`/db`)

This is the real proof. The API opens a connection and runs `SELECT 1`.

```powershell
curl.exe "$App/db"
```

**Working (HTTP 200):**

```json
{"status":"connected","ping":1,"database_name":"workshop","engine":"PostgreSQL"}
```

Open that URL in the browser too so the room *sees* it.

| Result | Meaning | Fix |
|---|---|---|
| `503` `"not-attached"` | `DATABASE_URL` is not in the task | Add the secret env var, wait for a new task |
| `502` timeout / could not connect | Bouncer or VPC | Inbound 5432 from the **task** SG; same default VPC; RDS Available |
| `502` password authentication failed | Wrong URL | Recreate `workshop/database-url`, update service |
| `502` database "workshop" does not exist | DB name blank at create | Use `/postgres` in the URL or create DB `workshop` |

### Test 4 — CloudWatch saw the query

**CloudWatch** → log stream → look for `GET /db status=connected`.

### Test 5 — RDS Monitoring (visual for beginners)

**RDS** → `workshop-db` → **Monitoring** → **Database connections**. After a few `/db` hits the line should bump above zero.

**One sentence for the room:** if `/db` returns `ping: 1` and CloudWatch shows `GET /db status=connected`, the filing cabinet is live.

---

## Cleanup in the Console (do this with the room)

Leaving Fargate + a load balancer running costs money.

1. **ECS** → **Express mode** (or **Clusters** → `default` → service `workshop-api`) → **Delete**.
2. **ECR** → repository `workshop-api` → **Delete**.
3. **Secrets Manager** → `workshop/api` → **Delete** (disable recovery if you want it gone today).
4. **RDS** → `workshop-db` → **Actions** → **Delete** → uncheck final snapshot → delete. Do this first if you created it; RDS is the expensive leftover.
5. **Secrets Manager** → also delete `workshop/database-url`.

IAM roles can stay; they do not charge by the hour.

---

## If the room gets stuck

| What they see | What it means | What you do |
|---|---|---|
| PowerShell `IDictionary` / Headers | They typed `curl` | `curl.exe` |
| Docker `_ping` 500 | Engine not running | Start Docker Desktop |
| ECR push `denied` | Not logged in or wrong region | Region N. Virginia + View push commands again |
| Express Mode health **unhealthy** | Port not 8000 or path not `/health` | Additional configurations: port `8000`, path `/health` |
| `/health` still `"stage":"local"` | Missing env var | Edit service, add `APP_STAGE=cloud`, deploy |
| `/db` is `not-attached` | No `DATABASE_URL` on the new task | Secret env var + wait until a new task is Running |
| `/db` timeout / 502 | SG or RDS not Available | Available badge + inbound 5432 from task `sg-...` |
| Blank browser page | Used `http://` | Use the `https://` Application URL |

---

## Suggested talking clock (demo ~50 min)

1. Laptop + Docker — 10 min  
2. ECR console + push commands — 10 min  
3. Secrets Manager — 5 min  
4. Express Mode wizard + wait — 15 min  
5. Live URL + CloudWatch — 10 min  
6. RDS create (overlap the wait) + `/db` test — 15 min
