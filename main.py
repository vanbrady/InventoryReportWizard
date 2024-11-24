import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils import (
    validate_excel_file, 
    load_and_process_inventory,
    format_currency,
    format_percentage,
    format_number
)
import io

# Page configuration
st.set_page_config(
    page_title="Inventory Analysis Dashboard",
    page_icon="📊",
    layout="wide"
)

# Load custom CSS
with open('style.css') as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# Title and description
st.title("📊 Inventory Analysis Dashboard")
st.markdown("""
This dashboard analyzes inventory data from Excel files containing 'Inventario' and 'Outlet' sheets.
Upload your file below to get started.
""")

# File upload section
st.markdown("### 📁 Upload Inventory File")
uploaded_files = st.file_uploader(
    "Drag and drop your Excel files here",
    type=['xlsx'],
    help="Files must contain 'Inventario' and 'Outlet' sheets",
    accept_multiple_files=True
)

if uploaded_files:
    # Dictionary to store processed data for each file
    processed_data = {}
    
    for uploaded_file in uploaded_files:
        # Validate file
        is_valid, message = validate_excel_file(uploaded_file)
        
        if not is_valid:
            st.error(f"{uploaded_file.name}: {message}")
            continue
        
        # Process file
        with st.spinner(f"Processing {uploaded_file.name}..."):
            try:
                inventario_df, outlet_df, metrics = load_and_process_inventory(uploaded_file)
                processed_data[uploaded_file.name] = {
                    'inventario_df': inventario_df,
                    'outlet_df': outlet_df,
                    'metrics': metrics
                }
            except Exception as e:
                st.error(f"Error processing {uploaded_file.name}: {str(e)}")
                continue
    
    if len(processed_data) > 0:
        st.success(f"✅ Processed {len(processed_data)} file(s) successfully!")
        
        # File selection for comparison
        if len(processed_data) > 1:
            st.markdown("### 📊 Compare Files")
            selected_files = st.multiselect(
                "Select files to compare",
                options=list(processed_data.keys()),
                default=list(processed_data.keys())[:2]
            )
            
            if len(selected_files) > 1:
                # Create comparison metrics
                comparison_data = []
                for file_name in selected_files:
                    metrics = processed_data[file_name]['metrics']
                    comparison_data.append({
                        'File': file_name,
                        'Total Sales (Outlet)': metrics['total_sales_outlet'],
                        'Total Sales (Floor)': metrics['total_sales_floor'],
                        'Total Units Sold': metrics['total_units_sold'],
                        'Avg Selling Price': metrics['avg_selling_price'],
                        'Avg Discount': metrics['avg_discount']
                    })
                
                comparison_df = pd.DataFrame(comparison_data)
                
                # Display comparison metrics
                st.markdown("#### 📈 Metrics Comparison")
                st.dataframe(comparison_df.style.format({
                    'Total Sales (Outlet)': '${:,.2f}',
                    'Total Sales (Floor)': '${:,.2f}',
                    'Total Units Sold': '{:,.0f}',
                    'Avg Selling Price': '${:,.2f}',
                    'Avg Discount': '{:.1f}%'
                }))
                
                # Comparison visualizations
                st.markdown("#### 📊 Visual Comparisons")
                
                # Sales comparison bar chart
                fig_sales_comp = go.Figure()
                for file_name in selected_files:
                    metrics = processed_data[file_name]['metrics']
                    fig_sales_comp.add_trace(go.Bar(
                        name=file_name,
                        x=['Outlet Sales', 'Floor Sales'],
                        y=[metrics['total_sales_outlet'], metrics['total_sales_floor']]
                    ))
                
                fig_sales_comp.update_layout(
                    title='Sales Comparison',
                    barmode='group',
                    xaxis_title="Sales Type",
                    yaxis_title="Amount ($)"
                )
                st.plotly_chart(fig_sales_comp, use_container_width=True)
                
                # Units sold comparison
                fig_units = go.Figure()
                for file_name in selected_files:
                    metrics = processed_data[file_name]['metrics']
                    fig_units.add_trace(go.Bar(
                        name=file_name,
                        x=['Units Sold'],
                        y=[metrics['total_units_sold']]
                    ))
                
                fig_units.update_layout(
                    title='Units Sold Comparison',
                    barmode='group',
                    xaxis_title="Metric",
                    yaxis_title="Units"
                )
                st.plotly_chart(fig_units, use_container_width=True)
        
        # Display individual file analysis
        st.markdown("### 📊 Individual File Analysis")
        for file_name, data in processed_data.items():
            with st.expander(f"Analysis for {file_name}"):
        
        # Display metrics in columns
                col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("### 💰 Sales Metrics")
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-label">Total Sales (Outlet Price)</div>
                    <div class="metric-value">{format_currency(metrics['total_sales_outlet'])}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Total Sales (Floor Price)</div>
                    <div class="metric-value">{format_currency(metrics['total_sales_floor'])}</div>
                </div>
                """,
                unsafe_allow_html=True
            )
        
        with col2:
            st.markdown("### 📈 Price Metrics")
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-label">Average Selling Price</div>
                    <div class="metric-value">{format_currency(metrics['avg_selling_price'])}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Average Discount</div>
                    <div class="metric-value">{format_percentage(metrics['avg_discount'])}</div>
                </div>
                """,
                unsafe_allow_html=True
            )
        
        with col3:
            st.markdown("### 📦 Inventory Metrics")
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-label">Total Units Sold</div>
                    <div class="metric-value">{format_number(metrics['total_units_sold'])}</div>
                </div>
                """,
                unsafe_allow_html=True
            )
        
        # Product Performance
        st.markdown("### 🏆 Product Performance")
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Best Selling Product")
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-label">Product</div>
                    <div class="metric-value">{metrics['best_seller']['description']}</div>
                    <div class="metric-label">Units Sold: {format_number(metrics['best_seller']['units'])}</div>
                </div>
                """,
                unsafe_allow_html=True
            )
        
        with col2:
            st.markdown("#### Least Selling Product")
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-label">Product</div>
                    <div class="metric-value">{metrics['worst_seller']['description']}</div>
                    <div class="metric-label">Units Sold: {format_number(metrics['worst_seller']['units'])}</div>
                </div>
                """,
                unsafe_allow_html=True
            )
        
        # Unsold Items
        with st.expander("View Unsold Items"):
            if metrics['unsold_items']:
                st.dataframe({'Product Description': metrics['unsold_items']})
            else:
                st.info("No unsold items found.")
        
        # Data Visualizations
        st.markdown("### 📊 Data Visualizations")

        def validate_dataframe(df, required_columns):
            """Validate DataFrame has required columns and non-empty."""
            if df is None or df.empty:
                return False, "DataFrame is empty"
            missing_cols = [col for col in required_columns if col not in df.columns]
            if missing_cols:
                return False, f"Missing required columns: {', '.join(missing_cols)}"
            return True, "DataFrame is valid"

        # Monthly Sales Trend
        try:
            monthly_columns = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre']
            
            # Validate outlet_df
            is_valid, message = validate_dataframe(outlet_df, monthly_columns)
            if not is_valid:
                st.error(f"Monthly Sales Trend: {message}")
                print(f"Monthly Sales validation error: {message}")
            else:
                # Process monthly sales data
                print("\nProcessing monthly sales data...")
                print(f"Data types of columns:\n{outlet_df[monthly_columns].dtypes}")
                print(f"Data shape: {outlet_df[monthly_columns].shape}")
                
                # Convert numeric columns and handle any non-numeric values
                numeric_df = outlet_df[monthly_columns].apply(pd.to_numeric, errors='coerce')
                nan_check = numeric_df.isna()
                if nan_check.values.any():
                    print("Warning: Found non-numeric values in monthly data")
                    print(f"NaN counts:\n{numeric_df.isna().sum()}")
                
                monthly_sales = numeric_df.sum()
                print(f"Monthly sales totals:\n{monthly_sales}")
                
                monthly_sales_df = pd.DataFrame({
                    'Month': monthly_sales.index,
                    'Units Sold': monthly_sales.values
                })
                print(f"\nMonthly sales DataFrame:\n{monthly_sales_df}")
                print(f"Monthly sales data types:\n{monthly_sales_df.dtypes}")
                
                if not monthly_sales_df.empty:
                    fig_sales = px.line(
                        monthly_sales_df,
                        x='Month',
                        y='Units Sold',
                        title='Monthly Sales Trend',
                        markers=True
                    )
                    fig_sales.update_layout(
                        xaxis_title="Month",
                        yaxis_title="Units Sold",
                        showlegend=True
                    )
                    st.plotly_chart(fig_sales, use_container_width=True)
                else:
                    st.warning("No monthly sales data available to display")
        except Exception as e:
            st.error(f"Error creating monthly sales trend chart: {str(e)}")
            print(f"Monthly sales visualization error: {str(e)}")

        # Price Distribution
        col1, col2 = st.columns(2)
        
        # Validate inventario_df
        price_columns = ['Floor_Price', 'Outlet_Price']
        is_valid, message = validate_dataframe(inventario_df, price_columns)
        
        if not is_valid:
            st.error(f"Price Distribution: {message}")
            print(f"Price distribution validation error: {message}")
        else:
            try:
                with col1:
                    print("\nProcessing floor price distribution...")
                    print(f"Floor Price data type: {inventario_df['Floor_Price'].dtype}")
                    print(f"Floor Price range: [{inventario_df['Floor_Price'].min()}, {inventario_df['Floor_Price'].max()}]")
                    floor_price_stats = inventario_df['Floor_Price'].describe()
                    print(f"Floor price statistics:\n{floor_price_stats}")
                    print(f"Number of unique prices: {inventario_df['Floor_Price'].nunique()}")
                    nan_check = inventario_df['Floor_Price'].isna()
                    if nan_check.values.any():
                        print(f"Number of missing values: {inventario_df['Floor_Price'].isna().sum()}")
                    
                    fig_floor = px.histogram(
                        inventario_df,
                        x='Floor_Price',
                        title='Floor Price Distribution',
                        labels={'Floor_Price': 'Price'},
                        nbins=30
                    )
                    fig_floor.update_layout(
                        xaxis_title="Floor Price",
                        yaxis_title="Count",
                        showlegend=False
                    )
                    st.plotly_chart(fig_floor, use_container_width=True)
            except Exception as e:
                st.error(f"Error creating floor price distribution chart: {str(e)}")
                print(f"Floor price visualization error: {str(e)}")
            
            try:
                with col2:
                    print("\nProcessing outlet price distribution...")
                    print(f"Outlet Price data type: {inventario_df['Outlet_Price'].dtype}")
                    print(f"Outlet Price range: [{inventario_df['Outlet_Price'].min()}, {inventario_df['Outlet_Price'].max()}]")
                    outlet_price_stats = inventario_df['Outlet_Price'].describe()
                    print(f"Outlet price statistics:\n{outlet_price_stats}")
                    print(f"Number of unique prices: {inventario_df['Outlet_Price'].nunique()}")
                    nan_check = inventario_df['Outlet_Price'].isna()
                    if nan_check.values.any():
                        print(f"Number of missing values: {inventario_df['Outlet_Price'].isna().sum()}")
                    
                    fig_outlet = px.histogram(
                        inventario_df,
                        x='Outlet_Price',
                        title='Outlet Price Distribution',
                        labels={'Outlet_Price': 'Price'},
                        nbins=30
                    )
                    fig_outlet.update_layout(
                        xaxis_title="Outlet Price",
                        yaxis_title="Count",
                        showlegend=False
                    )
                    st.plotly_chart(fig_outlet, use_container_width=True)
            except Exception as e:
                st.error(f"Error creating outlet price distribution chart: {str(e)}")
                print(f"Outlet price visualization error: {str(e)}")

        # Top 10 Products
        try:
            print("\nProcessing top 10 products data...")
            print(f"DataFrame columns: {inventario_df.columns.tolist()}")
            print(f"DataFrame shape: {inventario_df.shape}")
            
            if 'Units_Sold' not in inventario_df.columns or 'Description' not in inventario_df.columns:
                st.error("Missing required columns for top 10 products visualization")
                print("Top 10 products validation error: Missing required columns")
                print(f"Available columns: {inventario_df.columns.tolist()}")
            else:
                print(f"Units Sold data type: {inventario_df['Units_Sold'].dtype}")
                print(f"Description data type: {inventario_df['Description'].dtype}")
                print(f"Total number of products: {len(inventario_df)}")
                print(f"Number of products with sales > 0: {(inventario_df['Units_Sold'] > 0).sum()}")
                
                top_10_products = inventario_df.nlargest(10, 'Units_Sold')
                print(f"Top 10 products data:\n{top_10_products[['Description', 'Units_Sold']]}")
                
                if not top_10_products.empty:
                    fig_top10 = px.bar(
                        top_10_products,
                        x='Description',
                        y='Units_Sold',
                        title='Top 10 Products by Units Sold',
                        labels={'Description': 'Product', 'Units_Sold': 'Units Sold'}
                    )
                    fig_top10.update_layout(
                        xaxis_tickangle=45,
                        height=500,
                        xaxis_title="Product",
                        yaxis_title="Units Sold",
                        showlegend=False
                    )
                    st.plotly_chart(fig_top10, use_container_width=True)
                else:
                    st.warning("No product sales data available to display")
        except Exception as e:
            st.error(f"Error creating top 10 products chart: {str(e)}")
            print(f"Top 10 products visualization error: {str(e)}")

        # Data Tables
        st.markdown("### 📑 Detailed Data")
        tab1, tab2 = st.tabs(["Inventory Data", "Outlet Data"])
        
        with tab1:
            st.dataframe(inventario_df)
        
        with tab2:
            st.dataframe(outlet_df)
        
        # Export options
        st.markdown("### 💾 Export Data")
        col1, col2 = st.columns(2)
        
        with col1:
            inventory_csv = inventario_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                "Download Inventory Data (CSV)",
                inventory_csv,
                "inventory_data.csv",
                "text/csv",
                key='download-inventory-csv'
            )
        
        with col2:
            outlet_csv = outlet_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                "Download Outlet Data (CSV)",
                outlet_csv,
                "outlet_data.csv",
                "text/csv",
                key='download-outlet-csv'
            )

else:
    st.info("👆 Upload an Excel file to begin the analysis")
