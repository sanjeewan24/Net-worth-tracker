## 📌 Net Worth Tracker Pro – README

### 🚀 Overview
Net Worth Tracker Pro is a **professional desktop application** built with **Python & PyQt6** that helps you **manage assets, liabilities, track income/expenses, view charts, export reports, and calculate real-time net worth** with automated price updates using APIs.

## ✨ Features
**✔ Asset & Liability Management**  
**✔ Real-time Price Updates (Crypto / Stocks / Gold)**  
**✔ Interactive Charts using Matplotlib**  
**✔ Excel-based Data Storage**  
**✔ Smart Cash & Bank Currency Conversion**  
**✔ Auto Backup System**  
**✔ Export Report to PDF**  
**✔ Modern UI with Dark / Light Themes**  
**✔ Startup Loading Screen & Progress Logs**

## ⚙ Requirements
Add this as `requirements.txt`:
```
pandas
openpyxl
PyQt6
matplotlib
yfinance
pycoingecko
requests
reportlab
google-generativeai
```

## 🧠 How It Works
- All data stored **in Excel files**
- Startup screen **checks missing/corrupted files** and rebuilds them
- **Gemini API & CoinGecko & Yahoo Finance** used to update prices
- JSON **config.json** stores theme, API keys, last update date etc.

