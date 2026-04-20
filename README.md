# HackFlow

## Smart Hackathon Management System

A production-ready web-based platform for managing hackathons and large-scale tech events. HackFlow streamlines participant queues, volunteer coordination, and event operations through a unified, role-based interface.

---

## Features

### User Panel
- Join and track position in real-time queues
- View estimated wait times and counter availability
- Receive live updates and announcements
- Submit help requests

### Volunteer Panel
- Manage food and resource counters
- Handle participant help requests
- Monitor crowd zones and capacity
- Coordinate with other volunteers

### Admin Panel
- Complete user and role management
- Approve and manage volunteer registrations
- Control counter status and capacity
- Send event-wide announcements
- View analytics and insights

---

## Tech Stack

- **Backend:** Flask (Python)
- **Database:** Supabase (PostgreSQL)
- **Authentication:** Google OAuth + Email/Password
- **Frontend:** HTML, CSS, JavaScript (Responsive Dark Theme)
- **Deployment:** Google Cloud Run

---

## Architecture

HackFlow uses a role-based access control (RBAC) system with three distinct panels:

1. **User Panel** - For event participants to join queues and receive updates
2. **Volunteer Panel** - For event staff to manage operations
3. **Admin Panel** - For event organizers to control the entire system

All business logic is handled securely on the backend, with the database driving the application's state.

---

## Installation & Setup

### Prerequisites
- Python 3.8+
- Supabase account
- Google Cloud project (for OAuth)

### 1. Clone the repository
```bash
git clone <repository-url>
cd HackFlow
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Create environment file
Create a `.env` file in the project root:
```env
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_anon_key
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
SECRET_KEY=your_flask_secret_key
```

### 4. Run the application
```bash
python run.py
```

The app will be available at `http://localhost:5000`

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `SUPABASE_URL` | Yes | Your Supabase project URL |
| `SUPABASE_KEY` | Yes | Supabase anon/public key |
| `SUPABASE_SERVICE_KEY` | No | Supabase service role key |
| `GOOGLE_CLIENT_ID` | No | Google OAuth Client ID |
| `GOOGLE_CLIENT_SECRET` | No | Google OAuth Client Secret |
| `GOOGLE_REDIRECT_URI` | No | OAuth callback URL |
| `SECRET_KEY` | Yes | Flask secret key (generate random) |
| `FLASK_ENV` | No | development/production |
| `PORT` | No | Server port (default: 8080) |
| `BCRYPT_LOG_ROUNDS` | No | Password hashing rounds (default: 12) |
| `RATELIMIT_ENABLED` | No | Enable rate limiting |
| `SESSION_COOKIE_SECURE` | No | Require HTTPS for cookies |
| `WTF_CSRF_ENABLED` | No | Enable CSRF protection |

---

## Screenshots

> **Home Page**
> ![Home Page Placeholder]

> **User Dashboard**
> ![User Dashboard Placeholder]

> **Volunteer Dashboard**
> ![Volunteer Dashboard Placeholder]

> **Admin Panel**
> ![Admin Panel Placeholder]

---

## Future Improvements

- Real-time updates via WebSockets
- Advanced analytics dashboard
- AI-based crowd prediction
- Mobile application
- Multi-event support

---

## Security

- Role-based access control (RBAC)
- Backend validation for all requests
- Secure session management
- Password hashing with bcrypt
- CSRF protection in production
- Secure cookie settings (HttpOnly, SameSite)

---

## Testing

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-flask

# Run all tests
pytest

# Run with coverage
pytest --cov=hackflow --cov-report=html
```

### Test Structure

- `tests/test_auth.py` - Authentication routes and security
- `tests/test_protected.py` - Protected routes and authorization

### Test Coverage

- Login/logout flows
- Registration validation
- Role-based access control
- Session management
- API security

---

## Deployment (Google Cloud Run)

### 1. Build the Docker image

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

### 3. Set environment variables

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

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature-name`)
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

---

## License

MIT License

---

## Author

**Mukesh Kumar**  
B.Tech Student | Tech Hub BBS

- [GitHub](https://github.com/mukeshkumar)
- [LinkedIn](https://linkedin.com/in/mukeshkumar)
