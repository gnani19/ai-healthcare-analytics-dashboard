-- Healthcare Analytics SQL Queries

-- 1. Claims by status
SELECT claim_status, COUNT(*) AS total_claims
FROM healthcare_claims
GROUP BY claim_status;

-- 2. Denial rate by provider
SELECT
    provider_name,
    COUNT(*) AS total_claims,
    SUM(CASE WHEN claim_status = 'Denied' THEN 1 ELSE 0 END) AS denied_claims,
    ROUND(100.0 * SUM(CASE WHEN claim_status = 'Denied' THEN 1 ELSE 0 END) / COUNT(*), 2) AS denial_rate
FROM healthcare_claims
GROUP BY provider_name
ORDER BY denial_rate DESC;

-- 3. Top denial reasons
SELECT denial_reason, COUNT(*) AS denial_count
FROM healthcare_claims
WHERE claim_status = 'Denied'
GROUP BY denial_reason
ORDER BY denial_count DESC;

-- 4. Average authorization turnaround by department
SELECT department, AVG(days_to_authorization) AS avg_authorization_days
FROM healthcare_claims
WHERE prior_auth_required = 'Yes'
GROUP BY department
ORDER BY avg_authorization_days DESC;