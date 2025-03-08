from loanObjects import LtvScoreEnum

def get_loan_to_value(loan_amount: float, property_value: float)->float:
    return (loan_amount/property_value)*100


def get_loan_value_score(ltv : float)->LtvScoreEnum:
    """
        LTV ≤ 60% → Excellent (Low risk)
        60% < LTV ≤ 80% → Good (Moderate risk)
        80% < LTV ≤ 90% → Fair (Higher risk)
        LTV > 90% → Risky (Very high risk, less likely to be approved)
    """
    if ltv <= 60:
        return LtvScoreEnum.excellent
    if ltv <= 80:
        return LtvScoreEnum.good
    if ltv <= 90:
        return LtvScoreEnum.fair
    return LtvScoreEnum.risky
 
 