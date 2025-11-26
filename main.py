import sys
import os
import json
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
import openpyxl
from openpyxl import Workbook
import requests
from calculator import FinancialCalculator, CurrencyConverter
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QTableWidget, 
                             QTableWidgetItem, QLineEdit, QComboBox, QDialog,
                             QFormLayout, QMessageBox, QTabWidget, QScrollArea,
                             QProgressBar, QFileDialog, QInputDialog, QStatusBar,
                             QTextEdit, QDateEdit, QDoubleSpinBox, QCheckBox, QSizePolicy)
import google.generativeai as genai
from datetime import datetime
import traceback
from PyQt6.QtCore import Qt, QTimer, QDate
from PyQt6.QtGui import QFont, QIcon
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from theme_manager import ThemeManager
from pycoingecko import CoinGeckoAPI
import yfinance as yf

class DataManager:
    """Manages all Excel and JSON data operations"""
    
    def __init__(self):
        self.data_dir = Path("data")
        self.backup_dir = Path("backups")
        self.config_file = "config.json"
        self.initialize_storage()
        
    def initialize_storage(self):
        """Create all necessary directories and files"""
        self.data_dir.mkdir(exist_ok=True)
        self.backup_dir.mkdir(exist_ok=True)
        
        # Initialize Excel files
        excel_files = {
            "assets.xlsx": ["ID", "Date", "Category", "Name", "Quantity", "Price_Per_Unit", "Value", "Notes"],
            "liabilities.xlsx": ["ID", "Date", "Type", "Name", "Amount", "Interest_Rate", "Notes"],
            "transactions.xlsx": ["ID", "Timestamp", "Action", "Category", "Description", "Value_Before", "Value_After"],
            "monthly_networth.xlsx": ["Month", "Total_Assets", "Total_Liabilities", "Net_Worth", "Change_Percent"],
            "income_expense.xlsx": ["ID", "Date", "Type", "Category", "Description", "Amount"],
            "goals.xlsx": ["ID", "Goal_Name", "Target_Amount", "Current_Amount", "Deadline", "Status"]
        }
        
        for filename, headers in excel_files.items():
            filepath = self.data_dir / filename
            # Always recreate if file doesn't exist or is corrupted
            if not filepath.exists() or not self._is_valid_excel(filepath):
                self._create_excel_file(filepath, headers)
        
        # Initialize config
        if not os.path.exists(self.config_file):
            default_config = {
                "theme": "dark",
                "currency": "USD",
                "password_hash": None,
                "last_backup": None,
                "gemini_api_key": "",
                "auto_update_enabled": False,
                "current_user": "default",
                "last_auto_update_date": None  # ✅ ADD THIS LINE
            }
            self.save_config(default_config)
    
    def _is_valid_excel(self, filepath):
        """Check if file is a valid Excel file"""
        try:
            # Try to read just the first row to validate
            pd.read_excel(filepath, nrows=0)
            return True
        except Exception:
            return False
    
    def _create_excel_file(self, filepath, headers):
        """Create a new Excel file with headers"""
        try:
            # If file exists and is corrupted, remove it
            if filepath.exists():
                filepath.unlink()
            
            # Create new file using pandas (more reliable than openpyxl directly)
            df = pd.DataFrame(columns=headers)
            df.to_excel(filepath, index=False, engine='openpyxl')
            print(f"Created: {filepath}")
        except Exception as e:
            print(f"Error creating {filepath}: {e}")
            raise
    
    def save_config(self, config):
        """Save configuration to JSON"""
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=4)
    
    def load_config(self):
        """Load configuration from JSON"""
        try:
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            # Return default config if file doesn't exist
            default_config = {
                "theme": "dark",
                "currency": "USD",
                "password_hash": None,
                "last_backup": None,
                "gemini_api_key": "",
                "auto_update_enabled": False,
                "current_user": "default",
                "last_auto_update_date": None  # ✅ ADD THIS LINE
            }
            self.save_config(default_config)
            return default_config
    
    def read_excel(self, filename):
        """Read Excel file and return DataFrame with error handling"""
        filepath = self.data_dir / filename
        
        try:
            # Try to read the file
            df = pd.read_excel(filepath, engine='openpyxl')
            
            # ✅ Fix for assets.xlsx - ensure proper columns exist
            if filename == "assets.xlsx" and not df.empty:
                # Add missing columns with defaults
                if 'Quantity' not in df.columns:
                    df['Quantity'] = 1.0
                if 'Price_Per_Unit' not in df.columns:
                    df['Price_Per_Unit'] = df.get('Value', 0.0)
                
                # Fill NaN values
                df['Quantity'] = df['Quantity'].fillna(1.0)
                df['Price_Per_Unit'] = df['Price_Per_Unit'].fillna(0.0)
                df['Value'] = df['Value'].fillna(0.0)
            
            return df
        except Exception as e:
            print(f"Error reading {filename}: {e}")
            print(f"Attempting to recreate {filename}...")
            
            # Determine headers based on filename
            headers_map = {
                "assets.xlsx": ["ID", "Date", "Category", "Name", "Value", "Notes"],
                "liabilities.xlsx": ["ID", "Date", "Type", "Name", "Amount", "Interest_Rate", "Notes"],
                "transactions.xlsx": ["ID", "Timestamp", "Action", "Category", "Description", "Value_Before", "Value_After"],
                "monthly_networth.xlsx": ["Month", "Total_Assets", "Total_Liabilities", "Net_Worth", "Change_Percent"],
                "income_expense.xlsx": ["ID", "Date", "Type", "Category", "Description", "Amount"],
                "goals.xlsx": ["ID", "Goal_Name", "Target_Amount", "Current_Amount", "Deadline", "Status"]
            }
            
            headers = headers_map.get(filename, ["ID", "Data"])
            self._create_excel_file(filepath, headers)
            
            # Return empty DataFrame with correct columns
            return pd.DataFrame(columns=headers)
    
    def write_excel(self, filename, df):
        """Write DataFrame to Excel file"""
        filepath = self.data_dir / filename
        try:
            df.to_excel(filepath, index=False, engine='openpyxl')
        except Exception as e:
            print(f"Error writing to {filename}: {e}")
            raise
    
    def add_record(self, filename, record_dict):
        """Add a new record to Excel file"""
        df = self.read_excel(filename)
        new_row = pd.DataFrame([record_dict])
        df = pd.concat([df, new_row], ignore_index=True)
        self.write_excel(filename, df)
        
        # Only log transaction if not adding to transactions.xlsx itself
        if filename != "transactions.xlsx":
            self.log_transaction("ADD", filename, record_dict)
    
    def update_record(self, filename, record_id, updates):
        """Update existing record in Excel file"""
        df = self.read_excel(filename)
        old_value = df.loc[df['ID'] == record_id].to_dict('records')[0] if not df[df['ID'] == record_id].empty else {}
        
        for key, value in updates.items():
            df.loc[df['ID'] == record_id, key] = value
        
        self.write_excel(filename, df)
        self.log_transaction("UPDATE", filename, {"id": record_id, "old": old_value, "new": updates})
    
    def delete_record(self, filename, record_id):
        """Delete record from Excel file"""
        df = self.read_excel(filename)
        old_value = df.loc[df['ID'] == record_id].to_dict('records')[0] if not df[df['ID'] == record_id].empty else {}
        df = df[df['ID'] != record_id]
        self.write_excel(filename, df)
        self.log_transaction("DELETE", filename, {"id": record_id, "deleted": old_value})
    
    def log_transaction(self, action, category, details):
        """Log all changes to transactions file"""
        try:
            log_entry = {
                "ID": self.generate_id("transactions.xlsx"),
                "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Action": action,
                "Category": category,
                "Description": str(details),
                "Value_Before": str(details.get("old", "")),
                "Value_After": str(details.get("new", ""))
            }
            
            # Read current transactions
            df = self.read_excel("transactions.xlsx")
            new_row = pd.DataFrame([log_entry])
            df = pd.concat([df, new_row], ignore_index=True)
            self.write_excel("transactions.xlsx", df)
        except Exception as e:
            print(f"Error logging transaction: {e}")
            # Don't raise - logging failure shouldn't stop the main operation
    
    def generate_id(self, filename):
        """Generate unique ID for new records"""
        df = self.read_excel(filename)
        if df.empty:
            return 1
        return int(df['ID'].max()) + 1 if 'ID' in df.columns else len(df) + 1
    
    def create_backup(self):
        """Create backup of all Excel files"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_folder = self.backup_dir / f"backup_{timestamp}"
        backup_folder.mkdir(exist_ok=True)
        
        import shutil
        for file in self.data_dir.glob("*.xlsx"):
            try:
                shutil.copy(file, backup_folder / file.name)
            except Exception as e:
                print(f"Error backing up {file.name}: {e}")
        
        config = self.load_config()
        config["last_backup"] = timestamp
        self.save_config(config)
        return str(backup_folder)
    
    def get_crypto_price(self, crypto_id="bitcoin"):
        """Deprecated - use Gemini API instead"""
        return None
    
    def get_asset_price(self, asset_name, asset_category, log_callback=None):
        """
        Fetch current market price using CoinGecko (crypto) or yfinance (stocks/gold)
        
        Args:
            asset_name: Name of the asset (e.g., "BTC", "AAPL", "Gold")
            asset_category: Category from Excel ("Crypto", "Stocks", "Gold/Silver")
            log_callback: Optional callback for logging
        
        Returns:
            float: Current price in USD, or None if failed
        """
        try:
            if log_callback:
                log_callback(f"[INFO] Fetching price for: {asset_name} ({asset_category})")
            
            # Route to appropriate API based on category
            if asset_category == 'Crypto':
                return self._get_crypto_price_coingecko(asset_name, log_callback)
            elif asset_category in ['Stocks', 'Gold/Silver']:
                return self._get_price_yfinance(asset_name, asset_category, log_callback)
            else:
                if log_callback:
                    log_callback(f"[WARNING] Unsupported category: {asset_category}")
                return None
                
        except Exception as e:
            if log_callback:
                log_callback(f"[ERROR] Failed to fetch price for {asset_name}: {str(e)}")
            return None
    
    def _get_crypto_price_coingecko(self, asset_name, log_callback=None):
        """Fetch cryptocurrency price from CoinGecko"""
        try:
            cg = CoinGeckoAPI()
            
            # Map common crypto symbols to CoinGecko IDs
            crypto_map = {
                'BTC': 'bitcoin',
                'ETH': 'ethereum',
                'SOL': 'solana',
                'AVAX': 'avalanche-2',
                'INJ': 'injective-protocol',
                'DOT': 'polkadot',
                'NEAR': 'near',
                'OM': 'mantra-dao',
                'GRT': 'the-graph',
                'APT': 'aptos',
                'FIL': 'filecoin',
                'TIA': 'celestia',
                'POL': 'polygon-ecosystem-token',
                'MATIC': 'polygon-ecosystem-token',
                'OP': 'optimism',
                'ICP': 'internet-computer',
                'ARB': 'arbitrum',
                'LDO': 'lido-dao',
                'USDT': 'tether',
                'USDC': 'usd-coin',
                'BNB': 'binancecoin',
                'XRP': 'ripple',
                'ADA': 'cardano',
                'DOGE': 'dogecoin',
                'LINK': 'chainlink',
                'UNI': 'uniswap',
                'ATOM': 'cosmos',
                'LTC': 'litecoin',
                'BCH': 'bitcoin-cash',
                'XLM': 'stellar',
                'ALGO': 'algorand',
                'VET': 'vechain',
                'HBAR': 'hedera-hashgraph',
                'FTM': 'fantom',
                'SAND': 'the-sandbox',
                'MANA': 'decentraland',
                'AXS': 'axie-infinity',
                'THETA': 'theta-token',
                'XTZ': 'tezos',
                'EOS': 'eos',
                'AAVE': 'aave',
                'MKR': 'maker',
                'SNX': 'synthetix-network-token',
                'COMP': 'compound-governance-token',
            }
            
            # Get CoinGecko ID
            coin_id = crypto_map.get(asset_name.upper(), asset_name.lower())
            
            # Fetch price
            price_data = cg.get_price(ids=coin_id, vs_currencies='usd')
            
            if coin_id in price_data and 'usd' in price_data[coin_id]:
                price = price_data[coin_id]['usd']
                if log_callback:
                    log_callback(f"[SUCCESS] {asset_name}: ${price:,.2f} (CoinGecko)")
                return float(price)
            else:
                if log_callback:
                    log_callback(f"[ERROR] {asset_name}: Not found on CoinGecko")
                return None
                
        except Exception as e:
            if log_callback:
                log_callback(f"[ERROR] CoinGecko API error for {asset_name}: {str(e)}")
            return None
    
    def _get_price_yfinance(self, asset_name, asset_category, log_callback=None):
        """Fetch stock/commodity price from Yahoo Finance"""
        try:
            # Map asset names to Yahoo Finance tickers
            if asset_category == 'Gold/Silver':
                ticker_map = {
                    'Gold': 'GC=F',         # Gold Futures (per oz)
                    'GOLD': 'GC=F',
                    'Silver': 'SI=F',       # Silver Futures (per oz)
                    'SILVER': 'SI=F',
                    'Platinum': 'PL=F',
                    'Palladium': 'PA=F',
                }
                ticker = ticker_map.get(asset_name, asset_name)
                
                # Fetch data from yfinance
                asset = yf.Ticker(ticker)
                
                # Try to get current price
                try:
                    price_per_oz = asset.fast_info['lastPrice']
                except:
                    info = asset.info
                    price_per_oz = info.get('regularMarketPrice') or info.get('currentPrice')
                
                if price_per_oz and price_per_oz > 0:
                    # Convert from price per ounce to price per gram
                    # 1 troy ounce = 31.1035 grams
                    price_per_gram = price_per_oz / 31.1035
                    
                    if log_callback:
                        log_callback(f"[SUCCESS] {asset_name}: ${price_per_gram:.2f}/g (${price_per_oz:,.2f}/oz) (Yahoo Finance)")
                    return float(price_per_gram)
                else:
                    if log_callback:
                        log_callback(f"[ERROR] {asset_name}: No price data from Yahoo Finance")
                    return None
            else:
                # For stocks, use the name as-is (should be the ticker symbol)
                ticker = asset_name
                
                # Fetch data from yfinance
                asset = yf.Ticker(ticker)
                
                # Try to get current price
                try:
                    price = asset.fast_info['lastPrice']
                except:
                    info = asset.info
                    price = info.get('regularMarketPrice') or info.get('currentPrice')
                
                if price and price > 0:
                    if log_callback:
                        log_callback(f"[SUCCESS] {asset_name}: ${price:,.2f} (Yahoo Finance)")
                    return float(price)
                else:
                    if log_callback:
                        log_callback(f"[ERROR] {asset_name}: No price data from Yahoo Finance")
                    return None
                    
        except Exception as e:
            if log_callback:
                log_callback(f"[ERROR] Yahoo Finance error for {asset_name}: {str(e)}")
            return None
    
    def update_all_asset_prices(self, api_key=None, log_callback=None, progress_callback=None):
        """
        Update all asset prices using CoinGecko (crypto) and yfinance (stocks/gold)
        
        Args:
            api_key: Not used anymore (kept for backward compatibility)
            log_callback: Optional callback for logging
            progress_callback: Optional callback for progress updates (current, total, asset_name)
        
        Returns:
            tuple: (updated_count, failed_count)
        """
        import time
        
        if log_callback:
            log_callback(f"\n{'='*60}")
            log_callback(f"[START] Asset Price Update - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            log_callback(f"{'='*60}\n")
        
        # Read all assets from Excel
        assets_df = self.read_excel("assets.xlsx")
        
        if assets_df.empty:
            if log_callback:
                log_callback("[INFO] No assets found in assets.xlsx")
            return 0, 0
        
        # Filter only supported categories
        eligible_assets = assets_df[assets_df['Category'].isin(['Crypto', 'Stocks', 'Gold/Silver'])]
        
        if eligible_assets.empty:
            if log_callback:
                log_callback("[INFO] No eligible assets to update (supported: Crypto, Stocks, Gold/Silver)")
            return 0, 0
        
        total_assets = len(eligible_assets)
        
        if log_callback:
            log_callback(f"[INFO] Found {total_assets} assets to update")
            log_callback(f"[INFO] Categories: {eligible_assets['Category'].value_counts().to_dict()}\n")
        
        updated_count = 0
        failed_count = 0
        current_index = 0
        
        try:
            # Process each asset individually
            for idx, asset in eligible_assets.iterrows():
                current_index += 1
                asset_id = asset['ID']
                asset_name = asset['Name']
                asset_category = asset['Category']
                
                # Update progress
                if progress_callback:
                    progress_callback(current_index, total_assets, asset_name)
                
                try:
                    if log_callback:
                        log_callback(f"[FETCHING] {asset_name} ({asset_category})...")
                    
                    # Fetch current price
                    current_price = self.get_asset_price(asset_name, asset_category, log_callback)
                    
                    if current_price and current_price > 0:
                        # Get quantity (default to 1 if not present)
                        quantity = float(asset.get('Quantity', 1.0))
                        old_value = float(asset.get('Value', 0))
                        old_price = float(asset.get('Price_Per_Unit', 0))
                        
                        # Calculate new total value: Quantity × Current Price
                        new_value = quantity * current_price
                        
                        # Update the record with both price and value
                        self.update_record("assets.xlsx", asset_id, {
                            'Price_Per_Unit': current_price,
                            'Value': new_value
                        })
                        
                        # Calculate change percentage
                        if old_value > 0:
                            change = ((new_value - old_value) / old_value) * 100
                        else:
                            change = 0
                        
                        if log_callback:
                            log_callback(f"[UPDATED] {asset_name}: ${old_value:,.2f} → ${new_value:,.2f} ({change:+.2f}%)")
                            log_callback(f"          Price: ${old_price:,.2f} → ${current_price:,.2f} | Qty: {quantity:.8f}\n")
                        
                        updated_count += 1
                    else:
                        failed_count += 1
                        if log_callback:
                            log_callback(f"[FAILED] {asset_name}: Could not fetch valid price\n")
                    
                    # Rate limiting: small delay between requests to be nice to APIs
                    time.sleep(0.5)
                    
                except Exception as e:
                    failed_count += 1
                    if log_callback:
                        log_callback(f"[ERROR] {asset_name}: {str(e)}\n")
            
            # Log skipped assets (unsupported categories)
            skipped_assets = assets_df[~assets_df['Category'].isin(['Crypto', 'Stocks', 'Gold/Silver'])]
            if not skipped_assets.empty:
                if log_callback:
                    log_callback(f"[INFO] Skipped {len(skipped_assets)} assets with unsupported categories:")
                for _, asset in skipped_assets.iterrows():
                    if log_callback:
                        log_callback(f"        - {asset['Name']} (Category: '{asset['Category']}')")
            
            if log_callback:
                log_callback(f"\n{'='*60}")
                log_callback(f"[COMPLETE] Updated: {updated_count} | Failed: {failed_count} | Total: {total_assets}")
                log_callback(f"{'='*60}\n")
            
            return updated_count, failed_count
            
        except Exception as e:
            if log_callback:
                log_callback(f"[ERROR] Update process failed: {str(e)}")
                log_callback(f"[ERROR] Traceback: {traceback.format_exc()}")
            return 0, len(eligible_assets)
        
    def calculate_networth(self):
        """Calculate total net worth using FinancialCalculator"""
        assets_df = self.read_excel("assets.xlsx")
        liabilities_df = self.read_excel("liabilities.xlsx")
        
        # Use FinancialCalculator for proper Quantity × Price calculation
        return FinancialCalculator.calculate_net_worth(assets_df, liabilities_df)
    
    def update_monthly_snapshot(self):
        """Update monthly net worth snapshot (overwrite current month if it exists)"""
        current_month = datetime.now().strftime("%Y-%m")
        monthly_df = self.read_excel("monthly_networth.xlsx")

        # Clean stray/blank rows
        if not monthly_df.empty:
            monthly_df = monthly_df.dropna(subset=['Month'])

        networth_data = self.calculate_networth()

        # Find previous month net worth (exclude current month if present)
        prev_df = monthly_df[monthly_df['Month'] != current_month]
        last_networth = None
        if not prev_df.empty:
            try:
                last_networth = float(prev_df.iloc[-1]['Net_Worth'])
            except Exception:
                last_networth = None

        change_percent = 0.0
        if last_networth and last_networth != 0:
            change_percent = ((networth_data['net_worth'] - last_networth) / last_networth) * 100.0

        # Build entry
        new_entry = {
            "Month": current_month,
            "Total_Assets": float(networth_data['total_assets']),
            "Total_Liabilities": float(networth_data['total_liabilities']),
            "Net_Worth": float(networth_data['net_worth']),
            "Change_Percent": round(change_percent, 2)
        }

        # Overwrite current month if it exists; otherwise append
        if not monthly_df.empty and current_month in monthly_df['Month'].values:
            monthly_df.loc[monthly_df['Month'] == current_month, ['Total_Assets','Total_Liabilities','Net_Worth','Change_Percent']] = [
                new_entry['Total_Assets'], new_entry['Total_Liabilities'], new_entry['Net_Worth'], new_entry['Change_Percent']
            ]
            self.write_excel("monthly_networth.xlsx", monthly_df)
            self.log_transaction("UPDATE", "monthly_networth.xlsx", {"Month": current_month, "new": new_entry})
        else:
            self.add_record("monthly_networth.xlsx", new_entry)

class ChartWidget(QWidget):
    """Widget for displaying charts"""

    def plot_monthly_changes_bar(self, data_manager):
        """Plot bar chart showing monthly changes in assets and liabilities"""
        self.figure.clear()
        df = data_manager.read_excel("monthly_networth.xlsx")
        
        if df.empty or len(df) < 2:
            ax = self.figure.add_subplot(111)
            ax.text(0.5, 0.5, 'Insufficient data for chart', 
                    horizontalalignment='center',
                    verticalalignment='center',
                    transform=ax.transAxes,
                    fontsize=14, color='#64748b')
            ax.set_xticks([])
            ax.set_yticks([])
            self.canvas.draw()
            return
        
        # Get last 6 months
        df = df.tail(6)
        
        ax = self.figure.add_subplot(111)
        
        x = range(len(df))
        width = 0.35
        
        ax.bar([i - width/2 for i in x], df['Total_Assets'], width, 
            label='Assets', color='#10b981', alpha=0.8)
        ax.bar([i + width/2 for i in x], df['Total_Liabilities'], width,
            label='Liabilities', color='#ef4444', alpha=0.8)
        
        ax.set_xlabel('Month', fontsize=12, fontweight='bold')
        ax.set_ylabel('Amount ($)', fontsize=12, fontweight='bold')
        ax.set_title('Monthly Assets vs Liabilities', fontsize=14, fontweight='bold', pad=20)
        ax.set_xticks(x)
        ax.set_xticklabels(df['Month'], rotation=45, ha='right', fontsize=10)
        ax.tick_params(axis='both', which='major', labelsize=10)
        ax.legend(fontsize=10, loc='upper left')
        ax.grid(True, alpha=0.3, axis='y', linestyle='--')
        
        # Format y-axis with currency
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
        
        self.figure.tight_layout(pad=2.0)
        self.canvas.draw()

    def plot_cashflow_histogram(self, data_manager):
        """Plot histogram of cash flow volatility"""
        self.figure.clear()
        df = data_manager.read_excel("income_expense.xlsx")
        
        if df.empty:
            ax = self.figure.add_subplot(111)
            ax.text(0.5, 0.5, 'No cash flow data', 
                    horizontalalignment='center',
                    verticalalignment='center',
                    transform=ax.transAxes,
                    fontsize=14, color='#64748b')
            ax.set_xticks([])
            ax.set_yticks([])
            self.canvas.draw()
            return
        
        # Calculate monthly net cash flow
        df['Date'] = pd.to_datetime(df['Date'])
        df['Month'] = df['Date'].dt.to_period('M')
        
        monthly_income = df[df['Type'] == 'Income'].groupby('Month')['Amount'].sum()
        monthly_expense = df[df['Type'] == 'Expense'].groupby('Month')['Amount'].sum()
        
        # Align indices
        all_months = monthly_income.index.union(monthly_expense.index)
        monthly_income = monthly_income.reindex(all_months, fill_value=0)
        monthly_expense = monthly_expense.reindex(all_months, fill_value=0)
        
        net_cashflow = monthly_income - monthly_expense
        
        if len(net_cashflow) == 0:
            ax = self.figure.add_subplot(111)
            ax.text(0.5, 0.5, 'Insufficient cash flow data', 
                    horizontalalignment='center',
                    verticalalignment='center',
                    transform=ax.transAxes,
                    fontsize=14, color='#64748b')
            ax.set_xticks([])
            ax.set_yticks([])
            self.canvas.draw()
            return
        
        ax = self.figure.add_subplot(111)
        ax.hist(net_cashflow.values, bins=10, color='#3b82f6', edgecolor='black', alpha=0.7)
        ax.set_xlabel('Net Cash Flow ($)', fontsize=12, fontweight='bold')
        ax.set_ylabel('Frequency', fontsize=12, fontweight='bold')
        ax.set_title('Cash Flow Distribution', fontsize=14, fontweight='bold', pad=20)
        ax.grid(True, alpha=0.3, axis='y', linestyle='--')
        ax.tick_params(axis='both', which='major', labelsize=10)
        
        # Add mean line
        ax.axvline(net_cashflow.mean(), color='#ef4444', linestyle='--', 
                linewidth=2, label=f'Mean: ${net_cashflow.mean():,.2f}')
        ax.legend(fontsize=10)
        
        # Format x-axis with currency
        ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
        
        self.figure.tight_layout(pad=2.0)
        self.canvas.draw()
    def plot_income_expense_trends(self, data_manager):
        """Plot income vs expense trends"""
        self.figure.clear()
        df = data_manager.read_excel("income_expense.xlsx")
        
        if df.empty:
            return
        
        # Group by month and type
        df['Date'] = pd.to_datetime(df['Date'])
        df['Month'] = df['Date'].dt.to_period('M').astype(str)
        
        monthly_data = df.groupby(['Month', 'Type'])['Amount'].sum().unstack(fill_value=0)
        
        ax = self.figure.add_subplot(111)
        
        if 'Income' in monthly_data.columns:
            ax.plot(monthly_data.index, monthly_data['Income'], 
                marker='o', linewidth=2, color='#10b981', label='Income')
        
        if 'Expense' in monthly_data.columns:
            ax.plot(monthly_data.index, monthly_data['Expense'], 
                marker='o', linewidth=2, color='#ef4444', label='Expense')
        
        ax.set_xlabel('Month')
        ax.set_ylabel('Amount ($)')
        ax.set_title('Income vs Expense Trends')
        ax.legend()
        ax.grid(True, alpha=0.3)
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
        self.figure.tight_layout()
        self.canvas.draw()

    def plot_expense_breakdown(self, data_manager):
        """Plot expense category breakdown"""
        self.figure.clear()
        df = data_manager.read_excel("income_expense.xlsx")
        
        if df.empty:
            ax = self.figure.add_subplot(111)
            ax.text(0.5, 0.5, 'No expense data', 
                    horizontalalignment='center',
                    verticalalignment='center',
                    transform=ax.transAxes,
                    fontsize=14, color='#64748b')
            ax.set_xticks([])
            ax.set_yticks([])
            self.canvas.draw()
            return
        
        # Filter expenses only for current month
        current_month = datetime.now().strftime("%Y-%m")
        expenses = df[(df['Type'] == 'Expense') & 
                    (df['Date'].astype(str).str.startswith(current_month))]
        
        if expenses.empty:
            ax = self.figure.add_subplot(111)
            ax.text(0.5, 0.5, 'No expenses this month', 
                    horizontalalignment='center',
                    verticalalignment='center',
                    transform=ax.transAxes,
                    fontsize=14, color='#64748b')
            ax.set_xticks([])
            ax.set_yticks([])
            self.canvas.draw()
            return
        
        category_totals = expenses.groupby('Category')['Amount'].sum()
        
        ax = self.figure.add_subplot(111)
        colors = ['#ef4444', '#f59e0b', '#10b981', '#3b82f6', '#8b5cf6', '#ec4899']
        
        wedges, texts, autotexts = ax.pie(category_totals.values, 
                                        labels=category_totals.index, 
                                        autopct='%1.1f%%',
                                        startangle=90,
                                        colors=colors,
                                        textprops={'fontsize': 10, 'fontweight': 'bold'})
        
        # Make percentage text more readable
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontsize(10)
            autotext.set_fontweight('bold')
        
        ax.set_title('Expense Breakdown (Current Month)', fontsize=14, fontweight='bold', pad=20)
        self.figure.tight_layout(pad=2.0)
        self.canvas.draw()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        import matplotlib.pyplot as plt
        face = plt.rcParams.get('figure.facecolor', '#ffffff')
        self.figure = Figure(figsize=(9, 5), dpi=95, facecolor=face)
        self.canvas = FigureCanvas(self.figure)
        layout = QVBoxLayout()
        layout.addWidget(self.canvas)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
    
    def plot_networth_trend(self, data_manager, time_filter="Last 6 Months", currency="USD"):
        """Plot net worth trend over time with interactive tooltips"""
        self.figure.clear()
        df = data_manager.read_excel("monthly_networth.xlsx")
        
        if df.empty:
            ax = self.figure.add_subplot(111)
            ax.text(0.5, 0.5, 'No data available', 
                    horizontalalignment='center',
                    verticalalignment='center',
                    transform=ax.transAxes,
                    fontsize=16, color='#64748b')
            ax.set_xticks([])
            ax.set_yticks([])
            self.canvas.draw()
            return
        
        # ✅ APPLY TIME FILTER
        df['Month'] = pd.to_datetime(df['Month'])
        today = pd.Timestamp.now()
        
        if time_filter == "Last 7 Days":
            cutoff = today - pd.Timedelta(days=7)
        elif time_filter == "Last Month":
            cutoff = today - pd.DateOffset(months=1)
        elif time_filter == "Last 3 Months":
            cutoff = today - pd.DateOffset(months=3)
        elif time_filter == "Last 6 Months":
            cutoff = today - pd.DateOffset(months=6)
        elif time_filter == "Last Year":
            cutoff = today - pd.DateOffset(years=1)
        else:  # All Time
            cutoff = df['Month'].min()
        
        df = df[df['Month'] >= cutoff].copy()
        
        if df.empty:
            ax = self.figure.add_subplot(111)
            ax.text(0.5, 0.5, f'No data for {time_filter}', 
                    horizontalalignment='center',
                    verticalalignment='center',
                    transform=ax.transAxes,
                    fontsize=16, color='#64748b')
            ax.set_xticks([])
            ax.set_yticks([])
            self.canvas.draw()
            return
        
        # Ensure numeric values for calculations/plotting
        df['Net_Worth'] = pd.to_numeric(df['Net_Worth'], errors='coerce')
        df['Total_Assets'] = pd.to_numeric(df['Total_Assets'], errors='coerce')
        df['Total_Liabilities'] = pd.to_numeric(df['Total_Liabilities'], errors='coerce')

        # Convert values to selected currency
        currency_symbol = CurrencyConverter.get_symbol(currency)
        df['Net_Worth_Converted'] = df['Net_Worth'].apply(lambda x: CurrencyConverter.convert(x, currency))
        
        # Convert month format to short form
        df['Month_Short'] = df['Month'].dt.strftime("%b'%y")
        
        ax = self.figure.add_subplot(111)
        import matplotlib.pyplot as plt
        import matplotlib.patheffects as pe
        ax.set_facecolor(plt.rcParams.get('axes.facecolor', '#ffffff'))
        for s in ax.spines.values():
            s.set_edgecolor(plt.rcParams.get('axes.edgecolor', '#e2e8f0'))
        
        # Plot line
        line, = ax.plot(df['Month_Short'], df['Net_Worth_Converted'], 
                        marker='o', linewidth=3, color='#10b981', 
                        markersize=10, markerfacecolor='#10b981',
                        markeredgecolor='white', markeredgewidth=2)
        
        ax.set_xlabel('Month', fontsize=12, fontweight='bold')
        ax.set_ylabel(f'Net Worth ({currency})', fontsize=12, fontweight='bold')
        ax.set_title(f'Net Worth Trend - {time_filter}', fontsize=14, fontweight='bold', pad=15)
        ax.grid(True, alpha=0.3, linestyle='--')
        
        # Improve x-axis labels
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=35, ha='right', fontsize=10)
        ax.tick_params(axis='both', which='major', labelsize=10)
        
        # Format y-axis with currency
        ax.yaxis.set_major_formatter(plt.FuncFormatter(
            lambda x, p: f'{currency_symbol}{x:,.0f}'
        ))

        # ✅ Fix axis scaling when there is only 1 point (or flat data)
        y_values = df['Net_Worth_Converted'].astype(float).tolist()
        if len(y_values) == 1:
            v = y_values[0] if pd.notna(y_values[0]) else 0.0
            margin = max(abs(v) * 0.1, 1.0)
            ax.set_ylim(v - margin, v + margin)
        else:
            y_min = min(y for y in y_values if pd.notna(y))
            y_max = max(y for y in y_values if pd.notna(y))
            if y_min == y_max:
                margin = max(abs(y_max) * 0.1, 1.0)
                ax.set_ylim(y_max - margin, y_max + margin)
        
        # ✅ ADD INTERACTIVE TOOLTIPS
        # Create annotation (initially hidden)
        annot = ax.annotate("", xy=(0,0), xytext=(10,10), textcoords="offset points",
                        bbox=dict(boxstyle="round,pad=0.8", fc="#1e293b", ec="#3b82f6", lw=2),
                        arrowprops=dict(arrowstyle="->", color="#3b82f6", lw=2),
                        fontsize=11, color='#e2e8f0', fontweight='bold')
        annot.set_visible(False)
        
        # Store data for tooltip
        self.tooltip_data = {
            'dates': df['Month_Short'].tolist(),
            'values': df['Net_Worth_Converted'].tolist(),
            'currency_symbol': currency_symbol
        }
        
        def hover(event):
            """Show tooltip on hover"""
            if event.inaxes == ax:
                cont, ind = line.contains(event)
                if cont:
                    # Get the index of the point
                    idx = ind["ind"][0]
                    
                    # Get data
                    date = self.tooltip_data['dates'][idx]
                    value = self.tooltip_data['values'][idx]
                    symbol = self.tooltip_data['currency_symbol']
                    
                    # Update annotation
                    annot.xy = (idx, value)
                    text = f"{date}\n{symbol}{value:,.2f}"
                    annot.set_text(text)
                    annot.set_visible(True)
                    self.canvas.draw_idle()
                else:
                    if annot.get_visible():
                        annot.set_visible(False)
                        self.canvas.draw_idle()
        
        # Connect hover event
        self.canvas.mpl_connect("motion_notify_event", hover)
        
        self.figure.tight_layout(pad=1.5)
        self.canvas.draw()
    
    def plot_asset_allocation(self, data_manager):
        """Plot asset allocation pie chart"""
        self.figure.clear()
        df = data_manager.read_excel("assets.xlsx")
        
        if df.empty:
            ax = self.figure.add_subplot(111)
            ax.text(0.5, 0.5, 'No assets to display', 
                    horizontalalignment='center',
                    verticalalignment='center',
                    transform=ax.transAxes,
                    fontsize=16, color='#64748b')
            ax.set_xticks([])
            ax.set_yticks([])
            self.canvas.draw()
            return
        
        category_totals = df.groupby('Category')['Value'].sum()
        
        ax = self.figure.add_subplot(111)
        import matplotlib.pyplot as plt
        import matplotlib.patheffects as pe
        ax.set_facecolor(plt.rcParams.get('axes.facecolor', '#ffffff'))
        for s in ax.spines.values():
            s.set_edgecolor(plt.rcParams.get('axes.edgecolor', '#e2e8f0'))
        colors = ['#10b981', '#3b82f6', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#06b6d4']
        
        # Create pie chart with better label positioning
        wedges, texts, autotexts = ax.pie(category_totals.values, 
                                        labels=category_totals.index, 
                                        autopct='%1.1f%%',
                                        startangle=90,
                                        colors=colors,
                                        pctdistance=0.75,  # Move percentages closer to center
                                        labeldistance=1.15,  # Move labels further out
                                        textprops={'fontsize': 12, 'fontweight': 'bold', 'color': 'black'})
        
        # Percentage text in white for strong in-wedge contrast (previous style)
        for autotext in autotexts:
            autotext.set_color('#FFFFFF')
            autotext.set_fontsize(13)
            autotext.set_fontweight('bold')
        
        # Category labels outside the pie in black with light outline for contrast
        for text in texts:
            text.set_fontsize(12)
            text.set_fontweight('bold')
            text.set_color('black')
            text.set_path_effects([pe.withStroke(linewidth=2, foreground='white')])
        
        ax.set_title('Asset Allocation', fontsize=15, fontweight='bold', pad=15)
        self.figure.tight_layout(pad=1.8)
        self.canvas.draw()

class AddAssetDialog(QDialog):
    """Smart dialog for adding/editing assets with currency and unit support"""
    
    def __init__(self, data_manager, parent=None, edit_mode=False, record_id=None):
        super().__init__(parent)
        self.data_manager = data_manager
        self.edit_mode = edit_mode
        self.record_id = record_id
        self.setWindowTitle("Edit Asset" if edit_mode else "Add Asset")
        self.setMinimumWidth(500)
        self.setup_ui()
        
        if edit_mode and record_id:
            self.load_record()
    
    def setup_ui(self):
        layout = QFormLayout()
        
        # Category selection
        self.category_combo = QComboBox()
        self.category_combo.addItems(["Cash & Bank", "Crypto", "Stocks", "Real Estate", 
                                    "Vehicles", "Business", "Gold/Silver", "Other"])
        self.category_combo.currentTextChanged.connect(self.on_category_changed)
        
        # Asset name
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g., BTC, Gold Bar, Savings Account")
        
        # Currency selection (for Cash & Bank only)
        self.currency_label = QLabel("Currency:")
        self.currency_combo = QComboBox()
        self.currency_combo.addItems(["USD", "EUR", "GBP", "LKR", "INR", "JPY", "AUD", "CAD"])
        self.currency_label.setVisible(False)
        self.currency_combo.setVisible(False)
        
        # Unit type label (dynamic based on category)
        self.unit_label = QLabel("Quantity:")
        
        # Quantity input with dynamic decimals
        self.quantity_input = QDoubleSpinBox()
        self.quantity_input.setMaximum(999999999)
        self.quantity_input.setDecimals(8)  # Max decimals (will adjust per category)
        self.quantity_input.setValue(1.0)
        self.quantity_input.setMinimum(0.00000001)
        self.quantity_input.setSuffix("")  # Will be set dynamically
        
        # Price per unit input with dynamic currency symbol
        self.price_label = QLabel("Price Per Unit:")
        self.price_input = QDoubleSpinBox()
        self.price_input.setMaximum(999999999)
        self.price_input.setPrefix("$")  # Will change based on currency
        self.price_input.setDecimals(2)
        
        # Total value (auto-calculated, read-only)
        self.value_input = QDoubleSpinBox()
        self.value_input.setMaximum(999999999)
        self.value_input.setPrefix("$")
        self.value_input.setReadOnly(True)
        self.value_input.setStyleSheet("background-color: #334155; color: #94a3b8;")
        
        # Auto-calculate value when quantity or price changes
        self.quantity_input.valueChanged.connect(self.calculate_value)
        self.price_input.valueChanged.connect(self.calculate_value)
        self.currency_combo.currentTextChanged.connect(self.on_currency_changed)
        
        # Notes
        self.notes_input = QTextEdit()
        self.notes_input.setMaximumHeight(80)
        self.notes_input.setPlaceholderText("Additional notes (optional)")
        
        # Add all fields to layout
        layout.addRow("Category:", self.category_combo)
        layout.addRow("Name:", self.name_input)
        layout.addRow(self.currency_label, self.currency_combo)
        layout.addRow(self.unit_label, self.quantity_input)
        layout.addRow(self.price_label, self.price_input)
        layout.addRow("Total Value (USD):", self.value_input)
        layout.addRow("Notes:", self.notes_input)
        
        # Info label (shows conversion info for non-USD currencies)
        self.info_label = QLabel("")
        self.info_label.setStyleSheet("color: #3b82f6; font-size: 10px; font-style: italic;")
        self.info_label.setWordWrap(True)
        self.info_label.setVisible(False)
        layout.addRow("", self.info_label)
        
        # Buttons
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("💾 Save")
        cancel_btn = QPushButton("❌ Cancel")
        
        save_btn.clicked.connect(self.save_asset)
        cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        
        layout.addRow(btn_layout)
        self.setLayout(layout)
        
        # Set initial state
        self.on_category_changed(self.category_combo.currentText())
    
    def on_category_changed(self, category):
        """Adjust input fields based on selected category"""
        
        if category == "Cash & Bank":
            # Show currency selector
            self.currency_label.setVisible(True)
            self.currency_combo.setVisible(True)
            
            # Hide quantity (cash is just amount)
            self.unit_label.setText("Amount:")
            self.quantity_input.setDecimals(2)
            self.quantity_input.setSuffix("")
            self.quantity_input.setValue(1.0)
            
            # Price per unit becomes the exchange rate (auto-set)
            self.price_label.setText("Exchange Rate to USD:")
            self.on_currency_changed(self.currency_combo.currentText())
            
        elif category == "Gold/Silver":
            # Hide currency selector
            self.currency_label.setVisible(False)
            self.currency_combo.setVisible(False)
            
            # Show weight in grams
            self.unit_label.setText("Weight (grams):")
            self.quantity_input.setDecimals(4)  # 4 decimals for precise weight
            self.quantity_input.setSuffix(" g")
            self.quantity_input.setValue(1.0)
            
            # Price per gram in USD
            self.price_label.setText("Price Per Gram (USD):")
            self.price_input.setPrefix("$")
            self.price_input.setValue(0.0)
            
            self.info_label.setVisible(False)
            
        elif category == "Crypto":
            # Hide currency selector
            self.currency_label.setVisible(False)
            self.currency_combo.setVisible(False)
            
            # Show crypto quantity with high precision
            self.unit_label.setText("Quantity:")
            self.quantity_input.setDecimals(8)  # Crypto needs 8 decimals
            self.quantity_input.setSuffix("")
            self.quantity_input.setValue(1.0)
            
            # Price per unit in USD
            self.price_label.setText("Price Per Unit (USD):")
            self.price_input.setPrefix("$")
            self.price_input.setValue(0.0)
            
            self.info_label.setVisible(False)
            
        elif category == "Stocks":
            # Hide currency selector
            self.currency_label.setVisible(False)
            self.currency_combo.setVisible(False)
            
            # Show shares
            self.unit_label.setText("Shares:")
            self.quantity_input.setDecimals(4)  # Support fractional shares
            self.quantity_input.setSuffix(" shares")
            self.quantity_input.setValue(1.0)
            
            # Price per share in USD
            self.price_label.setText("Price Per Share (USD):")
            self.price_input.setPrefix("$")
            self.price_input.setValue(0.0)
            
            self.info_label.setVisible(False)
            
        else:
            # Other categories (Real Estate, Vehicles, Business, Other)
            self.currency_label.setVisible(False)
            self.currency_combo.setVisible(False)
            
            self.unit_label.setText("Quantity:")
            self.quantity_input.setDecimals(2)
            self.quantity_input.setSuffix("")
            self.quantity_input.setValue(1.0)
            
            self.price_label.setText("Price Per Unit (USD):")
            self.price_input.setPrefix("$")
            self.price_input.setValue(0.0)
            
            self.info_label.setVisible(False)
    
    def on_currency_changed(self, currency):
        """Update exchange rate when currency changes"""
        if self.category_combo.currentText() == "Cash & Bank":
            # Get exchange rate to USD
            exchange_rate = CurrencyConverter.EXCHANGE_RATES.get(currency, 1.0)
            self.price_input.setValue(1.0 / exchange_rate)  # Rate FROM currency TO USD
            
            # Update info label
            currency_symbol = CurrencyConverter.get_symbol(currency)
            self.info_label.setText(f"💡 Enter amount in {currency} ({currency_symbol}). "
                                   f"Will be stored as USD equivalent.\n"
                                   f"Exchange rate: 1 {currency} = ${1.0/exchange_rate:.4f} USD")
            self.info_label.setVisible(True)
            
            # Update prefix for quantity to show currency
            self.quantity_input.setPrefix(currency_symbol)
    
    def calculate_value(self):
        """Auto-calculate total value from quantity × price"""
        quantity = self.quantity_input.value()
        price_per_unit = self.price_input.value()
        
        if self.category_combo.currentText() == "Cash & Bank":
            # For cash: quantity (in foreign currency) × rate (to USD) = USD value
            total_usd = quantity * price_per_unit
            self.value_input.setValue(total_usd)
        else:
            # For other assets: quantity × price per unit = total value
            total = quantity * price_per_unit
            self.value_input.setValue(total)
    
    def load_record(self):
        """Load existing record for editing"""
        df = self.data_manager.read_excel("assets.xlsx")
        record = df[df['ID'] == self.record_id].iloc[0]
        
        # Set category first (this adjusts the fields)
        self.category_combo.setCurrentText(record['Category'])
        
        # Set name
        self.name_input.setText(record['Name'])
        
        # Load quantity and price (with fallbacks for old data)
        quantity = float(record.get('Quantity', 1.0))
        price = float(record.get('Price_Per_Unit', 0.0))
        
        # Check if this is a Cash & Bank record with currency info in notes
        if record['Category'] == 'Cash & Bank':
            # Try to extract currency from notes
            notes = str(record.get('Notes', ''))
            if 'Currency:' in notes:
                try:
                    currency = notes.split('Currency:')[1].split()[0].strip()
                    if currency in CurrencyConverter.EXCHANGE_RATES:
                        self.currency_combo.setCurrentText(currency)
                except:
                    pass
        
        self.quantity_input.setValue(quantity)
        self.price_input.setValue(price)
        self.notes_input.setText(str(record.get('Notes', '')))
    
    def save_asset(self):
        """Save asset record with proper currency handling"""
        if not self.name_input.text():
            QMessageBox.warning(self, "Error", "Please enter asset name")
            return
        
        # Prepare notes with currency info if Cash & Bank
        notes = self.notes_input.toPlainText()
        if self.category_combo.currentText() == "Cash & Bank":
            currency = self.currency_combo.currentText()
            original_amount = self.quantity_input.value()
            
            # Add currency info to notes (for reference)
            notes = f"Currency: {currency}\nOriginal Amount: {original_amount:,.2f} {currency}\n\n{notes}"
        
        record = {
            "ID": self.record_id if self.edit_mode else self.data_manager.generate_id("assets.xlsx"),
            "Date": datetime.now().strftime("%Y-%m-%d"),
            "Category": self.category_combo.currentText(),
            "Name": self.name_input.text(),
            "Quantity": float(self.quantity_input.value()),
            "Price_Per_Unit": float(self.price_input.value()),
            "Value": float(self.value_input.value()),
            "Notes": notes
        }
        
        if self.edit_mode:
            self.data_manager.update_record("assets.xlsx", self.record_id, record)
        else:
            self.data_manager.add_record("assets.xlsx", record)
        
        self.accept()

class AddLiabilityDialog(QDialog):
    """Dialog for adding/editing liabilities"""
    
    def __init__(self, data_manager, parent=None, edit_mode=False, record_id=None):
        super().__init__(parent)
        self.data_manager = data_manager
        self.edit_mode = edit_mode
        self.record_id = record_id
        self.setWindowTitle("Edit Liability" if edit_mode else "Add Liability")
        self.setMinimumWidth(400)
        self.setup_ui()
        
        if edit_mode and record_id:
            self.load_record()
    
    def setup_ui(self):
        layout = QFormLayout()
        
        self.type_combo = QComboBox()
        self.type_combo.addItems(["Credit Card", "Personal Loan", "Student Loan", 
                                 "Mortgage", "Crypto Loan", "Other"])
        
        self.name_input = QLineEdit()
        # Quantity input (supports up to 8 decimals for crypto)
        self.quantity_input = QDoubleSpinBox()
        self.quantity_input.setMaximum(999999999)
        self.quantity_input.setDecimals(8)
        self.quantity_input.setValue(1.0)
        self.quantity_input.setMinimum(0.00000001)

        # Price per unit input
        self.price_input = QDoubleSpinBox()
        self.price_input.setMaximum(999999999)
        self.price_input.setPrefix("$")
        self.price_input.setDecimals(2)

        # Total value (auto-calculated, read-only)
        self.value_input = QDoubleSpinBox()
        self.value_input.setMaximum(999999999)
        self.value_input.setPrefix("$")
        self.value_input.setReadOnly(True)
        self.value_input.setStyleSheet("background-color: #334155; color: #94a3b8;")

        # Auto-calculate value when quantity or price changes
        self.quantity_input.valueChanged.connect(self.calculate_value)
        self.price_input.valueChanged.connect(self.calculate_value)

        self.notes_input = QTextEdit()
        self.notes_input.setMaximumHeight(80)

        layout.addRow("Category:", self.category_combo)
        layout.addRow("Name:", self.name_input)
        layout.addRow("Quantity:", self.quantity_input)
        layout.addRow("Price Per Unit:", self.price_input)
        layout.addRow("Total Value:", self.value_input)
        layout.addRow("Notes:", self.notes_input)
        
        # Buttons
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        cancel_btn = QPushButton("Cancel")
        
        save_btn.clicked.connect(self.save_liability)
        cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        
        layout.addRow(btn_layout)
        self.setLayout(layout)
    
    def load_record(self):
        """Load existing record for editing"""
        df = self.data_manager.read_excel("liabilities.xlsx")
        record = df[df['ID'] == self.record_id].iloc[0]
        
        self.type_combo.setCurrentText(record['Type'])
        self.name_input.setText(record['Name'])
        self.amount_input.setValue(record['Amount'])
        self.interest_input.setValue(record['Interest_Rate'])
        self.notes_input.setText(str(record['Notes']))
    
    def save_liability(self):
        """Save liability record"""
        if not self.name_input.text():
            QMessageBox.warning(self, "Error", "Please enter liability name")
            return
        
        record = {
            "ID": self.record_id if self.edit_mode else self.data_manager.generate_id("liabilities.xlsx"),
            "Date": datetime.now().strftime("%Y-%m-%d"),
            "Type": self.type_combo.currentText(),
            "Name": self.name_input.text(),
            "Amount": self.amount_input.value(),
            "Interest_Rate": self.interest_input.value(),
            "Notes": self.notes_input.toPlainText()
        }
        
        if self.edit_mode:
            self.data_manager.update_record("liabilities.xlsx", self.record_id, record)
        else:
            self.data_manager.add_record("liabilities.xlsx", record)
        
        self.accept()

class StartupLoadingDialog(QDialog):
    """Professional startup loading dialog with detailed progress"""
    
    def __init__(self, data_manager, parent=None):
        super().__init__(parent)
        self.data_manager = data_manager
        self.setWindowTitle("Net Worth Tracker Pro - Starting Up")
        self.setModal(True)
        self.setFixedSize(600, 400)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        
        # Center on screen
        screen = QApplication.primaryScreen().geometry()
        self.move((screen.width() - self.width()) // 2, 
                 (screen.height() - self.height()) // 2)
        
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the loading dialog UI"""
        layout = QVBoxLayout()
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # App title
        title = QLabel("Net Worth Tracker Pro")
        title.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        title.setStyleSheet("color: #3b82f6;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Version
        version = QLabel("v1.0 - Professional Edition")
        version.setFont(QFont("Arial", 10))
        version.setStyleSheet("color: #64748b;")
        version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(version)
        
        layout.addSpacing(20)
        
        # Status label
        self.status_label = QLabel("Initializing...")
        self.status_label.setFont(QFont("Arial", 12))
        self.status_label.setStyleSheet("color: #e2e8f0;")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #334155;
                border-radius: 8px;
                background-color: #0f172a;
                text-align: center;
                color: white;
                font-weight: bold;
                font-size: 12px;
                min-height: 25px;
            }
            QProgressBar::chunk {
                background-color: #10b981;
                border-radius: 6px;
            }
        """)
        layout.addWidget(self.progress_bar)
        
        # Detailed log area
        log_label = QLabel("📋 Loading Details:")
        log_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        log_label.setStyleSheet("color: #94a3b8;")
        layout.addWidget(log_label)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(150)
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #0a0f1e;
                color: #e2e8f0;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 10px;
                border: 1px solid #334155;
                border-radius: 6px;
                padding: 8px;
            }
        """)
        layout.addWidget(self.log_text)
        
        # Footer
        footer = QLabel("Please wait while we prepare your financial dashboard...")
        footer.setFont(QFont("Arial", 9))
        footer.setStyleSheet("color: #64748b;")
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(footer)
        
        layout.addStretch()
        self.setLayout(layout)
        
        # Apply dark theme
        self.setStyleSheet("""
            QDialog {
                background-color: #1e293b;
                border: 2px solid #3b82f6;
                border-radius: 15px;
            }
        """)
    
    def log(self, message):
        """Add message to log with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Color coding
        if "[ERROR]" in message or "[FAILED]" in message:
            color = "#ef4444"
        elif "[SUCCESS]" in message or "[UPDATED]" in message:
            color = "#10b981"
        elif "[INFO]" in message or "[SYSTEM]" in message:
            color = "#3b82f6"
        elif "[WARNING]" in message or "[SKIPPED]" in message:
            color = "#f59e0b"
        else:
            color = "#e2e8f0"
        
        formatted = f'<span style="color: #64748b;">[{timestamp}]</span> <span style="color: {color};">{message}</span>'
        self.log_text.append(formatted)
        
        # Auto-scroll
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        
        QApplication.processEvents()
    
    def update_status(self, message):
        """Update main status label"""
        self.status_label.setText(message)
        QApplication.processEvents()
    
    def update_progress(self, value):
        """Update progress bar (0-100)"""
        self.progress_bar.setValue(value)
        QApplication.processEvents()
    
    def start_loading_sequence(self):
        """Execute the complete loading sequence"""
        try:
            # Phase 1: Initialize data
            self.update_status("🔧 Initializing data storage...")
            self.update_progress(10)
            self.log("[SYSTEM] Checking data directories...")
            QTimer.singleShot(200, self.phase_2_check_files)
            
        except Exception as e:
            self.log(f"[ERROR] Startup failed: {str(e)}")
            self.update_status("❌ Startup failed!")
            QMessageBox.critical(self, "Startup Error", f"Failed to start application:\n\n{str(e)}")
            self.reject()
    
    def phase_2_check_files(self):
        """Phase 2: Check data files"""
        try:
            self.update_status("📂 Verifying data files...")
            self.update_progress(20)
            self.log("[INFO] Verifying Excel files...")
            
            files = ["assets.xlsx", "liabilities.xlsx", "transactions.xlsx", 
                    "monthly_networth.xlsx", "income_expense.xlsx", "goals.xlsx"]
            
            for file in files:
                df = self.data_manager.read_excel(file)
                self.log(f"[SUCCESS] ✓ {file}: {len(df)} records")
            
            self.update_progress(40)
            QTimer.singleShot(300, self.phase_3_check_update)
            
        except Exception as e:
            self.log(f"[ERROR] File verification failed: {str(e)}")
            QTimer.singleShot(300, self.phase_3_check_update)
    
    def phase_3_check_update(self):
        """Phase 3: Check if price update is needed"""
        try:
            self.update_status("🔍 Checking for price updates...")
            self.update_progress(50)
            
            config = self.data_manager.load_config()
            last_update_date = config.get('last_auto_update_date')
            today = datetime.now().strftime('%Y-%m-%d')
            
            if last_update_date != today:
                self.log(f"[SYSTEM] Last update: {last_update_date or 'Never'}")
                self.log("[SYSTEM] Price update needed - starting...")
                QTimer.singleShot(300, self.phase_4_update_prices)
            else:
                self.log(f"[INFO] Already updated today ({today})")
                self.update_progress(90)
                QTimer.singleShot(300, self.phase_5_complete)
                
        except Exception as e:
            self.log(f"[ERROR] Update check failed: {str(e)}")
            self.update_progress(90)
            QTimer.singleShot(300, self.phase_5_complete)
    
    def phase_4_update_prices(self):
        """Phase 4: Execute price updates"""
        try:
            self.update_status("💰 Updating asset prices...")
            self.log("[START] Fetching real-time prices...")
            
            # Progress callback
            def progress_callback(current, total, asset_name):
                progress = 50 + int((current / total) * 35)  # 50-85%
                self.update_progress(progress)
                self.log(f"[FETCHING] {asset_name} ({current}/{total})")
            
            # Execute update
            updated, failed = self.data_manager.update_all_asset_prices(
                api_key=None,
                log_callback=self.log,
                progress_callback=progress_callback
            )
            
            # Save update date
            config = self.data_manager.load_config()
            config['last_auto_update_date'] = datetime.now().strftime('%Y-%m-%d')
            self.data_manager.save_config(config)
            
            self.log(f"[COMPLETE] Updated: {updated} | Failed: {failed}")
            self.update_progress(90)
            
            QTimer.singleShot(500, self.phase_5_complete)
            
        except Exception as e:
            self.log(f"[ERROR] Price update failed: {str(e)}")
            self.update_progress(90)
            QTimer.singleShot(500, self.phase_5_complete)
    
    def phase_5_complete(self):
        """Phase 5: Finalize and close"""
        self.update_status("✅ Startup complete!")
        self.update_progress(100)
        self.log("[SUCCESS] Application ready!")
        
        # Close after short delay
        QTimer.singleShot(800, self.accept)

class LoadingOverlay(QWidget):
    """Loading overlay for price updates"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setup_ui()
        self.hide()
    
    def setup_ui(self):
        """Setup overlay UI"""
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Semi-transparent background
        self.setStyleSheet("""
            QWidget {
                background-color: rgba(15, 23, 42, 0.95);
                border-radius: 15px;
            }
        """)
        
        # Container widget - INCREASED SIZE to prevent cropping
        container = QWidget()
        container.setFixedSize(500, 300)
        container.setStyleSheet("""
            QWidget {
                background-color: #1e293b;
                border: 2px solid #3b82f6;
                border-radius: 15px;
            }
        """)
        container_layout = QVBoxLayout(container)
        container_layout.setSpacing(20)
        container_layout.setContentsMargins(30, 30, 30, 30)
        
        # Title
        title = QLabel("🔄 Updating Prices")
        title.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        title.setStyleSheet("color: #3b82f6; background: transparent; border: none;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        container_layout.addWidget(title)
        
        # Status label - FIXED HEIGHT AND WORD WRAP
        self.status_label = QLabel("Initializing...")
        self.status_label.setFont(QFont("Arial", 13))
        self.status_label.setStyleSheet("color: #e2e8f0; background: transparent; border: none; padding: 5px;")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setWordWrap(True)
        self.status_label.setMinimumHeight(50)
        self.status_label.setMaximumHeight(80)
        container_layout.addWidget(self.status_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #334155;
                border-radius: 8px;
                background-color: #0f172a;
                text-align: center;
                color: white;
                font-weight: bold;
                font-size: 12px;
                min-height: 25px;
            }
            QProgressBar::chunk {
                background-color: #10b981;
                border-radius: 6px;
            }
        """)
        container_layout.addWidget(self.progress_bar)
        
        # Current asset label - PREVENT CROPPING
        self.asset_label = QLabel("")
        self.asset_label.setFont(QFont("Arial", 11))
        self.asset_label.setStyleSheet("color: #94a3b8; background: transparent; border: none; padding: 5px;")
        self.asset_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.asset_label.setWordWrap(True)
        self.asset_label.setMinimumHeight(40)
        self.asset_label.setMaximumHeight(60)
        container_layout.addWidget(self.asset_label)
        
        # Add container to main layout
        layout.addWidget(container)
        self.setLayout(layout)
    
    def show_overlay(self):
        """Show the overlay"""
        self.show()
        self.raise_()
        QApplication.processEvents()
    
    def hide_overlay(self):
        """Hide the overlay"""
        self.hide()
        QApplication.processEvents()
    
    def update_progress(self, current, total, asset_name=""):
        """Update progress bar and status"""
        if total > 0:
            progress = int((current / total) * 100)
            self.progress_bar.setValue(progress)
        
        # ✅ CLEANER TEXT FORMATTING
        self.status_label.setText(f"Updating asset {current} of {total}")
        
        # Truncate long asset names
        if len(asset_name) > 40:
            asset_name = asset_name[:37] + "..."
        self.asset_label.setText(f"Current: {asset_name}")
        
        # Force immediate UI update
        self.progress_bar.repaint()
        self.status_label.repaint()
        self.asset_label.repaint()
        self.repaint()
        QApplication.processEvents()
    
    def show_complete(self, updated, failed):
        """Show completion status"""
        self.status_label.setText(f"✅ Complete!")
        self.asset_label.setText(f"Updated: {updated} | Failed: {failed}")
        self.progress_bar.setValue(100)
        QApplication.processEvents()
    
    def show_error(self, message):
        """Show error status"""
        self.status_label.setText(f"❌ Error")
        self.asset_label.setText(message)
        self.progress_bar.setValue(0)
        QApplication.processEvents()

class MainWindow(QMainWindow):
    """Main application window"""
    def export_to_pdf(self):
        """Export report to PDF"""
        try:
            from reportlab.lib.pagesizes import letter, A4
            from reportlab.lib import colors
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
            from reportlab.lib.enums import TA_CENTER, TA_RIGHT
            
            filename, _ = QFileDialog.getSaveFileName(self, "Export to PDF",
                                                    f"NetWorth_Report_{datetime.now().strftime('%Y%m%d')}.pdf",
                                                    "PDF Files (*.pdf)")
            if not filename:
                return
            
            # Create PDF
            doc = SimpleDocTemplate(filename, pagesize=letter)
            story = []
            styles = getSampleStyleSheet()
            
            # Title
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                textColor=colors.HexColor('#1e293b'),
                spaceAfter=30,
                alignment=TA_CENTER
            )
            story.append(Paragraph("Net Worth Report", title_style))
            story.append(Paragraph(f"Generated: {datetime.now().strftime('%B %d, %Y')}", 
                                styles['Normal']))
            story.append(Spacer(1, 0.5*inch))
            
            # Net Worth Summary
            networth_data = self.data_manager.calculate_networth()
            
            summary_style = ParagraphStyle(
                'Summary',
                parent=styles['Heading2'],
                fontSize=16,
                textColor=colors.HexColor('#3b82f6'),
                spaceAfter=12
            )
            story.append(Paragraph("Financial Summary", summary_style))
            
            summary_data = [
                ['Metric', 'Value'],
                ['Total Assets', f"${networth_data['total_assets']:,.2f}"],
                ['Total Liabilities', f"${networth_data['total_liabilities']:,.2f}"],
                ['Net Worth', f"${networth_data['net_worth']:,.2f}"]
            ]
            
            summary_table = Table(summary_data, colWidths=[3*inch, 2*inch])
            summary_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3b82f6')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(summary_table)
            story.append(Spacer(1, 0.3*inch))
            
            # Assets Table
            story.append(Paragraph("Assets Breakdown", summary_style))
            assets_df = self.data_manager.read_excel("assets.xlsx")
            
            if not assets_df.empty:
                assets_data = [assets_df.columns.tolist()]
                for _, row in assets_df.iterrows():
                    assets_data.append([str(row[col]) for col in assets_df.columns])
                
                assets_table = Table(assets_data)
                assets_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#10b981')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                story.append(assets_table)
            else:
                story.append(Paragraph("No assets recorded.", styles['Normal']))
            
            story.append(PageBreak())
            
            # Liabilities Table
            story.append(Paragraph("Liabilities Breakdown", summary_style))
            liabilities_df = self.data_manager.read_excel("liabilities.xlsx")
            
            if not liabilities_df.empty:
                liabilities_data = [liabilities_df.columns.tolist()]
                for _, row in liabilities_df.iterrows():
                    liabilities_data.append([str(row[col]) for col in liabilities_df.columns])
                
                liabilities_table = Table(liabilities_data)
                liabilities_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#ef4444')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                story.append(liabilities_table)
            else:
                story.append(Paragraph("No liabilities recorded.", styles['Normal']))
            
            story.append(Spacer(1, 0.3*inch))
            
            # Monthly Net Worth History
            story.append(Paragraph("Monthly Net Worth History", summary_style))
            monthly_df = self.data_manager.read_excel("monthly_networth.xlsx")
            
            if not monthly_df.empty:
                monthly_data = [monthly_df.columns.tolist()]
                for _, row in monthly_df.iterrows():
                    monthly_data.append([str(row[col]) for col in monthly_df.columns])
                
                monthly_table = Table(monthly_data)
                monthly_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3b82f6')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                story.append(monthly_table)
            
            # Build PDF
            doc.build(story)
            
            QMessageBox.information(self, "Success", f"PDF report exported to {filename}")
            self.statusBar().showMessage("PDF export completed successfully", 3000)
            
        except ImportError:
            QMessageBox.warning(self, "Module Required",
                            "PDF export requires 'reportlab' package.\n\n"
                            "Install it using:\npip install reportlab")
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to export PDF: {str(e)}")

    def refresh_dashboard(self):
        """Refresh dashboard after data updates"""
        # Remove old dashboard
        old_dashboard = self.content_stack.widget(0)
        self.content_stack.removeTab(0)
        
        # Create new dashboard
        new_dashboard = self.create_dashboard()
        self.content_stack.insertTab(0, new_dashboard, "Dashboard")
        
        # Switch to dashboard
        self.content_stack.setCurrentIndex(0)
        
        QApplication.processEvents()

    def resizeEvent(self, event):
        """Handle window resize to update overlay geometry"""
        super().resizeEvent(event)
        if hasattr(self, 'loading_overlay'):
            self.loading_overlay.setGeometry(self.rect())

    def edit_goal(self):
        """Edit financial goal"""
        # Get selected goal from goals table or list
        goals_df = self.data_manager.read_excel("goals.xlsx")
        
        if goals_df.empty:
            QMessageBox.warning(self, "No Goals", "No goals to edit. Add a goal first.")
            return
        
        # Create selection dialog
        goal_names = goals_df['Goal_Name'].tolist()
        goal_name, ok = QInputDialog.getItem(self, "Select Goal", "Choose a goal to edit:", goal_names, 0, False)
        
        if not ok:
            return
        
        goal = goals_df[goals_df['Goal_Name'] == goal_name].iloc[0]
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Edit Goal")
        layout = QFormLayout()
        
        name_input = QLineEdit(goal['Goal_Name'])
        target_input = QDoubleSpinBox()
        target_input.setMaximum(999999999)
        target_input.setPrefix("$")
        target_input.setValue(goal['Target_Amount'])
        
        current_input = QDoubleSpinBox()
        current_input.setMaximum(999999999)
        current_input.setPrefix("$")
        current_input.setValue(goal['Current_Amount'])
        
        deadline_input = QDateEdit()
        deadline_input.setDate(QDate.fromString(goal['Deadline'], "yyyy-MM-dd"))
        
        status_combo = QComboBox()
        status_combo.addItems(["Active", "Completed", "Paused"])
        status_combo.setCurrentText(goal['Status'])
        
        layout.addRow("Goal Name:", name_input)
        layout.addRow("Target Amount:", target_input)
        layout.addRow("Current Amount:", current_input)
        layout.addRow("Deadline:", deadline_input)
        layout.addRow("Status:", status_combo)
        
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        cancel_btn = QPushButton("Cancel")
        
        def save():
            updates = {
                "Goal_Name": name_input.text(),
                "Target_Amount": target_input.value(),
                "Current_Amount": current_input.value(),
                "Deadline": deadline_input.date().toString("yyyy-MM-dd"),
                "Status": status_combo.currentText()
            }
            self.data_manager.update_record("goals.xlsx", goal['ID'], updates)
            dialog.accept()
            
            # Check if goal is completed
            if current_input.value() >= target_input.value():
                QMessageBox.information(self, "🎉 Goal Achieved!", 
                                    f"Congratulations! You've achieved your goal: {name_input.text()}")
            
            self.content_stack.setCurrentIndex(3)  # Refresh goals tab
            self.statusBar().showMessage("Goal updated successfully", 3000)
        
        save_btn.clicked.connect(save)
        cancel_btn.clicked.connect(dialog.reject)
        
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addRow(btn_layout)
        
        dialog.setLayout(layout)
        dialog.exec()

    def delete_goal(self):
        """Delete financial goal"""
        goals_df = self.data_manager.read_excel("goals.xlsx")
        
        if goals_df.empty:
            QMessageBox.warning(self, "No Goals", "No goals to delete.")
            return
        
        goal_names = goals_df['Goal_Name'].tolist()
        goal_name, ok = QInputDialog.getItem(self, "Select Goal", "Choose a goal to delete:", goal_names, 0, False)
        
        if not ok:
            return
        
        reply = QMessageBox.question(self, "Confirm Delete",
                                    f"Are you sure you want to delete the goal '{goal_name}'?",
                                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            goal = goals_df[goals_df['Goal_Name'] == goal_name].iloc[0]
            self.data_manager.delete_record("goals.xlsx", goal['ID'])
            self.content_stack.setCurrentIndex(3)  # Refresh goals tab
            self.statusBar().showMessage("Goal deleted successfully", 3000)

    def update_goal_progress(self):
        """Update progress towards a goal"""
        goals_df = self.data_manager.read_excel("goals.xlsx")
        
        if goals_df.empty:
            QMessageBox.warning(self, "No Goals", "No goals available. Add a goal first.")
            return
        
        active_goals = goals_df[goals_df['Status'] == 'Active']
        if active_goals.empty:
            QMessageBox.warning(self, "No Active Goals", "No active goals to update.")
            return
        
        goal_names = active_goals['Goal_Name'].tolist()
        goal_name, ok = QInputDialog.getItem(self, "Select Goal", "Choose a goal to update:", goal_names, 0, False)
        
        if not ok:
            return
        
        goal = active_goals[active_goals['Goal_Name'] == goal_name].iloc[0]
        
        amount, ok = QInputDialog.getDouble(self, "Update Progress",
                                        f"Current: ${goal['Current_Amount']:,.2f}\n"
                                        f"Target: ${goal['Target_Amount']:,.2f}\n\n"
                                        f"Enter new amount contributed:",
                                        goal['Current_Amount'], 0, 999999999, 2)
        
        if ok:
            updates = {"Current_Amount": amount}
            
            # Check if goal is completed
            if amount >= goal['Target_Amount']:
                updates["Status"] = "Completed"
                QMessageBox.information(self, "🎉 Goal Achieved!",
                                    f"Congratulations! You've achieved your goal: {goal_name}")
            
            self.data_manager.update_record("goals.xlsx", goal['ID'], updates)
            self.content_stack.setCurrentIndex(3)  # Refresh goals tab
            self.statusBar().showMessage("Goal progress updated", 3000)

    def create_api_config_tab(self):
        """Create Gemini API configuration tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("📊 Asset Price Updater")
        title.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        layout.addWidget(title)

        # Description
        desc_label = QLabel("Automatically fetch real-time prices using CoinGecko (crypto) and Yahoo Finance (stocks/gold).")
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #64748b; font-size: 13px; margin-bottom: 20px;")
        layout.addWidget(desc_label)

        # Manual refresh button (prominent)
        refresh_all_btn = QPushButton("🔄 Refresh All Prices Now")
        refresh_all_btn.clicked.connect(self.refresh_all_prices)
        refresh_all_btn.setStyleSheet("""
            QPushButton {
                background-color: #10b981; 
                font-weight: bold; 
                font-size: 16px;
                padding: 15px 30px;
                border: none;
            }
            QPushButton:hover {
                background-color: #059669;
            }
        """)
        layout.addWidget(refresh_all_btn)
        
        # Secondary action buttons (smaller, less prominent)
        btn_row = QHBoxLayout()

        test_btn = QPushButton("🧪 Test Connection")
        test_btn.clicked.connect(self.test_api_connections)
        test_btn.setStyleSheet("background-color: #3b82f6; font-size: 13px; padding: 8px 16px;")

        api_info_btn = QPushButton("ℹ️ API Info")
        api_info_btn.clicked.connect(self.show_api_info)
        api_info_btn.setStyleSheet("font-size: 13px; padding: 8px 16px;")

        btn_row.addWidget(test_btn)
        btn_row.addWidget(api_info_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)
        
        # Info about automatic updates (compact)
        auto_info = QLabel("💡 Prices automatically update once per day when you launch the app.\n"
                        "Use the button above to manually refresh prices at any time.")
        auto_info.setWordWrap(True)
        auto_info.setStyleSheet("color: #64748b; font-size: 12px; padding: 10px; "
                            "background-color: #1e293b; border-radius: 8px; margin-bottom: 15px;")
        layout.addWidget(auto_info)
        
        # Log Section
        log_section_label = QLabel("📋 Activity Log")
        log_section_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        log_section_label.setStyleSheet("margin-top: 20px;")
        layout.addWidget(log_section_label)
        
        # Log text area
        self.api_log_text = QTextEdit()
        self.api_log_text.setReadOnly(True)
        self.api_log_text.setMinimumHeight(300)
        self.api_log_text.setStyleSheet("""
            QTextEdit {
                background-color: #0a0f1e;
                color: #e2e8f0;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 12px;
                border: 1px solid #334155;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        self.api_log_text.setPlaceholderText("Activity log will appear here...")
        layout.addWidget(self.api_log_text)
        
        # Log control buttons
        log_btn_layout = QHBoxLayout()

        copy_log_btn = QPushButton("📋 Copy Log")
        copy_log_btn.clicked.connect(self.copy_log_to_clipboard)

        save_log_btn = QPushButton("💾 Save Log to File")
        save_log_btn.clicked.connect(self.save_log_to_file)

        clear_log_btn = QPushButton("🗑️ Clear Log")
        clear_log_btn.clicked.connect(self.clear_log)

        log_btn_layout.addStretch()  # ✅ Move stretch to LEFT
        log_btn_layout.addWidget(copy_log_btn)
        log_btn_layout.addWidget(save_log_btn)
        log_btn_layout.addWidget(clear_log_btn)

        layout.addLayout(log_btn_layout)
        
        widget.setLayout(layout)
        
        # Add initial log message
        self.append_to_log("[SYSTEM] API Configuration loaded. Ready to fetch prices.")
        
        return widget
    
    def show_api_info(self):
        """Show information about the APIs being used"""
        info_text = """
    📊 Asset Price APIs

    🔹 CoinGecko API (Crypto)
    • Coverage: 10,000+ cryptocurrencies
    • Rate Limit: 10-50 calls/minute (free tier)
    • No API key required
    • Data source: Aggregated from 600+ exchanges

    🔹 Yahoo Finance (Stocks & Commodities)
    • Coverage: All major stocks, ETFs, commodities
    • Rate Limit: Reasonable (no strict limits)
    • No API key required
    • Real-time and historical data

    ✅ Supported Asset Categories:
    • Crypto: BTC, ETH, SOL, AVAX, etc.
    • Stocks: AAPL, GOOGL, TSLA, etc.
    • Gold/Silver: GC=F (Gold), SI=F (Silver)

    💡 Tip: Use standard ticker symbols for stocks
        (e.g., AAPL for Apple, MSFT for Microsoft)
    """
        
        self.append_to_log(info_text)
        QMessageBox.information(self, "API Information", info_text)
    
    def append_to_log(self, message):
        """Append message to API log with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Color coding
        if "[ERROR]" in message:
            color = "#ef4444"
        elif "[SUCCESS]" in message:
            color = "#10b981"
        elif "[INFO]" in message:
            color = "#3b82f6"
        elif "[WARNING]" in message:
            color = "#f59e0b"
        else:
            color = "#e2e8f0"
        
        formatted_message = f'<span style="color: #64748b;">[{timestamp}]</span> <span style="color: {color};">{message}</span>'
        self.api_log_text.append(formatted_message)
        
        # Auto-scroll to bottom
        scrollbar = self.api_log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        
        QApplication.processEvents()
    
    
    def test_api_connections(self):
        """Test CoinGecko and yfinance APIs"""
        self.append_to_log("\n[TEST] Testing API connections...")
        QApplication.processEvents()
        
        try:
            # Test CoinGecko
            self.append_to_log("[TEST] Testing CoinGecko API...")
            cg = CoinGeckoAPI()
            btc_price = cg.get_price(ids='bitcoin', vs_currencies='usd')
            
            if 'bitcoin' in btc_price and 'usd' in btc_price['bitcoin']:
                price = btc_price['bitcoin']['usd']
                self.append_to_log(f"[SUCCESS] ✓ CoinGecko: BTC = ${price:,.2f}")
            else:
                self.append_to_log("[ERROR] ✗ CoinGecko: Failed to fetch BTC price")
            
            # Test yfinance
            self.append_to_log("[TEST] Testing Yahoo Finance API...")
            aapl = yf.Ticker("AAPL")
            aapl_price = aapl.fast_info['lastPrice']
            
            if aapl_price and aapl_price > 0:
                self.append_to_log(f"[SUCCESS] ✓ Yahoo Finance: AAPL = ${aapl_price:,.2f}")
            else:
                self.append_to_log("[ERROR] ✗ Yahoo Finance: Failed to fetch AAPL price")
            
            # Test Gold
            self.append_to_log("[TEST] Testing Gold prices...")
            gold = yf.Ticker("GC=F")
            gold_price = gold.fast_info['lastPrice']
            
            if gold_price and gold_price > 0:
                self.append_to_log(f"[SUCCESS] ✓ Gold: ${gold_price:,.2f} per oz")
            else:
                self.append_to_log("[ERROR] ✗ Gold: Failed to fetch price")
            
            self.append_to_log("\n[SUCCESS] ✅ All API tests completed!")
            QMessageBox.information(self, "API Test Success", 
                                "✅ All APIs are working correctly!\n\n"
                                "• CoinGecko: Connected\n"
                                "• Yahoo Finance: Connected\n\n"
                                "You can now fetch real-time prices.")
            
        except Exception as e:
            self.append_to_log(f"[ERROR] ✗ API test failed: {str(e)}")
            QMessageBox.critical(self, "API Test Failed", 
                            f"Failed to connect to APIs:\n\n{str(e)}\n\n"
                            "Please check:\n"
                            "1. Internet connection\n"
                            "2. Libraries installed (pycoingecko, yfinance)")
            
   
    def refresh_all_prices(self):
        """Refresh all asset prices using CoinGecko + yfinance (manual refresh)"""
        
        # Confirmation dialog
        assets_df = self.data_manager.read_excel("assets.xlsx")
        eligible_assets = assets_df[assets_df['Category'].isin(['Crypto', 'Stocks', 'Gold/Silver'])]
        
        if eligible_assets.empty:
            QMessageBox.information(self, "No Assets", "No eligible assets to update.\n\nSupported categories: Crypto, Stocks, Gold/Silver")
            return
        
        reply = QMessageBox.question(self, "Confirm Price Update",
                                    f"This will fetch current prices for {len(eligible_assets)} assets.\n\n"
                                    "This may take a few moments. Continue?",
                                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.No:
            return
        
        # ✅ Show loading overlay with proper geometry
        self.loading_overlay.setGeometry(self.rect())
        self.loading_overlay.raise_()
        self.loading_overlay.show_overlay()
        self.loading_overlay.repaint()
        QApplication.processEvents()

        self.loading_overlay.update_progress(0, len(eligible_assets), "Starting manual update...")
        QApplication.processEvents()

        # Small delay to ensure overlay is visible
        QTimer.singleShot(200, self.execute_manual_refresh)

    def execute_manual_refresh(self):
        """Execute manual price refresh with loading overlay"""
        try:
            self.append_to_log("[SYSTEM] Starting manual price refresh...")
            
            # Progress callback for overlay - forces UI updates
            def update_progress(current, total, asset_name):
                self.loading_overlay.update_progress(current, total, asset_name)
                QApplication.processEvents()  # Force immediate UI update
            
            # Execute update
            updated, failed = self.data_manager.update_all_asset_prices(
                api_key=None,
                log_callback=self.append_to_log,
                progress_callback=update_progress
            )
            
            # Show completion
            self.loading_overlay.show_complete(updated, failed)
            QApplication.processEvents()
            
            # Small delay before hiding overlay
            QTimer.singleShot(1500, lambda: self._complete_manual_refresh(updated, failed))
            
        except Exception as e:
            self.append_to_log(f"[ERROR] Manual update failed: {str(e)}")
            self.append_to_log(f"[ERROR] Traceback: {traceback.format_exc()}")
            self.loading_overlay.show_error(f"Update failed: {str(e)}")
            QApplication.processEvents()
            
            # Hide overlay and show error after delay
            QTimer.singleShot(2000, lambda: self._show_manual_refresh_error(str(e)))

    def _complete_manual_refresh(self, updated, failed):
        """Complete manual refresh - separate method to avoid blocking"""
        
        # ✅ HIDE THE OVERLAY FIRST
        self.loading_overlay.hide_overlay()
        
        # Refresh UI
        self.refresh_assets_table()
        self.refresh_dashboard()
        
        # Show result message
        QMessageBox.information(self, "Update Complete",
                            f"✅ Price update completed!\n\n"
                            f"Updated: {updated}\n"
                            f"Failed: {failed}")
        
        self.append_to_log(f"[SUCCESS] Manual refresh completed: {updated} updated, {failed} failed")

    def _show_manual_refresh_error(self, error_msg):
        """Show manual refresh error - separate method to avoid blocking"""
        
        # ✅ HIDE THE OVERLAY FIRST
        self.loading_overlay.hide_overlay()
        
        QMessageBox.critical(self, "Update Error", f"Failed to update prices:\n\n{error_msg}")
    
    def copy_log_to_clipboard(self):
        """Copy log contents to clipboard"""
        log_text = self.api_log_text.toPlainText()
        
        if not log_text:
            QMessageBox.information(self, "Empty Log", "Log is empty. Nothing to copy.")
            return
        
        clipboard = QApplication.clipboard()
        clipboard.setText(log_text)
        
        self.append_to_log("[INFO] Log copied to clipboard")
        QMessageBox.information(self, "Success", "Log copied to clipboard!")
        self.statusBar().showMessage("Log copied to clipboard", 3000)
    
    def save_log_to_file(self):
        """Save log to a text file"""
        log_text = self.api_log_text.toPlainText()
        
        if not log_text:
            QMessageBox.information(self, "Empty Log", "Log is empty. Nothing to save.")
            return
        
        filename, _ = QFileDialog.getSaveFileName(
            self, 
            "Save Log File",
            f"GeminiAPI_Log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            "Text Files (*.txt);;All Files (*)"
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(f"Gemini API Activity Log\n")
                    f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write("="*60 + "\n\n")
                    f.write(log_text)
                
                self.append_to_log(f"[SUCCESS] Log saved to: {filename}")
                QMessageBox.information(self, "Success", f"Log saved to:\n{filename}")
                self.statusBar().showMessage("Log saved successfully", 3000)
                
            except Exception as e:
                self.append_to_log(f"[ERROR] Failed to save log: {str(e)}")
                QMessageBox.critical(self, "Error", f"Failed to save log:\n{str(e)}")
    
    def clear_log(self):
        """Clear the log display"""
        reply = QMessageBox.question(self, "Clear Log",
                                    "Are you sure you want to clear the log?",
                                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            self.api_log_text.clear()
            self.append_to_log("[SYSTEM] Log cleared")
            self.statusBar().showMessage("Log cleared", 3000)

    def create_transaction_log_tab(self):
        """Create transaction log viewer tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("📂 Transaction Log")
        title.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # Search and filter toolbar
        toolbar = QHBoxLayout()
        
        search_label = QLabel("Search:")
        self.log_search_input = QLineEdit()
        self.log_search_input.setPlaceholderText("Search transactions...")
        self.log_search_input.textChanged.connect(self.filter_transaction_log)
        
        filter_label = QLabel("Action:")
        self.log_filter_combo = QComboBox()
        self.log_filter_combo.addItems(["All", "ADD", "UPDATE", "DELETE"])
        self.log_filter_combo.currentTextChanged.connect(self.filter_transaction_log)
        
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self.refresh_transaction_log)
        
        export_btn = QPushButton("📥 Export Log")
        export_btn.clicked.connect(self.export_transaction_log)
        
        toolbar.addWidget(search_label)
        toolbar.addWidget(self.log_search_input)
        toolbar.addWidget(filter_label)
        toolbar.addWidget(self.log_filter_combo)
        toolbar.addWidget(refresh_btn)
        toolbar.addWidget(export_btn)
        toolbar.addStretch()
        
        layout.addLayout(toolbar)
        
        # Table
        self.transaction_log_table = QTableWidget()
        self.refresh_transaction_log()
        layout.addWidget(self.transaction_log_table)
        
        widget.setLayout(layout)
        return widget

    def refresh_transaction_log(self):
        """Refresh transaction log table"""
        df = self.data_manager.read_excel("transactions.xlsx")
        
        # Sort by timestamp descending
        if not df.empty:
            df = df.sort_values('Timestamp', ascending=False)
        
        self.transaction_log_table.setRowCount(len(df))
        self.transaction_log_table.setColumnCount(len(df.columns))
        self.transaction_log_table.setHorizontalHeaderLabels(df.columns.tolist())
        
        for i, row in df.iterrows():
            for j, value in enumerate(row):
                self.transaction_log_table.setItem(i, j, QTableWidgetItem(str(value)))
        
        # Proper column resizing with forced update
        self.transaction_log_table.resizeColumnsToContents()
        self.transaction_log_table.horizontalHeader().setStretchLastSection(True)
        
        # Force immediate geometry update
        self.transaction_log_table.updateGeometry()
        self.transaction_log_table.viewport().update()
        self.transaction_log_table.horizontalHeader().updateGeometry()
        QApplication.processEvents()

    def filter_transaction_log(self):
        """Filter transaction log based on search and filter criteria"""
        search_text = self.log_search_input.text().lower()
        action_filter = self.log_filter_combo.currentText()
        
        for row in range(self.transaction_log_table.rowCount()):
            show_row = True
            
            # Check search text
            if search_text:
                row_text = ""
                for col in range(self.transaction_log_table.columnCount()):
                    item = self.transaction_log_table.item(row, col)
                    if item:
                        row_text += item.text().lower() + " "
                
                if search_text not in row_text:
                    show_row = False
            
            # Check action filter
            if action_filter != "All":
                action_item = self.transaction_log_table.item(row, 2)  # Action column
                if action_item and action_item.text() != action_filter:
                    show_row = False
            
            self.transaction_log_table.setRowHidden(row, not show_row)

    def export_transaction_log(self):
        """Export transaction log to CSV"""
        filename, _ = QFileDialog.getSaveFileName(self, "Export Transaction Log",
                                                f"TransactionLog_{datetime.now().strftime('%Y%m%d')}.csv",
                                                "CSV Files (*.csv)")
        if filename:
            df = self.data_manager.read_excel("transactions.xlsx")
            df.to_csv(filename, index=False)
            QMessageBox.information(self, "Success", f"Transaction log exported to {filename}")
    def create_income_expense_tab(self):
        """Create income and expense tracking tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("💸 Income & Expense Tracker")
        title.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # Summary cards
        summary_layout = QHBoxLayout()
        
        # Calculate totals
        df = self.data_manager.read_excel("income_expense.xlsx")
        current_month = datetime.now().strftime("%Y-%m")
        monthly_data = df[df['Date'].astype(str).str.startswith(current_month)]
        
        total_income = monthly_data[monthly_data['Type'] == 'Income']['Amount'].sum() if not monthly_data.empty else 0
        total_expense = monthly_data[monthly_data['Type'] == 'Expense']['Amount'].sum() if not monthly_data.empty else 0
        net_savings = total_income - total_expense
        
        income_card = self.create_card("Monthly Income", f"${total_income:,.2f}", "#10b981")
        expense_card = self.create_card("Monthly Expenses", f"${total_expense:,.2f}", "#ef4444")
        savings_card = self.create_card("Net Savings", f"${net_savings:,.2f}", "#3b82f6")
        
        summary_layout.addWidget(income_card)
        summary_layout.addWidget(expense_card)
        summary_layout.addWidget(savings_card)
        layout.addLayout(summary_layout)
        
        # Toolbar
        toolbar = QHBoxLayout()
        add_income_btn = QPushButton("➕ Add Income")
        add_income_btn.clicked.connect(lambda: self.add_income_expense("Income"))
        
        add_expense_btn = QPushButton("➖ Add Expense")
        add_expense_btn.clicked.connect(lambda: self.add_income_expense("Expense"))
        
        edit_btn = QPushButton("✏️ Edit")
        edit_btn.clicked.connect(self.edit_income_expense)
        
        delete_btn = QPushButton("🗑️ Delete")
        delete_btn.clicked.connect(self.delete_income_expense)
        
        analytics_btn = QPushButton("📊 Analytics")
        analytics_btn.clicked.connect(self.show_income_expense_analytics)
        
        toolbar.addWidget(add_income_btn)
        toolbar.addWidget(add_expense_btn)
        toolbar.addWidget(edit_btn)
        toolbar.addWidget(delete_btn)
        toolbar.addWidget(analytics_btn)
        toolbar.addStretch()
        
        layout.addLayout(toolbar)
        
        # Table
        self.income_expense_table = QTableWidget()
        self.refresh_income_expense_table()
        layout.addWidget(self.income_expense_table)
        
        widget.setLayout(layout)
        return widget

    def refresh_income_expense_table(self):
        """Refresh income/expense table"""
        df = self.data_manager.read_excel("income_expense.xlsx")
        
        # Sort by date descending
        if not df.empty:
            df = df.sort_values('Date', ascending=False)
        
        self.income_expense_table.setRowCount(len(df))
        self.income_expense_table.setColumnCount(len(df.columns))
        self.income_expense_table.setHorizontalHeaderLabels(df.columns.tolist())
        
        for i, row in df.iterrows():
            for j, value in enumerate(row):
                item = QTableWidgetItem(str(value))
                # Color code based on type
                if df.columns[j] == 'Type':
                    if value == 'Income':
                        item.setForeground(Qt.GlobalColor.green)
                    else:
                        item.setForeground(Qt.GlobalColor.red)
                self.income_expense_table.setItem(i, j, item)
        
        # Proper column resizing with forced update
        self.income_expense_table.resizeColumnsToContents()
        self.income_expense_table.horizontalHeader().setStretchLastSection(True)
        
        # Force immediate geometry update
        self.income_expense_table.updateGeometry()
        self.income_expense_table.viewport().update()
        self.income_expense_table.horizontalHeader().updateGeometry()
        QApplication.processEvents()

    def add_income_expense(self, transaction_type):
        """Add income or expense entry"""
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Add {transaction_type}")
        dialog.setMinimumWidth(400)
        layout = QFormLayout()
        
        # Category
        category_combo = QComboBox()
        if transaction_type == "Income":
            category_combo.addItems(["Salary", "Freelance", "Investment Returns", 
                                    "Business Income", "Rental Income", "Other"])
        else:
            category_combo.addItems(["Food & Dining", "Transportation", "Housing", 
                                    "Utilities", "Healthcare", "Entertainment", 
                                    "Shopping", "Education", "Debt Payment", "Other"])
        
        description_input = QLineEdit()
        amount_input = QDoubleSpinBox()
        amount_input.setMaximum(999999999)
        amount_input.setPrefix("$")
        
        date_input = QDateEdit()
        date_input.setDate(QDate.currentDate())
        date_input.setCalendarPopup(True)
        
        layout.addRow("Category:", category_combo)
        layout.addRow("Description:", description_input)
        layout.addRow("Amount:", amount_input)
        layout.addRow("Date:", date_input)
        
        # Buttons
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        cancel_btn = QPushButton("Cancel")
        
        def save():
            if not description_input.text():
                QMessageBox.warning(dialog, "Error", "Please enter description")
                return
            
            record = {
                "ID": self.data_manager.generate_id("income_expense.xlsx"),
                "Date": date_input.date().toString("yyyy-MM-dd"),
                "Type": transaction_type,
                "Category": category_combo.currentText(),
                "Description": description_input.text(),
                "Amount": amount_input.value()
            }
            
            self.data_manager.add_record("income_expense.xlsx", record)
            dialog.accept()
            self.refresh_income_expense_table()
            self.statusBar().showMessage(f"{transaction_type} added successfully", 3000)
        
        save_btn.clicked.connect(save)
        cancel_btn.clicked.connect(dialog.reject)
        
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addRow(btn_layout)
        
        dialog.setLayout(layout)
        dialog.exec()

    def edit_income_expense(self):
        """Edit selected income/expense entry"""
        current_row = self.income_expense_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Error", "Please select an entry to edit")
            return
        
        record_id = int(self.income_expense_table.item(current_row, 0).text())
        df = self.data_manager.read_excel("income_expense.xlsx")
        record = df[df['ID'] == record_id].iloc[0]
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Edit Entry")
        dialog.setMinimumWidth(400)
        layout = QFormLayout()
        
        # Pre-fill with existing data
        category_combo = QComboBox()
        if record['Type'] == "Income":
            category_combo.addItems(["Salary", "Freelance", "Investment Returns", 
                                    "Business Income", "Rental Income", "Other"])
        else:
            category_combo.addItems(["Food & Dining", "Transportation", "Housing", 
                                    "Utilities", "Healthcare", "Entertainment", 
                                    "Shopping", "Education", "Debt Payment", "Other"])
        category_combo.setCurrentText(record['Category'])
        
        description_input = QLineEdit(record['Description'])
        amount_input = QDoubleSpinBox()
        amount_input.setMaximum(999999999)
        amount_input.setPrefix("$")
        amount_input.setValue(record['Amount'])
        
        date_input = QDateEdit()
        date_input.setDate(QDate.fromString(record['Date'], "yyyy-MM-dd"))
        date_input.setCalendarPopup(True)
        
        layout.addRow("Category:", category_combo)
        layout.addRow("Description:", description_input)
        layout.addRow("Amount:", amount_input)
        layout.addRow("Date:", date_input)
        
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        cancel_btn = QPushButton("Cancel")
        
        def save():
            updates = {
                "Date": date_input.date().toString("yyyy-MM-dd"),
                "Category": category_combo.currentText(),
                "Description": description_input.text(),
                "Amount": amount_input.value()
            }
            self.data_manager.update_record("income_expense.xlsx", record_id, updates)
            dialog.accept()
            self.refresh_income_expense_table()
            self.statusBar().showMessage("Entry updated successfully", 3000)
        
        save_btn.clicked.connect(save)
        cancel_btn.clicked.connect(dialog.reject)
        
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addRow(btn_layout)
        
        dialog.setLayout(layout)
        dialog.exec()

    def delete_income_expense(self):
        """Delete selected income/expense entry"""
        current_row = self.income_expense_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Error", "Please select an entry to delete")
            return
        
        reply = QMessageBox.question(self, "Confirm Delete",
                                    "Are you sure you want to delete this entry?",
                                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            record_id = int(self.income_expense_table.item(current_row, 0).text())
            self.data_manager.delete_record("income_expense.xlsx", record_id)
            self.refresh_income_expense_table()
            self.statusBar().showMessage("Entry deleted successfully", 3000)

    def show_income_expense_analytics(self):
        """Show income/expense analytics dialog"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Income & Expense Analytics")
        dialog.setMinimumSize(800, 600)
        layout = QVBoxLayout()
        
        # Create chart widget
        chart_widget = ChartWidget()
        chart_widget.plot_income_expense_trends(self.data_manager)
        layout.addWidget(chart_widget)
        
        # Category breakdown
        breakdown_widget = ChartWidget()
        breakdown_widget.plot_expense_breakdown(self.data_manager)
        layout.addWidget(breakdown_widget)
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.close)
        layout.addWidget(close_btn)
        
        dialog.setLayout(layout)
        dialog.exec()

    def __init__(self):
        super().__init__()
        self.data_manager = DataManager()
        self.theme_manager = ThemeManager()
        
        # Apply theme BEFORE creating UI
        self.apply_theme()
        
        self.check_password()
        self.setup_ui()
        
        # ✅ CREATE LOADING OVERLAY AFTER UI IS SET UP
        self.loading_overlay = LoadingOverlay(self)
        self.loading_overlay.setGeometry(self.rect())
        self.loading_overlay.hide()
        
        # Force layout update after UI creation
        self.update()
        QApplication.processEvents()
        
        # Force refresh all tables after UI is created
        QTimer.singleShot(100, self.refresh_all_tables_on_startup)
        
        # Auto-update monthly snapshot
        self.data_manager.update_monthly_snapshot()
        
        # ✅ NOTE: Startup loading and price updates are now handled BEFORE MainWindow opens
        
    

    def check_and_auto_update(self):
        """Check if auto-update is needed (once per day) and execute with loading overlay"""
        try:
            config = self.data_manager.load_config()
            last_update_date = config.get('last_auto_update_date')
            today = datetime.now().strftime('%Y-%m-%d')
            
            # Check if we need to update (first time or new day)
            if last_update_date != today:
                if hasattr(self, 'append_to_log'):
                    self.append_to_log(f"[SYSTEM] New day detected. Last update: {last_update_date or 'Never'}")
                    self.append_to_log(f"[SYSTEM] Initiating automatic price update...")
                
                # âœ… CRITICAL: Show overlay with proper geometry
                self.loading_overlay.setGeometry(self.rect())
                self.loading_overlay.show_overlay()
                self.loading_overlay.update_progress(0, 1, "Initializing...")
                
                # Force UI update
                QApplication.processEvents()
                
                # Small delay to ensure overlay is visible
                QTimer.singleShot(300, self.execute_auto_update)
            else:
                if hasattr(self, 'append_to_log'):
                    self.append_to_log(f"[SYSTEM] Already updated today ({today}). Skipping auto-update.")
                self.statusBar().showMessage(f"Prices already updated today. Use 'Refresh All Prices' to update manually.", 5000)
        
        except Exception as e:
            if hasattr(self, 'append_to_log'):
                self.append_to_log(f"[ERROR] Auto-update check failed: {str(e)}")
            print(f"Auto-update check error: {e}")

    
    def check_password(self):
        """Check if password protection is enabled"""
        config = self.data_manager.load_config()
        if config.get('password_hash'):
            password, ok = QInputDialog.getText(None, "Password Required", 
                                               "Enter password:", QLineEdit.EchoMode.Password)
            if not ok:
                sys.exit()
            
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            if password_hash != config['password_hash']:
                QMessageBox.critical(None, "Error", "Incorrect password!")
                sys.exit()
    
    def setup_ui(self):
        self.setWindowTitle("Net Worth Tracker Pro")
        self.setMinimumSize(1455, 625)
        self.resize(1455, 625)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout()
        
        # Sidebar
        sidebar = self.create_sidebar()
        main_layout.addWidget(sidebar)
        
        # Content area
        self.content_stack = QTabWidget()
        self.content_stack.setTabPosition(QTabWidget.TabPosition.North)
        self.content_stack.tabBar().hide()
        
        # ✅ REMOVED GOALS TAB - indices updated
        self.content_stack.addTab(self.create_dashboard(), "Dashboard")
        self.content_stack.addTab(self.create_assets_tab(), "Assets")
        self.content_stack.addTab(self.create_liabilities_tab(), "Liabilities")
        self.content_stack.addTab(self.create_income_expense_tab(), "Income/Expense")
        self.content_stack.addTab(self.create_transaction_log_tab(), "Transaction Log")
        self.content_stack.addTab(self.create_reports_tab(), "Reports")
        self.content_stack.addTab(self.create_api_config_tab(), "API Config")
        self.content_stack.addTab(self.create_settings_tab(), "Settings")
        
        main_layout.addWidget(self.content_stack, stretch=1)
        
        central_widget.setLayout(main_layout)
        
        # Status bar
        self.setStatusBar(QStatusBar())
        self.statusBar().showMessage("Ready")
        
        # Force layout recalculation
        central_widget.updateGeometry()
        self.adjustSize()
        QApplication.processEvents()
    
    def create_sidebar(self):
        """Create navigation sidebar"""
        sidebar = QWidget()
        sidebar.setFixedWidth(200)
        sidebar.setObjectName("sidebar")
        layout = QVBoxLayout()
        
        title = QLabel("Net Worth Tracker")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # ✅ REMOVED GOALS - indices updated
        buttons = [
            ("Dashboard", 0),
            ("Assets", 1),
            ("Liabilities", 2),
            ("Income/Expense", 3),
            ("Transaction Log", 4),
            ("Reports", 5),
            ("API Config", 6),
            ("Settings", 7)
        ]
        for text, index in buttons:
            btn = QPushButton(text)
            btn.setMinimumHeight(40)
            btn.clicked.connect(lambda checked, i=index: self.content_stack.setCurrentIndex(i))
            layout.addWidget(btn)
        
        layout.addStretch()
        sidebar.setLayout(layout)
        return sidebar
    
    def create_dashboard(self):
        """Create dashboard tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Net worth cards
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(12)
        cards_layout.setContentsMargins(0, 0, 0, 12)

        networth_data = self.data_manager.calculate_networth()

        # Get currency settings
        config = self.data_manager.load_config()
        currency = config.get('currency', 'USD')
        currency_symbol = CurrencyConverter.get_symbol(currency)

        # ✅ FIX: Convert USD values to selected currency
        total_assets_usd = networth_data['total_assets']
        total_liabilities_usd = networth_data['total_liabilities']
        net_worth_usd = networth_data['net_worth']
        
        # Convert to display currency
        total_assets = CurrencyConverter.convert(total_assets_usd, currency)
        total_liabilities = CurrencyConverter.convert(total_liabilities_usd, currency)
        net_worth = CurrencyConverter.convert(net_worth_usd, currency)

        # Total Assets Card
        assets_card = self.create_card("Total Assets", 
                                    f"{currency_symbol}{total_assets:,.2f}",
                                    "#10b981")
        cards_layout.addWidget(assets_card, stretch=1)

        # Total Liabilities Card
        liabilities_card = self.create_card("Total Liabilities",
                                        f"{currency_symbol}{total_liabilities:,.2f}",
                                        "#ef4444")
        cards_layout.addWidget(liabilities_card, stretch=1)

        # Net Worth Card
        networth_card = self.create_card("Net Worth",
                                        f"{currency_symbol}{net_worth:,.2f}",
                                        "#3b82f6")
        cards_layout.addWidget(networth_card, stretch=1)

        layout.addLayout(cards_layout)

        # Force layout update
        QApplication.processEvents()
        
        # Time filter for chart
        filter_layout = QHBoxLayout()
        filter_label = QLabel("Chart Period:")
        
        self.chart_filter = QComboBox()
        self.chart_filter.addItems(["Last 7 Days", "Last Month", "Last 3 Months", "Last 6 Months", "Last Year", "All Time"])
        self.chart_filter.setCurrentText("Last 6 Months")
        self.chart_filter.currentTextChanged.connect(self.refresh_dashboard)
        
        filter_layout.addWidget(filter_label)
        filter_layout.addWidget(self.chart_filter)
        filter_layout.addStretch()
        layout.addLayout(filter_layout)
        
        # Charts - FIT FOR 1920x1080
        charts_layout = QHBoxLayout()
        charts_layout.setSpacing(15)

        # Net worth trend chart with interactive tooltips
        trend_chart = ChartWidget()
        trend_chart.setObjectName("card")
        trend_chart.setMinimumHeight(350)
        trend_chart.setMaximumHeight(400)
        trend_chart.setMinimumWidth(500)
        
        # Get filter value
        filter_value = self.chart_filter.currentText() if hasattr(self, 'chart_filter') else "Last 6 Months"
        trend_chart.plot_networth_trend(self.data_manager, filter_value, currency)
        charts_layout.addWidget(trend_chart, stretch=3)

        # Asset allocation chart
        allocation_chart = ChartWidget()
        allocation_chart.setObjectName("card")
        allocation_chart.setMinimumHeight(350)
        allocation_chart.setMaximumHeight(400)
        allocation_chart.setMinimumWidth(400)
        allocation_chart.plot_asset_allocation(self.data_manager)
        charts_layout.addWidget(allocation_chart, stretch=2)

        layout.addLayout(charts_layout)

        # Recent Updates Section - SINGLE LINE
        recent_label = QLabel("📋 Most Recent Update")
        recent_label.setObjectName("muted")
        recent_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        layout.addWidget(recent_label)

        recent_widget = self.create_recent_updates_widget()
        layout.addWidget(recent_widget)

        layout.addStretch()
        widget.setLayout(layout)
        return widget

    def create_recent_updates_widget(self):
        """Create widget showing recent updates - SINGLE LINE SCROLLABLE"""
        widget = QWidget()
        widget.setObjectName("card")
        widget.setMaximumHeight(60)
        widget.setMinimumHeight(60)
        
        # Use QScrollArea for long text
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")
        scroll.setMaximumHeight(60)
        
        content = QWidget()
        layout = QHBoxLayout(content)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Get recent transactions
        trans_df = self.data_manager.read_excel("transactions.xlsx")
        
        if trans_df.empty:
            no_updates = QLabel("No recent activity")
            no_updates.setObjectName("muted")
            layout.addWidget(no_updates)
        else:
            # Sort by timestamp and get ONLY THE LAST ONE
            trans_df = trans_df.sort_values('Timestamp', ascending=False).head(1)
            
            trans = trans_df.iloc[0]
            update_text = f"{trans['Timestamp']} - {trans['Action']}: {trans['Category']}"
            update_label = QLabel(update_text)
            update_label.setWordWrap(False)
            layout.addWidget(update_label)
            layout.addStretch()
        
        scroll.setWidget(content)
        
        container_layout = QVBoxLayout(widget)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.addWidget(scroll)
        
        return widget
        
    def create_card(self, title, value, color):
        """Create a compact stat card"""
        card = QWidget()
        card.setMinimumHeight(90)
        card.setMinimumWidth(280)
        card.setMaximumHeight(105)
        card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        
        # Use inline style with explicit text color
        card.setStyleSheet(f"""
            background-color: {color};
            border-radius: 10px;
        """)
        
        layout = QVBoxLayout(card)
        layout.setSpacing(6)
        layout.setContentsMargins(18, 14, 18, 14)
        
        # Title label with explicit styling
        title_label = QLabel(title)
        title_label.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        title_label.setStyleSheet("color: white; background: transparent;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        title_label.setFixedHeight(20)
        
        # Value label with explicit styling
        value_label = QLabel(value)
        value_label.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        value_label.setStyleSheet("color: white; background: transparent;")
        value_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignBottom)
        value_label.setFixedHeight(35)
        
        layout.addWidget(title_label)
        layout.addWidget(value_label)
        layout.addStretch(0)
        
        return card
    
    def get_currency_symbol(self, currency):
        """Get currency symbol based on currency code"""
        return CurrencyConverter.get_symbol(currency)
    
    def convert_currency(self, amount_usd, target_currency):
        """Convert USD amount to target currency"""
        return CurrencyConverter.convert(amount_usd, target_currency)
    
    def create_assets_tab(self):
        """Create assets management tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Toolbar
        toolbar = QHBoxLayout()
        add_btn = QPushButton("➕ Add Asset")
        add_btn.clicked.connect(self.add_asset)
        
        edit_btn = QPushButton("✏️ Edit")
        edit_btn.clicked.connect(self.edit_asset)
        
        delete_btn = QPushButton("🗑️ Delete")
        delete_btn.clicked.connect(self.delete_asset)
        
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self.refresh_assets_table)
        
        toolbar.addWidget(add_btn)
        toolbar.addWidget(edit_btn)
        toolbar.addWidget(delete_btn)
        toolbar.addWidget(refresh_btn)
        toolbar.addStretch()
        
        layout.addLayout(toolbar)
        
        # Table
        self.assets_table = QTableWidget()
        self.refresh_assets_table()
        layout.addWidget(self.assets_table)
        
        widget.setLayout(layout)
        return widget
    
    def refresh_assets_table(self):
        """Refresh assets table"""
        df = self.data_manager.read_excel("assets.xlsx")
        
        self.assets_table.setRowCount(len(df))
        self.assets_table.setColumnCount(len(df.columns))
        self.assets_table.setHorizontalHeaderLabels(df.columns.tolist())
        
        for i, row in df.iterrows():
            for j, value in enumerate(row):
                self.assets_table.setItem(i, j, QTableWidgetItem(str(value)))
        
        # Proper column resizing with forced update
        self.assets_table.resizeColumnsToContents()
        self.assets_table.horizontalHeader().setStretchLastSection(True)
        
        # Force immediate geometry update
        self.assets_table.updateGeometry()
        self.assets_table.viewport().update()
        self.assets_table.horizontalHeader().updateGeometry()
        QApplication.processEvents()

    def add_asset(self):
        """Open add asset dialog"""
        dialog = AddAssetDialog(self.data_manager, self)
        if dialog.exec():
            self.refresh_assets_table()
            self.statusBar().showMessage("Asset added successfully", 3000)
    
    def edit_asset(self):
        """Edit selected asset"""
        current_row = self.assets_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Error", "Please select an asset to edit")
            return
        
        record_id = int(self.assets_table.item(current_row, 0).text())
        dialog = AddAssetDialog(self.data_manager, self, edit_mode=True, record_id=record_id)
        if dialog.exec():
            self.refresh_assets_table()
            self.statusBar().showMessage("Asset updated successfully", 3000)
    
    def delete_asset(self):
        """Delete selected asset"""
        current_row = self.assets_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Error", "Please select an asset to delete")
            return
        
        reply = QMessageBox.question(self, "Confirm Delete", 
                                    "Are you sure you want to delete this asset?",
                                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            record_id = int(self.assets_table.item(current_row, 0).text())
            self.data_manager.delete_record("assets.xlsx", record_id)
            self.refresh_assets_table()
            self.statusBar().showMessage("Asset deleted successfully", 3000)

    def create_liabilities_tab(self):
        """Create liabilities management tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Toolbar
        toolbar = QHBoxLayout()
        add_btn = QPushButton("➕ Add Liability")
        add_btn.clicked.connect(self.add_liability)
        
        edit_btn = QPushButton("✏️ Edit")
        edit_btn.clicked.connect(self.edit_liability)
        
        delete_btn = QPushButton("🗑️ Delete")
        delete_btn.clicked.connect(self.delete_liability)
        
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self.refresh_liabilities_table)
        
        toolbar.addWidget(add_btn)
        toolbar.addWidget(edit_btn)
        toolbar.addWidget(delete_btn)
        toolbar.addWidget(refresh_btn)
        toolbar.addStretch()
        
        layout.addLayout(toolbar)
        
        # Table
        self.liabilities_table = QTableWidget()
        self.refresh_liabilities_table()
        layout.addWidget(self.liabilities_table)
        
        widget.setLayout(layout)
        return widget
    
    def refresh_liabilities_table(self):
        """Refresh liabilities table"""
        df = self.data_manager.read_excel("liabilities.xlsx")
        
        self.liabilities_table.setRowCount(len(df))
        self.liabilities_table.setColumnCount(len(df.columns))
        self.liabilities_table.setHorizontalHeaderLabels(df.columns.tolist())
        
        for i, row in df.iterrows():
            for j, value in enumerate(row):
                self.liabilities_table.setItem(i, j, QTableWidgetItem(str(value)))
        
        # Proper column resizing with forced update
        self.liabilities_table.resizeColumnsToContents()
        self.liabilities_table.horizontalHeader().setStretchLastSection(True)
        
        # Force immediate geometry update
        self.liabilities_table.updateGeometry()
        self.liabilities_table.viewport().update()
        self.liabilities_table.horizontalHeader().updateGeometry()
        QApplication.processEvents()
    
    def add_liability(self):
        """Open add liability dialog"""
        dialog = AddLiabilityDialog(self.data_manager, self)
        if dialog.exec():
            self.refresh_liabilities_table()
            self.statusBar().showMessage("Liability added successfully", 3000)
    
    def edit_liability(self):
        """Edit selected liability"""
        current_row = self.liabilities_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Error", "Please select a liability to edit")
            return
        
        record_id = int(self.liabilities_table.item(current_row, 0).text())
        dialog = AddLiabilityDialog(self.data_manager, self, edit_mode=True, record_id=record_id)
        if dialog.exec():
            self.refresh_liabilities_table()
            self.statusBar().showMessage("Liability updated successfully", 3000)
    
    def delete_liability(self):
        """Delete selected liability"""
        current_row = self.liabilities_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Error", "Please select a liability to delete")
            return
        
        reply = QMessageBox.question(self, "Confirm Delete",
                                    "Are you sure you want to delete this liability?",
                                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            record_id = int(self.liabilities_table.item(current_row, 0).text())
            self.data_manager.delete_record("liabilities.xlsx", record_id)
            self.refresh_liabilities_table()
            self.statusBar().showMessage("Liability deleted successfully", 3000)
    
    def create_goals_tab(self):
        """Create goals tracking tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        title = QLabel("🎯 Financial Goals")
        title.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # Toolbar
        toolbar = QHBoxLayout()
        add_goal_btn = QPushButton("➕ Add Goal")
        add_goal_btn.clicked.connect(self.add_goal)
        
        edit_goal_btn = QPushButton("✏️ Edit Goal")
        edit_goal_btn.clicked.connect(self.edit_goal)
        
        delete_goal_btn = QPushButton("🗑️ Delete Goal")
        delete_goal_btn.clicked.connect(self.delete_goal)
        
        update_progress_btn = QPushButton("📊 Update Progress")
        update_progress_btn.clicked.connect(self.update_goal_progress)
        
        toolbar.addWidget(add_goal_btn)
        toolbar.addWidget(edit_goal_btn)
        toolbar.addWidget(delete_goal_btn)
        toolbar.addWidget(update_progress_btn)
        toolbar.addStretch()
        
        layout.addLayout(toolbar)
        
        # Goals display in a scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout()
        
        goals_df = self.data_manager.read_excel("goals.xlsx")
        
        if goals_df.empty:
            no_goals_label = QLabel("No goals yet. Click 'Add Goal' to get started!")
            no_goals_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            no_goals_label.setStyleSheet("color: #64748b; font-size: 14px; padding: 40px;")
            scroll_layout.addWidget(no_goals_label)
        else:
            for _, goal in goals_df.iterrows():
                goal_widget = self.create_goal_widget(goal)
                scroll_layout.addWidget(goal_widget)
        
        scroll_layout.addStretch()
        scroll_content.setLayout(scroll_layout)
        scroll.setWidget(scroll_content)
        
        layout.addWidget(scroll)
        
        widget.setLayout(layout)
        return widget
    
    def create_goal_widget(self, goal):
        """Create a goal progress widget"""
        widget = QWidget()
        widget.setStyleSheet("background-color: #1e293b; border-radius: 10px; padding: 15px;")
        layout = QVBoxLayout()
        
        # Goal name
        name_label = QLabel(goal['Goal_Name'])
        name_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        layout.addWidget(name_label)
        
        # Progress bar
        progress = QProgressBar()
        progress_percent = (goal['Current_Amount'] / goal['Target_Amount'] * 100) if goal['Target_Amount'] > 0 else 0
        progress.setValue(int(progress_percent))
        layout.addWidget(progress)
        
        # Amount label
        amount_label = QLabel(f"${goal['Current_Amount']:,.2f} / ${goal['Target_Amount']:,.2f}")
        layout.addWidget(amount_label)
        
        widget.setLayout(layout)
        return widget
    
    def add_goal(self):
        """Add a new financial goal"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Add Goal")
        layout = QFormLayout()
        
        name_input = QLineEdit()
        target_input = QDoubleSpinBox()
        target_input.setMaximum(999999999)
        target_input.setPrefix("$")
        
        current_input = QDoubleSpinBox()
        current_input.setMaximum(999999999)
        current_input.setPrefix("$")
        
        deadline_input = QDateEdit()
        deadline_input.setDate(QDate.currentDate().addMonths(12))
        
        layout.addRow("Goal Name:", name_input)
        layout.addRow("Target Amount:", target_input)
        layout.addRow("Current Amount:", current_input)
        layout.addRow("Deadline:", deadline_input)
        
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        cancel_btn = QPushButton("Cancel")
        
        def save():
            goal = {
                "ID": self.data_manager.generate_id("goals.xlsx"),
                "Goal_Name": name_input.text(),
                "Target_Amount": target_input.value(),
                "Current_Amount": current_input.value(),
                "Deadline": deadline_input.date().toString("yyyy-MM-dd"),
                "Status": "Active"
            }
            self.data_manager.add_record("goals.xlsx", goal)
            dialog.accept()
            self.content_stack.setCurrentIndex(3)  # Refresh goals tab
        
        save_btn.clicked.connect(save)
        cancel_btn.clicked.connect(dialog.reject)
        
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addRow(btn_layout)
        
        dialog.setLayout(layout)
        dialog.exec()
    
    def create_reports_tab(self):
        """Create reports and export tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        title = QLabel("📊 Reports & Export")
        title.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # Export buttons
        export_layout = QHBoxLayout()
        
        excel_btn = QPushButton("📄 Export to Excel")
        excel_btn.clicked.connect(self.export_to_excel)
        
        pdf_btn = QPushButton("📑 Export to PDF")
        pdf_btn.clicked.connect(self.export_to_pdf)
        
        backup_btn = QPushButton("💾 Create Backup")
        backup_btn.clicked.connect(self.create_backup)
        
        export_layout.addWidget(excel_btn)
        export_layout.addWidget(pdf_btn)
        export_layout.addWidget(backup_btn)
        
        layout.addLayout(export_layout)
        
        # Monthly summary
        summary_label = QLabel("Monthly Net Worth Summary")
        summary_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        layout.addWidget(summary_label)
        
        self.summary_table = QTableWidget()
        self.refresh_summary_table()
        layout.addWidget(self.summary_table)
        
        widget.setLayout(layout)
        return widget
    
    def refresh_summary_table(self):
        """Refresh monthly summary table"""
        df = self.data_manager.read_excel("monthly_networth.xlsx")
        
        self.summary_table.setRowCount(len(df))
        self.summary_table.setColumnCount(len(df.columns))
        self.summary_table.setHorizontalHeaderLabels(df.columns.tolist())
        
        for i, row in df.iterrows():
            for j, value in enumerate(row):
                self.summary_table.setItem(i, j, QTableWidgetItem(str(value)))
        
        # Proper column resizing with forced update
        self.summary_table.resizeColumnsToContents()
        self.summary_table.horizontalHeader().setStretchLastSection(True)
        
        # Force immediate geometry update
        self.summary_table.updateGeometry()
        self.summary_table.viewport().update()
        self.summary_table.horizontalHeader().updateGeometry()
        QApplication.processEvents()
    
    def export_to_excel(self):
        """Export all data to a single Excel file"""
        filename, _ = QFileDialog.getSaveFileName(self, "Export to Excel", 
                                                   f"NetWorth_Report_{datetime.now().strftime('%Y%m%d')}.xlsx",
                                                   "Excel Files (*.xlsx)")
        if filename:
            with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                self.data_manager.read_excel("assets.xlsx").to_excel(writer, sheet_name="Assets", index=False)
                self.data_manager.read_excel("liabilities.xlsx").to_excel(writer, sheet_name="Liabilities", index=False)
                self.data_manager.read_excel("monthly_networth.xlsx").to_excel(writer, sheet_name="Monthly_Summary", index=False)
                self.data_manager.read_excel("goals.xlsx").to_excel(writer, sheet_name="Goals", index=False)
            
            QMessageBox.information(self, "Success", f"Report exported to {filename}")
            self.statusBar().showMessage("Export completed successfully", 3000)
    
    def export_to_pdf(self):
        """Export report to PDF"""
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.lib import colors
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
            from reportlab.lib.enums import TA_CENTER
            
            filename, _ = QFileDialog.getSaveFileName(self, "Export to PDF",
                                                    f"NetWorth_Report_{datetime.now().strftime('%Y%m%d')}.pdf",
                                                    "PDF Files (*.pdf)")
            if not filename:
                return
            
            doc = SimpleDocTemplate(filename, pagesize=letter)
            story = []
            styles = getSampleStyleSheet()
            
            # Title
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                textColor=colors.HexColor('#1e293b'),
                spaceAfter=30,
                alignment=TA_CENTER
            )
            story.append(Paragraph("Net Worth Report", title_style))
            story.append(Paragraph(f"Generated: {datetime.now().strftime('%B %d, %Y')}", styles['Normal']))
            story.append(Spacer(1, 0.5*inch))
            
            # Net Worth Summary
            networth_data = self.data_manager.calculate_networth()
            
            summary_data = [
                ['Metric', 'Value'],
                ['Total Assets', f"${networth_data['total_assets']:,.2f}"],
                ['Total Liabilities', f"${networth_data['total_liabilities']:,.2f}"],
                ['Net Worth', f"${networth_data['net_worth']:,.2f}"]
            ]
            
            summary_table = Table(summary_data, colWidths=[3*inch, 2*inch])
            summary_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3b82f6')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(summary_table)
            
            doc.build(story)
            
            QMessageBox.information(self, "Success", f"PDF report exported to {filename}")
            self.statusBar().showMessage("PDF export completed successfully", 3000)
            
        except ImportError:
            QMessageBox.warning(self, "Module Required",
                            "PDF export requires 'reportlab' package.\n\n"
                            "Install it using:\npip install reportlab")
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to export PDF: {str(e)}")
    
    def create_backup(self):
        """Create backup of all data"""
        backup_path = self.data_manager.create_backup()
        QMessageBox.information(self, "Backup Created", f"Backup saved to:\n{backup_path}")
        self.statusBar().showMessage("Backup created successfully", 3000)
    
    def create_settings_tab(self):
        """Create settings tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        title = QLabel("⚙️ Settings")
        title.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # Settings Form
        settings_widget = QWidget()
        settings_widget.setObjectName("card")
        settings_layout = QVBoxLayout()
        
        # Theme toggle
        theme_layout = QHBoxLayout()
        theme_label = QLabel("Theme:")
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Dark", "Light"])
        
        config = self.data_manager.load_config()
        self.theme_combo.setCurrentText(config['theme'].capitalize())
        
        theme_layout.addWidget(theme_label)
        theme_layout.addWidget(self.theme_combo)
        theme_layout.addStretch()
        settings_layout.addLayout(theme_layout)
        
        # Currency selection
        currency_layout = QHBoxLayout()
        currency_label = QLabel("Currency:")
        self.currency_combo = QComboBox()
        self.currency_combo.addItems(["USD", "EUR", "GBP", "LKR", "INR"])
        self.currency_combo.setCurrentText(config['currency'])
        
        currency_layout.addWidget(currency_label)
        currency_layout.addWidget(self.currency_combo)
        currency_layout.addStretch()
        settings_layout.addLayout(currency_layout)
        
        # Save Settings Button
        save_settings_btn = QPushButton("💾 Save Settings")
        save_settings_btn.setObjectName("primary")
        save_settings_btn.clicked.connect(self.save_settings)
        settings_layout.addWidget(save_settings_btn)
        
        settings_widget.setLayout(settings_layout)
        layout.addWidget(settings_widget)
        
        # Password settings
        password_btn = QPushButton("🔒 Set/Change Password")
        password_btn.clicked.connect(self.set_password)
        layout.addWidget(password_btn)
        
        # Data directory
        data_dir_btn = QPushButton("📁 Open Data Directory")
        def open_data_dir():
            import platform
            import subprocess
            path = str(self.data_manager.data_dir.absolute())
            if platform.system() == "Windows":
                os.startfile(path)
            elif platform.system() == "Darwin":  # macOS
                subprocess.Popen(["open", path])
            else:  # Linux
                subprocess.Popen(["xdg-open", path])
        data_dir_btn.clicked.connect(open_data_dir)
        layout.addWidget(data_dir_btn)
        
        # About
        about_label = QLabel("\n📊 Net Worth Tracker Pro v1.0\n\nA comprehensive personal finance management tool.\n\nFeatures:\n• Asset & Liability tracking\n• Monthly net worth snapshots\n• Goal tracking\n• Data visualization\n• Excel-based storage\n• Multi-user support")
        about_label.setWordWrap(True)
        about_label.setObjectName("muted")
        layout.addWidget(about_label)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def change_theme(self, theme):
        """Change application theme"""
        config = self.data_manager.load_config()
        config['theme'] = theme.lower()
        self.data_manager.save_config(config)
        self.apply_theme()
        
        # Force all widgets to update their geometry
        for i in range(self.content_stack.count()):
            widget = self.content_stack.widget(i)
            if widget:
                widget.updateGeometry()
                widget.update()
        
        self.refresh_all_views()

        # Refresh all tabs to apply new theme
        current_index = self.content_stack.currentIndex()
        self.content_stack.setCurrentIndex(0)
        QApplication.processEvents()
        self.content_stack.setCurrentIndex(current_index)
        QApplication.processEvents()

    def save_settings(self):
        """Save all settings at once"""
        theme = self.theme_combo.currentText()
        currency = self.currency_combo.currentText()
        
        config = self.data_manager.load_config()
        config['theme'] = theme.lower()
        config['currency'] = currency
        self.data_manager.save_config(config)
        
        # Apply theme
        self.apply_theme()
        
        # Refresh dashboard to show new currency
        self.content_stack.setCurrentIndex(0)
        QApplication.processEvents()
        
        QMessageBox.information(self, "Settings Saved", 
                              f"✅ Settings saved successfully!\n\n"
                              f"Theme: {theme}\n"
                              f"Currency: {currency}")
        self.statusBar().showMessage(f"Settings saved: {theme} theme, {currency} currency", 5000)
    
    def set_password(self):
        """Set or change password"""
        password, ok = QInputDialog.getText(self, "Set Password",
                                           "Enter new password:",
                                           QLineEdit.EchoMode.Password)
        if ok and password:
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            config = self.data_manager.load_config()
            config['password_hash'] = password_hash
            self.data_manager.save_config(config)
            QMessageBox.information(self, "Success", "Password set successfully!")
            self.statusBar().showMessage("Password updated", 3000)
    
    def apply_theme(self):
        """Apply theme to application"""
        config = self.data_manager.load_config()
        theme = config.get('theme', 'dark')
        
        if theme == 'dark':
            self.setStyleSheet(self.theme_manager.get_dark_theme())
        else:
            self.setStyleSheet(self.theme_manager.get_light_theme())
        
        # Force immediate style recalculation
        self.style().unpolish(self)
        self.style().polish(self)
        
        # Update matplotlib chart colors based on theme
        self.update_chart_theme(theme)
        
        # Force repaint
        self.update()
        QApplication.processEvents()

    def refresh_all_views(self):
        """Refresh all views after theme change"""
        try:
            self.refresh_assets_table()
        except:
            pass
        
        try:
            self.refresh_liabilities_table()
        except:
            pass
        
        try:
            self.refresh_income_expense_table()
        except:
            pass
        
        try:
            self.refresh_transaction_log()
        except:
            pass
        
        try:
            self.refresh_summary_table()
        except:
            pass

    def refresh_all_tables_on_startup(self):
        """Force refresh all tables on startup to prevent column crumbling"""
        try:
            # Refresh all table views
            if hasattr(self, 'assets_table'):
                self.refresh_assets_table()
            
            if hasattr(self, 'liabilities_table'):
                self.refresh_liabilities_table()
            
            if hasattr(self, 'income_expense_table'):
                self.refresh_income_expense_table()
            
            if hasattr(self, 'transaction_log_table'):
                self.refresh_transaction_log()
            
            if hasattr(self, 'summary_table'):
                self.refresh_summary_table()
            
            # Force geometry recalculation
            self.update()
            QApplication.processEvents()
            
        except Exception as e:
            print(f"Error refreshing tables on startup: {e}")

    def update_chart_theme(self, theme):
        """Update matplotlib chart colors based on theme"""
        import matplotlib.pyplot as plt
        
        if theme == 'dark':
            plt.style.use('dark_background')
            # Set matplotlib colors to match our dark theme
            plt.rcParams['figure.facecolor'] = '#0f172a'
            plt.rcParams['axes.facecolor'] = '#0f172a'
            plt.rcParams['axes.edgecolor'] = '#334155'
            plt.rcParams['axes.labelcolor'] = '#e2e8f0'
            plt.rcParams['text.color'] = '#e2e8f0'
            plt.rcParams['xtick.color'] = '#e2e8f0'
            plt.rcParams['ytick.color'] = '#e2e8f0'
            plt.rcParams['grid.color'] = '#334155'
        else:
            plt.style.use('default')
            # Set matplotlib colors to match our light theme
            plt.rcParams['figure.facecolor'] = '#ffffff'
            plt.rcParams['axes.facecolor'] = '#ffffff'
            plt.rcParams['axes.edgecolor'] = '#e2e8f0'
            plt.rcParams['axes.labelcolor'] = '#1e293b'
            plt.rcParams['text.color'] = '#1e293b'
            plt.rcParams['xtick.color'] = '#1e293b'
            plt.rcParams['ytick.color'] = '#1e293b'
            plt.rcParams['grid.color'] = '#e2e8f0'
    
    def generate_insights(self):
        """Generate smart insights based on data"""
        networth_data = self.data_manager.calculate_networth()
        assets_df = self.data_manager.read_excel("assets.xlsx")
        liabilities_df = self.data_manager.read_excel("liabilities.xlsx")
        monthly_df = self.data_manager.read_excel("monthly_networth.xlsx")
        
        return FinancialCalculator.generate_insights(
            networth_data, assets_df, liabilities_df, monthly_df
        )

    def main():
        """Main application entry point"""
        app = QApplication(sys.argv)
        app.setApplicationName("Net Worth Tracker Pro")
        
        window = MainWindow()
        window.show()
        
        sys.exit(app.exec())

        def create_liabilities_tab(self):
            """Create liabilities management tab"""
            widget = QWidget()
            layout = QVBoxLayout()
            
            # Toolbar
            toolbar = QHBoxLayout()
            add_btn = QPushButton("➕ Add Liability")
            add_btn.clicked.connect(self.add_liability)
            
            edit_btn = QPushButton("✏️ Edit")
            edit_btn.clicked.connect(self.edit_liability)
            
            delete_btn = QPushButton("🗑️ Delete")
            delete_btn.clicked.connect(self.delete_liability)
            
            refresh_btn = QPushButton("🔄 Refresh")
            refresh_btn.clicked.connect(self.refresh_liabilities_table)
            
            toolbar.addWidget(add_btn)
            toolbar.addWidget(edit_btn)
            toolbar.addWidget(delete_btn)
            toolbar.addWidget(refresh_btn)
            toolbar.addStretch()
            
            layout.addLayout(toolbar)
            
            # Table
            self.liabilities_table = QTableWidget()
            self.refresh_liabilities_table()
            layout.addWidget(self.liabilities_table)
            
            widget.setLayout(layout)
            return widget
    
    def refresh_liabilities_table(self):
        """Refresh liabilities table"""
        df = self.data_manager.read_excel("liabilities.xlsx")
        
        self.liabilities_table.setRowCount(len(df))
        self.liabilities_table.setColumnCount(len(df.columns))
        self.liabilities_table.setHorizontalHeaderLabels(df.columns.tolist())
        
        for i, row in df.iterrows():
            for j, value in enumerate(row):
                self.liabilities_table.setItem(i, j, QTableWidgetItem(str(value)))
        
        # Proper column resizing with forced update
        self.liabilities_table.resizeColumnsToContents()
        self.liabilities_table.horizontalHeader().setStretchLastSection(True)
        
        # Force immediate geometry update
        self.liabilities_table.updateGeometry()
        self.liabilities_table.viewport().update()
        self.liabilities_table.horizontalHeader().updateGeometry()
        QApplication.processEvents()
    
    def add_liability(self):
        """Open add liability dialog"""
        dialog = AddLiabilityDialog(self.data_manager, self)
        if dialog.exec():
            self.refresh_liabilities_table()
            self.statusBar().showMessage("Liability added successfully", 3000)
    
    def edit_liability(self):
        """Edit selected liability"""
        current_row = self.liabilities_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Error", "Please select a liability to edit")
            return
        
        record_id = int(self.liabilities_table.item(current_row, 0).text())
        dialog = AddLiabilityDialog(self.data_manager, self, edit_mode=True, record_id=record_id)
        if dialog.exec():
            self.refresh_liabilities_table()
            self.statusBar().showMessage("Liability updated successfully", 3000)
    
    def delete_liability(self):
        """Delete selected liability"""
        current_row = self.liabilities_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Error", "Please select a liability to delete")
            return
        
        reply = QMessageBox.question(self, "Confirm Delete",
                                    "Are you sure you want to delete this liability?",
                                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            record_id = int(self.liabilities_table.item(current_row, 0).text())
            self.data_manager.delete_record("liabilities.xlsx", record_id)
            self.refresh_liabilities_table()
            self.statusBar().showMessage("Liability deleted successfully", 3000)
    
    def create_goals_tab(self):
        """Create goals tracking tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        title = QLabel("🎯 Financial Goals")
        title.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # Goals display
        goals_df = self.data_manager.read_excel("goals.xlsx")
        
        for _, goal in goals_df.iterrows():
            goal_widget = self.create_goal_widget(goal)
            layout.addWidget(goal_widget)
        
        # Add goal button
        add_goal_btn = QPushButton("➕ Add New Goal")
        add_goal_btn.clicked.connect(self.add_goal)
        layout.addWidget(add_goal_btn)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def create_goal_widget(self, goal):
        """Create a goal progress widget"""
        widget = QWidget()
        widget.setStyleSheet("background-color: #1e293b; border-radius: 10px; padding: 15px;")
        layout = QVBoxLayout()
        
        # Goal name
        name_label = QLabel(goal['Goal_Name'])
        name_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        layout.addWidget(name_label)
        
        # Progress bar
        progress = QProgressBar()
        progress_percent = (goal['Current_Amount'] / goal['Target_Amount'] * 100) if goal['Target_Amount'] > 0 else 0
        progress.setValue(int(progress_percent))
        layout.addWidget(progress)
        
        # Amount label
        amount_label = QLabel(f"${goal['Current_Amount']:,.2f} / ${goal['Target_Amount']:,.2f}")
        layout.addWidget(amount_label)
        
        widget.setLayout(layout)
        return widget
    
    def add_goal(self):
        """Add a new financial goal"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Add Goal")
        layout = QFormLayout()
        
        name_input = QLineEdit()
        target_input = QDoubleSpinBox()
        target_input.setMaximum(999999999)
        target_input.setPrefix("$")
        
        current_input = QDoubleSpinBox()
        current_input.setMaximum(999999999)
        current_input.setPrefix("$")
        
        deadline_input = QDateEdit()
        deadline_input.setDate(QDate.currentDate().addMonths(12))
        
        layout.addRow("Goal Name:", name_input)
        layout.addRow("Target Amount:", target_input)
        layout.addRow("Current Amount:", current_input)
        layout.addRow("Deadline:", deadline_input)
        
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        cancel_btn = QPushButton("Cancel")
        
        def save():
            goal = {
                "ID": self.data_manager.generate_id("goals.xlsx"),
                "Goal_Name": name_input.text(),
                "Target_Amount": target_input.value(),
                "Current_Amount": current_input.value(),
                "Deadline": deadline_input.date().toString("yyyy-MM-dd"),
                "Status": "Active"
            }
            self.data_manager.add_record("goals.xlsx", goal)
            dialog.accept()
            self.content_stack.setCurrentIndex(4)  # Refresh goals tab
        
        save_btn.clicked.connect(save)
        cancel_btn.clicked.connect(dialog.reject)
        
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addRow(btn_layout)
        
        dialog.setLayout(layout)
        dialog.exec()
    
    def create_reports_tab(self):
        """Create reports and export tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        title = QLabel("📊 Reports & Export")
        title.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # Export buttons
        export_layout = QHBoxLayout()
        
        excel_btn = QPushButton("📄 Export to Excel")
        excel_btn.clicked.connect(self.export_to_excel)
        
        pdf_btn = QPushButton("📑 Export to PDF")
        pdf_btn.clicked.connect(self.export_to_pdf)
        
        backup_btn = QPushButton("💾 Create Backup")
        backup_btn.clicked.connect(self.create_backup)
        
        export_layout.addWidget(excel_btn)
        export_layout.addWidget(pdf_btn)
        export_layout.addWidget(backup_btn)
        
        layout.addLayout(export_layout)
        
        # Monthly summary
        summary_label = QLabel("Monthly Net Worth Summary")
        summary_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        layout.addWidget(summary_label)
        
        self.summary_table = QTableWidget()
        self.refresh_summary_table()
        layout.addWidget(self.summary_table)
        
        widget.setLayout(layout)
        return widget
    
    def refresh_summary_table(self):
        """Refresh monthly summary table"""
        df = self.data_manager.read_excel("monthly_networth.xlsx")
        
        self.summary_table.setRowCount(len(df))
        self.summary_table.setColumnCount(len(df.columns))
        self.summary_table.setHorizontalHeaderLabels(df.columns.tolist())
        
        for i, row in df.iterrows():
            for j, value in enumerate(row):
                self.summary_table.setItem(i, j, QTableWidgetItem(str(value)))
        
        # Proper column resizing
        self.summary_table.resizeColumnsToContents()
        self.summary_table.horizontalHeader().setStretchLastSection(True)
        
        # Force layout update
        self.summary_table.viewport().update()
        QApplication.processEvents()
    
    def export_to_excel(self):
        """Export all data to a single Excel file"""
        filename, _ = QFileDialog.getSaveFileName(self, "Export to Excel", 
                                                   f"NetWorth_Report_{datetime.now().strftime('%Y%m%d')}.xlsx",
                                                   "Excel Files (*.xlsx)")
        if filename:
            with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                self.data_manager.read_excel("assets.xlsx").to_excel(writer, sheet_name="Assets", index=False)
                self.data_manager.read_excel("liabilities.xlsx").to_excel(writer, sheet_name="Liabilities", index=False)
                self.data_manager.read_excel("monthly_networth.xlsx").to_excel(writer, sheet_name="Monthly_Summary", index=False)
                self.data_manager.read_excel("goals.xlsx").to_excel(writer, sheet_name="Goals", index=False)
            
            QMessageBox.information(self, "Success", f"Report exported to {filename}")
            self.statusBar().showMessage("Export completed successfully", 3000)
    
    def export_to_pdf(self):
        """Export report to PDF"""
        QMessageBox.information(self, "Info", "PDF export feature coming soon!")
    
    def create_backup(self):
        """Create backup of all data"""
        backup_path = self.data_manager.create_backup()
        QMessageBox.information(self, "Backup Created", f"Backup saved to:\n{backup_path}")
        self.statusBar().showMessage("Backup created successfully", 3000)
    
    def create_settings_tab(self):
        """Create settings tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        title = QLabel("⚙️ Settings")
        title.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # Theme toggle
        # Settings Form
        settings_widget = QWidget()
        settings_widget.setObjectName("card")
        settings_layout = QVBoxLayout()
        
        # Theme toggle
        theme_layout = QHBoxLayout()
        theme_label = QLabel("Theme:")
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Dark", "Light"])
        
        config = self.data_manager.load_config()
        self.theme_combo.setCurrentText(config['theme'].capitalize())
        
        theme_layout.addWidget(theme_label)
        theme_layout.addWidget(self.theme_combo)
        theme_layout.addStretch()
        settings_layout.addLayout(theme_layout)
        
        # Currency selection
        currency_layout = QHBoxLayout()
        currency_label = QLabel("Currency:")
        self.currency_combo = QComboBox()
        self.currency_combo.addItems(["USD", "EUR", "GBP", "LKR", "INR"])
        self.currency_combo.setCurrentText(config['currency'])
        
        currency_layout.addWidget(currency_label)
        currency_layout.addWidget(self.currency_combo)
        currency_layout.addStretch()
        settings_layout.addLayout(currency_layout)
        
        # Save Settings Button
        save_settings_btn = QPushButton("💾 Save Settings")
        save_settings_btn.setObjectName("primary")
        save_settings_btn.clicked.connect(self.save_settings)
        settings_layout.addWidget(save_settings_btn)
        
        settings_widget.setLayout(settings_layout)
        layout.addWidget(settings_widget)
        
        # Password settings
        password_btn = QPushButton("🔒 Set/Change Password")
        password_btn.clicked.connect(self.set_password)
        layout.addWidget(password_btn)
        
        # Data directory
        data_dir_btn = QPushButton("📁 Open Data Directory")
        data_dir_btn.clicked.connect(lambda: os.startfile(self.data_manager.data_dir))
        layout.addWidget(data_dir_btn)
        
        # About
        about_label = QLabel("\n📊 Net Worth Tracker Pro v1.0\n\nA comprehensive personal finance management tool.\n\nFeatures:\n• Asset & Liability tracking\n• Monthly net worth snapshots\n• Goal tracking\n• Data visualization\n• Excel-based storage\n• Multi-user support")
        about_label.setWordWrap(True)
        layout.addWidget(about_label)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def change_theme(self, theme):
        """Change application theme"""
        config = self.data_manager.load_config()
        config['theme'] = theme.lower()
        self.data_manager.save_config(config)
        self.apply_theme()
        self.refresh_all_views()
        self.statusBar().showMessage(f"Theme changed to {theme}", 3000)

        # Refresh all tabs to apply new theme
        current_index = self.content_stack.currentIndex()
        self.content_stack.setCurrentIndex(0)
        self.content_stack.setCurrentIndex(current_index)

    def save_settings(self):
        """Save all settings at once"""
        theme = self.theme_combo.currentText()
        currency = self.currency_combo.currentText()
        
        config = self.data_manager.load_config()
        config['theme'] = theme.lower()
        config['currency'] = currency
        self.data_manager.save_config(config)
        
        # Apply theme
        self.apply_theme()
        
        # Force complete UI rebuild to apply currency changes
        self.content_stack.removeTab(0)  # Remove old dashboard
        self.content_stack.insertTab(0, self.create_dashboard(), "Dashboard")  # Create new dashboard
        self.content_stack.setCurrentIndex(0)  # Go to dashboard
        
        QApplication.processEvents()
        
        QMessageBox.information(self, "Settings Saved", 
                              f"✅ Settings saved successfully!\n\n"
                              f"Theme: {theme}\n"
                              f"Currency: {currency}\n\n"
                              f"Dashboard has been refreshed.")
        self.statusBar().showMessage(f"Settings saved: {theme} theme, {currency} currency", 5000)
        
    def change_currency(self, currency):
        """Change currency setting"""
        config = self.data_manager.load_config()
        config['currency'] = currency
        self.data_manager.save_config(config)
        self.statusBar().showMessage(f"Currency changed to {currency}", 3000)
    
    def set_password(self):
        """Set or change password"""
        password, ok = QInputDialog.getText(self, "Set Password",
                                           "Enter new password:",
                                           QLineEdit.EchoMode.Password)
        if ok and password:
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            config = self.data_manager.load_config()
            config['password_hash'] = password_hash
            self.data_manager.save_config(config)
            QMessageBox.information(self, "Success", "Password set successfully!")
            self.statusBar().showMessage("Password updated", 3000)
    
    def apply_theme(self):
        """Apply theme to application"""
        config = self.data_manager.load_config()
        theme = config.get('theme', 'dark')
        
        if theme == 'dark':
            self.setStyleSheet(self.theme_manager.get_dark_theme())
        else:
            self.setStyleSheet(self.theme_manager.get_light_theme())
    
    def generate_insights(self):
        """Generate smart insights based on data"""
        insights = []
        networth_data = self.data_manager.calculate_networth()
        
        # Calculate liability ratio
        if networth_data['total_assets'] > 0:
            liability_ratio = (networth_data['total_liabilities'] / networth_data['total_assets']) * 100
            
            if liability_ratio > 40:
                insights.append(f"⚠️ Warning: Liabilities are {liability_ratio:.1f}% of assets (recommend <40%)")
            else:
                insights.append(f"✅ Healthy debt ratio: {liability_ratio:.1f}% of assets")
        
        # Check monthly growth
        monthly_df = self.data_manager.read_excel("monthly_networth.xlsx")
        if len(monthly_df) >= 2:
            last_change = monthly_df.iloc[-1]['Change_Percent']
            if last_change > 0:
                insights.append(f"📈 Net worth increased by {last_change:.1f}% last month!")
            elif last_change < 0:
                insights.append(f"📉 Net worth decreased by {abs(last_change):.1f}% - review expenses")
        
        # Asset allocation suggestion
        assets_df = self.data_manager.read_excel("assets.xlsx")
        if not assets_df.empty:
            cash = assets_df[assets_df['Category'] == 'Cash & Bank']['Value'].sum()
            if networth_data['total_assets'] > 0:
                cash_ratio = (cash / networth_data['total_assets']) * 100
                if cash_ratio < 10:
                    insights.append(f"💡 Consider increasing cash reserves (currently {cash_ratio:.1f}%)")
        
        if not insights:
            insights.append("✅ All financial metrics look good!")
        
        return insights

def generate_insights(self):
        """Generate smart insights based on data"""
        insights = []
        networth_data = self.data_manager.calculate_networth()
        
        # Calculate liability ratio
        if networth_data['total_assets'] > 0:
            liability_ratio = (networth_data['total_liabilities'] / networth_data['total_assets']) * 100
            
            if liability_ratio > 40:
                insights.append(f"⚠️ Warning: Liabilities are {liability_ratio:.1f}% of assets (recommend <40%)")
            else:
                insights.append(f"✅ Healthy debt ratio: {liability_ratio:.1f}% of assets")
        
        # Check monthly growth
        monthly_df = self.data_manager.read_excel("monthly_networth.xlsx")
        if len(monthly_df) >= 2:
            last_change = monthly_df.iloc[-1]['Change_Percent']
            if last_change > 0:
                insights.append(f"📈 Net worth increased by {last_change:.1f}% last month!")
            elif last_change < 0:
                insights.append(f"📉 Net worth decreased by {abs(last_change):.1f}% - review expenses")
        
        # Asset allocation suggestion
        assets_df = self.data_manager.read_excel("assets.xlsx")
        if not assets_df.empty:
            cash = assets_df[assets_df['Category'] == 'Cash & Bank']['Value'].sum()
            if networth_data['total_assets'] > 0:
                cash_ratio = (cash / networth_data['total_assets']) * 100
                if cash_ratio < 10:
                    insights.append(f"💡 Consider increasing cash reserves (currently {cash_ratio:.1f}%)")
        
        if not insights:
            insights.append("✅ All financial metrics look good!")
        
        return insights
    
def auto_update_prices_on_startup(self):
        """Auto-update prices on application startup"""
        try:
            config = self.data_manager.load_config()
            api_key = config.get('gemini_api_key', '')
            
            if not api_key:
                return
            
            self.append_to_log("[SYSTEM] Auto-update enabled - fetching current prices...")
            updated, failed = self.data_manager.update_all_asset_prices(api_key, self.append_to_log)
            
            if updated > 0:
                self.refresh_assets_table()
                self.content_stack.setCurrentIndex(0)  # Refresh dashboard
                self.statusBar().showMessage(f"Auto-update complete: {updated} assets updated", 5000)
                
        except Exception as e:
            self.append_to_log(f"[ERROR] Auto-update failed: {str(e)}")

def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    app.setApplicationName("Net Worth Tracker Pro")
    
    # Create data manager
    data_manager = DataManager()
    
    # Show startup loading dialog
    loading_dialog = StartupLoadingDialog(data_manager)
    loading_dialog.start_loading_sequence()
    
    # Only proceed if loading completed successfully
    if loading_dialog.exec() == QDialog.DialogCode.Accepted:
        # Create and show main window
        window = MainWindow()
        window.show()
        sys.exit(app.exec())
    else:
        # Loading was cancelled or failed
        sys.exit(1)


if __name__ == "__main__":
    main()


if __name__ == "__main__":
    main()
