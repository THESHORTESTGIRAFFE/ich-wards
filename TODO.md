# 📋 ICH-Wards Improvement Roadmap

This document outlines planned enhancements and future features for the Hospital Ward Management System.

## 🚀 Phase 1: Clinical Enhancements
- [ ] **Clinical Observations (Vitals Tracking)**:
    - Implement `Observation` model (Temp, BP, Pulse, SpO2).
    - Create observation entry forms.
    - Add visual trend charts on patient history page.
- [ ] **Patient Triage Levels**:
    - Add priority levels (Red, Orange, Yellow, Green).
    - Color-code patient lists and dashboard highlights based on triage.

## 🏥 Phase 2: Operational Efficiency
- [ ] **Bed-Level Tracking**:
    - Move from Ward-level to specific Bed-level assignments.
    - Implement a visual "Ward Map" grid layout.
- [ ] **Waitlist Management**:
    - Allow adding patients to a waitlist when a ward is at full capacity.
    - Automatic notifications when beds become available.
- [ ] **Advanced Analytics**:
    - Calculate Average Length of Stay (ALOS).
    - Track Ward Turnover rates.
    - Export analytical reports in PDF format.

## 💻 Phase 3: UX & Performance
- [ ] **Real-time Updates**:
    - Integrate Socket.io for live dashboard updates when admissions/transfers occur.
- [ ] **AJAX Search Autocomplete**:
    - Implement instant search results for patients in the top navigation bar.
- [ ] **Mobile App Wrapper**:
    - Prepare the UI for PWA (Progressive Web App) support for tablet use in wards.

## 🛠️ Phase 4: Technical Debt & Security
- [ ] **Unit & Integration Testing**:
    - Implement comprehensive test suite using `pytest`.
- [ ] **Audit Logging**:
    - Track all user actions in a dedicated `AuditLog` table for security compliance.
- [ ] **Password Reset Workflow**:
    - Add email-based password recovery for staff.
