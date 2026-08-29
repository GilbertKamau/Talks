# Live demo walkthrough — From Backend Code to the Cloud

Speaker script for the AWS Student Builder Group session. **Windows PowerShell** is the path we use on stage. Every command is here. Say the **why** before you paste the command.

On stage, use `curl.exe`, not `curl`. PowerShell’s `curl` is `Invoke-WebRequest` and will break the POST.

---

## What you are proving

Same API, four places:

1. Laptop (`localhost`)
2. Docker on the laptop
3. Image in **Amazon ECR**
4. Running on **Amazon ECS Express Mode** (Fargate + load balancer) with a public HTTPS URL

Then you show **Secrets Manager** (how config gets in) and **CloudWatch** (how you see traffic). **RDS** is explained and optional — do not start it unless you have spare time.

> **App Runner note:** The original architecture slide said App Runner or ECS. AWS closed App Runner to new accounts. ECS Express Mode is the replacement: you hand it a container image and two IAM roles, and it builds ECS on Fargate, an Application Load Balancer, security groups, autoscaling, HTTPS, and CloudWatch. You still explain every service it creates.

---

## Services you will name (keep this table on a backup slide)

| Service | What it is | What it entails tonight | Why we use it |
|---|---|---|---|
| **IAM** | Identity and Access Management: users, roles, policies | Two roles the platform assumes | Least privilege. The app never carries your long-lived access keys. |
| **STS** | Security Token Service | `get-caller-identity` | Proves which account you are in before you create resources. |
| **ECR** | Elastic Container Registry | One private repo, login, push | Versioned image store. ECS pulls from here instead of building on a random laptop. |
| **ECS** | Elastic Container Service | Express Mode service | Orchestrates containers. You do not SSH into a snowflake EC2 box. |
| **Fargate** | Serverless compute for ECS | Launch type under Express Mode | AWS runs the hosts. You only size CPU/memory. |
| **ELB / ALB** | Application Load Balancer | Created for you by Express Mode | Public HTTPS entry point, health checks, multi-AZ. |
| **VPC** | Virtual Private Cloud | Default VPC + public subnets | Isolated network. Default VPC is enough for this demo. |
| **Security groups** | Virtual firewalls | Created for ALB and tasks | Only the ports you intend (80/443 in, 8000 from ALB to task). |
| **Secrets Manager** | Managed secrets store | One secret, never printed on the slide | Passwords and API keys stay out of Git and out of the image. |
| **CloudWatch** | Logs, metrics, alarms | Tail logs after the live curl | You see errors before students report them in chat. |
| **ACM** | Certificate Manager | Automatic on `*.ecs.region.on.aws` | HTTPS without buying a cert for the workshop URL. |
| **RDS** (optional) | Managed relational database | Postgres instance + security group | State that survives task restarts. Skip if the clock is tight. |

---

## Before the room (you, 20 minutes earlier)

- [ ] Docker Desktop is **open** and the whale says **Engine running** (`docker info` works).
- [ ] AWS CLI v2 is installed: `aws --version`
- [ ] You are logged in: `aws sts get-caller-identity`
- [ ] Region is set. Use `us-east-1` unless you already know Express Mode in another region.
- [ ] You are in the demo folder (commands below assume that).
- [ ] Local Python venv or global install of `demo/requirements.txt` already done.

```powershell
cd C:\Users\user\Talks\talks\2026-08-19-backend-to-cloud\demo
aws sts get-caller-identity
docker info
```

If `docker info` errors with `dockerDesktopLinuxEngine` / `_ping` 500: start Docker Desktop, wait until it is healthy, open a **new** PowerShell window, retry. Do not debug Docker in front of the room for more than two minutes — skip Beat 2 and go to ECR with an image you built earlier.

Set these once and reuse them:

```powershell
$Region = "us-east-1"
$AccountId = aws sts get-caller-identity --query Account --output text
$Repo = "workshop-api"
$EcrUri = "$AccountId.dkr.ecr.$Region.amazonaws.com/$Repo"
aws configure get region
# If that is empty:
aws configure set region $Region
```

**Say:** STS answers “who am I?” IAM is the rulebook. We will not paste access keys into the Dockerfile.

---

## Beat 1 — Prove it on the laptop

**Say:** A modern backend still starts as code that answers on localhost. Production is what we add after this works.

```powershell
python -m pip install -r requirements.txt
python -m uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

Leave that window running. **New** PowerShell window:

```powershell
curl.exe http://localhost:8000/health
curl.exe http://localhost:8000/
curl.exe -X POST http://localhost:8000/echo -H "Content-Type: application/json" -d "{\"message\":\"JKUAT to the cloud\"}"
```

Expected:

```json
{"status":"ok","service":"workshop-api","stage":"local","secret_loaded":false,"database":"not-attached"}
```

```json
{"ok":true,"echo":"JKUAT to the cloud","ready_for_aws":true}
```

**Say:** `stage` is `local` because `APP_STAGE` is unset. After AWS it must become `cloud`. We never print secrets, only `secret_loaded: true/false`.

---

## Beat 2 — Same app, now a container

**Say:** Docker is not AWS. It is the box we ship. The Dockerfile binds to `0.0.0.0` so the process is reachable inside the container, not only on localhost inside the box.

Stop uvicorn first so port 8000 is free (Ctrl+C in that window), then:

```powershell
cd C:\Users\user\Talks\talks\2026-08-19-backend-to-cloud\demo
docker build -t workshop-api .
docker run --rm -p 8000:8000 workshop-api
```

New window — **same three curls**. You should get the same JSON.

**Say:** Business logic did not change. We only wrapped it. That is the rule for the rest of the night.

Stop the container with Ctrl+C in the `docker run` window.

---

## Beat 3 — Amazon ECR (the image warehouse)

**Say:** ECR is a private Docker Hub in your account. ECS will pull this image. If it is not in ECR, Fargate has nothing to run.

### Create the repository

```powershell
aws ecr create-repository --repository-name $Repo --region $Region
```

If it already exists, that is fine. Continue.

### Login Docker to ECR

```powershell
aws ecr get-login-password --region $Region | docker login --username AWS --password-stdin "$AccountId.dkr.ecr.$Region.amazonaws.com"
```

**Say:** This password is short-lived. That is STS again. We do not save it in a file.

### Tag and push

```powershell
docker tag workshop-api:latest "${EcrUri}:latest"
docker push "${EcrUri}:latest"
```

**Say:** `latest` is fine for a workshop. In production you would tag with a git SHA so you can roll back.

---

## Beat 4 — IAM roles ECS will assume

**Say:** Two different jobs, two roles. That is least privilege.

1. **Task execution role** (`ecsTaskExecutionRole`) — ECS itself: pull from ECR, write logs to CloudWatch. Trust: `ecs-tasks.amazonaws.com`.
2. **Infrastructure role** (`ecsInfrastructureRoleForExpressServices`) — Express Mode: create the load balancer, security groups, autoscaling. Trust: `ecs.amazonaws.com`.

```powershell
aws iam create-role --role-name ecsTaskExecutionRole --assume-role-policy-document file://iam/ecs-task-execution-trust.json
aws iam attach-role-policy --role-name ecsTaskExecutionRole --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy

aws iam create-role --role-name ecsInfrastructureRoleForExpressServices --assume-role-policy-document file://iam/ecs-express-infra-trust.json
aws iam attach-role-policy --role-name ecsInfrastructureRoleForExpressServices --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSInfrastructureRoleforExpressGatewayServices
```

If `EntityAlreadyExists`, the role is already there — continue.

```powershell
Start-Sleep -Seconds 20
```

**Say:** IAM is eventually consistent. We wait 20 seconds so Express Mode can assume the new roles.

---

## Beat 5 — Secrets Manager (config that is not Git)

**Say:** Secrets Manager stores values encrypted at rest. The image does not contain the secret. Tonight we create a workshop secret. We will inject `APP_STAGE=cloud` as a normal env var (not secret). A real password would only live here.

```powershell
aws secretsmanager create-secret --name workshop/api --secret-string "do-not-put-this-in-git" --region $Region
```

If it exists:

```powershell
aws secretsmanager put-secret-value --secret-id workshop/api --secret-string "do-not-put-this-in-git" --region $Region
```

Show metadata only — **do not paste the secret string on the projector**:

```powershell
aws secretsmanager describe-secret --secret-id workshop/api --region $Region --query "{Name:Name,ARN:ARN}"
```

**Say:** `describe-secret` has no secret value. `get-secret-value` does — we are not running that on the big screen.

---

## Beat 6 — ECS Express Mode (compute + HTTPS)

**Say this while it creates (3–5 minutes):**

- **ECS** schedules the container.
- **Fargate** is the worker. No EC2 for you to patch.
- **ALB** is the front door: TLS, health check on `/health`, more than one AZ.
- **VPC** default public subnets: tasks need a path to ECR and the internet.
- **Security groups**: ALB accepts 443; tasks accept 8000 from the ALB.
- **ACM**: the `*.on.aws` URL is already HTTPS.

Generate the container JSON from the template:

```powershell
(Get-Content .\primary-container.template.json -Raw) `
  -replace "ACCOUNT_ID", $AccountId `
  -replace "AWS_REGION", $Region `
  | Set-Content .\primary-container.json -Encoding ascii
Get-Content .\primary-container.json
```

Create the service (keep `--monitor-resources` so the CLI waits):

```powershell
aws ecs create-express-gateway-service `
  --service-name workshop-api `
  --execution-role-arn "arn:aws:iam::${AccountId}:role/ecsTaskExecutionRole" `
  --infrastructure-role-arn "arn:aws:iam::${AccountId}:role/ecsInfrastructureRoleForExpressServices" `
  --primary-container file://primary-container.json `
  --health-check-path "/health" `
  --cpu 1 `
  --memory 2 `
  --scaling-target "minTaskCount=1,maxTaskCount=2" `
  --monitor-resources
```

If `--primary-container file://...` is rejected on your CLI version, pass the JSON as one line:

```powershell
$containerJson = Get-Content .\primary-container.json -Raw
aws ecs create-express-gateway-service `
  --service-name workshop-api `
  --execution-role-arn "arn:aws:iam::${AccountId}:role/ecsTaskExecutionRole" `
  --infrastructure-role-arn "arn:aws:iam::${AccountId}:role/ecsInfrastructureRoleForExpressServices" `
  --primary-container $containerJson `
  --health-check-path "/health" `
  --monitor-resources
```

Read the URL:

```powershell
$ServiceArn = aws ecs list-services --cluster default --query "serviceArns[?contains(@, 'workshop-api')]" --output text
aws ecs describe-express-gateway-service --service-arn $ServiceArn
```

The URL looks like:

```text
https://workshop-api.ecs.us-east-1.on.aws/
```

If `list-services` is noisy, copy `serviceArn` from the create output.

**If create fails with assume-role:** wait one minute, run the same `create-express-gateway-service` again.

**If create fails because Express Mode is not in the region:** set `$Region = "us-west-2"` (or `eu-west-1`), recreate ECR in that region, retag/push, retry.

---

## Beat 7 — Same three requests, now on the cloud URL

Replace the host with **your** URL:

```powershell
$App = "https://workshop-api.ecs.us-east-1.on.aws"
curl.exe "$App/health"
curl.exe "$App/"
curl.exe -X POST "$App/echo" -H "Content-Type: application/json" -d "{\"message\":\"JKUAT to the cloud\"}"
```

`/health` must now show `"stage":"cloud"`. That is the punchline: identical code, different place.

---

## Beat 8 — CloudWatch (see the hits)

**Say:** CloudWatch Logs is the notebook of the service. Fargate sends stdout here. That is why `app.py` prints `GET /health`.

```powershell
aws logs describe-log-groups --region $Region --query "logGroups[?contains(logGroupName, 'workshop') || contains(logGroupName, 'ecs')].logGroupName"
```

Typical ECS log group is `/ecs/workshop-api` or similar. Tail whatever `describe-log-groups` returned:

```powershell
aws logs tail "/ecs/workshop-api" --follow --region $Region
```

If the name differs, paste the group from the previous command. Hit `/health` again in another window and watch the line appear.

**Say:** Metrics live in CloudWatch too (`CPUUtilization`, `RequestCount` on the ALB). An alarm is how you get paged before the WhatsApp group.

---

## Optional Beat 9 — RDS (only if you have time)

**Say:** RDS is a managed Postgres/MySQL. AWS patches the engine, takes backups, fails over. Our demo API does not query a database yet — `/health` only reports `database: not-attached` until `DATABASE_URL` is set. Creating RDS takes ~10 minutes and costs money. Students: skip unless you will delete it tonight.

What it entails:

1. Subnets in at least two AZs (DB subnet group)
2. Security group: port 5432 from the **ECS task** security group only, never `0.0.0.0/0`
3. Master password in **Secrets Manager**, not in the task definition plaintext
4. `DATABASE_URL` injected as a secret, then `/health` shows `"database":"configured"`

Sketch (do not run unless you mean it):

```powershell
aws rds create-db-instance `
  --db-instance-identifier workshop-db `
  --db-instance-class db.t4g.micro `
  --engine postgres `
  --master-username workshop `
  --master-user-password "USE_SECRETS_MANAGER_NOT_THIS" `
  --allocated-storage 20 `
  --publicly-accessible false `
  --region $Region
```

**Say:** `publicly-accessible false` is the point. The API in the VPC talks to RDS. The internet does not.

---

## Cleanup (do this before you leave the venue)

Students: leftover Fargate + ALB + RDS will burn the free tier.

```powershell
aws ecs delete-express-gateway-service --service-arn $ServiceArn --monitor-resources
aws ecr delete-repository --repository-name $Repo --force --region $Region
aws secretsmanager delete-secret --secret-id workshop/api --force-delete-without-recovery --region $Region
```

IAM roles can stay; they have no hourly cost. If you created RDS:

```powershell
aws rds delete-db-instance --db-instance-identifier workshop-db --skip-final-snapshot --region $Region
```

---

## If something fails on stage

| Symptom | Likely cause | Move |
|---|---|---|
| PowerShell `Headers` / `IDictionary` | Used `curl` instead of `curl.exe` | Rerun with `curl.exe` |
| Docker `_ping` 500 | Docker Desktop engine down | Start Desktop; or skip Beat 2 |
| `docker login` no basic auth | Pipe broke in PowerShell | Rerun login command as one pipeline |
| ECR `denied` | Wrong account/region or login expired | `get-caller-identity` + login again |
| Express Mode assume-role | Role too new | Sleep 60s, retry create |
| ALB unhealthy | App still bound to 127.0.0.1 or wrong port | Dockerfile already uses `0.0.0.0` and `PORT` |
| `/health` still `stage: local` | Env not in `primary-container.json` | Check the file, update the service |
| HTTPS browser warning | You used `http://` on the `.on.aws` URL | Use `https://` |

---

## Suggested spoken timeline (demo block ~50 minutes)

1. Beats 1–2 — 10 min (local + Docker)
2. Beats 3–5 — 12 min (ECR, IAM, Secrets Manager)
3. Beat 6 — 10 min create + explanation while it provisions
4. Beats 7–8 — 10 min live URL + logs
5. Buffer — 8 min for retries

Then return to the production-habits slide.
