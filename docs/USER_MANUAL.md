# 📖 ICH-Wards User Manual

Welcome to the **ICH-Wards Hospital Ward Management System**. This manual provides comprehensive guidance on how to use the system effectively to manage patient flow, ward capacity, and clinical reporting.

---

## 📑 Table of Contents
1. [Introduction](#1-introduction)
2. [Getting Started](#2-getting-started)
3. [Dashboard & Analytics](#3-dashboard--analytics)
4. [Patient Management](#4-patient-management)
5. [Clinical Operations](#5-clinical-operations)
   - [Admission](#admission)
   - [Transfer](#transfer)
   - [Discharge](#discharge)
6. [Reports & Administration](#6-reports--administration)
7. [UI Customization (Dark Mode)](#7-ui-customization)

---

## 1. Introduction
ICH-Wards is a modern web-based platform designed to streamline hospital operations. It focuses on tracking patient movements between specialized wards, enforcing capacity limits, and providing real-time data to clinical managers.

## 2. Getting Started
### Accessing the System
1. Open your browser and navigate to the system URL.
2. Log in using your assigned **Email** and **Password**.
3. Your access levels (Admin, CMO, Sister In Charge, Nurse) determine which features you can see and use.

### Role-Based Access
- **Admin**: Full system control, user management, and data deletion.
- **CMO / Executive**: High-level reporting and ward oversight.
- **Sister In Charge**: Manage specific ward transfers and admissions.
- **Nurse**: Perform admissions and view patient history.

## 3. Dashboard & Analytics
The Dashboard is your command center. It provides:
- **Key Metrics**: Total active patients, today's admissions, transfers, and discharges.
- **Ward Occupancy**: A real-time table showing how full each ward is.
  - 🟢 **Green**: Plenty of space.
  - 🟡 **Amber**: Nearing capacity (70%+).
  - 🔴 **Red**: Critically full (90%+).
- **Activity Trends**: A 7-day chart showing the flow of patients into and out of the facility.

## 4. Patient Management
### Registering a New Patient
Before a patient can be admitted, they must be registered in the system.
1. Navigate to **Patient Management > Register Patient**.
2. Enter Name, Age, Gender, and National/Hospital ID.
3. Click **Register Patient**.

### Searching for Patients
Use the **Patients List** to find any record.
- Search by **Name** or **National ID**.
- Filter by **Status** (Admitted, Registered, Discharged).

## 5. Clinical Operations
### Admission
Admissions are only allowed into wards designated as **"Admission"** types.
1. Find a "Registered" patient in the list.
2. Click **Admit**.
3. Select the target Admission Ward.
4. If the ward is full, the system will block the admission until space is cleared.

### Transfer
Moving patients between specialized wards (e.g., from Admission to General).
1. Click **Transfer** on an admitted patient's card.
2. Select the destination ward.
3. The system will record the history of this move for audit purposes.

### Discharge
Finalizing a patient's stay.
1. **Note**: Patients must usually be moved to a "Discharge Ward" before final exit.
2. Click **Discharge**.
3. Add clinical notes summarizing the stay.
4. Once discharged, the patient's bed is immediately marked as available.

## 6. Reports & Administration
### Generating Reports
1. Navigate to **Administration > Reports**.
2. Select the report type (Admissions, Transfers, or Discharges).
3. Set your date range.
4. Click **Export CSV** to download a spreadsheet for administrative meetings.

### Managing Wards (Admin Only)
Administrators can update ward names, types, and capacities under **Administration > Wards**.

## 7. UI Customization
### Dark Mode
For night shifts or reduced eye strain, click the **Moon Icon** in the top navigation bar to toggle Dark Mode. This preference is saved to your browser and will persist across sessions.

### Printing
All lists and reports are optimized for printing. Simply press `Ctrl + P`. The system will automatically hide navigation sidebars and top bars to provide a clean, professional document.

---
**Need Support?** Contact the Hospital IT Department or the System Administrator.
