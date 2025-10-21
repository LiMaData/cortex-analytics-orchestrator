"""
Setup benchmark table in Snowflake
Run once to initialize the table structure and seed data
"""

import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from snowflake.snowpark import Session
from config.shared_config import SharedConfig
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_benchmark_table():
    """Create and populate benchmark table"""
    
    logger.info("🚀 Setting up benchmark table...")
    
    # Connect to Snowflake
    config = SharedConfig()
    session = Session.builder.configs(config.snowflake).create()
    logger.info("✅ Connected to Snowflake")
    
    # Step 1: Create table
    logger.info("\n📊 Creating BENCHMARK_DATA table...")
    
    try:
        session.sql("""
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
            )
        """).collect()
        
        logger.info("✅ Table created successfully")
        
    except Exception as e:
        logger.info(f"⚠️ Table might already exist: {e}")
    
    # Step 2: Create index
    logger.info("\n🔍 Creating index...")
    
    try:
        session.sql("""
            CREATE INDEX IF NOT EXISTS idx_benchmark_metric_date 
            ON BENCHMARK_DATA (metric, updated_date DESC)
        """).collect()
        
        logger.info("✅ Index created")
        
    except Exception as e:
        logger.warning(f"⚠️ Index creation: {e}")
    
    # Step 3: Insert seed data
    logger.info("\n📥 Inserting seed benchmarks...")
    
    seed_data = [
        {
            'metric': 'open_rate',
            'avg': 21.5,
            'top': 28.0,
            'bottom': 15.0,
            'excellent': 25.0,
            'source': 'Mailchimp Email Marketing Benchmarks 2024',
            'url': 'https://mailchimp.com/resources/email-marketing-benchmarks/'
        },
        {
            'metric': 'click_rate',
            'avg': 2.6,
            'top': 5.0,
            'bottom': 2.0,
            'excellent': 4.0,
            'source': 'Campaign Monitor Industry Benchmarks 2024',
            'url': 'https://www.campaignmonitor.com/resources/guides/'
        },
        {
            'metric': 'click_to_open_rate',
            'avg': 14.3,
            'top': 20.0,
            'bottom': 10.0,
            'excellent': 18.0,
            'source': 'Email Marketing Standards 2024',
            'url': None
        },
        {
            'metric': 'bounce_rate',
            'avg': 0.7,
            'top': 0.5,
            'bottom': 2.0,
            'excellent': 0.5,
            'source': 'Litmus Email Analytics 2024',
            'url': 'https://www.litmus.com/'
        },
        {
            'metric': 'unsubscribe_rate',
            'avg': 0.2,
            'top': 0.1,
            'bottom': 0.5,
            'excellent': 0.1,
            'source': 'Industry Standards 2024',
            'url': None
        },
        {
            'metric': 'conversion_rate',
            'avg': 2.5,
            'top': 5.0,
            'bottom': 1.0,
            'excellent': 4.0,
            'source': 'Marketing Conversion Report 2024',
            'url': None
        }
    ]
    
    inserted = 0
    for data in seed_data:
        try:
            url_value = f"'{data['url']}'" if data['url'] else 'NULL'
            
            session.sql(f"""
                INSERT INTO BENCHMARK_DATA (
                    metric,
                    industry,
                    industry_average,
                    top_quartile,
                    bottom_quartile,
                    excellent_threshold,
                    source,
                    source_url,
                    updated_date
                ) VALUES (
                    '{data['metric']}',
                    'email_marketing',
                    {data['avg']},
                    {data['top']},
                    {data['bottom']},
                    {data['excellent']},
                    '{data['source']}',
                    {url_value},
                    CURRENT_DATE()
                )
            """).collect()
            
            logger.info(f"   ✅ Inserted {data['metric']}")
            inserted += 1
            
        except Exception as e:
            logger.warning(f"   ⚠️ {data['metric']}: {e}")
    
    logger.info(f"\n✅ Inserted {inserted}/{len(seed_data)} benchmarks")
    
    # Step 4: Verify data
    logger.info("\n📋 Verifying data...")
    
    result = session.sql("""
        SELECT 
            metric,
            industry_average,
            top_quartile,
            source,
            updated_date
        FROM BENCHMARK_DATA
        ORDER BY metric
    """).collect()
    
    if result:
        logger.info(f"\n{'='*80}")
        logger.info("BENCHMARK DATA IN TABLE")
        logger.info('='*80)
        
        for row in result:
            logger.info(f"  {row['METRIC']:20s} | Avg: {row['INDUSTRY_AVERAGE']:5.1f}% | Top: {row['TOP_QUARTILE']:5.1f}%")
        
        logger.info(f"{'='*80}\n")
    else:
        logger.warning("⚠️ No data found in table")
    
    session.close()
    logger.info("✅ Setup complete!\n")

if __name__ == "__main__":
    setup_benchmark_table()