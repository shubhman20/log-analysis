import os
import tempfile
import streamlit as st
import json
import spacy
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from io import BytesIO


class ComplianceMonitor:
    def __init__(self, rule_definitions, compliance_standards):
        self.rule_definitions = rule_definitions
        self.compliance_standards = compliance_standards
        self.nlp = spacy.load("en_core_web_sm")

    def extract_entities(self, text):
        doc = self.nlp(text)
        return [ent.text for ent in doc.ents]

    def check_compliance(self, entity, rule):
        return rule in self.compliance_standards.get(entity, [])

    def _analyze_logs(self, log_file_name):
        with open(log_file_name, "r") as log_file:
            logs = [line.strip() for line in log_file.readlines()]

        compliance_results = {}

        for idx, log in enumerate(logs, start=1):
            entities = self.extract_entities(log)
            results = {}

            for entity in entities:
                if entity in self.rule_definitions:
                    rule = self.rule_definitions[entity]
                    # compliance = self.check_compliance(entity, rule)
                    results[entity] = {
                        "Rule": rule,
                        # "Compliance": compliance
                        "Compliance": True
                    }

            if not results:  # Add this check to handle cases with no entities
                results["Compliant"] = {
                "Rule": rule,
                "Compliance": False
                }

            compliance_results[f"Log {idx}"] = results

        return compliance_results
    
    def analyze_logs(self, log_file_name):
        
        # Save the uploaded file to a temporary location.
        tmp_file_path = tempfile.NamedTemporaryFile(delete=False).name
        log_file = open(tmp_file_path, "wb")
        log_file.write(log_file_name.read())
        log_file.close()

        # Analyze the logs in the temporary file.
        compliance_results = self._analyze_logs(tmp_file_path)

        # Delete the temporary file.
        os.remove(tmp_file_path)

        return compliance_results



# Function to process data and generate PDF
def process_data_and_generate_pdf(rule_definitions, compliance_standards, log_data):
    # Process data using your custom function
    monitor = ComplianceMonitor(rule_definitions, compliance_standards)
    log_compliance_results = monitor.analyze_logs(log_data)

    for log_num, results in log_compliance_results.items():
        # print(log_num + ":")
        for entity, data in results.items():
            status = "Compliant" if data["Compliance"] else "Non-compliant"
            # if data["Compliance"]:
            #     print(f" - {entity}: {status} ({data['Rule']})")
            # else:
            #     print(f" - {status} ({data['Rule']})")

    compliant_logs = []
    non_compliant_logs = []

    for log_num, results in log_compliance_results.items():
        compliant_entities = []
        non_compliant_entities = []

        for entity, data in results.items():
            status = "Compliant" if data["Compliance"] else "Non-compliant"
            if data["Compliance"]:
                log_entry = f"{entity}: {status} ({data['Rule']})"
                compliant_entities.append(log_entry)
            else:
                log_entry = f"{status} ({data['Rule']})"
                non_compliant_entities.append(log_entry)

        if compliant_entities:
            compliant_logs.append(f"{log_num}: " + "\n".join(compliant_entities))
        if non_compliant_entities:
            non_compliant_logs.append(f"{log_num}: " + "\n".join(non_compliant_entities))

    pdf_buffer = BytesIO()  # Create a BytesIO buffer to hold the PDF content
    doc = SimpleDocTemplate(pdf_buffer, pagesize=landscape(letter))  # Create a single doc instance

    elements = []

    if compliant_logs:
        compliant_table_data = [["Compliant Logs"]] + [[log] for log in compliant_logs]
        compliant_table = Table(compliant_table_data, colWidths=[700], rowHeights=20)
        compliant_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),  # Center the heading horizontally
            ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),  # Center the heading vertically
            ('ALIGN', (0, 1), (-1, -1), 'LEFT'),   # Left-align other entries
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('TOPPADDING', (0, 0), (1, 0), 6),  # Adjust top padding for vertical centering
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),  # Adjust bottom padding for vertical centering
            ('BACKGROUND', (0, 0), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        elements.append(compliant_table)

    if non_compliant_logs:
        non_compliant_table_data = [["Non-compliant Logs"]] + [[log] for log in non_compliant_logs]
        non_compliant_table = Table(non_compliant_table_data, colWidths=[700], rowHeights=20)
        non_compliant_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),  # Center the heading horizontally
            ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),  # Center the heading vertically
            ('ALIGN', (0, 1), (-1, -1), 'LEFT'),   # Left-align other entries
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('TOPPADDING', (0, 0), (1, 0), 6),  # Adjust top padding for vertical centering
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),  # Adjust bottom padding for vertical centering
            ('BACKGROUND', (0, 0), (-1, -1), colors.lightcoral),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        elements.append(non_compliant_table)

    # doc.build(elements)
    # return doc
    doc.build(elements)
    pdf_buffer.seek(0)  # Reset buffer position

    return pdf_buffer.getvalue()  # Return the binary content of the PDF


# Streamlit UI
def main():
    st.title("Log Analysis and PDF Generator")

    # Upload rule definitions JSON file
    st.subheader("Upload Rule Definitions File")
    rule_definitions_file = st.file_uploader("Upload a rule definitions file")

    # Upload compliance standards JSON file
    st.subheader("Upload Compliance Standards File")
    compliance_standards_file = st.file_uploader("Upload a compliance standards file")

    # Upload log text file
    st.subheader("Upload Log File")
    log_file = st.file_uploader("Upload a log file")

    if st.button("Process and Generate PDF"):
        if rule_definitions_file is not None and compliance_standards_file is not None and log_file is not None:
            rule_definitions = json.load(rule_definitions_file)
            compliance_standards = json.load(compliance_standards_file)

            # Process data and generate PDF
            pdf_buffer = process_data_and_generate_pdf(rule_definitions, compliance_standards, log_file)

            st.text("PDF generated. You can download it using the button below.")

            # Download PDF
            st.download_button("Download PDF", pdf_buffer, file_name="log_analysis.pdf")



if __name__ == "__main__":
    main()
