# Deploying Talently to Railway

Everything on Railway - simple and free ($5 credit).

## Prerequisites
1. GitHub account with this repo pushed
2. Railway account (https://railway.app)
3. Cloudinary account for file storage (https://cloudinary.com) - free
4. OpenAI API key

---

## Step 1: Set up Cloudinary (2 min)
1. Sign up at https://cloudinary.com
2. Go to Dashboard
3. Copy your `CLOUDINARY_URL` (looks like `cloudinary://123456:abcdef@cloudname`)

---

## Step 2: Deploy to Railway (10 min)

### Create Project
1. Go to https://railway.app → Sign in with GitHub
2. Click **"New Project"** → **"Deploy from GitHub repo"**
3. Select your repository

### Add PostgreSQL Database
1. In your project, click **"New"** → **"Database"** → **"PostgreSQL"**
2. Railway automatically sets `DATABASE_URL` ✓

### Deploy Backend
1. Click **"New"** → **"GitHub Repo"** → Select same repo
2. Click on the new service → **Settings**
3. Set **Root Directory**: `backend`
4. Go to **Variables** tab, add:
   ```
   AI_PROVIDER=openai
   OPENAI_API_KEY=sk-your-key-here
   SECRET_KEY=any-random-string-here-abc123
   JWT_SECRET_KEY=another-random-string-xyz789
   CLOUDINARY_URL=cloudinary://your-url-from-step-1
   FRONTEND_URL=https://your-frontend.up.railway.app
   ```
5. Railway auto-deploys! Copy the backend URL (e.g., `https://talently-backend-xxx.up.railway.app`)

### Deploy Frontend
1. Click **"New"** → **"GitHub Repo"** → Select same repo again
2. Click on the new service → **Settings**
3. Set **Root Directory**: `frontend`
4. Set **Build Command**: `npm run build`
5. Set **Start Command**: `npm run start`
6. Go to **Variables** tab, add:
   ```
   VITE_API_URL=https://your-backend-url.up.railway.app/api
   ```
7. Copy the frontend URL

### Update Backend CORS
1. Go back to your **backend** service → Variables
2. Update `FRONTEND_URL` with your actual frontend URL

---

## Step 3: Test It!

1. Open your frontend URL
2. Sign up for an account
3. Upload a resume
4. Watch the AI extract data ✨

---

## Cost

Railway gives **$5 free credit** - enough for ~1-2 weeks of light usage.

After that: ~$5-10/month for small apps.

---

## Troubleshooting

### "Application failed to respond"
- Check your environment variables are set correctly
- Check Railway logs for errors

### Database connection errors
- Make sure PostgreSQL is added and linked
- Railway auto-sets `DATABASE_URL`

### Files not uploading
- Check `CLOUDINARY_URL` is set correctly
- Verify Cloudinary dashboard shows uploads

### CORS errors
- Make sure `FRONTEND_URL` in backend matches your actual frontend URL
- Include the full URL with `https://`

---

## Local Development

Still works exactly the same:

```bash
# Terminal 1 - Backend
cd backend
./venv/Scripts/activate  # Windows
source venv/bin/activate  # Mac/Linux
pip install -r requirements.txt
python run.py

# Terminal 2 - Frontend  
cd frontend
npm install
npm run dev
```

No cloud services needed locally!
