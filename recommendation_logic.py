import requests
from config import RAPID_API_KEY, RAPID_API_HOST


def get_market_salary(job_title, location):
    url = "https://job-salary-data.p.rapidapi.com/job-salary"
    querystring = {
        "job_title": job_title,
        "location": location,
        "location_type": "CITY",
        "years_of_experience": "ALL"
    }
    headers = {
        "x-rapidapi-key": RAPID_API_KEY,
        "x-rapidapi-host": RAPID_API_HOST
    }

    try:
        response = requests.get(url, headers=headers, params=querystring)
        response.raise_for_status()  # Raises exception for 4XX/5XX status codes

        salary_data = response.json()

        # Check if response has expected structure
        if not isinstance(salary_data, dict):
            print("Unexpected response format")
            return None

        # Check status code
        if salary_data.get("status") != "OK":
            print(f"API returned non-OK status: {salary_data.get('status')}")
            return None

        # Check if data exists and is non-empty
        if not salary_data.get("data") or not isinstance(salary_data["data"], list) or len(salary_data["data"]) == 0:
            print("No salary data found for the given job title and location")
            return None

        # Validate required fields exist in first result
        salary_info = salary_data["data"][0]
        required_fields = ["median_salary", "min_salary", "max_salary", "salary_currency", "salary_period"]
        if not all(field in salary_info for field in required_fields):
            print("Response missing required salary information fields")
            return None

        # Convert to INR if needed
        if salary_info["salary_currency"] != "INR":
            # Assuming USD to INR conversion (you may want to use a real-time forex API)
            conversion_rate = 90  # Example USD to INR rate
            return {
                    "median_salary": salary_info["median_salary"] * conversion_rate,
                    "min_salary": salary_info["min_salary"] * conversion_rate,
                    "max_salary": salary_info["max_salary"] * conversion_rate,
                    "currency": "INR",
                    "period": salary_info["salary_period"]
                }

        return {
            "median_salary": salary_info["median_salary"],
            "min_salary": salary_info["min_salary"],
            "max_salary": salary_info["max_salary"],
            "currency": salary_info["salary_currency"],
            "period": salary_info["salary_period"]
        }

    except requests.exceptions.RequestException as e:
        print(f"API request failed: {str(e)}")
        return None
    except ValueError as e:
        print(f"Failed to parse JSON response: {str(e)}")
        return None
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return None


def analyze_offer(ctc, deductions, notice_period, benefits, job_title, location):
    score = 0
    recommendations = []
    pros = []
    cons = []

    # Get market salary data
    market_data = get_market_salary(job_title, location)

    # CTC Analysis with market data
    if market_data:
        if ctc > (market_data["median_salary"] * 1.1):
            score += 2
            pros.append(
                f"The offered salary (₹{ctc:,.2f}) is {((ctc / market_data['median_salary']) - 1) * 100:.1f}% "
                f"above the market median of ₹{market_data['median_salary']:,.2f}"
            )
        elif ctc < (market_data["median_salary"] * 0.85):
            score -= 2
            cons.append(
                f"The offered salary (₹{ctc:,.2f}) is {((market_data['median_salary'] / ctc) - 1) * 100:.1f}% "
                f"below the market median of ₹{market_data['median_salary']:,.2f}"
            )
            recommendations.append(
                f"Consider negotiating the salary closer to the market range: "
                f"₹{market_data['min_salary']:,.2f} - ₹{market_data['max_salary']:,.2f}"
            )

    # Deductions Analysis
    if deductions > (0.3 * ctc):
        score -= 1
        cons.append(
            f"Deductions (₹{deductions:,.2f}) represent {(deductions / ctc) * 100:.1f}% of your CTC, "
            "which is higher than the recommended maximum of 30%"
        )
        recommendations.append(
            "Request a detailed breakdown of deductions and explore if any can be reduced"
        )
    else:
        pros.append(f"Deductions are within acceptable range at {(deductions / ctc) * 100:.1f}% of CTC")

    # Notice Period Analysis
    if notice_period > 90:
        score -= 1
        cons.append(f"Notice period of {notice_period} days exceeds the standard 60-90 days")
        recommendations.append(
            "Consider negotiating a shorter notice period to maintain career flexibility"
        )
    else:
        pros.append("Notice period is within industry standard")

    # Benefits Analysis
    essential_benefits = {
        'health_insurance': 'Health Insurance',
        'retirement_plan': 'Retirement Plan',
        'paid_time_off': 'Paid Time Off'
    }

    present_benefits = [b for b in essential_benefits.keys() if b in benefits]
    missing_benefits = [essential_benefits[b] for b in essential_benefits.keys() if b not in benefits]

    if present_benefits:
        pros.append(f"Offer includes key benefits: {', '.join([essential_benefits[b] for b in present_benefits])}")

    if missing_benefits:
        score -= len(missing_benefits)
        cons.append(f"Missing important benefits: {', '.join(missing_benefits)}")
        recommendations.append(
            "Discuss the possibility of including additional benefits as part of your compensation package"
        )

    # Final Decision and Explanation
    if score >= 2:
        decision = "Accept"
        explanation = (
            "This appears to be a strong offer that exceeds market standards in several areas. "
            "The combination of competitive salary and benefits makes it an attractive package."
        )
    elif score >= -1:
        decision = "Negotiate"
        explanation = (
            "While this offer has potential, there are some areas that could be improved through negotiation. "
            "Consider discussing the points mentioned in the recommendations."
        )
    else:
        decision = "Decline"
        explanation = (
            "This offer falls significantly below market standards and may not align with your career goals. "
            "Unless there are other compelling factors, you may want to explore other opportunities."
        )

    return {
        "decision": decision,
        "explanation": explanation,
        "pros": pros,
        "cons": cons,
        "recommendations": recommendations,
        "score": score,
        "market_data": market_data
    }

