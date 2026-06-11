# Implementation Plan - Enhancements and Access Control

This plan details the proposed updates to address the user requests:
1. **Fix Patient Discharge**: Ensure the reason for discharge is rendered, and make the discharge action accessible for all admitted/transferred patients.
2. **Clinical Readmission Flow**: Allow readmitting previously discharged patients by reusing their hospital ID and updating their clinical/admission details.
3. **Average Length of Stay (ALOS) & History Statistics**: Render the calculated stays statistics on the patient history page and improve calculation accuracy.
4. **Ward-Level Access Restriction**: Restrict Ward-level users (Nurses, Sisters in Charge) to only see and access patients, wards, admissions, transfers, and reports associated with their assigned ward.

---

## Proposed Changes

### 1. Database Model (`app/models/models.py`)

#### [MODIFY] [models.py](file:///home/ellie/Documents/Workspace/Projects/Python/ich-wards/app/models/models.py)
- Add a `@property` for `name` on `Patient` model that returns `f"{self.surname}, {self.first_names}"`. This avoids `AttributeError` on existing templates and reports.

---

### 2. Discharge Feature

#### [MODIFY] [discharge.html](file:///home/ellie/Documents/Workspace/Projects/Python/ich-wards/app/templates/patients/discharge.html)
- Render `form.discharge_type` SelectField so users can select between "Left Hospital" or "Patient Passed Away".

#### [MODIFY] [list_patients.html](file:///home/ellie/Documents/Workspace/Projects/Python/ich-wards/app/templates/patients/list_patients.html)
- Show the `Discharge` button for any patient whose status is `'Admitted'` or `'Transferred'`, if the current user has permission (Admin, CMO, Sister In Charge), regardless of whether they are in a "Discharge Ward".

#### [MODIFY] [detail.html](file:///home/ellie/Documents/Workspace/Projects/Python/ich-wards/app/templates/patients/detail.html)
- Add clinical actions ("Admit", "Transfer", "Discharge", "Readmit") to the patient details page based on the patient's state and current user's role.

---

### 3. Clinical Readmission Flow

#### [MODIFY] [forms.py](file:///home/ellie/Documents/Workspace/Projects/Python/ich-wards/app/patients/forms.py)
- Create `ReadmitPatientForm` which contains clinical fields for a new admission: `admission_datetime`, `referring_doctor_hospital`, `diagnosis`, `doctor_name`, `consultant_name`, `pharmacy_name`, and `ward`.

#### [NEW] [readmit.html](file:///home/ellie/Documents/Workspace/Projects/Python/ich-wards/app/templates/patients/readmit.html)
- Implement search screen for readmission by existing hospital ID (if not already found), and if found/passed directly, show the new admission details form.

#### [MODIFY] [routes.py](file:///home/ellie/Documents/Workspace/Projects/Python/ich-wards/app/patients/routes.py)
- Update `@patients.route('/patient/readmit')` to render search.
- Add `@patients.route('/patient/<int:patient_id>/readmit_details')` to render `ReadmitPatientForm`, update patient details, and record a new `Admission`.
- Show readmission action on patient list and details pages for discharged/deceased patients.

#### [MODIFY] [layout.html](file:///home/ellie/Documents/Workspace/Projects/Python/ich-wards/app/templates/layout.html)
- Add a sidebar link for "Readmission" under Operations.

#### [MODIFY] [register.html](file:///home/ellie/Documents/Workspace/Projects/Python/ich-wards/app/templates/patients/register.html)
- Add a helpful banner at the top informing users that if this is a readmission, they should use the "Readmit Patient" form to reuse the patient's existing hospital number.

---

### 4. Average Length of Stay & Statistics

#### [MODIFY] [routes.py](file:///home/ellie/Documents/Workspace/Projects/Python/ich-wards/app/patients/routes.py)
- Improve length of stay calculation in `patient_history` to compute fractional days using `.total_seconds() / 86400` instead of rounding down to whole days using `.days`.

#### [MODIFY] [history.html](file:///home/ellie/Documents/Workspace/Projects/Python/ich-wards/app/templates/patients/history.html)
- Display the `stats` card at the top, showing:
  - Average Length of Stay
  - Current Stay Duration (if currently admitted)
  - Total Admissions, Transfers, and Discharges

---

### 5. Access Control for Ward-level Users

#### [MODIFY] [routes.py](file:///home/ellie/Documents/Workspace/Projects/Python/ich-wards/app/patients/routes.py)
- Restrict `view_patient` and `patient_history` so that Nurses and Sisters in Charge can only view patients in their assigned ward.

#### [MODIFY] [routes.py](file:///home/ellie/Documents/Workspace/Projects/Python/ich-wards/app/wards/routes.py)
- Restrict `/wards` list view for Nurses and Sisters in Charge so they only see their assigned ward.

#### [MODIFY] [routes.py](file:///home/ellie/Documents/Workspace/Projects/Python/ich-wards/app/reports/routes.py)
- Allow `Sister In Charge` and `Nurse` roles to access `/reports`.
- Filter reporting results (Admissions, Transfers, Discharges, Patients, Wards) to only include records related to their assigned ward.
- Fix bugs in CSV export where old Patient fields (`gender`, `national_id`) were accessed, causing application crashes.

---

## Verification Plan

### Automated/Manual Tests
- Run the flask app locally and verify the following flows:
  1. Log in as an Admin:
     - Register a new patient and verify hospital ID generation (starts at 025000+).
     - Admit the patient to an admission ward.
     - Verify patient is listed as Admitted.
     - Discharge the patient (testing both "Left Hospital" and "Passed Away" options).
     - Verify the discharge record appears in the history timeline and reports.
     - Search and readmit the discharged patient using their previous hospital ID.
     - Verify the new admission details (diagnosis, doctor, ward) are saved and a second admission event is logged in the history.
     - View the patient's history page and verify the Average Length of Stay (ALOS) statistics card is displayed and calculates correctly.
     - Verify patient report export works without errors.
  2. Log in as a Sister in Charge or Nurse:
     - Verify they are restricted to seeing patients only in their own ward on the patients list and details pages.
     - Verify they can only view reports and ward details corresponding to their assigned ward.
     - Verify they cannot access patient files/histories from other wards (resulting in redirect with error message).
