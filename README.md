# 🏥 CRC Screening Navigator

A patient outreach and tracking system for colorectal cancer (CRC) screening programs, designed for Maniilaq Health Center serving rural Alaska communities.

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![Streamlit](https://img.shields.io/badge/streamlit-1.28+-red.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

## 📋 Overview

The CRC Screening Navigator helps healthcare navigators manage and track colorectal cancer screening for patients across remote Alaska Native villages. It prioritizes outreach, tracks contact attempts, and ensures patients receive timely screening according to USPSTF guidelines.

### Key Features

- **📊 Patient Dashboard** - View all patients with filtering, sorting, and export capabilities
- **📞 Daily Outreach Queue** - Prioritized contact list with risk-based sorting
- **👤 Patient Details** - Complete patient history and contact logs
- **📈 Analytics** - Visual insights into program performance and screening rates
- **⚙️ Admin Tools** - Patient management and data export functions

## 🎯 Target Users

- Healthcare navigators
- Community health workers
- Clinic administrators
- Public health coordinators

## 🚀 Getting Started

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/YOUR-USERNAME/crc-navigator.git
   cd crc-navigator
   ```

2. **Create a virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Initialize the database**
   ```bash
   python3 init_db.py
   ```

5. **Launch the application**
   ```bash
   streamlit run app.py
   ```

The app will open in your browser at `http://localhost:8501`

## 📁 Project Structure

```
crc-navigator/
├── app.py                 # Main Streamlit application
├── models.py              # SQLAlchemy database models
├── db.py                  # Database connection and queries
├── logic.py               # Business logic and calculations
├── init_db.py             # Database initialization script
├── view_patients.py       # CLI tool for viewing patient data
├── requirements.txt       # Python dependencies
├── crc_navigator.db       # SQLite database (generated)
└── README.md             # This file
```

## 💡 Usage Guide

### Dashboard Tab
- View all patients and program statistics
- Filter by status, village, or risk level
- Sort by priority metrics
- Export filtered data to CSV
- Select a patient for detailed view

### Daily Outreach Tab
- See prioritized list of patients needing contact
- Filter by priority level and contact history
- Log contact attempts with outcomes
- Quick action buttons (complete, skip, decline)
- Export daily contact list

### Patient Details Tab
- View complete patient information
- See full screening history
- Review all contact attempts
- Track transportation barriers

### Settings Tab
- Add new patients to the system
- Export complete database
- Refresh patient calculations
- View recent activity logs

## 📊 Screening Guidelines

The system follows USPSTF colorectal cancer screening guidelines:

- **Target Age**: 45-75 years old
- **Colonoscopy**: Every 10 years (standard risk) or 5 years (high risk)
- **FIT Test**: Annually
- **Cologuard**: Every 3 years
- **Status Priorities**:
  - 🔴 High Priority: Never Screened, Critically Overdue
  - 🟠 Medium Priority: Overdue
  - 🟡 Low Priority: Due Soon (within 90 days)

## 🗄️ Database Schema

### Patient Table
- Demographics (name, DOB, MRN, village)
- Contact information (phone, email, language)
- Screening history (dates, types)
- Calculated fields (status, next due date)
- Risk factors and barriers

### Contact Table
- Contact attempts log
- Method (phone, text, in-person, etc.)
- Outcome and notes
- Timestamp and user

## 🔧 Development

### Running in Development Mode

```bash
streamlit run app.py --server.runOnSave true
```

### Database Reset (Demo Data)

```bash
python3 init_db.py
```

This creates 342 demo patients with realistic data for testing.

### View Patients via CLI

```bash
python3 view_patients.py
```

## 📦 Dependencies

- **streamlit** - Web application framework
- **pandas** - Data manipulation and analysis
- **plotly** - Interactive visualizations
- **sqlalchemy** - Database ORM
- **Faker** - Demo data generation

See `requirements.txt` for complete list with versions.

## 🌍 Alaska Native Community Context

This application is designed specifically for rural Alaska:
- Multi-village support (Kotzebue, Kivalina, Noatak, Point Hope, etc.)
- Transportation barrier tracking
- Language preferences (English, Iñupiaq)
- Remote healthcare delivery considerations

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Maniilaq Health Center
- Alaska Native communities in the Northwest Arctic Borough
- USPSTF colorectal cancer screening guidelines

## 📧 Contact

For questions or support, please open an issue on GitHub.

## 🚀 Deployment

### Streamlit Community Cloud (Free)

1. Push your code to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Sign in with GitHub
4. Deploy your app with one click

The app will be live at: `https://your-app-name.streamlit.app`

---

**Built with ❤️ for improving colorectal cancer screening rates in rural Alaska**