#!/usr/bin/env python3
"""
lemina scraper - main entry point
"""

import argparse
import logging
from core.orchestrator import Orchestrator


def setup_logging():
    """setup logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s | %(message)s',
        handlers=[
            logging.StreamHandler(),
        ]
    )


def main():
    """main entry point"""
    parser = argparse.ArgumentParser(description='lemina startup data scraper')
    parser.add_argument('--dry-run', action='store_true',
                       help='run without database writes')
    parser.add_argument('--config', type=str, default='config/scrapers.yaml',
                       help='path to config file')

    args = parser.parse_args()

    # setup logging
    setup_logging()

    # create orchestrator
    orchestrator = Orchestrator(
        config_path=args.config,
        dry_run=args.dry_run
    )

    # run pipeline
    orchestrator.run()


if __name__ == '__main__':
    main()
