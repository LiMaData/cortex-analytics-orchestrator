"""
Monthly benchmark update script
Run this to refresh benchmarks from latest research

Usage:
    python scripts/update_benchmarks.py
"""

import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from snowflake.snowpark import Session
from config.shared_config import SharedConfig
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# UPDATE THESE VALUES MONTHLY
# Research from: Mailchimp, Campaign Monitor, Litmus, HubSpot
# ============================================================================

LATEST_BENCHMARKS = {
    'open_rate': {
        'average': 21.5,
        'top_quartile': 28.0,
        'bottom_quartile': 15.0,
        'excellent_threshold': 25.0,
        'source': 'Mailchimp Email Marketing Benchmarks 2024',
        'url': 'https://mailchimp.com/resources/email-marketing-benchmarks/'
    },
    'click_rate': {
        'average': 2.6,
        'top_quartile': 5.0,
        'bottom_quartile': 2.0,
        'excellent_threshold': 4.0,
        'source': 'Campaign Monitor Industry Benchmarks 2024',
        'url': 'https://www.campaignmonitor.com/resources/guides/'
    },
    'click_to_open_rate': {
        'average': 14.3,
        'top_quartile': 20.0,
        'bottom_quartile': 10.0,
        'excellent_threshold': 18.0,
        'source': 'Email Marketing Standards 2024',
        'url': None
    },
    'bounce_rate': {
        'average': 0.7,
        'top_quartile': 0.5,
        'bottom_quartile': 2.0,
        'excellent_threshold': 0.5,
        'source': 'Litmus Email Analytics 2024',
        'url': 'https://www.litmus.com/'
    },
    'unsubscribe_rate': {
        'average': 0.2,
        'top_quartile': 0.1,
        'bottom_quartile': 0.5,
        'excellent_threshold': 0.1,
        'source': 'Industry Standards 2024',
        'url': None
    },
    'conversion_rate': {
        'average': 2.5,
        'top_quartile': 5.0,
        'bottom_quartile': 1.0,
        'excellent_threshold': 4.0,
        'source': 'Marketing Conversion Report 2024',
        'url': None
    }
}

# ============================================================================
# SCRIPT LOGIC - NO NEED TO EDIT BELOW
# ============================================================================

def update_benchmarks():
    """Update benchmark table with latest research data"""
    
    logger.info("="*80)
    logger.info("🚀 MONTHLY BENCHMARK UPDATE")
    logger.info(f"   Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("="*80)
    
    # Connect to Snowflake
    config = SharedConfig()
    session = Session.builder.configs(config.snowflake).create()
    logger.info("✅ Connected to Snowflake")
    
    # Show what will be updated
    logger.info(f"\n📋 Preparing to update {len(LATEST_BENCHMARKS)} metrics:")
    for metric in LATEST_BENCHMARKS.keys():
        logger.info(f"   • {metric}")
    
    # Confirm before proceeding
    logger.info("\n⚠️  This will insert new benchmark records.")
    logger.info("   Old records will remain for historical tracking.")
    response = input("\nProceed? (yes/no): ").strip().lower()
    
    if response != 'yes':
        logger.info("❌ Update cancelled by user")
        session.close()
        return
    
    # Insert new benchmarks
    logger.info("\n📥 Inserting benchmarks...")
    updated_count = 0
    errors = []
    
    for metric, data in LATEST_BENCHMARKS.items():
        try:
            url_value = f"'{data['url']}'" if data.get('url') else 'NULL'
            
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
                    '{metric}',
                    'email_marketing',
                    {data['average']},
                    {data['top_quartile']},
                    {data['bottom_quartile']},
                    {data.get('excellent_threshold', data['top_quartile'])},
                    '{data['source']}',
                    {url_value},
                    CURRENT_DATE()
                )
            """).collect()
            
            logger.info(f"   ✅ Updated {metric}: {data['average']}% avg")
            updated_count += 1
            
        except Exception as e:
            logger.error(f"   ❌ Failed to update {metric}: {e}")
            errors.append((metric, str(e)))
    
    # Summary
    logger.info(f"\n{'='*80}")
    logger.info("📊 UPDATE SUMMARY")
    logger.info('='*80)
    logger.info(f"   Successfully updated: {updated_count}/{len(LATEST_BENCHMARKS)} metrics")
    
    if errors:
        logger.warning(f"   Failed: {len(errors)} metrics")
        for metric, error in errors:
            logger.warning(f"      • {metric}: {error}")
    
    # Show current benchmarks in table
    logger.info(f"\n📋 CURRENT BENCHMARKS IN TABLE:")
    logger.info("="*80)
    
    recent = session.sql("""
        SELECT 
            metric,
            industry_average,
            top_quartile,
            source,
            updated_date,
            DATEDIFF(day, updated_date, CURRENT_DATE()) as age_days
        FROM BENCHMARK_DATA
        WHERE updated_date >= DATEADD(day, -7, CURRENT_DATE())
        ORDER BY metric, updated_date DESC
    """).collect()
    
    if recent:
        for row in recent:
            logger.info(f"   {row['METRIC']:20s} | Avg: {row['INDUSTRY_AVERAGE']:5.1f}% | Age: {row['AGE_DAYS']} days")
    else:
        logger.warning("   No recent benchmarks found!")
    
    logger.info("="*80)
    
    # Close connection
    session.close()
    
    logger.info("\n✅ Benchmark update complete!")
    logger.info(f"   Next update recommended: {datetime.now().replace(month=datetime.now().month+1 if datetime.now().month<12 else 1).strftime('%Y-%m-%d')}")

if __name__ == "__main__":
    update_benchmarks()