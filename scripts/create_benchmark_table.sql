-- In case there is SnowSQL CLI installed, this script can be run directly to create the benchmark data table and insert initial data.
-- Create benchmark data table 
CREATE TABLE IF NOT EXISTS BENCHMARK_DATA (
    metric VARCHAR(100) NOT NULL,
    industry VARCHAR(100) DEFAULT 'email_marketing',
    industry_average FLOAT NOT NULL,
    top_quartile FLOAT NOT NULL,
    bottom_quartile FLOAT NOT NULL,
    excellent_threshold FLOAT,
    source VARCHAR(500),
    source_url VARCHAR(1000),
    updated_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
    
    PRIMARY KEY (metric, industry, updated_date)
);

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_benchmark_metric_date 
ON BENCHMARK_DATA (metric, updated_date DESC);

-- Insert initial data
INSERT INTO BENCHMARK_DATA VALUES
('open_rate', 'email_marketing', 21.5, 28.0, 15.0, 25.0, 'Mailchimp Email Marketing Benchmarks 2024', 'https://mailchimp.com/resources/email-marketing-benchmarks/', CURRENT_DATE()),
('click_rate', 'email_marketing', 2.6, 5.0, 2.0, 4.0, 'Campaign Monitor Industry Benchmarks 2024', 'https://www.campaignmonitor.com/resources/guides/', CURRENT_DATE()),
('bounce_rate', 'email_marketing', 0.7, 0.5, 2.0, 0.5, 'Litmus Email Analytics 2024', 'https://www.litmus.com/', CURRENT_DATE()),
('conversion_rate', 'email_marketing', 2.5, 5.0, 1.0, 4.0, 'Marketing Industry Report 2024', NULL, CURRENT_DATE());

SELECT * FROM BENCHMARK_DATA ORDER BY updated_date DESC;