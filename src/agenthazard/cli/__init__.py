import argparse
import sys


def main():
    parser = argparse.ArgumentParser(description="AgentHazard CLI")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Generate command
    generate_parser = subparsers.add_parser(
        "generate", help="Generate attack configurations"
    )

    # Eval command
    eval_parser = subparsers.add_parser(
        "eval", help="Mobile application security evaluation tool"
    )

    command = None
    help_requested = False

    for arg in sys.argv[1:]:
        if arg == "generate" or arg == "eval":
            command = arg
        elif arg == "--help" or arg == "-h":
            help_requested = True

    if command == "generate" or (help_requested and not command):
        from .generate import add_generate_arguments

        generate_parser = add_generate_arguments(generate_parser)

    if command == "eval" or (help_requested and not command):
        from .eval import add_eval_arguments

        eval_parser = add_eval_arguments(eval_parser)

    args = parser.parse_args()

    if args.command == "generate":
        from .generate import generate

        generate(args)
    elif args.command == "eval":
        from .eval import main as eval_main

        eval_main(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
