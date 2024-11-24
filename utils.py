import pandas as pd
import numpy as np
from typing import Tuple, Dict

def format_currency(value: float) -> str:
    """Format number as currency."""
    return f"${value:,.2f}"

def format_percentage(value: float) -> str:
    """Format number as percentage."""
    return f"{value:.1f}%"

def format_number(value: float) -> str:
    """Format number with thousand separators."""
    return f"{value:,.0f}"

def validate_excel_file(file) -> Tuple[bool, str]:
    """Validate uploaded Excel file has required sheets."""
    try:
        excel_file = pd.ExcelFile(file)
        required_sheets = {"Inventario", "Outlet"}
        file_sheets = set(excel_file.sheet_names)
        
        if not required_sheets.issubset(file_sheets):
            missing_sheets = required_sheets - file_sheets
            return False, f"Missing required sheets: {', '.join(missing_sheets)}"
        
        return True, "File is valid"
    except Exception as e:
        return False, f"Error validating file: {str(e)}"

def load_and_process_inventory(file) -> Tuple[pd.DataFrame, pd.DataFrame, Dict]:
    """Process inventory data and return calculated metrics."""
    try:
        # Load the Excel file
        inventory_data = pd.ExcelFile(file)
        
        # Load the sheets
        inventario_df = pd.read_excel(inventory_data, sheet_name='Inventario')
        outlet_df = pd.read_excel(inventory_data, sheet_name='Outlet')
        
        if inventario_df.empty or outlet_df.empty:
            raise ValueError("One or more sheets are empty")
    except Exception as e:
        raise ValueError(f"Error loading Excel file: {str(e)}")
    
    # Rename columns for standardization in inventario_df
    inventario_df.rename(columns={
        'Codigo': 'Item_Number',
        'Descripcion': 'Description',
        'Stock': 'Units_Sold',
        'Precio Sala': 'Floor_Price',
        'Outlet': 'Outlet_Price'
    }, inplace=True)
    
    # Rename columns for standardization in outlet_df
    outlet_df.rename(columns={
        'Número de artículo': 'Item_Number',
        'Descripción del artículo': 'Description',
        'Total anual': 'Total_Annual_Sales',
        'Stock al 1 de oct': 'Units_In_Stock'
    }, inplace=True)
    
    # Convert columns to numeric
    inventario_df['Outlet_Price'] = pd.to_numeric(inventario_df['Outlet_Price'], errors='coerce').fillna(0)
    inventario_df['Units_Sold'] = pd.to_numeric(inventario_df['Units_Sold'], errors='coerce').fillna(0)
    inventario_df['Floor_Price'] = pd.to_numeric(inventario_df['Floor_Price'], errors='coerce').fillna(0)
    outlet_df['Units_In_Stock'] = pd.to_numeric(outlet_df['Units_In_Stock'], errors='coerce').fillna(0)
    
    # Calculate metrics
    monthly_columns = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre']
    
    metrics = {}
    
    # Sales calculations
    inventario_df['Total_Sales_Outlet_Price'] = inventario_df['Outlet_Price'] * inventario_df['Units_Sold']
    inventario_df['Total_Sales_Floor_Price'] = inventario_df['Floor_Price'] * inventario_df['Units_Sold']
    
    # Average price and discount
    inventario_df['Average_Selling_Price'] = (inventario_df['Total_Sales_Outlet_Price'] / 
                                            inventario_df['Units_Sold']).replace([np.inf, -np.inf], 0)
    
    inventario_df['Discount_Percentage'] = ((inventario_df['Floor_Price'] - inventario_df['Outlet_Price']) / 
                                          inventario_df['Floor_Price'] * 100).replace([np.inf, -np.inf], 0)
    
    # Units and inventory calculations
    outlet_df['Total_Units_Sold'] = outlet_df[monthly_columns].sum(axis=1)
    outlet_df['Beginning_Inventory'] = outlet_df[monthly_columns].sum(axis=1) + outlet_df['Units_In_Stock']
    
    # Calculate new metrics
    # Inventory Turnover
    cost_of_goods_sold = (inventario_df['Units_Sold'] * inventario_df['Outlet_Price']).sum()
    average_inventory = outlet_df['Units_In_Stock'].mean()
    inventory_turnover = (cost_of_goods_sold / average_inventory) if average_inventory != 0 else 0

    # Sell-Through Rate
    total_units_sold = outlet_df['Total_Units_Sold'].sum()
    total_units_in_stock = outlet_df['Units_In_Stock'].sum()
    sell_through_rate = (total_units_sold / (total_units_sold + total_units_in_stock) * 100) if (total_units_sold + total_units_in_stock) != 0 else 0

    # Stock to Sales Ratio
    inventory_value = (outlet_df['Units_In_Stock'] * inventario_df['Outlet_Price']).sum()
    total_sales = inventario_df['Total_Sales_Outlet_Price'].sum()
    stock_to_sales_ratio = (inventory_value / total_sales) if total_sales != 0 else 0

    # Inventory Coverage (in days)
    monthly_sales_rate = inventario_df['Units_Sold'].sum() / 30  # Daily sales rate
    inventory_coverage = (outlet_df['Units_In_Stock'].sum() / monthly_sales_rate) if monthly_sales_rate != 0 else 0

    # Compile metrics
    metrics['total_sales_outlet'] = inventario_df['Total_Sales_Outlet_Price'].sum()
    metrics['total_sales_floor'] = inventario_df['Total_Sales_Floor_Price'].sum()
    metrics['total_units_sold'] = outlet_df['Total_Units_Sold'].sum()
    metrics['avg_selling_price'] = inventario_df['Average_Selling_Price'].mean()
    metrics['avg_discount'] = inventario_df['Discount_Percentage'].mean()
    
    # Add new metrics
    metrics['inventory_turnover'] = inventory_turnover
    metrics['sell_through_rate'] = sell_through_rate
    metrics['stock_to_sales_ratio'] = stock_to_sales_ratio
    metrics['inventory_coverage'] = inventory_coverage
    
    # Best/Worst sellers
    best_selling = inventario_df.loc[inventario_df['Units_Sold'].idxmax()]
    least_selling = inventario_df.loc[inventario_df['Units_Sold'].idxmin()]
    
    metrics['best_seller'] = {
        'description': best_selling['Description'],
        'units': best_selling['Units_Sold']
    }
    
    metrics['worst_seller'] = {
        'description': least_selling['Description'],
        'units': least_selling['Units_Sold']
    }
    
    # Unsold items
    metrics['unsold_items'] = inventario_df[inventario_df['Units_Sold'] == 0]['Description'].tolist()
    
    return inventario_df, outlet_df, metrics
