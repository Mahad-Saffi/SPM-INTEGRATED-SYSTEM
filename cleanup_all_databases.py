"""
Master cleanup script - removes all data from all service databases
"""
import subprocess
import logging
import sys

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CLEANUP_SCRIPTS = [
    ("Orchestrator", "services/orchestrator/cleanup_db.py"),
    ("Atlas", "services/atlas/cleanup_db.py"),
    ("WorkPulse", "services/workpulse/cleanup_db.py"),
    ("Labs", "services/labs/cleanup_db.py"),
    ("EPR", "services/epr/cleanup_db.py"),
]


def run_cleanup(service_name, script_path):
    """Run cleanup script for a service"""
    logger.info(f"\n{'='*60}")
    logger.info(f"🔄 Cleaning {service_name} database...")
    logger.info(f"{'='*60}")
    
    try:
        result = subprocess.run(
            [sys.executable, script_path],
            capture_output=False,
            text=True
        )
        
        if result.returncode == 0:
            logger.info(f"✅ {service_name} cleanup completed")
            return True
        else:
            logger.error(f"❌ {service_name} cleanup failed")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error running {service_name} cleanup: {str(e)}")
        return False


def main():
    """Run cleanup for all services"""
    logger.info("\n" + "="*60)
    logger.info("🗑️  STARTING FULL DATABASE CLEANUP")
    logger.info("="*60)
    
    results = {}
    for service_name, script_path in CLEANUP_SCRIPTS:
        results[service_name] = run_cleanup(service_name, script_path)
    
    # Summary
    logger.info("\n" + "="*60)
    logger.info("📊 CLEANUP SUMMARY")
    logger.info("="*60)
    
    for service_name, success in results.items():
        status = "✅ SUCCESS" if success else "❌ FAILED"
        logger.info(f"{service_name}: {status}")
    
    all_success = all(results.values())
    
    if all_success:
        logger.info("\n✅ All databases cleaned successfully!")
    else:
        logger.warning("\n⚠️  Some cleanups failed. Check logs above.")
    
    logger.info("="*60 + "\n")
    
    return 0 if all_success else 1


if __name__ == "__main__":
    sys.exit(main())
