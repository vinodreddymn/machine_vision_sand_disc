"""Clean up AI training data and optionally inspection history.

This script safely removes training datasets, metadata, and optionally
inspection records to allow for training on new parts.

Usage:
    python scripts/cleanup_ai_data.py --help
    python scripts/cleanup_ai_data.py --dataset-only
    python scripts/cleanup_ai_data.py --full (includes inspection history)
"""

from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime
from pathlib import Path

from config.settings import DATASET_DIR, OUTPUT_DIR, STORAGE_DIR
from storage.postgres import PostgresInspectionRepository


def count_directory_items(path: Path) -> int:
    """Count files in a directory tree."""
    if not path.exists():
        return 0
    return sum(1 for _ in path.rglob("*") if _.is_file())


def get_directory_size_mb(path: Path) -> float:
    """Get total size of directory in MB."""
    if not path.exists():
        return 0.0
    total = sum(f.stat().st_size for f in path.rglob("*") if f.is_file())
    return total / (1024 * 1024)


def cleanup_dataset() -> dict[str, int | float]:
    """Delete all training dataset files (good/defect images and metadata)."""
    report = {
        "good_images_deleted": 0,
        "defect_images_deleted": 0,
        "metadata_files_deleted": 0,
        "dataset_size_mb_freed": 0.0,
    }

    # Count before cleanup
    good_dir = DATASET_DIR / "good"
    defect_dir = DATASET_DIR / "defect"
    metadata_dir = DATASET_DIR / "metadata"

    report["good_images_deleted"] = count_directory_items(good_dir)
    report["defect_images_deleted"] = count_directory_items(defect_dir)
    report["metadata_files_deleted"] = count_directory_items(metadata_dir)

    total_size_before = (
        get_directory_size_mb(good_dir)
        + get_directory_size_mb(defect_dir)
        + get_directory_size_mb(metadata_dir)
    )

    # Delete dataset subdirectories
    for directory in [good_dir, defect_dir, metadata_dir]:
        if directory.exists():
            try:
                shutil.rmtree(directory)
                print(f"✓ Deleted: {directory}")
            except Exception as e:
                print(f"✗ Failed to delete {directory}: {e}")
                return report

    # Recreate empty structure for future use
    for subdir in ["good/station1", "good/station2", "defect/station1", "defect/station2", "metadata"]:
        (DATASET_DIR / subdir).mkdir(parents=True, exist_ok=True)
    print("✓ Recreated empty dataset structure")

    report["dataset_size_mb_freed"] = round(total_size_before, 2)
    return report


def cleanup_inspection_outputs() -> dict[str, int | float]:
    """Delete generated inspection output files."""
    report = {
        "passed_images_deleted": 0,
        "failed_images_deleted": 0,
        "inspection_logs_deleted": 0,
        "output_size_mb_freed": 0.0,
    }

    passed_dir = OUTPUT_DIR / "passed"
    failed_dir = OUTPUT_DIR / "failed"
    logs_dir = OUTPUT_DIR / "logs"

    report["passed_images_deleted"] = count_directory_items(passed_dir)
    report["failed_images_deleted"] = count_directory_items(failed_dir)
    report["inspection_logs_deleted"] = count_directory_items(logs_dir)

    total_size_before = (
        get_directory_size_mb(passed_dir)
        + get_directory_size_mb(failed_dir)
        + get_directory_size_mb(logs_dir)
    )

    # Delete output subdirectories (keep outputs folder itself)
    for directory in [passed_dir, failed_dir, logs_dir]:
        if directory.exists():
            try:
                shutil.rmtree(directory)
                directory.mkdir(parents=True, exist_ok=True)
                print(f"✓ Cleared: {directory}")
            except Exception as e:
                print(f"✗ Failed to clear {directory}: {e}")
                return report

    report["output_size_mb_freed"] = round(total_size_before, 2)
    return report


def cleanup_inspection_history(dsn: str) -> dict[str, int | str]:
    """Delete all inspection records from database."""
    report = {
        "inspections_deleted": 0,
        "status": "pending",
        "message": "",
    }

    try:
        repo = PostgresInspectionRepository(dsn)

        # Get count before deletion
        with repo.connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM inspection_records")
                count = cur.fetchone()[0]
                report["inspections_deleted"] = count

                # Delete all inspection records
                cur.execute("DELETE FROM inspection_records")
                conn.commit()

        report["status"] = "success"
        report["message"] = f"Deleted {count} inspection records from database"
        print(f"✓ Database cleanup: {count} inspection records deleted")

    except Exception as e:
        report["status"] = "error"
        report["message"] = str(e)
        print(f"✗ Database cleanup failed: {e}")

    return report


def generate_cleanup_report(
    dataset_report: dict,
    outputs_report: dict,
    db_report: dict | None = None,
) -> str:
    """Generate human-readable cleanup report."""
    report_lines = [
        "\n" + "=" * 60,
        "AI DATA CLEANUP REPORT",
        f"Timestamp: {datetime.now().isoformat()}",
        "=" * 60,
        "\n📦 TRAINING DATASET CLEANUP:",
        f"  • Good images deleted: {dataset_report['good_images_deleted']}",
        f"  • Defect images deleted: {dataset_report['defect_images_deleted']}",
        f"  • Metadata files deleted: {dataset_report['metadata_files_deleted']}",
        f"  • Storage freed: {dataset_report['dataset_size_mb_freed']:.2f} MB",
        "\n📂 INSPECTION OUTPUT CLEANUP:",
        f"  • Passed images deleted: {outputs_report['passed_images_deleted']}",
        f"  • Failed images deleted: {outputs_report['failed_images_deleted']}",
        f"  • Log files deleted: {outputs_report['inspection_logs_deleted']}",
        f"  • Storage freed: {outputs_report['output_size_mb_freed']:.2f} MB",
    ]

    if db_report:
        report_lines.extend([
            "\n🗄️  DATABASE CLEANUP:",
            f"  • Inspection records deleted: {db_report['inspections_deleted']}",
            f"  • Status: {db_report['status'].upper()}",
            f"  • Message: {db_report['message']}",
        ])

    total_freed = dataset_report["dataset_size_mb_freed"] + outputs_report["output_size_mb_freed"]
    report_lines.extend([
        "\n" + "=" * 60,
        f"TOTAL STORAGE FREED: {total_freed:.2f} MB",
        "=" * 60,
        "\n✅ System ready for new training data collection",
        "",
    ])

    return "\n".join(report_lines)


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Clean up AI training data and inspection history",
    )
    parser.add_argument(
        "--dataset-only",
        action="store_true",
        help="Delete only training dataset (default behavior)",
    )
    parser.add_argument(
        "--outputs-only",
        action="store_true",
        help="Delete only inspection outputs",
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="Delete dataset, outputs, AND inspection history from database",
    )
    parser.add_argument(
        "--keep-database",
        action="store_true",
        help="When used with --full, keeps inspection database intact",
    )
    parser.add_argument(
        "--confirm",
        action="store_true",
        help="Skip confirmation prompts (for automation)",
    )

    args = parser.parse_args()

    # Determine what to clean
    clean_dataset = args.dataset_only or args.full or (
        not args.outputs_only and not args.full
    )
    clean_outputs = args.outputs_only or args.full
    clean_database = args.full and not args.keep_database

    # Show what will be deleted
    print("\n🗑️  AI DATA CLEANUP UTILITY")
    print("=" * 60)
    if clean_dataset:
        print("✓ Will delete: Training dataset (good/defect images & metadata)")
    if clean_outputs:
        print("✓ Will delete: Inspection outputs (passed/failed images & logs)")
    if clean_database:
        print("✓ Will delete: Inspection records from PostgreSQL database")
    print("=" * 60)

    # Confirmation
    if not args.confirm:
        response = input("\n⚠️  This action cannot be undone. Continue? (yes/NO): ").strip().lower()
        if response != "yes":
            print("❌ Cleanup cancelled")
            return 1

    # Perform cleanup
    dataset_report = cleanup_dataset() if clean_dataset else {}
    outputs_report = cleanup_outputs() if clean_outputs else {}
    db_report = None

    if clean_database:
        from config.settings import POSTGRES_DSN
        db_report = cleanup_inspection_history(POSTGRES_DSN)

    # Generate and display report
    report = generate_cleanup_report(dataset_report, outputs_report, db_report)
    print(report)

    # Save report to file
    report_path = OUTPUT_DIR / f"cleanup_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    try:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(report)
        print(f"📄 Report saved to: {report_path}")
    except Exception as e:
        print(f"⚠️  Failed to save report: {e}")

    return 0


if __name__ == "__main__":
    exit(main())
