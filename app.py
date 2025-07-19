import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import os
from datetime import datetime
import time

# Import our custom modules
import sys
sys.path.append('./utils')
sys.path.append('./models')

from data_processor import LeadProcessor
from lead_scorer import LeadScorer
from hubspot_formatter import HubSpotFormatter

# Try to import HubSpot API - IMPROVED ERROR HANDLING
HUBSPOT_SDK_INSTALLED = False
HUBSPOT_IMPORT_ERROR = None
try:
    import hubspot
    HUBSPOT_SDK_INSTALLED = True
    print("✅ HubSpot SDK imported successfully")
except ImportError as e:
    HUBSPOT_IMPORT_ERROR = str(e)
    print(f"❌ HubSpot SDK import failed: {e}")

# Try to import custom HubSpot API wrapper
HUBSPOT_API_AVAILABLE = False
HUBSPOT_API_ERROR = None
try:
    from utils.hubspot_api import create_hubspot_client, HUBSPOT_AVAILABLE
    HUBSPOT_API_AVAILABLE = True
    print("✅ Custom HubSpot API wrapper imported successfully")
except ImportError as e:
    HUBSPOT_API_ERROR = str(e)
    print(f"❌ Custom HubSpot API wrapper import failed: {e}")

# Page config
st.set_page_config(
    page_title="Lead Quality Engine",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .stButton > button {
        width: 100%;
    }
    .success-box {
        padding: 1rem;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 0.25rem;
        color: #155724;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state - ADD API KEY STORAGE
if 'processed_data' not in st.session_state:
    st.session_state.processed_data = None
if 'hubspot_data' not in st.session_state:
    st.session_state.hubspot_data = None
if 'hubspot_api_key' not in st.session_state:
    st.session_state.hubspot_api_key = ""
if 'connection_tested' not in st.session_state:
    st.session_state.connection_tested = False

@st.cache_data
def load_and_process_data(uploaded_file=None):
    """Load and process lead data"""
    
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
    else:
        # Use sample data
        df = pd.read_csv('data/sample_leads.csv')
    
    # Process the data
    processor = LeadProcessor()
    processed_df = processor.process_leads(df)
    
    # Train model and score leads
    scorer = LeadScorer()
    training_results = scorer.train(processed_df)
    scores = scorer.predict_scores(processed_df)
    
    processed_df['lead_score'] = scores
    processed_df['category'] = scorer.categorize_leads(scores)
    
    return processed_df, scorer, training_results

def simulate_hubspot_upload(data, delay=True):
    """Simulate HubSpot API upload with progress"""
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    steps = [
        ("Authenticating with HubSpot...", 20),
        ("Validating contact data...", 40),
        ("Creating/updating contacts...", 70),
        ("Setting up workflows...", 90),
        ("Finalizing import...", 100)
    ]
    
    for step, progress in steps:
        status_text.text(step)
        progress_bar.progress(progress)
        if delay:
            time.sleep(0.5)
    
    status_text.text("✅ Import completed successfully!")
    return True

def main():
    st.title("🎯 Lead Quality Engine")
    st.markdown("### AI-Powered Lead Scoring + HubSpot Integration")
    st.markdown("*Built for Caprae Capital - Enhanced SaaSSquatch Lead Analysis*")
    
    # Sidebar
    st.sidebar.header("📤 Upload Your Data")
    st.sidebar.markdown("Upload a CSV file from SaaSSquatch or use our sample data")
    
    uploaded_file = st.sidebar.file_uploader(
        "Choose CSV file",
        type="csv",
        help="Upload your lead data in SaaSSquatch format"
    )
    
    # Demo mode toggle
    demo_mode = st.sidebar.checkbox(
        "🎭 Demo Mode", 
        value=True,
        help="Enable for demo without real HubSpot API calls"
    )
    
    # IMPROVED API KEY SECTION
    api_key = None
    if not demo_mode:
        st.sidebar.subheader("🔗 HubSpot Integration")
        
        # Show SDK status with debugging
        if HUBSPOT_SDK_INSTALLED:
            st.sidebar.success("✅ HubSpot SDK installed")
        else:
            st.sidebar.error("❌ HubSpot SDK not installed")
            if HUBSPOT_IMPORT_ERROR:
                st.sidebar.code(f"Error: {HUBSPOT_IMPORT_ERROR}")
            st.sidebar.info("Run: `pip install hubspot-api-client`")
        
        # Show API wrapper status
        if HUBSPOT_API_AVAILABLE:
            st.sidebar.success("✅ HubSpot API wrapper available")
        else:
            st.sidebar.warning("⚠️ HubSpot API wrapper not available")
            if HUBSPOT_API_ERROR:
                st.sidebar.code(f"Error: {HUBSPOT_API_ERROR}")
        
        # API Key input with session state
        api_key_input = st.sidebar.text_input(
            "HubSpot API Key",
            value=st.session_state.hubspot_api_key,
            type="password",
            help="Enter your HubSpot private app access token",
            placeholder="pat-na1-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
            key="api_key_input"
        )
        
        # Store in session state
        if api_key_input:
            st.session_state.hubspot_api_key = api_key_input
            api_key = api_key_input
        
        # Validate API key format
        if api_key and not api_key.startswith('pat-'):
            st.sidebar.error("❌ API key should start with 'pat-'")
            api_key = None
        
        # Test connection button
        if api_key and HUBSPOT_SDK_INSTALLED and HUBSPOT_API_AVAILABLE:
            if st.sidebar.button("🧪 Test Connection"):
                with st.spinner("Testing connection..."):
                    try:
                        hubspot_client = create_hubspot_client(api_key)
                        if hubspot_client:
                            account_info = hubspot_client.get_account_info()
                            if 'error' not in account_info:
                                st.sidebar.success("✅ Connection successful!")
                                st.session_state.connection_tested = True
                            else:
                                st.sidebar.error(f"❌ Connection failed: {account_info.get('error', 'Unknown error')}")
                        else:
                            st.sidebar.error("❌ Failed to create HubSpot client")
                    except Exception as e:
                        st.sidebar.error(f"❌ Connection failed: {str(e)}")
    
    # Process data
    with st.spinner("🤖 Processing leads with AI..."):
        processed_df, scorer, training_results = load_and_process_data(uploaded_file)
        st.session_state.processed_data = processed_df
    
    # Main dashboard
    st.header("📊 Lead Analysis Dashboard")
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total Leads", 
            len(processed_df),
            help="Total number of leads processed"
        )
    
    with col2:
        hot_leads = len(processed_df[processed_df['lead_score'] >= 0.8])
        st.metric(
            "🔥 Hot Leads", 
            hot_leads,
            delta=f"{hot_leads/len(processed_df):.1%} of total"
        )
    
    with col3:
        avg_score = processed_df['lead_score'].mean()
        st.metric(
            "Average Score", 
            f"{avg_score:.2f}",
            delta=f"Range: {processed_df['lead_score'].min():.2f}-{processed_df['lead_score'].max():.2f}"
        )
    
    with col4:
        complete_contacts = len(processed_df[processed_df['data_completeness'] >= 0.75])
        st.metric(
            "Complete Profiles", 
            complete_contacts,
            delta=f"{complete_contacts/len(processed_df):.1%} complete"
        )
    
    # Model performance info
    with st.expander("🤖 Model Performance"):
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Training Accuracy", f"{training_results['train_accuracy']:.1%}")
            st.metric("Test Accuracy", f"{training_results['test_accuracy']:.1%}")
        with col2:
            st.metric("Good Leads Identified", f"{training_results['positive_leads']}")
            st.metric("Total Training Samples", f"{training_results['total_samples']}")
    
    # Visualizations
    st.header("📈 Lead Quality Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Score distribution
        fig_hist = px.histogram(
            processed_df, 
            x='lead_score',
            nbins=20,
            title="Lead Score Distribution",
            color_discrete_sequence=['#1f77b4']
        )
        fig_hist.update_layout(
            xaxis_title="Lead Score",
            yaxis_title="Number of Leads"
        )
        st.plotly_chart(fig_hist, use_container_width=True)
    
    with col2:
        # Category breakdown
        category_counts = processed_df['category'].value_counts()
        fig_pie = px.pie(
            values=category_counts.values,
            names=category_counts.index,
            title="Lead Categories",
            color_discrete_sequence=['#ff4444', '#ffaa44', '#44aaff', '#44ff44']
        )
        st.plotly_chart(fig_pie, use_container_width=True)
    
    # Feature importance
    col1, col2 = st.columns(2)
    
    with col1:
        importance = scorer.get_feature_importance()
        fig_bar = px.bar(
            x=list(importance.values()),
            y=list(importance.keys()),
            orientation='h',
            title="Feature Importance",
            color=list(importance.values()),
            color_continuous_scale='viridis'
        )
        fig_bar.update_layout(
            xaxis_title="Importance Score",
            yaxis_title="Features"
        )
        st.plotly_chart(fig_bar, use_container_width=True)
    
    with col2:
        # Industry distribution
        industry_counts = processed_df['Industry'].value_counts().head(6)
        fig_industry = px.bar(
            x=industry_counts.values,
            y=industry_counts.index,
            orientation='h',
            title="Top Industries",
            color=industry_counts.values,
            color_continuous_scale='plasma'
        )
        st.plotly_chart(fig_industry, use_container_width=True)
    
    # Top leads table
    st.header("🏆 Top Quality Leads")
    
    top_leads = processed_df.nlargest(10, 'lead_score')[
        ['Company', 'Contact_Name', 'Contact_Title', 'Contact_Email', 'lead_score', 'category']
    ].round({'lead_score': 3})
    
    st.dataframe(
        top_leads,
        use_container_width=True,
        hide_index=True
    )
    
    # HubSpot Integration Section
    st.header("🔗 HubSpot CRM Integration")
    st.markdown("*Export your enhanced leads directly to HubSpot with AI-powered insights*")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📤 Data Export")
        
        if st.button("🚀 Generate HubSpot Import", type="primary"):
            formatter = HubSpotFormatter()
            
            with st.spinner("Preparing HubSpot data..."):
                hubspot_data = formatter.format_for_hubspot(processed_df)
                st.session_state.hubspot_data = hubspot_data
            
            st.success("✅ HubSpot import data generated!")
            
            # Show summary
            summary = hubspot_data['summary']
            st.json({
                "Import Summary": {
                    "Total Contacts": summary['total_contacts'],
                    "Hot Leads": summary['hot_leads'],
                    "Import Date": summary['import_date'],
                    "Source": summary['source']
                }
            })
            
            # Download button
            json_data = json.dumps(hubspot_data, indent=2)
            st.download_button(
                label="📥 Download HubSpot JSON",
                data=json_data,
                file_name=f"hubspot_import_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
                mime="application/json"
            )

    with col2:
        st.subheader("⚡ Workflow Automation")
        
        if st.button("🔄 Generate Workflows & Tasks"):
            formatter = HubSpotFormatter()
            
            workflows = formatter.generate_recommended_workflows(processed_df)
            tasks = formatter.create_sales_tasks(processed_df)
            
            st.success(f"✅ Generated {len(workflows)} workflows and {len(tasks)} tasks!")
            
            # Show workflows
            with st.expander("📋 Recommended Workflows"):
                for i, workflow in enumerate(workflows, 1):
                    st.markdown(f"**{i}. {workflow['name']}**")
                    st.markdown(f"*Trigger:* {workflow['trigger']}")
                    st.markdown(f"*Affects:* {workflow['affected_leads']} leads")
                    st.markdown("*Actions:*")
                    for action in workflow['actions']:
                        st.markdown(f"  • {action}")
                    st.markdown("---")
            
            # Show tasks
            with st.expander("✅ Priority Tasks"):
                if tasks:
                    tasks_df = pd.DataFrame(tasks)
                    st.dataframe(tasks_df, use_container_width=True, hide_index=True)

    # Real API Integration Section - FIXED
    if st.session_state.hubspot_data:
        st.header("🌐 Live HubSpot Integration")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            if demo_mode:
                st.info("🎭 Demo Mode: Simulated HubSpot integration")
                if st.button("🚀 Simulate HubSpot Upload", type="secondary"):
                    if simulate_hubspot_upload(st.session_state.hubspot_data):
                        st.balloons()
                        st.markdown("""
                        <div class="success-box">
                        <h4>✅ Simulated Upload Complete!</h4>
                        <p>In real mode, this would:</p>
                        <ul>
                        <li>Create/update contacts in HubSpot</li>
                        <li>Set custom properties (AI scores, priorities)</li>
                        <li>Trigger automated workflows</li>
                        <li>Create sales tasks</li>
                        </ul>
                        </div>
                        """, unsafe_allow_html=True)
            else:
                if not HUBSPOT_SDK_INSTALLED:
                    st.error("❌ HubSpot SDK not installed. Run: `pip install hubspot-api-client`")
                elif not api_key:
                    st.warning("🔑 Enter your HubSpot API key in the sidebar to continue")
                    st.info("💡 Get your API key from HubSpot → Settings → Integrations → Private Apps")
                else:
                    st.info("🔗 Connecting to HubSpot...")
                    
                    # Create HubSpot client
                    try:
                        hubspot_client = create_hubspot_client(api_key)
                        
                        if hubspot_client:
                            # Show account info
                            account_info = hubspot_client.get_account_info()
                            if 'error' not in account_info:
                                st.success(f"✅ Connected to HubSpot Account: {account_info.get('account_id', 'Unknown')}")
                            
                            col_a, col_b = st.columns(2)
                            
                            with col_a:
                                if st.button("🔧 Setup Custom Properties", type="secondary"):
                                    with st.spinner("Creating custom properties..."):
                                        prop_results = hubspot_client.create_custom_properties()
                                    
                                    if prop_results['created']:
                                        st.success(f"✅ Created {len(prop_results['created'])} new properties")
                                        for prop in prop_results['created']:
                                            st.write(f"  • {prop}")
                                    if prop_results['existed']:
                                        st.info(f"ℹ️ {len(prop_results['existed'])} properties already existed")
                                        for prop in prop_results['existed']:
                                            st.write(f"  • {prop}")
                                    if prop_results['errors']:
                                        st.error(f"❌ {len(prop_results['errors'])} errors occurred")
                                        for error in prop_results['errors'][:3]:  # Show first 3 errors
                                            st.error(f"  • {error}")
                            
                            with col_b:
                                if st.button("🚀 Upload to HubSpot", type="primary"):
                                    contacts_to_upload = st.session_state.hubspot_data['contacts']
                                    
                                    st.info(f"📤 Uploading {len(contacts_to_upload)} contacts to HubSpot...")
                                    
                                    # Upload contacts
                                    upload_results = hubspot_client.upload_contacts(contacts_to_upload)
                                    
                                    # Show results
                                    if upload_results['successful'] > 0:
                                        st.success(f"✅ Successfully uploaded {upload_results['successful']} contacts!")
                                        st.balloons()
                                    
                                    if upload_results['failed'] > 0:
                                        st.warning(f"⚠️ {upload_results['failed']} contacts failed to upload")
                                        
                                        with st.expander("View Upload Errors"):
                                            for error in upload_results['errors'][:5]:  # Show first 5 errors
                                                st.error(error)
                                    
                                    # Show created contacts
                                    if upload_results['created_contacts']:
                                        with st.expander("📋 View Created Contacts"):
                                            created_df = pd.DataFrame(upload_results['created_contacts'])
                                            st.dataframe(created_df, use_container_width=True)
                                            
                                            st.success("🎯 Check your HubSpot contacts to see the new leads with AI scores!")
                    
                    except Exception as e:
                        st.error(f"❌ Failed to connect to HubSpot: {str(e)}")
                        st.info("💡 Make sure your API key is correct and has the required permissions")
        
        with col2:
            st.markdown("**Integration Benefits:**")
            st.markdown("• Live contact creation/updates")
            st.markdown("• Custom AI score properties")  
            st.markdown("• Automated workflow triggers")
            st.markdown("• Real-time data sync")
            
            if not demo_mode and HUBSPOT_SDK_INSTALLED:
                st.markdown("**Required Steps:**")
                st.markdown("1. Enter valid API key")
                st.markdown("2. Setup custom properties")
                st.markdown("3. Upload contacts")
                st.markdown("4. Check HubSpot dashboard")
    
    # Export options
    st.header("📤 Export Options")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        enhanced_csv = processed_df.to_csv(index=False)
        st.download_button(
            label="📊 Download Enhanced CSV",
            data=enhanced_csv,
            file_name=f"enhanced_leads_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv"
        )
    
    with col2:
        if st.session_state.hubspot_data:
            json_data = json.dumps(st.session_state.hubspot_data, indent=2)
            st.download_button(
                label="🔗 Download HubSpot JSON",
                data=json_data,
                file_name=f"hubspot_data_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
                mime="application/json"
            )
    
    with col3:
        # Model summary
        model_summary = {
            "model_type": "Random Forest Classifier",
            "features": scorer.feature_columns,
            "training_accuracy": training_results['train_accuracy'],
            "test_accuracy": training_results['test_accuracy'],
            "feature_importance": scorer.get_feature_importance()
        }
        
        summary_json = json.dumps(model_summary, indent=2)
        st.download_button(
            label="🤖 Download Model Summary",
            data=summary_json,
            file_name=f"model_summary_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
            mime="application/json"
        )
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666;'>
    <p>🎯 Lead Quality Engine | Built by Sushruth for Caprae Capital</p>
    <p>Enhancing SaaSSquatch leads with AI-powered insights and HubSpot integration</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()