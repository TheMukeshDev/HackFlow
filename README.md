# 🚀 HackFlow

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.8%2B-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/Flask-%23000000?style=for-the-badge&logo=flask&logoColor=white" alt="Flask">
  <img src="https://img.shields.io/badge/Supabase-3ECFAC?style=for-the-badge&logo=supabase&logoColor=white" alt="Supabase">
  <img src="https://img.shields.io/badge/Google%20Cloud%20Run-4285F4?style=for-the-badge&logo=googlecloud&logoColor=white" alt="Cloud Run">
  <img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" alt="License">
  <a href="https://github.com/TheMukeshDev/HackFlow/actions/workflows/test.yml"><img src="https://img.shields.io/badge/Tests-passing-success?style=for-the-badge" alt="Tests"></a>
  <a href="https://codecov.io/gh/TheMukeshDev/HackFlow"><img src="https://img.shields.io/badge/Coverage-80%25%2B-green?style=for-the-badge" alt="Coverage"></a>
</p>

<p align="center">
  <a href="https://github.com/TheMukeshDev/HackFlow/stargazers"><img src="https://img.shields.io/github/stars/TheMukeshDev/HackFlow?style=flat-square&color=yellow" alt="Stars"></a>
  <a href="https://github.com/TheMukeshDev/HackFlow/network"><img src="https://img.shields.io/github/forks/TheMukeshDev/HackFlow?style=flat-square&color=orange" alt="Forks"></a>
  <a href="https://github.com/TheMukeshDev/HackFlow/issues"><img src="https://img.shields.io/github/issues/TheMukeshDev/HackFlow?style=flat-square&color=red" alt="Issues"></a>
</p>

---

> **Smart Hackathon Management System** — A production-ready platform for managing hackathons and large-scale tech events. Streamline participant queues, volunteer coordination, and event operations through a unified, role-based interface.

---

## ✨ Features

### 🔹 User Panel
- Join and track position in real-time queues
- View estimated wait times and counter availability
- Receive live updates and announcements
- Submit help requests

### 🔹 Volunteer Panel
- Manage food and resource counters
- Handle participant help requests
- Monitor crowd zones and capacity
- Coordinate with other volunteers

### 🔹 Admin Panel
- Complete user and role management
- Approve and manage volunteer registrations
- Control counter status and capacity
- Send event-wide announcements
- View analytics and insights

### 🔐 Security & Scalability
- **Role-based access control (RBAC)** — Three distinct user roles with granular permissions
- **Secure authentication** — Google OAuth + Email/Password login with bcrypt hashing
- **Backend validation** — All requests validated server-side
- **Production security** — CSRF protection, secure cookies (HttpOnly, SameSite)
- **Cloud-native** — Scales automatically on Google Cloud Run

---

## 🛠 Tech Stack

| Category | Technology |
|----------|------------|
| **Backend** | Flask (Python) |
| **Database** | Supabase (PostgreSQL) |
| **Authentication** | Google OAuth + Email/Password |
| **Frontend** | HTML, CSS, JavaScript |
| **Deployment** | Google Cloud Run |
| **Testing** | Pytest + Coverage |
| **Containerization** | Docker |

---

## 📁 Project Structure

```
HackFlow/
├── app/
│   ├── __init__.py
│   ├── auth/
│   │   ├── __init__.py
│   │   └── routes.py
│   ├── main/
│   │   ├── __init__.py
│   │   └── routes.py
│   ├── models/
│   │   ├── __init__.py
│   │   └── user.py
│   ├── templates/
│   │   ├── auth/
│   │   ├── main/
│   │   └── base.html
│   ├── static/
│   │   ├── css/
│   │   ├── js/
│   │   └── images/
│   └── utils/
│       ├── __init__.py
│       └── decorators.py
├── tests/
│   ├── test_auth.py
│   └── test_protected.py
├── .env
├── .gitignore
├── requirements.txt
├── run.py
└── Dockerfile
```

---

## 🚦 Quick Start

```bash
# Clone the repository
git clone https://github.com/TheMukeshDev/HackFlow.git
cd HackFlow

# Install dependencies
pip install -r requirements.txt

# Run the application
python run.py
```

> Access the app at `http://localhost:5000`

---

## ⚙️ Installation & Setup

### Prerequisites
- Python 3.8+
- Supabase account
- Google Cloud project (for OAuth)

### 1. Clone the Repository
```bash
git clone https://github.com/TheMukeshDev/HackFlow.git
cd HackFlow
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables
Create a `.env` file in the project root:

```env
# Supabase
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_anon_key

# Google OAuth
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret

# Flask
SECRET_KEY=your_flask_secret_key
FLASK_ENV=development
```

### 4. Run the Application
```bash
python run.py
```

---

## 🔧 Environment Variables

| Variable | Required | Description |
|----------|:--------:|-------------|
| `SUPABASE_URL` | ✅ | Your Supabase project URL |
| `SUPABASE_KEY` | ✅ | Supabase anon/public key |
| `SUPABASE_SERVICE_KEY` | ❌ | Supabase service role key |
| `GOOGLE_CLIENT_ID` | ❌ | Google OAuth Client ID |
| `GOOGLE_CLIENT_SECRET` | ❌ | Google OAuth Client Secret |
| `GOOGLE_REDIRECT_URI` | ❌ | OAuth callback URL |
| `SECRET_KEY` | ✅ | Flask secret key |
| `FLASK_ENV` | ❌ | `development` or `production` |
| `PORT` | ❌ | Server port (default: 8080) |
| `BCRYPT_LOG_ROUNDS` | ❌ | Hashing rounds (default: 12) |
| `RATELIMIT_ENABLED` | ❌ | Enable rate limiting |
| `SESSION_COOKIE_SECURE` | ❌ | Require HTTPS for cookies |
| `WTF_CSRF_ENABLED` | ❌ | Enable CSRF protection |

---

## 🧪 Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=hackflow --cov-report=html
```

### Test Coverage
- Login/logout flows
- Registration validation
- Role-based access control
- Session management
- API security

---

## ☁️ Deployment (Google Cloud Run)

### 1. Build the Docker Image
```bash
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/hackflow
```

### 2. Deploy to Cloud Run
```bash
gcloud run deploy hackflow \
  --image gcr.io/YOUR_PROJECT_ID/hackflow \
  --platform managed \
  --region asia-south2 \
  --allow-unauthenticated
```

### 3. Set Environment Variables
```bash
gcloud run services update hackflow \
  --update-env-vars "\
SUPABASE_URL=your-supabase-url,\
SUPABASE_KEY=your-supabase-key,\
FLASK_ENV=production,\
SECRET_KEY=your-secure-secret,\
GOOGLE_CLIENT_ID=your-client-id,\
GOOGLE_CLIENT_SECRET=your-secret,\
GOOGLE_REDIRECT_URI=https://your-app.run.app/auth/google/callback" \
  --region asia-south2
```

### 4. Configure Google OAuth
In Google Cloud Console > APIs & Services > Credentials:

- **Authorized redirect URIs:**
  ```
  https://your-app.run.app/auth/google/callback
  ```
- **Authorized JavaScript origins:**
  ```
  https://your-app.run.app
  ```

---

## 🔮 Future Enhancements

- 🌐 Real-time updates via WebSockets
- 📊 Advanced analytics dashboard
- 🤖 AI-based crowd prediction
- 📱 Mobile application
- 🎪 Multi-event support

---

## 🤝 Contributing

Contributions are welcome! Follow these steps:

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature-name`)
3. **Commit** your changes
4. **Push** to the branch
5. **Open** a Pull Request

---

## 📄 License

MIT License — See [LICENSE](LICENSE) for details.

---

## 👤 Author

<p>
  <strong>Mukesh Kumar</strong><br>
  B.Tech Student | Tech Hub BBS
</p>

<p>
  <a href="https://linkedin.com/in/themukeshdev"><img src="https://img.shields.io/badge/LinkedIn-0077B5?style=flat-square&logo=linkedin&logoColor=white" alt="LinkedIn"></a>
  <a href="https://github.com/TheMukeshDev"><img src="https://img.shields.io/badge/GitHub-181717?style=flat-square&logo=github&logoColor=white" alt="GitHub"></a>
</p>

---

<p align="center">Made with ❤️ by <a href="https://github.com/TheMukeshDev">Mukesh Kumar</a></p>