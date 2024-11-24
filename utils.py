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
    # Load the Excel file
    inventory_data = pd.ExcelFile(file)
    
    # Load the sheets
    inventario_df = inventory_data.parse('Inventario')
    outlet_df = inventory_data.parse('Outlet')
    
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
    
    # Compile metrics
    metrics['total_sales_outlet'] = inventario_df['Total_Sales_Outlet_Price'].sum()
    metrics['total_sales_floor'] = inventario_df['Total_Sales_Floor_Price'].sum()
    metrics['total_units_sold'] = outlet_df['Total_Units_Sold'].sum()
    metrics['avg_selling_price'] = inventario_df['Average_Selling_Price'].mean()
    metrics['avg_discount'] = inventario_df['Discount_Percentage'].mean()
    
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
