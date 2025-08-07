import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    print("Warning: GROQ_API_KEY not found in .env file. AI features will be disabled.")
    client = None
else:
    try:
        client = Groq(api_key=GROQ_API_KEY)
    except Exception as e:
        print(f"Error initializing Groq client: {e}")
        client = None

def get_ai_insights(project_name, kloc, cocomo_mode, effort_pm, duration_m, total_cost, roles_data_str):
    if not client:
        return "AI client not initialized. Please ensure your GROQ_API_KEY is correctly set in the .env file." 

    prompt = f"""
    You are an expert Software Project Management consultant and Cost Estimator.
    Analyze the following software project details (all costs are in Indian Rupees (₹)):

    Project Name: {project_name}
    Estimated KLOC (Kilo Lines of Code): {kloc}
    COCOMO Model Used: {cocomo_mode}
    Original COCOMO Estimated Effort: {effort_pm} Person-Months
    Original COCOMO Estimated Duration: {duration_m} Months
    Original Calculated Total Cost (including contingency): ₹{total_cost:,.2f}
    Current Team Composition and Rates (in ₹):
    {roles_data_str}

    Please provide a detailed analysis with the following sections, formatted clearly using Markdown (all monetary values should be in Indian Rupees (₹)):

    1.  **Explanation of Original Cost Drivers:**
        *   Briefly explain the main factors contributing to the *original estimated cost* based on the inputs (KLOC, COCOMO model, team size, rates, duration).

    2.  **Cost and Time Optimization Suggestions:**
        *   Offer 2-3 specific, actionable suggestions to potentially reduce costs or improve efficiency without significantly compromising quality.
        *   For each suggestion, elaborate on:
            *   **How it could be implemented** (e.g., adjusting team composition, phasing, technology choices, process improvements).
            *   **Potential impact on team size/structure** (e.g., "could reduce the number of X roles by Y").
            *   **Estimated quantitative impact (in ₹):**
                *   **Approximate New Total Cost:** Estimate the new total project cost if this optimization is applied (e.g., "New estimated cost: ₹X, saving approx. ₹Y or Z%").
                *   **Approximate New Duration:** Estimate the new project duration if this optimization is applied (e.g., "New estimated duration: A months, saving B months").
        *   Base your quantitative estimates on reasonable assumptions and clearly state them if necessary.

    3.  **Overall Optimized Scenario (Hypothetical):**
        *   If a combination of your best suggestions were applied, provide a hypothetical *overall optimized* project estimate.
        *   **Approximate Overall Optimized Cost:** ₹ [Your Estimate]
        *   **Approximate Overall Optimized Duration:** [Your Estimate] Months
        *   Briefly justify how you arrived at this combined estimate.

    4.  **Potential Risks & Mitigation (Brief):**
        *   Identify 1-2 key potential risks for a project of this nature.
        *   Suggest a brief mitigation strategy for each risk.

    Ensure your response is professional, well-structured, and uses Markdown for bold headings and bullet points.
    Be clear about assumptions made for quantitative estimates. All costs should be in Indian Rupees (₹).
    Example for one optimization suggestion's quantitative impact:
    *   **Suggestion:** Optimize QA Team Allocation
        *   **Implementation:** Delay full QA team onboarding until 1 month before User Acceptance Testing.
        *   **Team Impact:** Reduces active QA members from 2 to 1 for the first 3 months.
        *   **Estimated quantitative impact (in ₹):**
            *   **Approximate New Total Cost:** If original was ₹1,000,000, this might lead to a new cost of ₹950,000 (saving approx. ₹50,000 or 5%). (Assuming QA rate is ₹X/hr, 1 QA less for Y months).
            *   **Approximate New Duration:** May slightly shift internal milestones but overall project duration of {duration_m} months could remain similar or reduce by 0.5 months if development is efficient.
    """

    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            model="llama3-8b-8192", 
            temperature=0.5, 
            max_tokens=1500, 
        )
        response_content = chat_completion.choices[0].message.content
        return response_content
    
    except Exception as e:
        print(f"Error calling Groq API: {e}")
        return f"Error generating AI insights due to an API issue: {str(e)}. Please check the console for more details."