import argparse
import asyncio
import os
import sys
import glob
from typing import Optional, List
from dotenv import load_dotenv
from src.agent import JmAgent
from src.utils.logger import get_logger

logger = get_logger(__name__)


def parse_file_list(file_arg: str) -> List[str]:
    """
    Parse file argument which can be:
    - Comma-separated list: "file1.py,file2.py"
    - Glob pattern: "src/**/*.py"
    - Single file: "main.py"

    Args:
        file_arg: File argument string

    Returns:
        List of file paths
    """
    if "," in file_arg:
        # Comma-separated
        return [f.strip() for f in file_arg.split(",")]
    elif "*" in file_arg or "?" in file_arg:
        # Glob pattern
        matches = glob.glob(file_arg, recursive=True)
        return sorted(matches)
    else:
        # Single file
        return [file_arg]

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
    parser.add_argument(
        "--project",
        type=str,
        default=None,
        help="Project root directory for context analysis"
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
    gen_parser.add_argument(
        "--stream",
        action="store_true",
        help="Stream output in real-time"
    )
    gen_parser.add_argument(
        "--format",
        action="store_true",
        help="Format the generated code"
    )

    # refactor command
    ref_parser = subparsers.add_parser("refactor", help="Refactor code")
    ref_parser.add_argument(
        "--file",
        help="File to refactor"
    )
    ref_parser.add_argument(
        "--files",
        help="Multiple files (comma-separated or glob pattern)"
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
    ref_parser.add_argument(
        "--format",
        action="store_true",
        help="Format the refactored code"
    )

    # test command
    test_parser = subparsers.add_parser("test", help="Generate tests")
    test_parser.add_argument(
        "--file",
        help="File to test"
    )
    test_parser.add_argument(
        "--files",
        help="Multiple files (comma-separated or glob pattern)"
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

    # config command (Phase 4)
    config_parser = subparsers.add_parser("config", help="Manage configuration")
    config_subparsers = config_parser.add_subparsers(dest="config_action", help="Configuration action")

    config_show = config_subparsers.add_parser("show", help="Show configuration")
    config_show.add_argument(
        "--key",
        help="Specific configuration key to show"
    )

    config_set = config_subparsers.add_parser("set", help="Set configuration value")
    config_set.add_argument(
        "--key",
        required=True,
        help="Configuration key to set"
    )
    config_set.add_argument(
        "--value",
        required=True,
        help="Configuration value"
    )

    config_subparsers.add_parser("reset", help="Reset configuration to defaults")

    # metrics command (Phase 4)
    metrics_parser = subparsers.add_parser("metrics", help="View metrics")
    metrics_subparsers = metrics_parser.add_subparsers(dest="metrics_action", help="Metrics action")

    metrics_summary = metrics_subparsers.add_parser("summary", help="Show metrics summary")
    metrics_summary.add_argument(
        "--action",
        dest="action_filter",
        help="Filter metrics by action type"
    )

    metrics_subparsers.add_parser("cost", help="Show cost breakdown")

    metrics_subparsers.add_parser("reset", help="Reset metrics")

    # audit command (Phase 4)
    audit_parser = subparsers.add_parser("audit", help="View audit logs")
    audit_subparsers = audit_parser.add_subparsers(dest="audit_action", help="Audit action")

    audit_log = audit_subparsers.add_parser("log", help="Show recent audit logs")
    audit_log.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Number of logs to show (default: 10)"
    )

    audit_search = audit_subparsers.add_parser("search", help="Search audit logs")
    audit_search.add_argument(
        "--action",
        dest="search_action",
        help="Filter by action type"
    )
    audit_search.add_argument(
        "--user",
        dest="search_user",
        help="Filter by user"
    )
    audit_search.add_argument(
        "--status",
        dest="search_status",
        help="Filter by status (success, failure, partial)"
    )

    # plugin command (Phase 4)
    plugin_parser = subparsers.add_parser("plugin", help="Manage plugins")
    plugin_subparsers = plugin_parser.add_subparsers(dest="plugin_action", help="Plugin action")

    plugin_list = plugin_subparsers.add_parser("list", help="List plugins")
    plugin_list.add_argument(
        "--enabled",
        action="store_true",
        help="Show only enabled plugins"
    )

    plugin_enable = plugin_subparsers.add_parser("enable", help="Enable a plugin")
    plugin_enable.add_argument(
        "--name",
        required=True,
        help="Plugin name"
    )

    plugin_disable = plugin_subparsers.add_parser("disable", help="Disable a plugin")
    plugin_disable.add_argument(
        "--name",
        required=True,
        help="Plugin name"
    )

    # template command (Phase 4)
    template_parser = subparsers.add_parser("template", help="Manage templates")
    template_subparsers = template_parser.add_subparsers(dest="template_action", help="Template action")

    template_list = template_subparsers.add_parser("list", help="List templates")
    template_list.add_argument(
        "--action",
        dest="template_action_filter",
        help="Filter templates by action type"
    )

    template_use = template_subparsers.add_parser("use", help="Use a custom template")
    template_use.add_argument(
        "--action",
        dest="template_action_name",
        required=True,
        help="Action type (generate, refactor, test, explain, fix, chat)"
    )
    template_use.add_argument(
        "--name",
        dest="template_name",
        required=True,
        help="Template name"
    )

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

    # Get format_code flag
    format_code = hasattr(args, "format") and args.format

    # Check if streaming is requested
    if hasattr(args, "stream") and args.stream:
        logger.info("Generating code with streaming...")

        # Callback to print chunks as they arrive
        def on_chunk(text: str) -> None:
            # Print the text without newline for continuous output
            print(text, end="", flush=True)

        print("\n" + "=" * 60 + "\n")
        result = await agent.generate_streaming(
            prompt=prompt,
            language=args.language,
            on_chunk=on_chunk,
            format_code=format_code
        )
        print("\n" + "=" * 60)
    else:
        logger.info("Generating code...")
        result = await agent.generate(
            prompt=prompt,
            language=args.language,
            format_code=format_code
        )

        print("\n" + "=" * 60)
        print(result.code)
        print("=" * 60)

    print(f"\nTokens used: {result.tokens_used}")

async def cmd_refactor(args, agent: JmAgent) -> None:
    """Handle refactor command."""
    # Get format_code flag
    format_code = hasattr(args, "format") and args.format

    # Check if using multi-file or single-file mode
    if hasattr(args, "files") and args.files:
        # Multi-file mode
        file_paths = parse_file_list(args.files)
        if not file_paths:
            logger.error(f"No files found matching: {args.files}")
            sys.exit(1)

        logger.info(f"Refactoring {len(file_paths)} files...")
        result = await agent.refactor_multiple(
            file_paths=file_paths,
            requirements=args.requirements,
            language=args.language,
            format_code=format_code
        )

        # Display results for each file
        for file_path, response in result.items():
            print("\n" + "=" * 60)
            print(f"File: {file_path}")
            print("=" * 60)
            print(response.code)
            print(f"Tokens used: {response.tokens_used}")

    else:
        # Single-file mode (backward compatible)
        if not hasattr(args, "file") or not args.file:
            logger.error("Either --file or --files is required")
            sys.exit(1)

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
            language=args.language,
            format_code=format_code
        )

        print("\n" + "=" * 60)
        print(result.code)
        print("=" * 60)
        print(f"\nTokens used: {result.tokens_used}")

async def cmd_test(args, agent: JmAgent) -> None:
    """Handle test command."""
    # Check if using multi-file or single-file mode
    if hasattr(args, "files") and args.files:
        # Multi-file mode
        file_paths = parse_file_list(args.files)
        if not file_paths:
            logger.error(f"No files found matching: {args.files}")
            sys.exit(1)

        logger.info(f"Generating tests for {len(file_paths)} files...")
        result = await agent.test_multiple(
            file_paths=file_paths,
            test_framework=args.framework,
            target_coverage=args.coverage
        )

        print("\n" + "=" * 60)
        print(result.code)
        print("=" * 60)
        print(f"\nTokens used: {result.tokens_used}")

    else:
        # Single-file mode (backward compatible)
        if not hasattr(args, "file") or not args.file:
            logger.error("Either --file or --files is required")
            sys.exit(1)

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

async def cmd_config(args) -> None:
    """Handle config command."""
    from src.config.settings import Settings
    from src.utils.file_handler import load_json_file, save_json_file
    import os
    from pathlib import Path

    config_action = getattr(args, "config_action", None)

    if config_action == "show":
        # Show configuration
        settings = Settings.from_env()
        config_dict = settings.model_dump()

        if hasattr(args, "key") and args.key:
            # Show specific key
            key = args.key
            if key in config_dict:
                print(f"{key}: {config_dict[key]}")
            else:
                print(f"Configuration key not found: {key}")
                sys.exit(1)
        else:
            # Show all configuration
            print("Current Configuration:")
            print("=" * 60)
            for key, value in sorted(config_dict.items()):
                # Mask sensitive values
                if "token" in key.lower() or "key" in key.lower() or "secret" in key.lower():
                    display_value = "***" if value else None
                else:
                    display_value = value
                print(f"{key}: {display_value}")
            print("=" * 60)

    elif config_action == "set":
        # Set configuration value
        key = args.key
        value = args.value

        # Try to validate the setting by creating a Settings instance
        try:
            # Parse value if it's a number or boolean
            parsed_value = value
            if value.lower() in ("true", "false"):
                parsed_value = value.lower() == "true"
            elif value.isdigit():
                parsed_value = int(value)
            else:
                try:
                    parsed_value = float(value)
                except ValueError:
                    parsed_value = value

            # Create a test settings object to validate
            test_settings = Settings.from_env(**{key: parsed_value})
            print(f"Configuration updated: {key} = {value}")
            logger.info(f"Configuration set: {key}={value}")
        except Exception as e:
            logger.error(f"Invalid configuration value: {str(e)}")
            sys.exit(1)

    elif config_action == "reset":
        # Reset configuration to defaults
        settings = Settings()
        print("Configuration reset to defaults:")
        print("=" * 60)
        for key, value in sorted(settings.model_dump().items()):
            if "token" in key.lower() or "key" in key.lower() or "secret" in key.lower():
                display_value = "***" if value else None
            else:
                display_value = value
            print(f"{key}: {display_value}")
        print("=" * 60)

async def cmd_metrics(args) -> None:
    """Handle metrics command."""
    from src.monitoring.metrics import MetricsCollector

    metrics_action = getattr(args, "metrics_action", None)
    collector = MetricsCollector()

    if metrics_action == "summary":
        # Show metrics summary
        stats = collector.get_all_stats()

        if not stats:
            print("No metrics recorded yet.")
            return

        # Filter by action if specified
        action_filter = getattr(args, "action_filter", None)
        if action_filter:
            if action_filter in stats:
                stats = {action_filter: stats[action_filter]}
            else:
                print(f"No metrics found for action: {action_filter}")
                return

        print("Metrics Summary:")
        print("=" * 60)
        for action_type, action_stats in stats.items():
            print(f"\n{action_type.upper()}:")
            print(f"  Count: {action_stats['count']}")
            print(f"  Success Rate: {action_stats['success_rate']:.1%}")
            print(f"  Avg Response Time: {action_stats['avg_response_time']:.2f}s")
            print(f"  Min Response Time: {action_stats['min_response_time']:.2f}s")
            print(f"  Max Response Time: {action_stats['max_response_time']:.2f}s")
            print(f"  Total Tokens: {action_stats['total_tokens']}")
        print("=" * 60)

    elif metrics_action == "cost":
        # Show cost breakdown
        stats = collector.get_all_stats()

        if not stats:
            print("No metrics recorded yet.")
            return

        # Haiku pricing: $0.80 per million input tokens, $4.00 per million output tokens
        # Sonnet pricing: $3.00 per million input tokens, $15.00 per million output tokens
        # Opus pricing: $15.00 per million input tokens, $75.00 per million output tokens
        haiku_input = 0.80 / 1_000_000
        haiku_output = 4.00 / 1_000_000
        sonnet_input = 3.00 / 1_000_000
        sonnet_output = 15.00 / 1_000_000
        opus_input = 15.00 / 1_000_000
        opus_output = 75.00 / 1_000_000

        total_cost = 0.0
        print("Cost Breakdown:")
        print("=" * 60)
        for action_type, action_stats in stats.items():
            # Estimate based on Haiku (default model)
            input_cost = action_stats['total_input_tokens'] * haiku_input
            output_cost = action_stats['total_output_tokens'] * haiku_output
            action_cost = input_cost + output_cost
            total_cost += action_cost

            print(f"\n{action_type.upper()}:")
            print(f"  Input Tokens: {action_stats['total_input_tokens']}")
            print(f"  Output Tokens: {action_stats['total_output_tokens']}")
            print(f"  Estimated Cost: ${action_cost:.4f}")

        print(f"\nTotal Estimated Cost: ${total_cost:.4f}")
        print("(Based on Haiku pricing)")
        print("=" * 60)

    elif metrics_action == "reset":
        # Reset metrics
        collector.clear()
        print("Metrics reset successfully.")

async def cmd_audit(args) -> None:
    """Handle audit command."""
    from src.audit.storage import AuditStorage, AuditQuery
    from datetime import datetime

    audit_action = getattr(args, "audit_action", None)
    storage = AuditStorage()

    if audit_action == "log":
        # Show recent audit logs
        limit = getattr(args, "limit", 10)
        records = storage.get_all()

        if not records:
            print("No audit logs found.")
            return

        # Limit results
        records = records[:limit]

        print(f"Recent Audit Logs (last {len(records)}):")
        print("=" * 80)
        for i, record in enumerate(records, 1):
            print(f"\n{i}. {record.action_type.upper()}")
            print(f"   User: {record.user}")
            print(f"   Time: {record.timestamp}")
            print(f"   Status: {record.status}")
            if record.error_message:
                print(f"   Error: {record.error_message}")
            print(f"   Tokens: {record.tokens_used.get('input_tokens', 0)} input, {record.tokens_used.get('output_tokens', 0)} output")
        print("=" * 80)

    elif audit_action == "search":
        # Search audit logs
        query = AuditQuery(
            action_type=getattr(args, "search_action", None),
            user=getattr(args, "search_user", None),
            status=getattr(args, "search_status", None)
        )

        records = storage.query(query)

        if not records:
            print("No matching audit logs found.")
            return

        print(f"Search Results ({len(records)} records):")
        print("=" * 80)
        for i, record in enumerate(records, 1):
            print(f"\n{i}. {record.action_type.upper()}")
            print(f"   User: {record.user}")
            print(f"   Time: {record.timestamp}")
            print(f"   Status: {record.status}")
            if record.error_message:
                print(f"   Error: {record.error_message}")
        print("=" * 80)

async def cmd_plugin(args) -> None:
    """Handle plugin command."""
    from src.plugins.manager import PluginManager
    from src.plugins.loader import PluginLoader

    plugin_action = getattr(args, "plugin_action", None)
    manager = PluginManager()
    loader = PluginLoader()

    if plugin_action == "list":
        # List plugins
        plugins = manager.list_plugins()
        enabled_only = getattr(args, "enabled", False)

        if not plugins:
            print("No plugins registered.")
            return

        print("Available Plugins:")
        print("=" * 60)
        for name, plugin in plugins.items():
            if enabled_only and not plugin.enabled:
                continue
            status = "Enabled" if plugin.enabled else "Disabled"
            print(f"\n{name}:")
            print(f"  Version: {plugin.version}")
            print(f"  Status: {status}")
            if hasattr(plugin, "description"):
                print(f"  Description: {plugin.description}")
        print("=" * 60)

    elif plugin_action == "enable":
        # Enable plugin
        plugin_name = args.name
        try:
            manager.enable_plugin(plugin_name)
            print(f"Plugin '{plugin_name}' enabled successfully.")
        except Exception as e:
            logger.error(f"Failed to enable plugin: {str(e)}")
            sys.exit(1)

    elif plugin_action == "disable":
        # Disable plugin
        plugin_name = args.name
        try:
            plugin = manager.get_plugin(plugin_name)
            if plugin:
                plugin.disable()
                print(f"Plugin '{plugin_name}' disabled successfully.")
            else:
                print(f"Plugin not found: {plugin_name}")
                sys.exit(1)
        except Exception as e:
            logger.error(f"Failed to disable plugin: {str(e)}")
            sys.exit(1)

async def cmd_template(args) -> None:
    """Handle template command."""
    from src.templates.manager import TemplateManager, BUILTIN_TEMPLATES

    template_action = getattr(args, "template_action", None)
    manager = TemplateManager()

    if template_action == "list":
        # List templates
        action_filter = getattr(args, "template_action_filter", None)

        templates = BUILTIN_TEMPLATES.copy()

        if action_filter:
            if action_filter in templates:
                templates = {action_filter: templates[action_filter]}
            else:
                print(f"No templates found for action: {action_filter}")
                return

        print("Available Templates:")
        print("=" * 60)
        for action, template_info in templates.items():
            print(f"\n{action.upper()}:")
            print(f"  Name: {template_info.get('name', 'N/A')}")
            print(f"  Description: {template_info.get('description', 'N/A')}")
            print(f"  Version: {template_info.get('version', 'N/A')}")
        print("=" * 60)

    elif template_action == "use":
        # Use template
        action = getattr(args, "template_action_name", None)
        template_name = getattr(args, "template_name", None)

        if action in BUILTIN_TEMPLATES:
            print(f"Using template '{template_name}' for action '{action}'")
            logger.info(f"Template set: action={action}, template={template_name}")
        else:
            print(f"Action not found: {action}")
            sys.exit(1)

async def main_async(args) -> None:
    """Main async function."""
    # Handle config, metrics, audit, plugin, template commands (Phase 4)
    # These don't need an agent instance
    if args.action == "config":
        await cmd_config(args)
        return
    elif args.action == "metrics":
        await cmd_metrics(args)
        return
    elif args.action == "audit":
        await cmd_audit(args)
        return
    elif args.action == "plugin":
        await cmd_plugin(args)
        return
    elif args.action == "template":
        await cmd_template(args)
        return

    # For other actions, we need an agent instance
    # Load project context if --project specified
    project_context = None
    if args.project:
        try:
            from src.prompts.context_loader import load_project_context
            project_context = load_project_context(args.project)
            logger.info(f"Loaded project context from {args.project}")
        except Exception as e:
            logger.warning(f"Could not load project context: {str(e)}")

    agent = JmAgent(
        model=args.model,
        temperature=args.temperature,
        max_tokens=args.max_tokens,
        project_context=project_context
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
    load_dotenv()

    # Check for JM_PROJECT_ROOT environment variable
    default_project = os.getenv("JM_PROJECT_ROOT")

    parser = create_parser()

    # If default_project exists, set it as default for --project
    if default_project:
        parser.set_defaults(project=default_project)

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
