--top 5 stadium_cleaned by capacity --
SELECT top 5 rank, stadium, capacity
FROM stadium_cleaned
ORDER BY capacity DESC

-- average capacity by region --
SELECT region, AVG(capacity) as avg_capacity
FROM stadium_cleaned
GROUP BY region
ORDER BY avg_capacity DESC;

--count of stadium_cleaned in each country--
SELECT country, count(country) stadium_count
FROM stadium_cleaned
GROUP BY country
ORDER BY stadium_count desc, country asc

--stadium ranking within each region--
SELECT rank, stadium, region,
    RANK() OVER(PARTITION BY region ORDER BY capacity DESC) as region_rank
FROM stadium_cleaned;

--top 3 stadium ranking within each region--
SELECT rank, stadium, region, capacity, region_rank
FROM (
    SELECT rank, stadium, region, capacity,
           RANK() OVER (PARTITION BY region ORDER BY capacity DESC) as region_rank
    FROM stadium_cleaned
) ranked_stadium_cleaned
WHERE region_rank <= 3;

-- stadium_cleaned with capacity above average --
SELECT stadium, t2.region, capacity, avg_capacity
FROM stadium_cleaned, (SELECT region, AVG(capacity) avg_capacity FROM stadium_cleaned GROUP BY region) t2
WHERE t2.region = stadium_cleaned.region
and capacity > avg_capacity
ORDER BY region

--stadium_cleaned with the closest capacity to regional median--
WITH MedianCTE AS (
    SELECT
        region, PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY capacity) OVER (PARTITION BY region) AS median_capacity
    FROM stadium_cleaned
)
SELECT rank, stadium, region, capacity, ranked_stadium_cleaned.median_rank
FROM (
    SELECT
        s.rank, s.stadium, s.region, s.capacity,
        ROW_NUMBER() OVER (PARTITION BY s.region ORDER BY ABS(s.capacity - m.median_capacity)) AS median_rank
    FROM stadium_cleaned s JOIN MedianCTE m ON s.region = m.region
) ranked_stadium_cleaned
WHERE median_rank = 1;