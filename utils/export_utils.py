import pandas as pd
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, Preformatted, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
import matplotlib.pyplot as plt
import re
from html import escape
from datetime import datetime

CURRENCY_SYMBOL = "₹" # Define currency symbol globally for this module

def df_to_excel_bytes(df_dict):
    """Exports a dictionary of DataFrames to an Excel file in memory."""
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        for sheet_name, df in df_dict.items():
            df.to_excel(writer, sheet_name=sheet_name, index=False)
    return output.getvalue()

def generate_cost_pie_chart_bytes(cost_breakdown_details):
    if not cost_breakdown_details:
        return None
    labels = []
    sizes = []
    for role, details in cost_breakdown_details.items():
        if details.get("total_role_cost", 0) > 0:
            labels.append(role)
            sizes.append(details["total_role_cost"])
    if not labels or not sizes: 
        return None
    fig, ax = plt.subplots(figsize=(6, 4)) 
    ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90, textprops={'fontsize': 8})
    ax.axis('equal')  
    plt.title("Cost Distribution by Role/Item", fontsize=10)
    img_bytes = BytesIO()
    plt.savefig(img_bytes, format='png', bbox_inches='tight', dpi=150)
    plt.close(fig) 
    img_bytes.seek(0)
    return img_bytes

def extract_optimized_scenario(ai_text):
    if not ai_text or not isinstance(ai_text, str):
        return None
    optimized_cost = None
    optimized_duration = None

    # Regex to find "Approximate Overall Optimized Cost: ₹ [Estimate]"
    cost_match = re.search(r"Approximate Overall Optimized Cost:\s*" + re.escape(CURRENCY_SYMBOL) + r"\s*([\d,]+\.?\d*)\s*(?:INR|Rupees)?", ai_text, re.IGNORECASE)
    if cost_match:
        optimized_cost = cost_match.group(1)

    duration_match = re.search(r"Approximate Overall Optimized Duration:\s*([\d\.]+\s*Months?)", ai_text, re.IGNORECASE)
    if duration_match:
        optimized_duration = duration_match.group(1)
    
    if not optimized_cost and not optimized_duration: 
        overall_scenario_match = re.search(r"Overall Optimized Scenario \(Hypothetical\):(.*?)(?=(?:Potential Risks & Mitigation|##|$))", ai_text, re.IGNORECASE | re.DOTALL)
        if overall_scenario_match:
            scenario_text = overall_scenario_match.group(1)
            if not optimized_cost:
                cost_match_alt = re.search(r"Cost:\s*" + re.escape(CURRENCY_SYMBOL) + r"\s*([\d,]+\.?\d*)", scenario_text, re.IGNORECASE)
                if cost_match_alt: optimized_cost = cost_match_alt.group(1)
            if not optimized_duration:
                duration_match_alt = re.search(r"Duration:\s*([\d\.]+\s*Months?)", scenario_text, re.IGNORECASE)
                if duration_match_alt: optimized_duration = duration_match_alt.group(1)

    if optimized_cost or optimized_duration:
        return {
            "cost": optimized_cost if optimized_cost else "Not specified",
            "duration": optimized_duration if optimized_duration else "Not specified"
        }
    return None


def create_pdf_report(project_data, cocomo_results, cost_summary, cost_breakdown_df, ai_insights_raw):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter,
                            rightMargin=inch, leftMargin=inch,
                            topMargin=inch, bottomMargin=inch)
    
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='CodeSmall', parent=styles['Code'], fontSize=8, leading=9))
    styles.add(ParagraphStyle(name='RightAlign', parent=styles['Normal'], alignment=2)) 

    story = []

    current_date = datetime.now().strftime("%B %d, %Y")
    story.append(Paragraph(current_date, styles['RightAlign']))
    story.append(Spacer(1, 0.1*inch))

    story.append(Paragraph(f"Project Cost Estimation Report (Amounts in {CURRENCY_SYMBOL})", styles['h1']))
    story.append(Spacer(1, 0.2*inch))

    story.append(Paragraph("Project Inputs", styles['h2']))
    project_details_list = [
        ["Project Name:", project_data.get("name", "N/A")],
        ["KLOC (Lines of Code):", str(project_data.get("kloc", "N/A"))],
        ["COCOMO Model:", project_data.get("cocomo_mode", "N/A").capitalize()],
        ["Contingency:", f"{project_data.get('contingency', 0)}%"]
    ]
    story.append(Table(project_details_list, colWidths=[2*inch, 4*inch], style=TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
    ])))
    story.append(Spacer(1, 0.1*inch)) 

    team_composition = project_data.get("roles_data", [])
    if team_composition:
        story.append(Paragraph("Team Composition (Original Estimate)", styles['h3']))
        team_details_list = []
        for role in team_composition:
            rate_val = role.get('rate_ph', 'N/A')
            if isinstance(rate_val, (int,float)):
                rate_display = f"{CURRENCY_SYMBOL}{rate_val:,.2f}"
            else:
                rate_display = f"{CURRENCY_SYMBOL}{rate_val}"

            team_details_list.append([f"- {role.get('role_name', 'Unknown Role')}", 
                                      f"Count: {role.get('count', 'N/A')}", 
                                      f"Rate/hr: {rate_display}"])
        story.append(Table(team_details_list, colWidths=[2*inch, 1.5*inch, 2.5*inch], style=TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ])))
    story.append(Spacer(1, 0.2*inch))

    story.append(Paragraph("COCOMO Estimation (Original)", styles['h2']))
    cocomo_data = [
        ["Estimated Effort:", f"{cocomo_results.get('effort_pm', 'N/A')} Person-Months"],
        ["Estimated Duration:", f"{cocomo_results.get('duration_m', 'N/A')} Months"],
    ]
    cocomo_table = Table(cocomo_data, colWidths=[2*inch, 4*inch])
    cocomo_table.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
    ]))
    story.append(cocomo_table)
    story.append(Spacer(1, 0.2*inch))

    story.append(Paragraph(f"Cost Summary (Original, in {CURRENCY_SYMBOL})", styles['h2']))
    cost_data = [
        ["Subtotal (without Contingency):", f"{CURRENCY_SYMBOL}{cost_summary.get('subtotal', 0):,.2f}"],
        ["Total Cost (with Contingency):", f"{CURRENCY_SYMBOL}{cost_summary.get('total_with_contingency', 0):,.2f}"],
    ]
    cost_summary_table = Table(cost_data, colWidths=[2.5*inch, 3.5*inch])
    cost_summary_table.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
        ('FONTNAME', (0,1), (0,1), 'Helvetica-Bold'), 
        ('TEXTCOLOR', (0,1), (1,1), colors.red),      
        ('ALIGN', (1,0), (1,-1), 'RIGHT'),
    ]))
    story.append(cost_summary_table)
    story.append(Spacer(1, 0.1*inch))

    optimized_scenario = extract_optimized_scenario(ai_insights_raw if isinstance(ai_insights_raw, str) else "")
    if optimized_scenario:
        story.append(HRFlowable(width="100%", thickness=1, color=colors.black))
        story.append(Paragraph(f"AI Hypothetical Optimized Scenario Summary (in {CURRENCY_SYMBOL})", styles['h2']))
        optimized_data = []
        cost_val_opt = optimized_scenario.get("cost")
        if cost_val_opt and cost_val_opt != "Not specified":
            # AI should provide the symbol, but we add it if missing or ensure it's there
            if CURRENCY_SYMBOL not in cost_val_opt:
                optimized_data.append(["Approx. Optimized Cost:", f"{CURRENCY_SYMBOL}{cost_val_opt}"])
            else: # Assume AI included it correctly
                optimized_data.append(["Approx. Optimized Cost:", cost_val_opt])
        else:
             optimized_data.append(["Approx. Optimized Cost:", "Not specified by AI"])

        if optimized_scenario.get("duration"):
            optimized_data.append(["Approx. Optimized Duration:", optimized_scenario['duration']])
        
        if optimized_data:
            optimized_table = Table(optimized_data, colWidths=[2.5*inch, 3.5*inch])
            optimized_table.setStyle(TableStyle([
                ('GRID', (0,0), (-1,-1), 0.5, colors.darkseagreen), 
                ('FONTNAME', (0,0), (-1,-1), 'Helvetica-Bold'),
                ('TEXTCOLOR', (0,0), (-1,-1), colors.darkgreen),
                ('ALIGN', (1,0), (1,-1), 'RIGHT'),
            ]))
            story.append(optimized_table)
        else:
            story.append(Paragraph("Optimized scenario details not clearly extractable from AI response.", styles['Normal']))
        story.append(Spacer(1, 0.2*inch))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.black)) 

    chart_bytes = generate_cost_pie_chart_bytes(cost_summary.get('breakdown_details', {}))
    if chart_bytes:
        story.append(Paragraph("Cost Distribution (Original Estimate)", styles['h3']))
        img = Image(chart_bytes, width=5*inch, height=3.33*inch) 
        img.hAlign = 'CENTER'
        story.append(img)
        story.append(Spacer(1, 0.2*inch))

    if not cost_breakdown_df.empty:
        story.append(Paragraph(f"Detailed Cost Breakdown (Original Estimate, in {CURRENCY_SYMBOL})", styles['h3']))
        
        pdf_df_columns = ["Item/Role", "Count/Multiplier", f"Rate/hr ({CURRENCY_SYMBOL})", 
                          f"Monthly Cost ({CURRENCY_SYMBOL})", f"Total Cost ({CURRENCY_SYMBOL})"]
        
        data_list = [pdf_df_columns]

        for index, row in cost_breakdown_df.iterrows():
            # Get values from DataFrame, default to '-' or 0
            item_role = row.get(cost_breakdown_df.columns[0], "-") # Assuming first col is Item/Role
            count_multiplier = row.get(cost_breakdown_df.columns[1], "-") # Assuming second col is Count/Multiplier
            
            # Find the actual column names from the DataFrame for currency values
            # This assumes the df from Estimator.py has column names like "Rate/hr or Factor (₹)"
            rate_val = row.get(cost_breakdown_df.columns[2], 0) 
            monthly_val = row.get(cost_breakdown_df.columns[3], 0) 
            total_val = row.get(cost_breakdown_df.columns[4], 0) 

            new_row_data = [item_role, count_multiplier, rate_val, monthly_val, total_val]
            data_list.append(new_row_data)

        # Format currency in data_list
        for i_row, row_val_list in enumerate(data_list):
            if i_row > 0: # Skip header row
                for i_col in [2, 3, 4]: # Indices for Rate, Monthly Cost, Total Cost
                    cell_content = row_val_list[i_col]
                    if isinstance(cell_content, (int, float)):
                        data_list[i_row][i_col] = f"{CURRENCY_SYMBOL}{cell_content:,.2f}"
                    elif isinstance(cell_content, str):
                        # If it's a string that might already be formatted or just a number string
                        try:
                            # Remove existing currency symbol (if any) and commas for clean conversion
                            cleaned_str = cell_content.replace(CURRENCY_SYMBOL, "").replace(",", "")
                            num_val = float(cleaned_str)
                            data_list[i_row][i_col] = f"{CURRENCY_SYMBOL}{num_val:,.2f}"
                        except ValueError:
                             # If conversion fails, and it's not just '-', display as is or with symbol if it's a number
                            if cell_content != '-' and cell_content.replace('.', '', 1).isdigit():
                                data_list[i_row][i_col] = f"{CURRENCY_SYMBOL}{cell_content}"
                            else:
                                data_list[i_row][i_col] = cell_content # e.g., '-' or 'N/A'

        breakdown_table = Table(data_list, hAlign='LEFT')
        breakdown_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.grey),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0,0), (-1,0), 12),
            ('BACKGROUND', (0,1), (-1,-1), colors.beige),
            ('GRID', (0,0), (-1,-1), 1, colors.black),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ]))
        story.append(breakdown_table)
    story.append(Spacer(1, 0.2*inch))

    if ai_insights_raw and isinstance(ai_insights_raw, str):
        story.append(Paragraph(f"AI-Enhanced Insights (Detailed Analysis, amounts in {CURRENCY_SYMBOL})", styles['h2']))
        
        processed_text = escape(ai_insights_raw) 
        processed_text = processed_text.replace("\n", "<br/>")
        # Ensure AI's ₹ symbols are preserved by not over-escaping them
        # The AI prompt now asks for ₹, so we expect it in the raw text.
        # The html.escape handles <, >, & correctly.
        
        # Regex for bold, headings, lists, etc. remain the same as they don't interfere with ₹
        processed_text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', processed_text)
        processed_text = re.sub(r'^### (.*?)<br/>', r'<b><i>\1</i></b><br/>', processed_text, flags=re.MULTILINE) 
        processed_text = re.sub(r'^## (.*?)<br/>', r'<b>\1</b><br/>', processed_text, flags=re.MULTILINE) 
        processed_text = re.sub(r'^(?:\*|-)\s*(.*?)<br/>', r'• \1<br/>', processed_text, flags=re.MULTILINE)
        processed_text = re.sub(r'<br/>(?:\*|-)\s*(.*?)<br/>', r'<br/>• \1<br/>', processed_text, flags=re.MULTILINE)
        processed_text = re.sub(r'^(\d+\.)\s*(.*?)<br/>', r'\1 \2<br/>', processed_text, flags=re.MULTILINE)
        processed_text = re.sub(r'<br/>(\d+\.)\s*(.*?)<br/>', r'<br/>\1 \2<br/>', processed_text, flags=re.MULTILINE)
        processed_text = re.sub(r'^\s*---\s*<br/>', '<br/>-----------------------------------<br/>', processed_text, flags=re.MULTILINE)
        processed_text = re.sub(r'^\s*===\s*<br/>', '<br/>===================================<br/>', processed_text, flags=re.MULTILINE)
        processed_text = re.sub(r'```(.*?)```', r'<font name="Courier">\1</font>', processed_text, flags=re.DOTALL)
        if processed_text.endswith("<br/>"):
            processed_text = processed_text[:-5]
        try:
            story.append(Paragraph(processed_text, styles['Normal']))
        except Exception as e_para:
            print(f"Error creating Paragraph for AI insights: {e_para}")
            story.append(Paragraph("<b>AI-Enhanced Insights (Error in Formatting)</b>", styles['h2']))
            story.append(Paragraph(f"Could not fully format AI insights for PDF due to: {str(e_para)}. Displaying as preformatted text:", styles['Normal']))
            story.append(Spacer(1, 0.1*inch))
            story.append(Preformatted(ai_insights_raw, styles['CodeSmall'])) 
    elif ai_insights_raw: 
        story.append(Paragraph("AI-Enhanced Insights", styles['h2']))
        story.append(Paragraph(str(ai_insights_raw), styles['Normal'])) 
    else:
        story.append(Paragraph("AI-Enhanced Insights", styles['h2']))
        story.append(Paragraph("No AI insights were generated or provided.", styles['Normal']))

    try:
        doc.build(story)
        pdf_bytes = buffer.getvalue()
    except Exception as e_build:
        print(f"Error building PDF document: {e_build}")
        buffer = BytesIO()
        doc_error = SimpleDocTemplate(buffer, pagesize=letter)
        story_error = [Paragraph("Error Generating PDF", styles['h1']),
                       Paragraph(f"An error occurred while building the PDF: {str(e_build)}", styles['Normal'])]
        if ai_insights_raw and isinstance(ai_insights_raw, str): 
            story_error.append(Spacer(1,0.2*inch))
            story_error.append(Paragraph("Raw AI Insights (for debugging):", styles['h3']))
            story_error.append(Preformatted(ai_insights_raw, styles['CodeSmall']))
        doc_error.build(story_error)
        pdf_bytes = buffer.getvalue()
    finally:
        buffer.close()
        
    return pdf_bytes