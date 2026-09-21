# DigiWallet 💸

DigiWallet is a modern, feature-rich personal finance management desktop application built with Python and `customtkinter`. It helps you track your expenses, manage incomes and savings, set financial goals, and visualize your financial health with an intuitive interface.

## ✨ Features

- **Multi-user Authentication:** Create an account, sign in securely, and keep your financial data private.
- **Transaction Tracking:** Record your expenses, incomes, and savings with ease.
- **Categories & Tags:** Organize and filter your transactions effectively.
- **Multiple Currencies:** Support for custom currencies alongside your base currency.
- **Recurring Transactions:** Automate your finances with recurring rules for rent, salary, etc.
- **Projects & Goals:** Create funds (e.g., "New Laptop") and track your saving progress.
- **Visual Reports & Exports:** Analyze your spending with charts (via `matplotlib`) and export data (via `reportlab`).
- **Customizable Appearance:** Choose between Light and Dark modes, and personalize the app with Blue, Pink, or Green accent colors.
- **Local Storage:** All your data is securely stored locally using SQLite.

---

## 🚀 Getting Started

### Prerequisites

- **Python 3.13+** installed on your system.
- **`uv` package manager**: We recommend using `uv` for fast dependency management. If you don't have it installed, you can get it by following the [official uv installation guide](https://docs.astral.sh/uv/getting-started/installation/).

### Cloning the Repository

First, open your terminal (or Command Prompt / PowerShell on Windows) and clone the project:

```bash
git clone <your-repository-url>
cd DigiWallet
```

### Installation and Running

We use `uv` to manage the environment and dependencies. It automatically creates a virtual environment, installs dependencies, and runs the app.

#### 🍎 macOS & 🐧 Linux

```bash
# Sync dependencies and create a virtual environment
uv sync

# Run the application
uv run main.py
```

#### 🪟 Windows

```powershell
# Sync dependencies and create a virtual environment
uv sync

# Run the application
uv run main.py
```

*Note: Alternatively, if you prefer using standard `pip`, you can create a virtual environment with `python -m venv venv`, activate it, install dependencies from `pyproject.toml` or `requirements.txt`, and run `python main.py`.*

### 🐳 Running via Docker

Because DigiWallet is a GUI application, running it in a Docker container requires connecting the container to your host machine's display server via X11 forwarding.

**1. Build the image:**
```bash
docker build -t digiwallet .
```

**2. Run the container:**

*On Linux:*
```bash
# Allow local X11 connections
xhost +local:docker

# Run the container with X11 forwarding and a volume for the database
docker run -it --rm \
    --net=host \
    -e DISPLAY=$DISPLAY \
    -v /tmp/.X11-unix:/tmp/.X11-unix \
    -v ~/.digital_wallet:/root/.digital_wallet \
    digiwallet
```

*On macOS:*
1. Install [XQuartz](https://www.xquartz.org/).
2. Open XQuartz > Settings > Security > Check "Allow connections from network clients".
3. Restart your Mac.
4. Run in your terminal:
```bash
# Allow connections from your local IP
xhost + $(ipconfig getifaddr en0)

# Run the container
docker run -it --rm \
    -e DISPLAY=$(ipconfig getifaddr en0):0 \
    -v /tmp/.X11-unix:/tmp/.X11-unix \
    -v ~/.digital_wallet:/root/.digital_wallet \
    digiwallet
```

*On Windows:*
1. Install an X Server like [VcXsrv](https://sourceforge.net/projects/vcxsrv/).
2. Launch XLaunch. Check "Multiple windows", "Start no client", and crucially, **check "Disable access control"**.
3. Run in PowerShell:
```powershell
# Replace YOUR_IP with your machine's local IPv4 address
docker run -it --rm `
    -e DISPLAY=YOUR_IP:0.0 `
    -v $env:USERPROFILE\.digital_wallet:/root/.digital_wallet `
    digiwallet
```

---

## 📖 User Guide

### 1. Creating an Account
When you first launch the app, you will be greeted by the Sign In screen. Click on **"Create a new account"**. You will be asked to provide a display name, username, password, and your preferred Base Currency (e.g., MAD, USD).

### 2. Dashboard
Once signed in, the Dashboard provides a quick overview of your finances. You can view your total balance, recent transactions, and a snapshot of your spending patterns.

### 3. Adding Transactions
To add a new record, navigate to the **Ledger Book** or use the quick add button. 
- **Type**: Choose between Expense, Income, or Savings.
- **Amount & Currency**: Enter the amount. You can change the currency if it's different from your base currency.
- **Category & Tags**: Assign a category (e.g., Food, Transport) and optional tags to keep things organized.
- **Project**: If it's a Savings transaction, you can link it to a specific Project/Goal.

### 4. Projects & Goals
In the **Settings > Projects** tab, you can create financial goals (e.g., "Vacation Fund") with a target amount and an optional deadline. By linking savings transactions to a project, you can visually track your progress through progress bars.

### 5. Recurring Rules
Automate your regular transactions by navigating to **Settings > Recurring**. Add a rule for your monthly rent, bi-weekly salary, or weekly subscriptions. DigiWallet will automatically apply these when you sign in on or after the scheduled date.

### 6. Managing Settings
The Settings panel is your control center:
- **Profile**: Update your display name and change your password.
- **Appearance**: Toggle between Light and Dark mode, and choose your favorite accent color.
- **Categories, Tags & Currencies**: Add, edit, or delete items to customize the app to your specific needs. 

### Data Privacy
All data is stored locally in an SQLite database on your machine. Your passwords are hashed and salted for security.

---

## 🛠 Built With

- [Python 3.13+](https://www.python.org/)
- [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) - A modern and customizable UI library based on Tkinter.
- [Matplotlib](https://matplotlib.org/) - For generating financial charts.
- [ReportLab](https://www.reportlab.com/) - For generating PDF reports.
- [SQLite3](https://docs.python.org/3/library/sqlite3.html) - For local data storage.
