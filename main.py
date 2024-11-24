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
uploaded_file = st.file_uploader(
    "Drag and drop your Excel file here",
    type=['xlsx'],
    help="File must contain 'Inventario' and 'Outlet' sheets"
)

if uploaded_file is not None:
    # Validate file
    is_valid, message = validate_excel_file(uploaded_file)
    
    if not is_valid:
        st.error(message)
    else:
        # Process file
        with st.spinner("Processing inventory data..."):
            inventario_df, outlet_df, metrics = load_and_process_inventory(uploaded_file)
        
        st.success("✅ File processed successfully!")
        
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
        
        try:
            # Monthly Sales Trend
            monthly_columns = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre']
            monthly_sales = outlet_df[monthly_columns].sum()
            
            # Debug print for monthly sales data
            print("Monthly Sales Data:")
            print(monthly_sales)
            
            monthly_sales_df = pd.DataFrame({
                'Month': monthly_sales.index,
                'Units Sold': monthly_sales.values
            })
            
            # Debug print for monthly sales DataFrame
            print("\nMonthly Sales DataFrame:")
            print(monthly_sales_df)
            
            fig_sales = px.line(
                monthly_sales_df,
                x='Month',
                y='Units Sold',
                title='Monthly Sales Trend',
                markers=True
            )
            st.plotly_chart(fig_sales, use_container_width=True)
        except Exception as e:
            st.error(f"Error creating monthly sales trend chart: {str(e)}")
            print(f"Monthly sales visualization error: {str(e)}")

        # Price Distribution
        col1, col2 = st.columns(2)
        
        try:
            with col1:
                # Debug print for floor price data
                print("\nFloor Price Distribution Data:")
                print(inventario_df['Floor_Price'].describe())
                
                fig_floor = px.histogram(
                    inventario_df,
                    x='Floor_Price',
                    title='Floor Price Distribution',
                    labels={'Floor_Price': 'Price'},
                )
                st.plotly_chart(fig_floor, use_container_width=True)
        except Exception as e:
            st.error(f"Error creating floor price distribution chart: {str(e)}")
            print(f"Floor price visualization error: {str(e)}")
        
        try:
            with col2:
                # Debug print for outlet price data
                print("\nOutlet Price Distribution Data:")
                print(inventario_df['Outlet_Price'].describe())
                
                fig_outlet = px.histogram(
                    inventario_df,
                    x='Outlet_Price',
                    title='Outlet Price Distribution',
                    labels={'Outlet_Price': 'Price'},
                )
                st.plotly_chart(fig_outlet, use_container_width=True)
        except Exception as e:
            st.error(f"Error creating outlet price distribution chart: {str(e)}")
            print(f"Outlet price visualization error: {str(e)}")

        try:
            # Top 10 Products by Units Sold
            top_10_products = inventario_df.nlargest(10, 'Units_Sold')
            
            # Debug print for top 10 products data
            print("\nTop 10 Products Data:")
            print(top_10_products[['Description', 'Units_Sold']])
            
            fig_top10 = px.bar(
                top_10_products,
                x='Description',
                y='Units_Sold',
                title='Top 10 Products by Units Sold',
                labels={'Description': 'Product', 'Units_Sold': 'Units Sold'}
            )
            fig_top10.update_layout(
                xaxis_tickangle=45,
                height=500
            )
            st.plotly_chart(fig_top10, use_container_width=True)
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
