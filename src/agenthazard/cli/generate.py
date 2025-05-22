import json
import argparse
from pathlib import Path
from shutil import rmtree

from ..generator.registry import AttackSettingRegistry


def generate(args):
    """Generate attack configurations and save to JSON file"""
    # Initialize registry
    registry = AttackSettingRegistry(
        args.data_root, print_registry_summary=args.print_summary
    )

    if not args.print_summary:
        # Convert lists or None
        tasks_list = args.tasks if args.tasks else None
        difficulty_list = args.difficulty if args.difficulty else None
        action_list = args.action if args.action else None

        # Generate configurations based on provided filters
        setting_configs = registry.generate_config(
            task_name=tasks_list, difficulty=difficulty_list, action=action_list
        )

        # Create output directory if it doesn't exist
        output_dir_path = Path(args.output_dir)
        rmtree(output_dir_path, ignore_errors=True)
        output_dir_path.mkdir(parents=True, exist_ok=True)

        # Save configurations to separate JSON files for each setting
        for (difficulty_val, action_val), config in setting_configs.items():
            output_path = (
                output_dir_path / f"setting_d{difficulty_val}_a{action_val}.json"
            )
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2, ensure_ascii=False)

        task_info = (
            f"for tasks: {', '.join(args.tasks)}" if args.tasks else "for all tasks"
        )
        print(f"✅ Generated {len(setting_configs)} setting configurations {task_info}")
        for (difficulty_val, action_val), config in setting_configs.items():
            print(
                f"📝 Setting (difficulty={difficulty_val}, action={action_val}): {len(config)} task(s)"
            )
        print(f"💾 All files saved to: {output_dir_path}")


def add_generate_arguments(parser):
    """Add generate arguments to a parser"""
    parser.add_argument(
        "--tasks",
        action="append",
        help="One or more task names to generate config for",
    )
    parser.add_argument(
        "--difficulty",
        action="append",
        type=int,
        help="One or more difficulty levels to filter by",
    )
    parser.add_argument(
        "--action",
        action="append",
        help="One or more action types to filter by",
    )
    parser.add_argument(
        "--output-dir",
        "-o",
        default="output",
        help="Output directory for JSON files",
    )
    parser.add_argument(
        "--data-root",
        default="data/dynamic",
        help="Root directory containing task templates",
    )
    parser.add_argument(
        "--print-summary",
        action="store_true",
        help="Print registry summary",
    )
    return parser


def main(args=None):
    """Generate attack configurations and save to JSON file"""
    if args is None:
        parser = argparse.ArgumentParser(
            description="Generate attack configurations and save to JSON file"
        )
        parser = add_generate_arguments(parser)
        args = parser.parse_args()

    generate(args)


if __name__ == "__main__":
    main()
