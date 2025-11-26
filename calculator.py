"""
Financial Calculations Engine for Net Worth Tracker Pro
Pure calculation functions - no UI dependencies
"""

import pandas as pd
from datetime import datetime
from typing import Dict, List, Tuple


class FinancialCalculator:
    """Core financial calculations"""
    
    @staticmethod
    def calculate_portfolio_value(assets_df: pd.DataFrame) -> Dict[str, float]:
        """
        Calculate total portfolio value using Quantity × Price_Per_Unit
        
        Args:
            assets_df: DataFrame with columns [Quantity, Price_Per_Unit, Category]
        
        Returns:
            {
                'total_crypto': float,
                'total_metals': float,
                'total_cash': float,
                'total_assets': float,
                'by_category': dict
            }
        """
        if assets_df.empty:
            return {
                'total_crypto': 0.0,
                'total_metals': 0.0,
                'total_cash': 0.0,
                'total_assets': 0.0,
                'by_category': {}
            }
        
        # Ensure required columns exist
        if 'Quantity' not in assets_df.columns:
            assets_df['Quantity'] = 1.0
        if 'Price_Per_Unit' not in assets_df.columns:
            assets_df['Price_Per_Unit'] = assets_df.get('Value', 0.0)
        
        # Calculate value for each asset
        assets_df['Calculated_Value'] = assets_df['Quantity'] * assets_df['Price_Per_Unit']
        
        # Sum by category
        by_category = assets_df.groupby('Category')['Calculated_Value'].sum().to_dict()
        
        total_crypto = by_category.get('Crypto', 0.0)
        total_metals = by_category.get('Gold/Silver', 0.0)
        total_cash = by_category.get('Cash & Bank', 0.0)
        total_assets = assets_df['Calculated_Value'].sum()
        
        return {
            'total_crypto': float(total_crypto),
            'total_metals': float(total_metals),
            'total_cash': float(total_cash),
            'total_assets': float(total_assets),
            'by_category': {k: float(v) for k, v in by_category.items()}
        }
    
    @staticmethod
    def calculate_net_worth(assets_df: pd.DataFrame, liabilities_df: pd.DataFrame) -> Dict[str, float]:
        """
        Calculate net worth: Assets - Liabilities
        
        Returns:
            {
                'total_assets': float,
                'total_liabilities': float,
                'net_worth': float
            }
        """
        portfolio = FinancialCalculator.calculate_portfolio_value(assets_df)
        total_assets = portfolio['total_assets']
        
        total_liabilities = 0.0
        if not liabilities_df.empty and 'Amount' in liabilities_df.columns:
            total_liabilities = float(liabilities_df['Amount'].sum())
        
        return {
            'total_assets': total_assets,
            'total_liabilities': total_liabilities,
            'net_worth': total_assets - total_liabilities
        }
    
    @staticmethod
    def calculate_asset_allocation(assets_df: pd.DataFrame) -> Dict[str, float]:
        """
        Calculate percentage allocation by category
        
        Returns:
            {'Crypto': 85.5, 'Gold/Silver': 10.2, 'Cash & Bank': 4.3}
        """
        portfolio = FinancialCalculator.calculate_portfolio_value(assets_df)
        total = portfolio['total_assets']
        
        if total == 0:
            return {}
        
        allocation = {}
        for category, value in portfolio['by_category'].items():
            allocation[category] = (value / total) * 100
        
        return allocation
    
    @staticmethod
    def generate_insights(networth_data: dict, assets_df: pd.DataFrame, 
                         liabilities_df: pd.DataFrame, monthly_df: pd.DataFrame) -> List[str]:
        """Generate smart financial insights"""
        insights = []
        
        # Liability ratio check
        if networth_data['total_assets'] > 0:
            liability_ratio = (networth_data['total_liabilities'] / networth_data['total_assets']) * 100
            
            if liability_ratio > 40:
                insights.append(f"⚠️ Warning: Liabilities are {liability_ratio:.1f}% of assets (recommend <40%)")
            else:
                insights.append(f"✅ Healthy debt ratio: {liability_ratio:.1f}% of assets")
        
        # Monthly growth check
        if not monthly_df.empty and len(monthly_df) >= 2:
            last_change = monthly_df.iloc[-1]['Change_Percent']
            if last_change > 0:
                insights.append(f"📈 Net worth increased by {last_change:.1f}% last month!")
            elif last_change < 0:
                insights.append(f"📉 Net worth decreased by {abs(last_change):.1f}% - review expenses")
        
        # Cash reserves check
        portfolio = FinancialCalculator.calculate_portfolio_value(assets_df)
        if portfolio['total_assets'] > 0:
            cash_ratio = (portfolio['total_cash'] / portfolio['total_assets']) * 100
            if cash_ratio < 10:
                insights.append(f"💡 Consider increasing cash reserves (currently {cash_ratio:.1f}%)")
            else:
                insights.append(f"✅ Good cash reserves: {cash_ratio:.1f}% of portfolio")
        
        if not insights:
            insights.append("✅ All financial metrics look good!")
        
        return insights


class CurrencyConverter:
    """Currency conversion utilities"""
    
    EXCHANGE_RATES = {
        'USD': 1.0,
        'EUR': 0.92,
        'GBP': 0.79,
        'LKR': 305.0,      # Sri Lankan Rupee
        'INR': 83.0,       # Indian Rupee
        'JPY': 149.0,      # Japanese Yen
        'AUD': 1.52,       # Australian Dollar
        'CAD': 1.36,       # Canadian Dollar
    }
    
    SYMBOLS = {
        'USD': '$',
        'EUR': '€',
        'GBP': '£',
        'LKR': 'Rs. ',
        'INR': '₹',
        'JPY': '¥',
        'AUD': 'A$',
        'CAD': 'C$',
    }
    
    @classmethod
    def convert(cls, amount_usd: float, to_currency: str) -> float:
        """Convert USD amount to target currency"""
        rate = cls.EXCHANGE_RATES.get(to_currency, 1.0)
        return amount_usd * rate
    
    @classmethod
    def convert_to_usd(cls, amount: float, from_currency: str) -> float:
        """Convert amount from any currency to USD"""
        rate = cls.EXCHANGE_RATES.get(from_currency, 1.0)
        return amount / rate
    
    @classmethod
    def get_symbol(cls, currency: str) -> str:
        """Get currency symbol"""
        return cls.SYMBOLS.get(currency, '$')