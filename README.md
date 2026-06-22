# 🏥 Hospital Ward Management System

A modern, professional Hospital Ward Management System built with Flask and Vanilla CSS. Designed for clarity, efficiency, and clinical reliability.

![Modern Dashboard](https://img.shields.io/badge/UI-Modern-blue)
![Backend](https://img.shields.io/badge/Backend-Flask-green)
![Database](https://img.shields.io/badge/Database-SQLite-lightgrey)

---

## 🚀 Key Features

### 📊 Modern Analytics Dashboard
- **7-Day Activity Trends**: Visual line charts showing admission vs. discharge patterns using Chart.js.
- **Ward Occupancy**: Real-time visualization of ward capacity with color-coded alerts (Green/Amber/Red).
- **Quick Stats**: At-a-glance metrics for total patients, daily admissions, transfers, and discharges.

### 👥 Comprehensive Patient Management
- **Advanced Search**: Find patients instantly by Name or National ID.
- **Dynamic Filtering**: Filter patient lists by status (Registered, Admitted, Transferred, Discharged).
- **Movement History**: Detailed chronological timeline for every patient, tracking every ward movement and staff interaction.
- **Soft Deletion**: Securely remove records without losing historical audit data.

### 🏥 Ward & Operations Control
- **Capacity Enforcement**: Intelligent validation blocks admissions or transfers to wards that are at full capacity.
- **Role-Based Access**: Granular control for Admin, CMO, and Executive roles.
- **Transfer Workflow**: Streamlined internal movement tracking between specialized wards.

### 📄 Professional Reporting & Export
- **CSV Export**: Download filtered admission, transfer, and discharge reports for offline analysis.
- **Print Optimization**: High-quality, hard-copy ready layouts for medical records, with navigation elements automatically hidden.

### 🌗 User Experience
- **Dark Mode**: Eye-friendly dark theme with persistence across sessions.
- **Responsive Design**: Fully mobile-first architecture that works perfectly on tablets and smartphones.
- **Modern UI**: Custom-built healthcare-themed design system with smooth animations and intuitive navigation.

---

## 🛠️ Technology Stack

- **Backend**: Python 3.x, Flask
- **Database**: SQLite (SQLAlchemy ORM)
- **Frontend**: Vanilla HTML5, CSS3 (Modern Flexbox/Grid), Vanilla JS
- **Visuals**: Chart.js, Font Awesome
- **Migrations**: Flask-Migrate

---

## ⚙️ Installation

### 1. Clone the repository
```bash
git clone https://github.com/THESHORTESTGIRAFFE/ich-wards.git
cd ich-wards
```

### 2. Set up virtual environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure environment
Create a `.env` file from the template:
```bash
cp .env.template .env
```
Edit `.env` and set a secure `SECRET_KEY`.

### 5. Initialize Database
```bash
flask db upgrade
python seed.py  # Optional: Seed initial wards and admin user
```

### 6. Run Application
```bash
python run.py
```
Visit `http://localhost:5000` in your browser.

---

## 🧭 Navigation Structure

- **📊 Dashboard**: High-level overview and ward occupancy.
- **👥 Patient Management**:
    - **Patients List**: Search, Filter, History, and CRUD operations.
    - **Register Patient**: onboarding new clinical records.
- **⚙️ Operations**: Specialized routes for Admission, Transfer, and Discharge.
- **🏥 Administration**:
    - **Wards**: Manage facility capacity and ward types.
    - **Reports**: Advanced data extraction and CSV exporting.
    - **User Management**: (Admin Only) Maintain staff accounts and roles.

---

## 🎨 Design System

| Element | Light Color | Dark Color | Usage |
|---------|-------------|------------|-------|
| **Primary** | `#0369a1` | `#0ea5e9` | Main Branding & Actions |
| **Success** | `#16a34a` | `#22c55e` | Admitted, Completed |
| **Warning** | `#f59e0b` | `#fbbf24` | Transfers, Pending |
| **Danger** | `#dc2626` | `#f87171` | Discharge, High Risk |

---

## 📜 License
This project is licensed under the MIT License - see the LICENSE file for details.

---

## 📚 Documentation & Roadmap

- **[User Manual](docs/USER_MANUAL.md)**: Comprehensive guide for staff and administrators.
- **[Future Roadmap](TODO.md)**: Planned features and technical improvements.

---

**Developed with ❤️ for Modern Healthcare.**
