# 🚀 RailBlock AI Deployment Guide

Comprehensive instructions for deploying **RailBlock AI (IR-ABPS)** across cloud platforms, Docker containers, virtual servers, or local network environments.

---

## 📑 Deployment Options

| Option | Best For | Complexity | Cost |
| :--- | :--- | :---: | :---: |
| **Option 1: 1-Click Free Cloud (Render / Railway)** | Quick public demo & sharing | ⭐ Easy | Free |
| **Option 2: Docker / Docker Compose** | Containers, Kubernetes, On-Premises | ⭐⭐ Medium | Flexible |
| **Option 3: Linux Cloud Server (AWS / Azure / DigitalOcean)** | Enterprise production & high availability | ⭐⭐⭐ Advanced | Standard |
| **Option 4: Local LAN / Divisional Control Room** | Internal railway network deployment | ⭐ Easy | Free |

---

## Option 1: 1-Click Cloud Deployment (Render / Railway / Koyeb)

### Deploy to Render.com (Free)
1. Fork or push this repository to your **GitHub** account.
2. Sign in to [Render.com](https://render.com) and click **"New Web Service"**.
3. Connect your GitHub repository.
4. Render automatically detects `render.yaml` or you can configure manually:
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
5. Click **"Deploy Web Service"** — your live URL will be ready in ~60 seconds!

### Deploy to Railway.app
1. Go to [Railway.app](https://railway.app) and click **"New Project" ➔ "Deploy from GitHub repo"**.
2. Select your repository. Railway will detect the `Procfile` and deploy automatically.

---

## Option 2: Docker & Docker Compose

### Build and Run with Docker Compose
```bash
# Clone or navigate to the repository
cd railblock_ai

# Build and start container in detached mode
docker-compose up -d --build

# View container logs
docker-compose logs -f
```
Your service will be live at `http://localhost:8000`.

### Standalone Docker Run
```bash
# Build docker image
docker build -t railblock-ai:latest .

# Run container
docker run -d -p 8000:8000 --name railblock-server railblock-ai:latest
```

---

## Option 3: Enterprise Linux VPS Deployment (AWS EC2 / Ubuntu)

### Step 1: Server Setup
```bash
# Update system packages
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3-pip python3-venv nginx certbot python3-certbot-nginx git

# Create application directory
sudo mkdir -p /var/www/railblock_ai
sudo chown -R $USER:$USER /var/www/railblock_ai

# Copy or clone files to /var/www/railblock_ai
cd /var/www/railblock_ai
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Step 2: Configure Systemd Service
```bash
# Copy systemd unit file
sudo cp railblock-ai.service /etc/systemd/system/

# Reload and start service
sudo systemctl daemon-reload
sudo systemctl enable railblock-ai
sudo systemctl start railblock-ai
sudo systemctl status railblock-ai
```

### Step 3: Configure Nginx & SSL Certificate
```bash
# Copy Nginx configuration
sudo cp nginx.conf /etc/nginx/sites-available/railblock
sudo ln -s /etc/nginx/sites-available/railblock /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Test and reload Nginx
sudo nginx -t
sudo systemctl reload nginx

# Optional: Enable HTTPS with free Let's Encrypt SSL
sudo certbot --nginx -d your-domain.com -d abps.indianrailways.gov.in
```

---

## Option 4: Local LAN / Divisional Network Deployment

To make the application accessible to other computers on your local WiFi / Divisional office network:

```powershell
# Run Uvicorn listening on 0.0.0.0
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

Colleagues on the same network can access via your computer's IP address:
`http://<YOUR_LOCAL_IP>:8000` (e.g. `http://192.168.1.45:8000`).

---

## 🔒 Post-Deployment Verification Checklist

1. **Health Check Endpoint**:
   ```bash
   curl http://localhost:8000/api/network
   ```
2. **AI Optimizer Test**:
   ```bash
   curl -X POST http://localhost:8000/api/optimize
   ```
3. **Interactive API Documentation**: Navigate to `http://<YOUR_DOMAIN>/docs`
4. **Log in to Officer Portal**: Use default credentials (`operating` / `rail123`) or create custom accounts in `backend/auth.py`.
