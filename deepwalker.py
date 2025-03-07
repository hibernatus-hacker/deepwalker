import os
import argparse
import replicate
import logging
import sys
from pathlib import Path
from typing import Dict, List, Optional
import json
from datetime import datetime
import colorama
from colorama import Fore, Style, Back
import time

# Initialize colorama for cross-platform colored terminal output
colorama.init(autoreset=True)

def load_system_prompt(system_prompt_source=None) -> str:
    """
    Load the system prompt from a string, file, or use default.

    Args:
        system_prompt_source: Either a string containing the system prompt or a path to a file

    Returns:
        The system prompt as a string
    """
    # If no source is provided, try to load from default file
    if system_prompt_source is None:
        try:
            with open("system_prompt.txt", 'r', encoding='utf-8') as f:
                return f.read().strip()
        except FileNotFoundError:
            return "Default system prompt"
        except Exception as e:
            print(f"{Fore.RED}Error loading default system prompt: {str(e)}{Style.RESET_ALL}")
            return "Default system prompt"

    # If source is a string path to a file
    if os.path.isfile(system_prompt_source):
        try:
            with open(system_prompt_source, 'r', encoding='utf-8') as f:
                return f.read().strip()
        except Exception as e:
            print(f"{Fore.RED}Error loading system prompt from file {system_prompt_source}: {str(e)}{Style.RESET_ALL}")
            return "Default system prompt"

    # If source is a direct string
    return system_prompt_source

# Configure logging
def setup_logger(log_level=logging.INFO):
    """Configure and return a logger with proper formatting."""
    logger = logging.getLogger("deepwalker")

    # Clear any existing handlers to avoid duplicate logs
    if logger.handlers:
        logger.handlers.clear()

    logger.setLevel(log_level)

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)

    # Create formatter
    formatter = logging.Formatter(
        f'{Fore.CYAN}%(asctime)s{Style.RESET_ALL} - '
        f'{Fore.GREEN}%(name)s{Style.RESET_ALL} - '
        f'{Fore.YELLOW}%(levelname)s{Style.RESET_ALL} - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger

# Create the banner
def display_banner():
    """Display a cool ASCII art banner for the tool."""
    banner = f"""
{Fore.CYAN}║ {Fore.RED}     _                                  _ _
{Fore.CYAN}║ {Fore.RED}    | |                                | | |
{Fore.CYAN}║ {Fore.RED}  __| | ___  ___ _ __  __      ____ _| | | __
{Fore.CYAN}║ {Fore.RED} / _` |/ _ \/ _ \ '_ \ \ \ /\ / / _` | | |/ / _ \ '__|
{Fore.CYAN}║ {Fore.RED}| (_| |  __/  __/ |_) | \ V  V / (_| | |   <  __/ |
{Fore.CYAN}║ {Fore.RED} \__,_|\___|\___| .__/   \_/\_/ \__,_|_|_|\_\___|_|
{Fore.CYAN}║ {Fore.RED}                | |
{Fore.CYAN}║ {Fore.RED}                |_|
{Fore.CYAN}║
{Fore.CYAN}  {Fore.GREEN}by Hibernatus
"""
    print(banner)

class CodeAnalyzer:
    """Analyzes code for using AI."""

    def __init__(self, api_model: str = "anthropic/claude-3.5-sonnet", logger=None, system_prompt=None):
        self.api_model = api_model
        self.logger = logger or setup_logger()
        self.system_prompt = system_prompt
        self.stats = {
            "files_analyzed": 0,
            "files_with_issues": 0,
            "errors": 0
        }

    def analyze_file(self, file_path: Path) -> Dict:
        """Analyze a single file and return structured results."""
        self.logger.info(f"Analyzing file: {Fore.BLUE}{file_path}{Style.RESET_ALL}")

        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read().strip()

            if not content:
                self.logger.warning(f"File is empty: {file_path}")
                return {"file": str(file_path), "status": "skipped", "reason": "empty file"}

            # Generate detailed analysis prompt
            prompt = self._create_analysis_prompt(content)

            # Get analysis from AI model
            self.logger.debug(f"Sending file to AI model for analysis: {file_path}")
            response = self._get_ai_analysis(prompt)

            # Check if there was an error in getting the AI analysis
            if response.startswith("Error getting AI analysis"):
                self.stats["errors"] += 1
                return {"file": str(file_path), "status": "failed", "error": response}

            # Extract and structure information
            result = self._structure_results(response, file_path)

            # Update stats - all successfully analyzed files count as analyzed
            self.stats["files_analyzed"] += 1

            self.logger.info(f"✅ Completed analysis of: {Fore.BLUE}{file_path}{Style.RESET_ALL}")
            return result

        except Exception as e:
            self.stats["errors"] += 1
            error_msg = f"❌ Error analyzing {file_path}: {str(e)}"
            self.logger.error(error_msg)
            return {"error": str(e), "file": str(file_path), "status": "failed"}

    def _create_analysis_prompt(self, content: str) -> str:
        """Create a detailed analysis prompt for the AI model."""
        return f"""
{content}
"""

    def _get_ai_analysis(self, prompt: str) -> str:
        """Get analysis from the AI model using streaming with retry mechanism."""
        max_retries = 3
        retry_count = 0
        backoff_factor = 2  # Exponential backoff factor

        while retry_count < max_retries:
            try:
                self.logger.debug("Connecting to AI model...")
                response = ""
                for event in replicate.stream(
                    self.api_model,
                    input={
                        "prompt": prompt,
                        "max_tokens": 8192,
                        "system_prompt": self.system_prompt,
                        "max_image_resolution": 0.5
                    }
                ):
                    response += str(event)

                self.logger.debug("Received response from AI model")
                return response.strip()

            except Exception as e:
                retry_count += 1
                if retry_count < max_retries:
                    wait_time = backoff_factor ** retry_count
                    self.logger.warning(f"Error getting AI analysis: {str(e)}. Retrying in {wait_time} seconds (attempt {retry_count}/{max_retries})...")
                    time.sleep(wait_time)
                else:
                    self.logger.error(f"Failed to get AI analysis after {max_retries} attempts: {str(e)}")
                    return f"Error getting AI analysis after {max_retries} attempts: {str(e)}"

    def _structure_results(self, response: str, file_path: Path) -> Dict:
        """Structure the analysis results."""
        return {
            "file": str(file_path),
            "analysis": response,
            "timestamp": datetime.now().isoformat(),
            "status": "completed"
        }

    def analyze_directory(self, directory: Path, file_extensions=None) -> List[Dict]:
        """
        Analyze all files in a directory recursively.

        Args:
            directory: Path to the directory to analyze
            file_extensions: Optional file extension(s) to filter files (without the dot)
                             Can be a single string or a list of strings
        """
        self.logger.info(f"Starting analysis of directory: {Fore.BLUE}{directory}{Style.RESET_ALL}")

        results = []
        files = list(self._find_files(directory, file_extensions))

        if not files:
            self.logger.warning(f"No matching files found in {directory}")
            return results

        self.logger.info(f"Found {Fore.YELLOW}{len(files)}{Style.RESET_ALL} files to analyze")

        for i, file_path in enumerate(files, 1):
            self.logger.info(f"Processing file {i}/{len(files)}: {Fore.BLUE}{file_path}{Style.RESET_ALL}")
            result = self.analyze_file(file_path)
            results.append(result)

        self.logger.info(f"Completed analysis of directory: {Fore.BLUE}{directory}{Style.RESET_ALL}")
        return results

    def _find_files(self, directory: Path, file_extensions=None):
        """
        Find all matching files in a directory recursively.

        Args:
            directory: Path to the directory to search
            file_extensions: Optional file extension(s) to filter files (without the dot)
                             Can be a single string or a list of strings
        """
        for file_path in directory.rglob("*"):
            if file_path.is_file():
                if file_extensions is None:
                    # No extension filter, yield all files
                    yield file_path
                elif isinstance(file_extensions, list):
                    # Multiple extensions provided
                    if any(file_path.suffix.lower() == f".{ext}" for ext in file_extensions):
                        yield file_path
                else:
                    # Single extension provided
                    if file_path.suffix.lower() == f".{file_extensions}":
                        yield file_path

    def save_report(self, results: List[Dict], output_path: Path):
        """Save the analysis results to a text file with nice formatting."""
        self.logger.info(f"Saving report to: {Fore.BLUE}{output_path}{Style.RESET_ALL}")

        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write("=== REPORT ===\n")
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

                successful_analyses = 0
                failed_analyses = 0
                skipped_files = 0
                for i, result in enumerate(results, 1):
                    # Write file header
                    f.write(f"FILE #{i}: {result['file']}\n")
                    f.write("=" * 80 + "\n")

                    # Write status and count by status
                    status = result.get('status', 'unknown')
                    f.write(f"Status: {status.upper()}\n")

                    if status == 'completed':
                        successful_analyses += 1
                    elif status == 'failed':
                        failed_analyses += 1
                    elif status == 'skipped':
                        skipped_files += 1

                    # Write timestamp if available
                    if 'timestamp' in result:
                        f.write(f"Analyzed: {result['timestamp']}\n\n")
                    else:
                        f.write("\n")

                    # Write analysis or error
                    if 'error' in result:
                        f.write(f"ERROR: {result['error']}\n")
                    elif 'reason' in result:
                        f.write(f"NOTE: {result['reason']}\n")
                    else:
                        f.write("ANALYSIS:\n")
                        f.write("-" * 80 + "\n")
                        f.write(f"{result['analysis']}\n")

                    # Add separator between files
                    f.write("\n\n" + "=" * 80 + "\n\n")

                # Write summary
                f.write("=== SUMMARY ===\n")
                f.write(f"Total files processed: {len(results)}\n")
                f.write(f"Successfully analyzed: {successful_analyses}\n")
                f.write(f"Failed analyses: {failed_analyses}\n")
                f.write(f"Skipped files: {skipped_files}\n")

            self.logger.info(f"✅ Report successfully saved to: {Fore.BLUE}{output_path}{Style.RESET_ALL}")
        except Exception as e:
            self.logger.error(f"❌ Failed to save report: {str(e)}")

    def generate_summary(self, results: List[Dict]) -> str:
        """Generate a summary of the analysis results."""
        # Count results by status
        successful = sum(1 for r in results if r.get('status') == 'completed')
        failed = sum(1 for r in results if r.get('status') == 'failed')
        skipped = sum(1 for r in results if r.get('status') == 'skipped')

        summary = f"""
{Fore.CYAN}
{Fore.CYAN}║ {Fore.YELLOW} ANALYSIS SUMMARY
{Fore.CYAN}
{Fore.CYAN}║ {Fore.WHITE}Total files processed:    {Fore.GREEN}{len(results):<5}
{Fore.CYAN}║ {Fore.WHITE}Successfully analyzed:    {Fore.GREEN}{successful:<5}
{Fore.CYAN}║ {Fore.WHITE}Failed analyses:          {Fore.RED if failed > 0 else Fore.GREEN}{failed:<5}
{Fore.CYAN}║ {Fore.WHITE}Skipped files:            {Fore.YELLOW}{skipped:<5}
{Fore.CYAN}
"""
        return summary


def main():
    """Main entry point for the script."""
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Code Analysis Tool')
    parser.add_argument('directory', type=str, help='Path to the directory to analyze')
    parser.add_argument('--output', type=str, default='analysis_report.txt',
                      help='Path to save the analysis report (default: analysis_report.txt)')
    parser.add_argument('--summary', action='store_true',
                      help='Generate and display a summary')
    parser.add_argument('--verbose', '-v', action='store_true',
                      help='Enable verbose logging')
    parser.add_argument('--model', type=str, default='anthropic/claude-3.5-sonnet',
                      help='AI model to use for analysis (default: anthropic/claude-3.5-sonnet)')
    parser.add_argument('--system-prompt', type=str,
                      help='System prompt as a string or path to a system prompt file')
    parser.add_argument('--file-extension', type=str,
                      help='File extension to analyze (without the dot, e.g. "js" for JavaScript files)')
    parser.add_argument('--extensions', nargs='+',
                      help='Multiple file extensions to analyze (e.g. --extensions js py txt)')

    args = parser.parse_args()

    # Display banner
    display_banner()

    # Set up logger
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logger = setup_logger(log_level)

    # Load system prompt
    system_prompt = load_system_prompt(args.system_prompt)
    logger.debug(f"Using system prompt: {system_prompt[:50]}..." if len(system_prompt) > 50 else system_prompt)

    # Create analyzer
    analyzer = CodeAnalyzer(api_model=args.model, logger=logger, system_prompt=system_prompt)

    # Validate directory
    directory = Path(args.directory)
    if not directory.exists() or not directory.is_dir():
        logger.error(f"❌ Invalid directory: {directory}")
        sys.exit(1)

    # Determine file extensions to analyze
    file_extensions = None
    if args.extensions:
        # If multiple extensions are provided via --extensions
        file_extensions = [ext.lstrip('.') for ext in args.extensions]
        logger.info(f"Analyzing files with extensions: {', '.join(file_extensions)}")
    elif args.file_extension:
        # If a single extension is provided via --file-extension
        file_extensions = args.file_extension.lstrip('.')
        logger.info(f"Analyzing files with extension: {file_extensions}")

    # Analyze directory
    logger.info(f"Starting analysis of: {Fore.BLUE}{directory}{Style.RESET_ALL}")
    results = analyzer.analyze_directory(directory, file_extensions)

    # Check if any analysis was performed
    if not results:
        print(f"\n{Fore.YELLOW}No files were analyzed. Please check your file extensions or directory path.{Style.RESET_ALL}")
    else:
        # Save report
        output_path = Path(args.output)
        analyzer.save_report(results, output_path)

        # Display summary if requested
        if args.summary or True:  # Always show summary
            summary = analyzer.generate_summary(results)
            print(summary)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Analysis interrupted by user. Exiting...{Style.RESET_ALL}")
        sys.exit(0)
    except Exception as e:
        print(f"\n{Fore.RED}An unexpected error occurred: {str(e)}{Style.RESET_ALL}")
        sys.exit(1)
    finally:
        # Clean up resources, if any
        colorama.deinit()
        print(f"\n{Fore.GREEN}Analysis complete. Thank you for using deepwalker.{Style.RESET_ALL}")
