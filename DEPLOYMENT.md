# Step-by-Step Deployment Guide (Render.com)

Deploying to Render is the easiest free method to get your bot's web interface online 24/7. Heroku or Railway follow nearly the exact same steps.

## Prerequisites
1. You must have your code pushed to a **GitHub** repository.
2. An account on [Render.com](https://render.com/).

---

## Step 1: Create a Web Service
1. Log in to Render.com.
2. Click **New** in the top right, and select **Web Service**.
3. Under "Build and deploy from a Git repository", click **Next**.
4. Connect your GitHub account and select your `Binance_Futures_Testnet_Trading_Bot_CLI` repository.

## Step 2: Configure the Service
Fill out the service details as follows:
- **Name:** Whatever you want (e.g., `binance-testnet-bot`).
- **Region:** Choose whatever is closest to you or the exchange servers.
- **Branch:** `main` (or whatever your default branch is).
- **Environment:** Select `Python 3`.
- **Build Command:** `pip install -r requirements.txt` (this is the default).
- **Start Command:** `uvicorn web.server:app --host 0.0.0.0 --port $PORT`

## Step 3: Add Environment Variables
This is the most critical step. Since `.env` is (and should be!) ignored by Git, Render won't know your keys. You need to inject them securely.

1. Scroll down to the **Environment Variables** section.
2. Click **Add Environment Variable**.
3. Add your keys exactly as they appear in your `.env` file:
   - Key 1: 
     - **Name:** `BINANCE_FUTURES_API_KEY`
     - **Value:** `[paste your key here]`
   - Key 2:
     - **Name:** `BINANCE_FUTURES_API_SECRET`
     - **Value:** `[paste your secret here]`

## Step 4: Deploy
1. Click the **Create Web Service** button at the bottom.
2. Render will automatically pull your code, install the requirements, and start the Uvicorn server.
3. You will see a log console showing the progress. Wait until you see `Build successful` and `Uvicorn running on http://0.0.0.0...`.

## Step 5: Access Your Bot
Once the deployment finishes, Render will provide you with a live URL at the top left (it usually looks like `https://binance-testnet-bot-xxxx.onrender.com`).

Click that link, and you will see your glassmorphic Web Interface running live on the internet! 

> [!WARNING]
> Because it's a testnet bot, it's safe if someone accidentally clicks the link, but it's generally best practice not to share the URL publicly since it has direct access to your testnet account. On Render, you can also add simple HTTP authentication if desired.
