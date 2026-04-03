import argparse
import asyncio
import sys
from typing import Optional
from src.agent import JmAgent
from src.utils.logger import get_logger

logger = get_logger(__name__)

def create_parser() -> argparse.ArgumentParser:
    """Create and configure argument parser."""
    parser = argparse.ArgumentParser(
        description="jmAgent - Personal Claude coding assistant using AWS Bedrock"
    )

    # Global options
    parser.add_argument(
        "--model",
        choices=["haiku", "sonnet", "opus"],
        default="haiku",
        help="LLM model to use (default: haiku)"
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.2,
        help="Sampling temperature (0.0-1.0, default: 0.2)"
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=4096,
        help="Maximum output tokens (default: 4096)"
    )

    subparsers = parser.add_subparsers(dest="action", help="Action to perform")

    # generate command
    gen_parser = subparsers.add_parser("generate", help="Generate code")
    gen_parser.add_argument(
        "--prompt",
        required=True,
        help="Code generation prompt"
    )
    gen_parser.add_argument(
        "--language",
        help="Programming language"
    )
    gen_parser.add_argument(
        "--file",
        help="File path for context"
    )

    # refactor command
    ref_parser = subparsers.add_parser("refactor", help="Refactor code")
    ref_parser.add_argument(
        "--file",
        required=True,
        help="File to refactor"
    )
    ref_parser.add_argument(
        "--requirements",
        required=True,
        help="Refactoring requirements"
    )
    ref_parser.add_argument(
        "--language",
        help="Programming language"
    )

    # test command
    test_parser = subparsers.add_parser("test", help="Generate tests")
    test_parser.add_argument(
        "--file",
        required=True,
        help="File to test"
    )
    test_parser.add_argument(
        "--framework",
        default="pytest",
        choices=["pytest", "jest", "vitest"],
        help="Test framework (default: pytest)"
    )
    test_parser.add_argument(
        "--coverage",
        type=float,
        default=0.8,
        help="Target coverage (0.0-1.0, default: 0.8)"
    )

    # explain command
    exp_parser = subparsers.add_parser("explain", help="Explain code")
    exp_parser.add_argument(
        "--file",
        required=True,
        help="File to explain"
    )
    exp_parser.add_argument(
        "--language",
        help="Programming language"
    )

    # fix command
    fix_parser = subparsers.add_parser("fix", help="Fix bug in code")
    fix_parser.add_argument(
        "--file",
        required=True,
        help="File with bug"
    )
    fix_parser.add_argument(
        "--error",
        required=True,
        help="Error message"
    )
    fix_parser.add_argument(
        "--context",
        help="Additional context"
    )

    # chat command
    subparsers.add_parser("chat", help="Interactive chat mode")

    return parser

async def cmd_generate(args, agent: JmAgent) -> None:
    """Handle generate command."""
    if args.file:
        try:
            with open(args.file, "r") as f:
                context = f.read()
            prompt = f"{args.prompt}\n\nContext from {args.file}:\n{context}"
        except FileNotFoundError:
            logger.error(f"File not found: {args.file}")
            sys.exit(1)
    else:
        prompt = args.prompt

    logger.info("Generating code...")
    result = await agent.generate(
        prompt=prompt,
        language=args.language
    )

    print("\n" + "=" * 60)
    print(result.code)
    print("=" * 60)
    print(f"\nTokens used: {result.tokens_used}")

async def cmd_refactor(args, agent: JmAgent) -> None:
    """Handle refactor command."""
    try:
        with open(args.file, "r") as f:
            code = f.read()
    except FileNotFoundError:
        logger.error(f"File not found: {args.file}")
        sys.exit(1)

    logger.info(f"Refactoring {args.file}...")
    result = await agent.refactor(
        code=code,
        requirements=args.requirements,
        language=args.language
    )

    print("\n" + "=" * 60)
    print(result.code)
    print("=" * 60)
    print(f"\nTokens used: {result.tokens_used}")

async def cmd_test(args, agent: JmAgent) -> None:
    """Handle test command."""
    try:
        with open(args.file, "r") as f:
            code = f.read()
    except FileNotFoundError:
        logger.error(f"File not found: {args.file}")
        sys.exit(1)

    logger.info(f"Generating tests for {args.file}...")
    result = await agent.add_tests(
        code=code,
        test_framework=args.framework,
        target_coverage=args.coverage
    )

    print("\n" + "=" * 60)
    print(result.code)
    print("=" * 60)
    print(f"\nTokens used: {result.tokens_used}")

async def cmd_explain(args, agent: JmAgent) -> None:
    """Handle explain command."""
    try:
        with open(args.file, "r") as f:
            code = f.read()
    except FileNotFoundError:
        logger.error(f"File not found: {args.file}")
        sys.exit(1)

    logger.info(f"Explaining {args.file}...")
    result = await agent.explain(
        code=code,
        language=args.language
    )

    print("\n" + "=" * 60)
    print(result)
    print("=" * 60)

async def cmd_fix(args, agent: JmAgent) -> None:
    """Handle fix command."""
    try:
        with open(args.file, "r") as f:
            code = f.read()
    except FileNotFoundError:
        logger.error(f"File not found: {args.file}")
        sys.exit(1)

    logger.info(f"Fixing bug in {args.file}...")
    result = await agent.fix_bug(
        code=code,
        error_message=args.error,
        context=args.context
    )

    print("\n" + "=" * 60)
    print(result.code)
    print("=" * 60)
    print(f"\nTokens used: {result.tokens_used}")

async def cmd_chat(args, agent: JmAgent) -> None:
    """Handle interactive chat command."""
    print("Starting interactive chat (type 'exit' to quit)...")
    print("=" * 60)

    while True:
        try:
            user_input = input("\n> ").strip()

            if user_input.lower() in ("exit", "quit"):
                print("Goodbye!")
                break

            if not user_input:
                continue

            response = await agent.chat(user_input)
            print(f"\nAssistant: {response}")

        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            logger.error(f"Error: {str(e)}")

async def main_async(args) -> None:
    """Main async function."""
    agent = JmAgent(
        model=args.model,
        temperature=args.temperature,
        max_tokens=args.max_tokens
    )

    if args.action == "generate":
        await cmd_generate(args, agent)
    elif args.action == "refactor":
        await cmd_refactor(args, agent)
    elif args.action == "test":
        await cmd_test(args, agent)
    elif args.action == "explain":
        await cmd_explain(args, agent)
    elif args.action == "fix":
        await cmd_fix(args, agent)
    elif args.action == "chat":
        await cmd_chat(args, agent)
    else:
        print("No action specified. Use --help for usage.")

def main() -> None:
    """Entry point."""
    parser = create_parser()
    args = parser.parse_args()

    if not args.action:
        parser.print_help()
        sys.exit(0)

    try:
        asyncio.run(main_async(args))
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
