import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import date, datetime
from db import get_session, get_all_patients, get_patient_by_id, add_patient
from models import Contact, Patient, Task
from constants import TASK_TYPES, TASK_PRIORITIES, TASK_STATUSES, ROLES
from db import (get_session, get_all_patients, get_patient_by_id, add_patient,
                add_task, get_all_tasks, get_tasks_by_patient, update_task_status)
# Auto-initialize database if it doesn't exist
import os
from models import Base
from db import engine, get_session
from models import Patient

# Check if database needs initialization
if not os.path.exists('crc_navigator_v2.db'):
    # Create database structure
    Base.metadata.create_all(engine)
    
    # Silently create demo data
    from init_db import create_demo_data
    create_demo_data(verbose=False)  # Silent for Streamlit


# Verify database has data before continuing
try:
    session_check = get_session()
    patient_count = session_check.query(Patient).count()
    if patient_count == 0:
        # Database exists but is empty - populate it
        from init_db import create_demo_data
        create_demo_data(verbose=False)  # Silent for Streamlit
except Exception:
    # If there's any error, initialize the database
    Base.metadata.create_all(engine)
    from init_db import create_demo_data
    create_demo_data(verbose=False)  # Silent for Streamlit

# Page config - must be first Streamlit command
st.set_page_config(
    page_title="CRC Screening Navigator",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'selected_patient_id' not in st.session_state:
    st.session_state.selected_patient_id = None

st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
    }
    /* Make expanders more prominent */
    .streamlit-expanderHeader {
        background-color: #f0f2f6;
        border-radius: 5px;
        font-weight: 600;
    }
    /* Better button styling */
    .stButton>button {
        border-radius: 5px;
        font-weight: 500;
    }
    /* Color code priority badges */
    .high-priority {
        background-color: #fee;
        padding: 5px 10px;
        border-radius: 5px;
        color: #c00;
    }
    </style>
""", unsafe_allow_html=True)

# Header
col1, col2 = st.columns([3, 1])

with col1:
    st.markdown('<p class="main-header">🏥 CRC Screening Navigator</p>', unsafe_allow_html=True)
    st.markdown("**Maniilaq Health Center** - Colorectal Cancer Screening Program")
    st.caption("Empowering community health through proactive colorectal cancer screening")

with col2:
    st.metric("Program Status", "Active", delta="Live")
    st.caption(f"Last updated: {datetime.now().strftime('%b %d, %Y at %I:%M %p')}")

st.markdown("---")

# Sidebar
st.sidebar.title("🏥 Navigation")
st.sidebar.markdown("---")

# Quick Stats in Sidebar
st.sidebar.subheader("📊 Quick Stats")
session_sidebar = get_session()
patients_sidebar = get_all_patients(session_sidebar)

if patients_sidebar:
    total = len(patients_sidebar)
    overdue = len([p for p in patients_sidebar if 'Overdue' in (p.status or '')])
    never = len([p for p in patients_sidebar if p.status == 'Never Screened'])
    
    st.sidebar.metric("Total Patients", total)
    st.sidebar.metric("Need Attention", overdue + never)
    
st.sidebar.markdown("---")

# Navigation Tips
st.sidebar.subheader("💡 Quick Guide")
st.sidebar.markdown("""
**Dashboard Tab:**
- View all patients
- Filter and sort
- Download data
- Select patient

**Patient Details Tab:**
- View patient info
- See screening history
- Log contact attempts

**Admin Tab:**
- Add new patients
- Export full database
- Refresh calculations
""")

# Main tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Dashboard", 
    "📞 Daily Outreach", 
    "✅ Tasks",  # NEW TAB
    "👤 Patient Details", 
    "⚙️ Settings"
])

# TAB 1: Dashboard
with tab1:
    st.header("Patient Dashboard")
    
    # Get all patients
    session = get_session()
    patients = get_all_patients(session)

    if not patients:
        st.warning("⚠️ No patients in database. Run `python3 init_db.py` to create demo data.")
    else:
        # Convert to DataFrame for display
        patient_data = []
        for p in patients:
            days_overdue = (date.today() - p.next_due_date).days if p.next_due_date else 0
            
            # Build risk factors string
            risk_factors = []
            if p.family_history_crc:
                risk_factors.append("Family Hx")
            if p.major_comorbidities:
                risk_factors.append("Comorbidities")
            risk_str = ", ".join(risk_factors) if risk_factors else "None"
            
            patient_data.append({
                'id': p.id,
                'Name': p.name,
                'Age': p.age,
                'Village': p.village,
                'Last Screen': p.last_screen_type or 'Never',
                'Next Due': p.next_due_date.strftime('%Y-%m-%d') if p.next_due_date else 'N/A',
                'Status': p.status,
                'Days Overdue': max(days_overdue, 0),
                'Risk Factors': risk_str,
                'Phone': p.phone,
                'Language': p.language,
                'Transportation Barrier': p.transportation_barrier,
                'Family History CRC': p.family_history_crc,
                'Major Comorbidities': p.major_comorbidities
            })
        
        df = pd.DataFrame(patient_data)
        
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Patients", len(df))
        
        with col2:
            overdue_count = len(df[df['Status'].str.contains('Overdue', na=False)])
            st.metric("⚠️ Overdue", overdue_count)
        
        with col3:
            due_soon = len(df[df['Status'] == 'Due Soon'])
            st.metric("📅 Due Soon (90 days)", due_soon)
        
        with col4:
            never_screened = len(df[df['Last Screen'] == 'Never'])
            st.metric("🔴 Never Screened", never_screened)

        st.markdown("---")
        
        # Screening completion rate
        eligible_patients = len([p for p in patients if 45 <= p.age <= 75])
        up_to_date = len([p for p in patients if p.status in ['Not Due', 'Completed']])
        completion_rate = (up_to_date / eligible_patients * 100) if eligible_patients > 0 else 0
        
        st.subheader("🎯 Program Performance")
        prog_col1, prog_col2, prog_col3 = st.columns([2, 1, 1])
        
        with prog_col1:
            st.progress(completion_rate / 100)
            st.caption(f"**{completion_rate:.1f}%** of eligible patients (ages 45-75) are up-to-date with screening")
        
        with prog_col2:
            st.metric("Up-to-Date", up_to_date)
        
        with prog_col3:
            st.metric("Eligible Patients", eligible_patients)
        
        st.markdown("---")
        
        # ANALYTICS SECTION
        st.subheader("📊 Program Analytics")
        
        # Create two columns for charts
        chart_col1, chart_col2 = st.columns(2)
        
        with chart_col1:
            # Status breakdown pie chart
            status_counts = df['Status'].value_counts()
            
            # Convert to lists (this is key!)
            labels = status_counts.index.tolist()
            values = status_counts.values.tolist()
            
            colors = []
            for label in labels:
                if 'Never' in label:
                    colors.append('#ff6666')
                elif 'Critically' in label:
                    colors.append('#ff4444')
                elif label == 'Overdue':
                    colors.append('#ffaa44')
                elif 'Soon' in label:
                    colors.append('#ffee44')
                else:
                    colors.append('#90EE90')
            
            fig_status = go.Figure(data=[go.Pie(
                labels=labels,
                values=values,
                marker=dict(colors=colors),
                hole=0.3
            )])
            
            fig_status.update_layout(
                title='Patient Status Breakdown',
                showlegend=True
            )
            st.plotly_chart(fig_status, use_container_width=True)
        
        with chart_col2:
            # Village breakdown bar chart
            village_counts = df['Village'].value_counts().sort_values()
            
            fig_village = go.Figure(data=[go.Bar(
                x=village_counts.values.tolist(),
                y=village_counts.index.tolist(),
                orientation='h',
                marker_color='#1f77b4',
                text=village_counts.values.tolist(),
                textposition='auto'
            )])
            
            fig_village.update_layout(
                title='Patients by Village',
                xaxis_title='Number of Patients',
                yaxis_title='',
                height=400
            )
            st.plotly_chart(fig_village, use_container_width=True)
        
        # Second row of charts
        chart_col3, chart_col4 = st.columns(2)
        
        with chart_col3:
            # Age distribution histogram
            fig_age = go.Figure(data=[go.Histogram(
                x=df['Age'].tolist(),
                nbinsx=16,
                marker_color='#1f77b4',
                marker_line_color='#ffffff',
                marker_line_width=2
            )])
            
            fig_age.update_layout(
                title='Age Distribution',
                xaxis_title='Age (years)',
                yaxis_title='Number of Patients',
                xaxis=dict(
                    range=[0, 100],
                    dtick=10
                ),
                height=400,
                bargap=0.05
            )
            
            st.plotly_chart(fig_age, use_container_width=True)
        
        with chart_col4:
            # Risk factors breakdown
            family_hx_count = len([p for p in patients if p.family_history_crc])
            comorbidity_count = len([p for p in patients if p.major_comorbidities])
            both_count = len([p for p in patients if p.family_history_crc and p.major_comorbidities])
            none_count = len([p for p in patients if not p.family_history_crc and not p.major_comorbidities])
            
            fig_risk = go.Figure(data=[go.Bar(
                x=['Family Hx CRC', 'Major\nComorbidities', 'Both', 'None'],
                y=[family_hx_count, comorbidity_count, both_count, none_count],
                marker_color=['#ff6666', '#ffaa66', '#ff4444', '#90EE90'],
                text=[family_hx_count, comorbidity_count, both_count, none_count],
                textposition='auto'
            )])
            
            fig_risk.update_layout(
                title='Risk Factors Distribution',
                xaxis_title='',
                yaxis_title='Number of Patients',
                height=400
            )
            st.plotly_chart(fig_risk, use_container_width=True)
        
        # Third row of charts
        chart_col5, chart_col6 = st.columns(2)
        
        with chart_col5:
            # Screening type breakdown (original chart)
            screen_counts = df['Last Screen'].value_counts()
            
            fig_screen = go.Figure(data=[go.Bar(
                x=screen_counts.index.tolist(),
                y=screen_counts.values.tolist(),
                marker_color=['#ff6666', '#66b3ff', '#99ff99', '#ffcc99'][:len(screen_counts)],
                text=screen_counts.values.tolist(),
                textposition='auto'
            )])
            
            fig_screen.update_layout(
                title='Last Screening Type Distribution',
                xaxis_title='',
                yaxis_title='Number of Patients',
                height=400
            )
            st.plotly_chart(fig_screen, use_container_width=True)
        
        with chart_col6:
            # Outstanding Tasks Chart
            all_tasks = get_all_tasks(session)
            
            if all_tasks:
                pending_tasks = len([t for t in all_tasks if t.status == 'Pending'])
                in_progress_tasks = len([t for t in all_tasks if t.status == 'In Progress'])
                completed_tasks = len([t for t in all_tasks if t.status == 'Completed'])
                
                fig_tasks = go.Figure(data=[go.Bar(
                    x=['Pending', 'In Progress', 'Completed'],
                    y=[pending_tasks, in_progress_tasks, completed_tasks],
                    marker_color=['#ffaa44', '#66b3ff', '#90EE90'],
                    text=[pending_tasks, in_progress_tasks, completed_tasks],
                    textposition='auto'
                )])
                
                fig_tasks.update_layout(
                    title='Tasks Status Overview',
                    xaxis_title='',
                    yaxis_title='Number of Tasks',
                    height=400
                )
                st.plotly_chart(fig_tasks, use_container_width=True)
            else:
                st.info("📊 **No tasks yet**\n\nTasks will appear here once created from contact logs or the Tasks tab.")
        
        st.markdown("---")
        
        # FILTERS SECTION
        st.subheader("🔍 Filter Patients")
        
        # Filters in expandable section
        with st.expander("📋 Filter Options", expanded=True):
            # Search by name
            st.markdown("**🔎 Search by Name**")
            name_search = st.text_input(
                "Enter patient name",
                placeholder="Type patient name to search...",
                label_visibility="collapsed"
            )
            
            st.markdown("---")
            
            # Quick action buttons
            button_col1, button_col2 = st.columns(2)
            with button_col1:
                if st.button("✅ Select All Filters", use_container_width=True):
                    st.session_state.status_filter = df['Status'].unique().tolist()
                    st.session_state.village_filter = sorted(df['Village'].unique().tolist())
                    st.session_state.risk_filter = df['Risk Factors'].unique().tolist()
                    st.rerun()
            
            with button_col2:
                if st.button("❌ Clear All Filters", use_container_width=True):
                    st.session_state.status_filter = []
                    st.session_state.village_filter = []
                    st.session_state.risk_filter = []
                    st.rerun()
            
            st.markdown("---")
            
            filter_col1, filter_col2, filter_col3 = st.columns(3)
            
            # Initialize session state for filters if not exists
            if 'status_filter' not in st.session_state:
                st.session_state.status_filter = df['Status'].unique().tolist()
            if 'village_filter' not in st.session_state:
                st.session_state.village_filter = sorted(df['Village'].unique().tolist())
            if 'risk_filter' not in st.session_state:
                st.session_state.risk_filter = df['Risk Factors'].unique().tolist()
            
            with filter_col1:
                status_options = df['Status'].unique().tolist()
                status_filter = st.multiselect(
                    "Status",
                    options=status_options,
                    default=st.session_state.status_filter,
                    key="status_multiselect"
                )
                st.session_state.status_filter = status_filter
            
            with filter_col2:
                village_options = sorted(df['Village'].unique().tolist())
                village_filter = st.multiselect(
                    "Village",
                    options=village_options,
                    default=st.session_state.village_filter,
                    key="village_multiselect"
                )
                st.session_state.village_filter = village_filter
            
            with filter_col3:
                risk_options = df['Risk Factors'].unique().tolist()
                risk_filter = st.multiselect(
                    "Risk Factors",
                    options=risk_options,
                    default=st.session_state.risk_filter,
                    key="risk_multiselect"
                )
                st.session_state.risk_filter = risk_filter
        
        # Apply filters
        filtered_df = df[
            (df['Status'].isin(status_filter)) &
            (df['Village'].isin(village_filter)) &
            (df['Risk Factors'].isin(risk_filter))
        ]
        
        # Apply name search if provided
        if name_search:
            filtered_df = filtered_df[
                filtered_df['Name'].str.contains(name_search, case=False, na=False)
            ]
        
        # Sort and display options
        sort_col1, sort_col2 = st.columns([3, 1])
        
        with sort_col1:
            sort_by = st.selectbox(
                "Sort by",
                options=['Days Overdue', 'Age', 'Name', 'Village', 'Status'],
                index=0
            )
        
        with sort_col2:
            sort_order = st.radio("Order", ["Descending", "Ascending"], index=0, horizontal=True)
        
        ascending = True if sort_order == "Ascending" else False
        filtered_df = filtered_df.sort_values(by=sort_by, ascending=ascending)
        
        # Show filter results
        st.info(f"📊 Showing **{len(filtered_df)}** of **{len(df)}** patients")
        
        # Priority patients callout
        priority_patients = filtered_df[
            (filtered_df['Status'].isin(['Never Screened', 'Critically Overdue', 'Overdue']))
        ]
        
        if len(priority_patients) > 0:
            st.warning(f"⚠️ **{len(priority_patients)} patients need immediate attention**")
        
        # Display table with color coding
        def color_status(row):
            colors = {
                'Critically Overdue': 'background-color: #ff4444; color: white',
                'Overdue': 'background-color: #ffaa44',
                'Due Soon': 'background-color: #ffee44',
                'Not Due': 'background-color: #e8e8e8',
                'Never Screened': 'background-color: #ff6666; color: white'
            }
            return [colors.get(row['Status'], '')] * len(row)
        
        # Display the dataframe
        display_df = filtered_df.drop(columns=['id', 'Language', 'Transportation Barrier', 'Family History CRC', 'Major Comorbidities'])
        st.dataframe(
            display_df.style.apply(color_status, axis=1),
            use_container_width=True,
            hide_index=True,
            height=400
        )
        
        # Export option
        csv = display_df.to_csv(index=False)
        st.download_button(
            label="📥 Download Filtered Data as CSV",
            data=csv,
            file_name=f"crc_patients_{date.today()}.csv",
            mime="text/csv",
        )
        
       # Select patient
        st.markdown("---")
        st.subheader("👤 Select Patient for Details")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            selected_name = st.selectbox(
                "Choose a patient to view full details",
                options=[''] + filtered_df['Name'].tolist(),
                index=0
            )
        
        if selected_name:
            selected_row = filtered_df[filtered_df['Name'] == selected_name].iloc[0]
            st.session_state.selected_patient_id = int(selected_row['id'])
            
            # Also store the patient object itself
            session_for_selection = get_session()
            all_patients_list = get_all_patients(session_for_selection)
            selected_patient_obj = [p for p in all_patients_list if p.id == st.session_state.selected_patient_id][0]
            st.session_state.selected_patient = selected_patient_obj
            
            # Show selected patient info with call-to-action
            st.success(f"✅ Selected: **{selected_name}**")
            
            # Patient quick info
            info_col1, info_col2, info_col3 = st.columns(3)
            with info_col1:
                st.write(f"**Village:** {selected_patient_obj.village}")
            with info_col2:
                st.write(f"**Status:** {selected_patient_obj.status}")
            with info_col3:
                st.write(f"**Age:** {selected_patient_obj.age}")
            
            # Alternative: Add a visual reminder
            st.info("💡 **Next Step:** Click the 'Patient Details' tab at the top of the page to see complete patient information, screening history, and log contact attempts.")

# TAB 2: Daily Outreach
with tab2:
    st.header("📞 Daily Outreach Queue")
    st.caption(f"Priority contact list for {date.today().strftime('%A, %B %d, %Y')}")
    
    # Get all patients
    session = get_session()
    patients = get_all_patients(session)
    
    if not patients:
        st.warning("⚠️ No patients in database.")
    else:
        # Filter for patients who need contact
        priority_patients = []
        for p in patients:
            # Calculate priority
            needs_contact = False
            priority_level = 0
            
            if p.status == 'Never Screened':
                needs_contact = True
                priority_level = 3
            elif p.status == 'Critically Overdue':
                needs_contact = True
                priority_level = 3
            elif p.status == 'Overdue':
                needs_contact = True
                priority_level = 2
            elif p.status == 'Due Soon':
                needs_contact = True
                priority_level = 1
            
            if needs_contact:
                # Check last contact date
                last_contacts = session.query(Contact).filter(
                    Contact.patient_id == p.id
                ).order_by(Contact.timestamp.desc()).limit(1).all()
                
                last_contact_date = last_contacts[0].timestamp.date() if last_contacts else None
                days_since_contact = (date.today() - last_contact_date).days if last_contact_date else 999
                
                priority_patients.append({
                    'patient': p,
                    'priority_level': priority_level,
                    'days_since_contact': days_since_contact,
                    'last_contact_date': last_contact_date
                })
        
        # Sort by priority level (highest first), then by days since contact
        priority_patients.sort(key=lambda x: (-x['priority_level'], -x['days_since_contact']))
        
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("📋 Total in Queue", len(priority_patients))
        
        with col2:
            high_priority = len([p for p in priority_patients if p['priority_level'] == 3])
            st.metric("🔴 High Priority", high_priority)
        
        with col3:
            medium_priority = len([p for p in priority_patients if p['priority_level'] == 2])
            st.metric("🟠 Medium Priority", medium_priority)
        
        with col4:
            low_priority = len([p for p in priority_patients if p['priority_level'] == 1])
            st.metric("🟡 Low Priority", low_priority)
        
        st.markdown("---")
        
        # Filter options
        st.subheader("🔍 Filter Queue")
        filter_col1, filter_col2 = st.columns(2)
        
        with filter_col1:
            priority_filter = st.multiselect(
                "Priority Level",
                options=[3, 2, 1],
                default=[3, 2, 1],
                format_func=lambda x: {3: "🔴 High", 2: "🟠 Medium", 1: "🟡 Low"}[x]
            )
        
        with filter_col2:
            contact_threshold = st.selectbox(
                "Not contacted in last...",
                options=[1, 3, 7, 14, 30, 999],
                index=3,
                format_func=lambda x: f"{x} days" if x < 999 else "Any time"
            )
        
        # Apply filters
        filtered_queue = [
            p for p in priority_patients 
            if p['priority_level'] in priority_filter 
            and p['days_since_contact'] >= contact_threshold
        ]
        
        st.info(f"📊 Showing **{len(filtered_queue)}** patients in outreach queue")

        # Export daily list
        if len(filtered_queue) > 0:
            export_queue = []
            for item in filtered_queue:
                p = item['patient']
                export_queue.append({
                    'Priority': {3: 'High', 2: 'Medium', 1: 'Low'}[item['priority_level']],
                    'Name': p.name,
                    'Phone': p.phone,
                    'Village': p.village,
                    'Status': p.status,
                    'Last Contact': item['last_contact_date'] or 'Never',
                    'Notes': ''
                })
            
            export_df = pd.DataFrame(export_queue)
            csv = export_df.to_csv(index=False)
            
            st.download_button(
                label=f"📥 Download Today's Contact List ({len(filtered_queue)} patients)",
                data=csv,
                file_name=f"daily_outreach_{date.today()}.csv",
                mime="text/csv",
            )
        
        if len(filtered_queue) == 0:
            st.markdown("""
                <div style='text-align: center; padding: 60px; background-color: #f0f9ff; border-radius: 15px; border: 2px dashed #3b82f6;'>
                    <h2>🎉 Excellent Work!</h2>
                    <p style='font-size: 18px; color: #666;'>All patients in your queue have been contacted.</p>
                    <p style='font-size: 16px; color: #888;'>Check back tomorrow or adjust filters to see more patients.</p>
                </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("---")
            
            # Display each patient in queue
            for idx, item in enumerate(filtered_queue, 1):
                p = item['patient']
                
                # Priority badge
                priority_badges = {
                    3: "🔴 HIGH PRIORITY",
                    2: "🟠 MEDIUM PRIORITY", 
                    1: "🟡 LOW PRIORITY"
                }
                
                with st.expander(
                    f"{idx}. {priority_badges[item['priority_level']]} - {p.name} ({p.village}) - {p.status}",
                    expanded=(idx == 1)  # First one expanded by default
                ):
                    # Patient info columns
                    info_col1, info_col2, info_col3 = st.columns(3)
                    
                    with info_col1:
                        st.write(f"**Name:** {p.name}")
                        st.write(f"**Age:** {p.age}")
                        st.write(f"**Village:** {p.village}")
                    
                    with info_col2:
                        st.write(f"**Phone:** {p.phone}")
                        st.write(f"**Language:** {p.language}")
                        st.write(f"**Status:** {p.status}")
                    
                    with info_col3:
                        st.write(f"**Last Screen:** {p.last_screen_type or 'Never'}")
                        if p.last_screen_date:
                            st.write(f"**Date:** {p.last_screen_date.strftime('%m/%d/%Y')}")
                        st.write(f"**Last Contact:** {item['last_contact_date'].strftime('%m/%d/%Y') if item['last_contact_date'] else 'Never'}")
                    
                    # Risk factors and barriers
                    if p.family_history_crc:
                        st.warning("⚠️ Family history of CRC")
                    if p.major_comorbidities:
                        st.warning("⚠️ Major comorbidities")
                    if p.transportation_barrier:
                        st.warning("🚗 Transportation barrier")
                    
                    st.markdown("---")
                    
                    # Recent contact history
                    st.markdown("**Recent Contact History:**")
                    recent_contacts = session.query(Contact).filter(
                        Contact.patient_id == p.id
                    ).order_by(Contact.timestamp.desc()).limit(3).all()
                    
                    if recent_contacts:
                        for contact in recent_contacts:
                            st.caption(f"• {contact.timestamp.strftime('%m/%d/%Y')} - {contact.method}: {contact.outcome}")
                    else:
                        st.caption("No previous contact attempts")
                    
                    st.markdown("---")

                    # Quick action buttons
                    quick_col1, quick_col2, quick_col3 = st.columns(3)
                    
                    with quick_col1:
                        if st.button("✅ Mark Completed", key=f"complete_{p.id}", use_container_width=True):
                            p.status = "Completed"
                            session.commit()
                            st.success("Marked as completed!")
                            st.rerun()
                    
                    with quick_col2:
                        if st.button("⏭️ Skip for Today", key=f"skip_{p.id}", use_container_width=True):
                            # Add a "skipped" contact log
                            skip_contact = Contact(
                                patient_id=p.id,
                                method="Skipped",
                                outcome="Skipped for today",
                                user="System",
                                timestamp=datetime.now()
                            )
                            session.add(skip_contact)
                            session.commit()
                            st.info("Skipped - will show tomorrow")
                            st.rerun()
                    
                    with quick_col3:
                        if st.button("❌ Declined Screening", key=f"decline_{p.id}", use_container_width=True):
                            p.status = "Declined"
                            session.commit()
                            st.warning("Marked as declined")
                            st.rerun()
                    
                    st.markdown("---")
                    
                    # Contact logging form
                    st.markdown("**📝 Log Contact Attempt:**")
                    
                    with st.form(f"contact_form_{p.id}"):
                        form_col1, form_col2 = st.columns(2)
                        
                        with form_col1:
                            contact_method = st.selectbox(
                                "Method",
                                ["Phone Call", "Text Message", "In-Person", "Mail", "Email"],
                                key=f"method_{p.id}"
                            )
                            
                            contact_user = st.text_input(
                                "Your Name", 
                                value="",
                                key=f"user_{p.id}"
                            )
                        
                        with form_col2:
                            contact_outcome = st.selectbox(
                                "Outcome",
                                [
                                    "No Answer",
                                    "Left Voicemail",
                                    "Reached - Scheduled",
                                    "Reached - Declined",
                                    "Reached - Already Completed",
                                    "Reached - Needs More Info",
                                    "Wrong Number",
                                    "Other"
                                ],
                                key=f"outcome_{p.id}"
                            )
                            
                            contact_role = st.selectbox(
                                "Role",
                                ["Navigator", "Social Worker", "CHAP", "Outreach Coordinator", 
                                 "Primary Care Physician", "Specialty Physician", "Nurse", "Other"],
                                key=f"role_{p.id}"
                            )
                        
                        contact_notes = st.text_area(
                            "Notes",
                            key=f"notes_{p.id}"
                        )
                        
                        st.markdown("---")
                        st.markdown("**📋 Create Follow-up Task** (optional)")
                        
                        create_task = st.checkbox("Create a task from this contact", key=f"create_task_{p.id}")
                        
                        if create_task:
                            task_col1, task_col2 = st.columns(2)
                            
                            with task_col1:
                                task_type = st.selectbox(
                                    "Task Type",
                                    options=TASK_TYPES,
                                    key=f"task_type_{p.id}"
                                )
                                
                                task_assigned_to = st.text_input(
                                    "Assign To",
                                    placeholder="Person's name",
                                    key=f"task_assign_{p.id}"
                                )
                            
                            with task_col2:
                                task_assigned_role = st.selectbox(
                                    "Assign Role",
                                    options=ROLES,
                                    key=f"task_role_{p.id}"
                                )
                                
                                task_priority = st.selectbox(
                                    "Priority",
                                    options=TASK_PRIORITIES,
                                    index=1,
                                    key=f"task_priority_{p.id}"
                                )
                            
                            task_due_date = st.date_input(
                                "Due Date",
                                value=date.today(),
                                key=f"task_due_{p.id}"
                            )
                        
                        submitted = st.form_submit_button(
                            "💾 Log Contact" + (" & Create Task" if create_task else ""),
                            use_container_width=True
                        )
                        
                        if submitted:
                            from datetime import datetime
                            
                            # Add contact log
                            contact_data = {
                                'patient_id': p.id,
                                'method': contact_method,
                                'outcome': contact_outcome,
                                'user': contact_user,
                                'role': contact_role,
                                'notes': contact_notes,
                                'timestamp': datetime.now()
                            }
                            new_contact = Contact(**contact_data)
                            session.add(new_contact)
                            
                            # Create task if checkbox was selected
                            if create_task and task_assigned_to:
                                task_data = {
                                    'patient_id': p.id,
                                    'task_type': task_type,
                                    'description': contact_notes,
                                    'assigned_to': task_assigned_to,
                                    'assigned_role': task_assigned_role,
                                    'priority': task_priority,
                                    'due_date': task_due_date,
                                    'created_by': contact_user,
                                    'created_by_role': contact_role,
                                    'status': 'Pending'
                                }
                                add_task(session, task_data)
                            
                            # Update patient status if applicable
                            if "Scheduled" in contact_outcome:
                                p.status = "Scheduled"
                            elif "Declined" in contact_outcome:
                                p.status = "Declined"
                            elif "Completed" in contact_outcome:
                                p.status = "Completed"
                            
                            session.commit()
                            
                            success_msg = f"✅ Contact logged for {p.name}!"
                            if create_task and task_assigned_to:
                                success_msg += f"\n✅ Task assigned to {task_assigned_to}!"
                            
                            st.success(success_msg)
                            st.balloons()
                            st.rerun()

# TAB 3: Tasks Management
with tab3:
    st.header("✅ Task Management")
    st.caption(f"Manage and track all patient-related tasks")
    
    # Get all tasks
    session = get_session()
    all_tasks = get_all_tasks(session)
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        pending = len([t for t in all_tasks if t.status == 'Pending'])
        st.metric("🕐 Pending", pending)
    
    with col2:
        in_progress = len([t for t in all_tasks if t.status == 'In Progress'])
        st.metric("🔄 In Progress", in_progress)
    
    with col3:
        overdue_tasks = len([t for t in all_tasks if t.due_date and t.due_date < date.today() and t.status != 'Completed'])
        st.metric("⚠️ Overdue", overdue_tasks)
    
    with col4:
        completed = len([t for t in all_tasks if t.status == 'Completed'])
        st.metric("✅ Completed", completed)
    
    st.markdown("---")
    
    # Filter tasks
    st.subheader("🔍 Filter Tasks")
    
    filter_col1, filter_col2, filter_col3 = st.columns(3)
    
    with filter_col1:
        status_filter_tasks = st.multiselect(
            "Status",
            options=TASK_STATUSES,
            default=['Pending', 'In Progress']
        )
    
    with filter_col2:
        priority_filter_tasks = st.multiselect(
            "Priority",
            options=TASK_PRIORITIES,
            default=TASK_PRIORITIES
        )
    
    with filter_col3:
        role_filter_tasks = st.multiselect(
            "Assigned Role",
            options=ROLES,
            default=ROLES
        )
    
    # Filter tasks
    filtered_tasks = [
        t for t in all_tasks
        if t.status in status_filter_tasks
        and t.priority in priority_filter_tasks
        and (t.assigned_role in role_filter_tasks if t.assigned_role else True)
    ]
    
    st.info(f"📊 Showing **{len(filtered_tasks)}** tasks")
    
    # Quick Create Task
    st.markdown("---")
    st.subheader("➕ Create New Task")
    
    with st.form("quick_create_task"):
        task_col1, task_col2 = st.columns(2)
        
        with task_col1:
            quick_patient = st.selectbox(
                "Patient *",
                options=[p.name for p in get_all_patients(session)],
                help="Select patient for this task"
            )
            
            quick_task_type = st.selectbox(
                "Task Type *",
                options=TASK_TYPES
            )
            
            quick_assigned_to = st.text_input(
                "Assign To *",
                placeholder="Person's name"
            )
            
            quick_assigned_role = st.selectbox(
                "Role *",
                options=ROLES
            )
        
        with task_col2:
            quick_priority = st.selectbox(
                "Priority *",
                options=TASK_PRIORITIES,
                index=1  # Default to Medium
            )
            
            quick_due_date = st.date_input(
                "Due Date",
                value=date.today()
            )
            
            quick_description = st.text_area(
                "Description/Notes",
                placeholder="Add any relevant details..."
            )
            
            quick_created_by = st.text_input(
                "Your Name",
                value=""
            )
        
        quick_submit = st.form_submit_button("➕ Create Task", use_container_width=True, type="primary")
        
        if quick_submit:
            if not quick_patient or not quick_assigned_to:
                st.error("❌ Patient and Assigned To are required!")
            else:
                # Get patient ID
                selected_patient = [p for p in get_all_patients(session) if p.name == quick_patient][0]
                
                task_data = {
                    'patient_id': selected_patient.id,
                    'task_type': quick_task_type,
                    'description': quick_description,
                    'assigned_to': quick_assigned_to,
                    'assigned_role': quick_assigned_role,
                    'priority': quick_priority,
                    'due_date': quick_due_date,
                    'created_by': quick_created_by,
                    'status': 'Pending'
                }
                
                add_task(session, task_data)
                st.success(f"✅ Task created and assigned to {quick_assigned_to}!")
                st.rerun()
    
    st.markdown("---")
    
    # Display tasks
    st.subheader("📋 All Tasks")
    
    if len(filtered_tasks) == 0:
        st.info("No tasks match your filters")
    else:
        # Group by status
        for status in ['Pending', 'In Progress', 'Completed', 'Cancelled']:
            status_tasks = [t for t in filtered_tasks if t.status == status]
            
            if status_tasks:
                status_emoji = {
                    'Pending': '🕐',
                    'In Progress': '🔄',
                    'Completed': '✅',
                    'Cancelled': '❌'
                }
                
                st.markdown(f"### {status_emoji[status]} {status} ({len(status_tasks)})")
                
                for task in status_tasks:
                    # Get patient info
                    task_patient = get_patient_by_id(session, task.patient_id)
                    
                    # Priority color
                    priority_colors = {
                        'Urgent': '🔴',
                        'High': '🟠',
                        'Medium': '🟡',
                        'Low': '⚪'
                    }
                    
                    # Check if overdue
                    is_overdue = task.due_date and task.due_date < date.today() and task.status != 'Completed'
                    overdue_text = " - ⚠️ OVERDUE" if is_overdue else ""
                    
                    with st.expander(
                        f"{priority_colors[task.priority]} [{task.priority}] {task.task_type} - {task_patient.name if task_patient else 'Unknown'} → {task.assigned_to} ({task.assigned_role}){overdue_text}"
                    ):
                        task_detail_col1, task_detail_col2 = st.columns(2)
                        
                        with task_detail_col1:
                            st.write(f"**Patient:** {task_patient.name if task_patient else 'Unknown'}")
                            st.write(f"**Village:** {task_patient.village if task_patient else 'N/A'}")
                            st.write(f"**Task Type:** {task.task_type}")
                            if task.description:
                                st.write(f"**Description:** {task.description}")
                        
                        with task_detail_col2:
                            st.write(f"**Assigned To:** {task.assigned_to}")
                            st.write(f"**Role:** {task.assigned_role}")
                            st.write(f"**Priority:** {task.priority}")
                            st.write(f"**Due Date:** {task.due_date.strftime('%m/%d/%Y') if task.due_date else 'No due date'}")
                            st.write(f"**Created:** {task.created_date.strftime('%m/%d/%Y')} by {task.created_by}")
                        
                        if task.notes:
                            st.info(f"**Notes:** {task.description}")
                        
                        st.markdown("---")
                        
                        # Task actions
                        action_col1, action_col2, action_col3 = st.columns(3)
                        
                        with action_col1:
                            if task.status == 'Pending' and st.button("▶️ Start Task", key=f"start_{task.id}", use_container_width=True):
                                update_task_status(session, task.id, 'In Progress')
                                st.success("Task started!")
                                st.rerun()
                        
                        with action_col2:
                            if task.status != 'Completed' and st.button("✅ Mark Complete", key=f"complete_task_{task.id}", use_container_width=True):
                                update_task_status(session, task.id, 'Completed')
                                st.success("Task completed!")
                                st.balloons()
                                st.rerun()
                        
                        with action_col3:
                            if task.status != 'Cancelled' and st.button("❌ Cancel Task", key=f"cancel_{task.id}", use_container_width=True):
                                update_task_status(session, task.id, 'Cancelled')
                                st.warning("Task cancelled")
                                st.rerun()

# TAB 4: Patient Details
with tab4:
    st.header("Patient Details & Information")
    
    if 'selected_patient' not in st.session_state or st.session_state.selected_patient is None:
        st.warning("⚠️ Please select a patient from the Dashboard first")
        st.info("👈 Go to the Dashboard tab and select a patient from the dropdown at the bottom")
    else:
        # Get patient from session state
        patient = st.session_state.selected_patient
        
        # Patient header
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader(f"👤 {patient.name}")
            st.write(f"**MRN:** {patient.mrn}")
            st.write(f"**Age:** {patient.age} | **DOB:** {patient.dob.strftime('%m/%d/%Y')}")
            st.write(f"**Village:** {patient.village}")
            st.write(f"**Phone:** {patient.phone}")
            if patient.email:
                st.write(f"**Email:** {patient.email}")
            st.write(f"**Language:** {patient.language}")
            if patient.transportation_barrier:
                st.warning("🚗 Transportation barrier noted")
        
        with col2:
            # Status badge
            status_colors = {
                'Critically Overdue': '🔴',
                'Overdue': '🟠',
                'Due Soon': '🟡',
                'Not Due': '🟢',
                'Never Screened': '🔴'
            }
            st.markdown(f"### {status_colors.get(patient.status, '⚪')} {patient.status}")
            
            # Display risk factors
            risk_factors = []
            if patient.family_history_crc:
                risk_factors.append("Family Hx of CRC")
            if patient.major_comorbidities:
                risk_factors.append("Major Comorbidities")
            
            if risk_factors:
                st.warning(f"⚠️ **Risk Factors:** {', '.join(risk_factors)}")
            else:
                st.info("ℹ️ **Risk Factors:** None documented")
        
        st.markdown("---")
        
        # Screening history
        st.subheader("📋 Screening History")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "Last Screening",
                patient.last_screen_type or "Never",
                patient.last_screen_date.strftime('%m/%d/%Y') if patient.last_screen_date else "N/A"
            )
        
        with col2:
            st.metric(
                "Next Due Date",
                patient.next_due_date.strftime('%m/%d/%Y') if patient.next_due_date else "N/A"
            )
        
        with col3:
            if patient.next_due_date:
                days_diff = (date.today() - patient.next_due_date).days
                if days_diff > 0:
                    st.metric("Days Overdue", days_diff, delta="Overdue", delta_color="inverse")
                else:
                    st.metric("Days Until Due", abs(days_diff), delta="On track", delta_color="normal")
        
        # Notes
        if patient.notes:
            st.info(f"**Notes:** {patient.notes}")
        
        st.markdown("---")
        
        # NEW: Update Screening Form
        st.subheader("🩺 Record New Screening")
        
        with st.form(f"update_screening_{patient.id}"):
            st.write("Record a completed screening for this patient:")
            
            screen_update_col1, screen_update_col2 = st.columns(2)
            
            with screen_update_col1:
                new_screen_type = st.selectbox(
                    "Screening Type *",
                    options=['Colonoscopy', 'FIT', 'Cologuard', 'Sigmoidoscopy', 'CT Colonography'],
                    key=f"new_screen_type_{patient.id}"
                )
                
                new_screen_date = st.date_input(
                    "Screening Date *",
                    value=date.today(),
                    max_value=date.today(),
                    key=f"new_screen_date_{patient.id}"
                )
                
                updated_by = st.text_input(
                    "Your Name",
                    value="",
                    key=f"screen_updated_by_{patient.id}"
                )
            
            with screen_update_col2:
                updated_by_role = st.selectbox(
                    "Your Role *",
                    options=ROLES,
                    key=f"screen_role_{patient.id}"
                )
                
                screen_notes = st.text_area(
                    "Notes",
                    placeholder="Add any relevant notes about this screening...",
                    key=f"screen_notes_{patient.id}"
                )
            
            screen_submitted = st.form_submit_button(
                "💾 Record Screening",
                use_container_width=True,
                type="primary"
            )
            
            if screen_submitted:
                from logic import update_patient_computed_fields
                
                # Get fresh patient object from database
                fresh_session = get_session()
                fresh_patient = get_patient_by_id(fresh_session, patient.id)
                
                # Update patient screening info
                fresh_patient.last_screen_type = new_screen_type
                fresh_patient.last_screen_date = new_screen_date
                
                # Add notes to patient record if provided
                if screen_notes:
                    current_notes = fresh_patient.notes or ""
                    new_note = f"[{date.today().strftime('%m/%d/%Y')}] {new_screen_type} completed. {screen_notes}"
                    fresh_patient.notes = f"{current_notes}\n{new_note}" if current_notes else new_note
                
                # Recalculate next due date and status
                update_patient_computed_fields(fresh_session, fresh_patient)
                
                # Create a contact log for this screening
                contact_log_notes = f"{new_screen_type} completed on {new_screen_date.strftime('%m/%d/%Y')}"
                if screen_notes:
                    contact_log_notes += f". Additional Notes: {screen_notes}"
                
                contact_log = Contact(
                    patient_id=fresh_patient.id,
                    method="Screening Recorded",
                    outcome="Screening Completed",
                    user=updated_by if updated_by else "Unknown",
                    role=updated_by_role,
                    notes=contact_log_notes,
                    timestamp=datetime.now()
                )
                fresh_session.add(contact_log)
                
                # Mark any "Schedule [screening type]" tasks as completed
                pending_screening_tasks = get_tasks_by_patient(fresh_session, fresh_patient.id)
                for task in pending_screening_tasks:
                    if "Schedule" in task.task_type and task.status != 'Completed':
                        update_task_status(fresh_session, task.id, 'Completed')
                
                fresh_session.commit()
                
                # **KEY FIX**: Update session state with fresh patient data
                st.session_state.selected_patient = fresh_patient
                
                st.success(f"✅ {new_screen_type} screening recorded for {fresh_patient.name}!")
                st.success(f"📅 Next screening due: {fresh_patient.next_due_date.strftime('%m/%d/%Y')}")
                st.success(f"📊 Status updated to: {fresh_patient.status}")
                st.balloons()
                st.rerun()
        
        st.markdown("---")
 
        # Patient's tasks
        st.subheader("✅ Active Tasks for This Patient")
        
        patient_tasks = get_tasks_by_patient(session, patient.id, status_filter=None)
        active_tasks = [t for t in patient_tasks if t.status in ['Pending', 'In Progress']]
        
        if active_tasks:
            for task in active_tasks:
                priority_colors = {'Urgent': '🔴', 'High': '🟠', 'Medium': '🟡', 'Low': '⚪'}
                status_colors = {'Pending': '🕐', 'In Progress': '🔄'}
                
                is_overdue = task.due_date and task.due_date < date.today()
                overdue_badge = " - ⚠️ OVERDUE" if is_overdue else ""
                
                with st.expander(f"{priority_colors[task.priority]}{status_colors[task.status]} {task.task_type} → {task.assigned_to}{overdue_badge}"):
                    st.write(f"**Assigned To:** {task.assigned_to} ({task.assigned_role})")
                    st.write(f"**Priority:** {task.priority}")
                    st.write(f"**Status:** {task.status}")
                    st.write(f"**Due:** {task.due_date.strftime('%m/%d/%Y') if task.due_date else 'No due date'}")
                    if task.description:
                        st.write(f"**Description:** {task.description}")
                    
                    # Quick actions
                    task_action_col1, task_action_col2 = st.columns(2)
                    with task_action_col1:
                        if st.button("✅ Complete", key=f"complete_task_detail_{task.id}", use_container_width=True):
                            update_task_status(session, task.id, 'Completed')
                            st.success("Task completed!")
                            st.rerun()
                    
                    with task_action_col2:
                        if st.button("❌ Cancel", key=f"cancel_task_detail_{task.id}", use_container_width=True):
                            update_task_status(session, task.id, 'Cancelled')
                            st.rerun()
        else:
            st.info("No active tasks for this patient")
        
        # Show completed tasks count
        completed_tasks = [t for t in patient_tasks if t.status == 'Completed']
        if completed_tasks:
            st.caption(f"✅ {len(completed_tasks)} completed task(s) - expand below to see history")        
        
        # NEW: Add contact logging form HERE (before contact history)
        st.subheader("📝 Log New Contact Attempt")
        
        with st.form(f"contact_form_details_{patient.id}", clear_on_submit=True):
            form_col1, form_col2 = st.columns(2)
            
            with form_col1:
                contact_method = st.selectbox(
                    "Method",
                    ["Phone Call", "Text Message", "In-Person", "Mail", "Email"],
                    key=f"method_details_{patient.id}"
                )
                
                contact_user = st.text_input(
                    "Your Name", 
                    value="",
                    key=f"user_details_{patient.id}"
                )
            
            with form_col2:
                contact_outcome = st.selectbox(
                    "Outcome",
                    [
                        "No Answer",
                        "Left Voicemail",
                        "Reached - Scheduled",
                        "Reached - Declined",
                        "Reached - Already Completed",
                        "Reached - Needs More Info",
                        "Wrong Number",
                        "Other"
                    ],
                    key=f"outcome_details_{patient.id}"
                )
                
                contact_role = st.selectbox(
                    "Role",
                    ["Navigator", "Social Worker", "CHAP", "Outreach Coordinator", 
                     "Primary Care Physician", "Specialty Physician", "Nurse", "Other"],
                    key=f"role_details_{patient.id}"
                )
            
            contact_notes = st.text_area(
                "Notes",
                placeholder="Add any relevant notes about this contact...",
                key=f"notes_details_{patient.id}"
            )
            
            submitted = st.form_submit_button(
                "💾 Log Contact Attempt",
                use_container_width=True,
                type="primary"
            )
            
            if submitted:
                # Add contact log
                contact_data = {
                    'patient_id': patient.id,
                    'method': contact_method,
                    'outcome': contact_outcome,
                    'user': contact_user,
                    'role': contact_role,
                    'notes': contact_notes,
                    'timestamp': datetime.now()
                }
                new_contact = Contact(**contact_data)
                session.add(new_contact)
                
                # Update patient status if applicable
                if "Scheduled" in contact_outcome:
                    patient.status = "Scheduled"
                elif "Declined" in contact_outcome:
                    patient.status = "Declined"
                elif "Completed" in contact_outcome:
                    patient.status = "Completed"
                
                session.commit()
                
                st.success(f"✅ Contact logged for {patient.name}!")
                st.balloons()
                st.rerun()
        
        st.markdown("---")
        
        # Complete contact history
        st.subheader("📞 Complete Contact History")
        
        session = get_session()
        contacts = session.query(Contact).filter(
            Contact.patient_id == patient.id
        ).order_by(Contact.timestamp.desc()).all()
        
        if contacts:
            st.write(f"**Total Contact Attempts:** {len(contacts)}")
            st.markdown("---")
            
            for contact in contacts:
                with st.expander(f"{contact.timestamp.strftime('%m/%d/%Y %I:%M %p')} - {contact.method} - {contact.outcome}"):
                    st.write(f"**Method:** {contact.method}")
                    st.write(f"**Outcome:** {contact.outcome}")
                    st.write(f"**Contact By:** {contact.user}")
                    st.write(f"**Role:** {contact.role}")
                    if contact.notes:
                        st.write(f"**Notes:** {contact.notes}")
        else:
            st.info("No contact history for this patient")

# TAB 5: Settings
with tab5:
    st.header("⚙️ Settings & Administration")
    
    st.markdown("---")
    
    # Database Statistics
    st.subheader("📊 Database Statistics")
    
    session = get_session()
    patients = get_all_patients(session)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Patients", len(patients))
    
    with col2:
        contacts_count = session.query(Contact).count()
        st.metric("Total Contact Logs", contacts_count)
    
    with col3:
        family_hx = len([p for p in patients if p.family_history_crc])
        st.metric("Family History CRC", family_hx)
    
    with col4:
        transport_barriers = len([p for p in patients if p.transportation_barrier])
        st.metric("Transportation Barriers", transport_barriers)
    
    st.markdown("---")
    
    # Add New Patient
    st.subheader("➕ Add New Patient")
    
    # Check if we just added a patient
    if 'patient_added' not in st.session_state:
        st.session_state.patient_added = False
    
    if st.session_state.patient_added:
        st.success(f"✅ Successfully added patient!")
        st.balloons()
        st.session_state.patient_added = False
        st.rerun()
    
    with st.form("add_patient_form", clear_on_submit=True):
        st.write("Enter patient information:")
        
        form_col1, form_col2 = st.columns(2)
        
        with form_col1:
            new_name = st.text_input("Full Name *", placeholder="John Smith")
            new_dob = st.date_input("Date of Birth *", value=date(1970, 1, 1))
            new_village = st.selectbox("Village *", [
                'Kotzebue', 'Kivalina', 'Noatak', 'Point Hope', 'Kiana',
                'Noorvik', 'Selawik', 'Ambler', 'Shungnak', 'Kobuk', 
                'Deering', 'Buckland'
            ])
            new_phone = st.text_input("Phone", placeholder="907-555-1234")
            new_language = st.selectbox("Language", ['English', 'Iñupiaq', 'Other'])
        
        with form_col2:
            new_mrn = st.text_input("MRN", placeholder="0012345")
            new_email = st.text_input("Email", placeholder="patient@example.com")
            new_family_hx = st.checkbox("Family History of CRC")
            new_comorbidities = st.checkbox("Major Comorbidities")
            new_transport = st.checkbox("Transportation Barrier")
            new_notes = st.text_area("Notes", placeholder="Any relevant patient notes...")
        
        st.markdown("**Screening History** (optional)")
        
        screen_col1, screen_col2 = st.columns(2)
        
        with screen_col1:
            new_last_screen_type = st.selectbox(
                "Last Screening Type",
                ['None', 'Colonoscopy', 'FIT', 'Cologuard', 'Sigmoidoscopy', 'CT Colonography']
            )
        
        with screen_col2:
            new_last_screen_date = st.date_input(
                "Last Screening Date",
                value=None,
                help="Leave blank if never screened"
            )
        
        submitted = st.form_submit_button("➕ Add Patient", use_container_width=True)
        
        if submitted:
            if not new_name:
                st.error("❌ Patient name is required!")
            else:
                from logic import calculate_age, update_patient_computed_fields
                
                # Prepare patient data
                patient_data = {
                    'mrn': new_mrn if new_mrn else f"MRN{len(patients) + 1000}",
                    'name': new_name,
                    'dob': new_dob,
                    'age': calculate_age(new_dob),
                    'village': new_village,
                    'phone': new_phone if new_phone else None,
                    'email': new_email if new_email else None,
                    'language': new_language,
                    'transportation_barrier': new_transport,
                    'last_screen_date': new_last_screen_date if new_last_screen_type != 'None' else None,
                    'last_screen_type': new_last_screen_type if new_last_screen_type != 'None' else None,
                    'family_history_crc': new_family_hx,
                    'major_comorbidities': new_comorbidities,
                    'notes': new_notes if new_notes else None
                }
                
                # Add patient
                new_patient = add_patient(session, patient_data)
                
                # Calculate computed fields
                update_patient_computed_fields(session, new_patient)
                
                # Set flag for success message
                st.session_state.patient_added = True
                st.rerun()
    
    st.markdown("---")
    
    # View Recent Contact Logs
    st.subheader("📞 Recent Contact Activity")
    
    recent_contacts = session.query(Contact).order_by(Contact.timestamp.desc()).limit(10).all()
    
    if recent_contacts:
        for contact in recent_contacts:
            patient = get_patient_by_id(session, contact.patient_id)
            with st.expander(f"{contact.timestamp.strftime('%m/%d/%Y %I:%M %p')} - {contact.method} - {contact.outcome}"):
                    st.write(f"**Method:** {contact.method}")
                    st.write(f"**Outcome:** {contact.outcome}")
                    st.write(f"**Contact By:** {contact.user}")
                    st.write(f"**Role:** {contact.role}")
                    if contact.notes:
                        st.write(f"**Notes:** {contact.notes}")
    else:
        st.info("No contact logs yet")
    
    st.markdown("---")
    
    # Administrative Actions (at bottom)
    st.subheader("🔧 Administrative Actions")
    
    admin_col1, admin_col2 = st.columns(2)
    
    with admin_col1:
        st.markdown("#### 🔄 Refresh Patient Data")
        st.write("Recalculate next due dates and status for all patients based on current screening guidelines.")
        
        if st.button("🔄 Refresh All Patient Data", use_container_width=True):
            from logic import update_patient_computed_fields
            
            with st.spinner("Updating patient data..."):
                for patient in patients:
                    update_patient_computed_fields(session, patient)
            
            st.success(f"✅ Successfully updated {len(patients)} patients!")
            st.balloons()
            st.rerun()
    
    with admin_col2:
        st.markdown("#### 📥 Export Full Database")
        st.write("Download complete patient database as CSV file.")
        
        # Prepare export data
        export_data = []
        for p in patients:
            export_data.append({
                'MRN': p.mrn,
                'Name': p.name,
                'DOB': p.dob,
                'Age': p.age,
                'Village': p.village,
                'Phone': p.phone,
                'Email': p.email,
                'Language': p.language,
                'Transportation Barrier': p.transportation_barrier,
                'Last Screen Date': p.last_screen_date,
                'Last Screen Type': p.last_screen_type,
                'Next Due Date': p.next_due_date,
                'Status': p.status,
                'Family History CRC': p.family_history_crc,
                'Major Comorbidities': p.major_comorbidities,
                'Notes': p.notes
            })
        
        export_df = pd.DataFrame(export_data)
        csv = export_df.to_csv(index=False)
        
        st.download_button(
            label="📥 Download Full Database (CSV)",
            data=csv,
            file_name=f"crc_patients_full_{date.today()}.csv",
            mime="text/csv",
            use_container_width=True
        )
    
    st.markdown("---")
    
    # Database Reset (at very bottom)
    st.subheader("⚠️ Database Reset")
    
    with st.expander("🗑️ Reset Database (Demo Data)", expanded=False):
        st.warning("**Warning:** This will delete all data and regenerate demo patients.")
        
        confirm = st.checkbox("Yes, I want to reset the database")
        
        if confirm:
            if st.button("⚠️ CONFIRM RESET", type="primary", use_container_width=True):
                # Delete all data
                session.query(Contact).delete()
                session.query(Patient).delete()
                session.commit()
                
                # Re-run init script
                from init_db import main as init_main
                init_main()
                
                st.success("✅ Database reset complete!")
                st.rerun()
                
                st.markdown("---")
    
    st.subheader("❓ Help & Documentation")
    
    with st.expander("📖 How to Use This Tool"):
        st.markdown("""
        ### Getting Started
        1. **Dashboard** - View all patients and program statistics
        2. **Daily Outreach** - See prioritized list of patients to contact today
        3. **Patient Details** - View complete patient information and history
        4. **Settings** - Add patients, export data, manage system
        
        ### Best Practices
        - Start each day in the **Daily Outreach** tab
        - Work from highest priority (🔴) to lowest (🟡)
        - Log every contact attempt for accurate tracking
        - Use filters to focus on specific villages or risk groups
        
        ### Screening Guidelines
        - **Colonoscopy**: Every 10 years (standard) or 5 years (family history of CRC)
        - **FIT Test**: Annually
        - **Cologuard**: Every 3 years
        - **Target Age**: 45-75 years old
        
        ### Risk Factors
        - **Family History of CRC**: Increases screening frequency
        - **Major Comorbidities**: May require special considerations for screening
        
        ### Support
        For questions or issues, contact: [support@example.com](mailto:support@example.com)
        """)
# Footer
st.sidebar.markdown("---")
st.sidebar.markdown("### About")
st.sidebar.info("""
**CRC Screening Navigator**  
Version 1.0 MVP  

Designed for Maniilaq Health Center  
Colorectal Cancer Screening Program

Built to improve screening rates and  
patient outreach in rural Alaska.
""")

st.sidebar.markdown("---")
st.sidebar.caption("💡 Tip: Start by selecting a patient from the Dashboard")