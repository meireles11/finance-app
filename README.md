# 💰 Stock Portfolio Web App

This is a Flask-based web application that simulates a stock trading platform.  
Originally developed as part of Harvard's [CS50x](https://cs50.harvard.edu/x/) course — Week 9: Flask.  
Users can register, log in, quote real stock prices, buy and sell shares, and view their portfolio and transaction history.

---

## 🚀 Features

- User registration and login with secure password hashing
- Quote real-time(ish) stock prices (via API)
- Buy and sell shares with cash balance updates
- Deposit additional funds
- View portfolio with current stock values
- Complete transaction history with timestamps
- Session management with Flask-Session
- SQLite database with raw SQL queries

---

## 🛠 Technologies

- Python + Flask
- HTML, CSS, Jinja Templates
- SQLite
- CS50's SQL library
- Flask-Session
- Bootstrap (if used)
- Lookup API (included in `helpers.py`)

---

## 💾 Getting Started

### 1. Clone the repo

```bash
git clone https://github.com/meireles11/finance-app.git
cd finance-app
