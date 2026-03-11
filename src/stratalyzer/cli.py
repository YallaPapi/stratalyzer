import json
from pathlib import Path
import click
from rich.console import Console
from rich.progress import Progress
from stratalyzer.scanner import scan_folder
from stratalyzer.extractor import extract_all
from stratalyzer.summarizer import summarize_post
from stratalyzer.synthesizer import synthesize_strategy
from stratalyzer.models import PostSummary, StrategyDocument, Extraction

console = Console()


@click.group()
def main():
    """Stratalyzer - Extract strategies from influencer content."""
    pass


@main.command()
@click.argument("folder", type=click.Path(exists=True, file_okay=False))
@click.option("--output", "-o", default=None, help="Output JSON file path")
@click.option("--skip-synthesis", is_flag=True, help="Only extract, don't synthesize")
def analyze(folder: str, output: str | None, skip_synthesis: bool):
    """Analyze a folder of influencer content."""
    folder_path = Path(folder)

    # Step 1: Scan
    console.print(f"[bold]Scanning {folder_path.name}...[/bold]")
    posts = scan_folder(folder_path)
    total_files = sum(len(p) for p in posts)
    console.print(f"Found {len(posts)} posts ({total_files} files)")

    if not posts:
        console.print("[yellow]No media files found.[/yellow]")
        return

    # Step 2: Extract
    console.print("[bold]Extracting content...[/bold]")
    with Progress() as progress:
        all_extractions = extract_all(posts, folder_path, progress)

    # Step 3: Summarize each post (with caching)
    console.print("[bold]Summarizing posts...[/bold]")
    summaries: list[PostSummary] = []
    username = posts[0][0].username if posts else "unknown"

    # Summary cache
    summary_cache_path = folder_path / ".stratalyzer_summaries.json"
    summary_cache = {}
    if summary_cache_path.exists():
        summary_cache = json.loads(summary_cache_path.read_text(encoding="utf-8"))

    with Progress() as progress:
        task = progress.add_task("Summarizing", total=len(posts))
        for post_files, extractions in zip(posts, all_extractions):
            first = post_files[0]

            # Check summary cache first
            if first.post_id in summary_cache:
                result = summary_cache[first.post_id]
            else:
                result = summarize_post(
                    post_id=first.post_id,
                    username=first.username,
                    timestamp=first.timestamp,
                    extractions=extractions,
                )
                summary_cache[first.post_id] = result
                summary_cache_path.write_text(
                    json.dumps(summary_cache, indent=2, default=str),
                    encoding="utf-8",
                )

            summary = PostSummary(
                post_id=first.post_id,
                username=first.username,
                timestamp=first.timestamp,
                num_images=sum(1 for f in post_files if f.is_image),
                num_videos=sum(1 for f in post_files if f.is_video),
                extractions=extractions,
                summary=result["summary"],
                topics=result.get("topics", []),
                is_educational=result.get("is_educational", False),
            )
            summaries.append(summary)
            progress.update(task, advance=1)

    edu_count = sum(1 for s in summaries if s.is_educational)
    console.print(f"[green]{edu_count}/{len(summaries)} posts are educational[/green]")

    if skip_synthesis:
        out_path = Path(output) if output else folder_path / "summaries.json"
        out_path.write_text(
            json.dumps([s.model_dump() for s in summaries], indent=2, default=str),
            encoding="utf-8",
        )
        console.print(f"[bold green]Summaries saved to {out_path}[/bold green]")
        return

    # Step 4: Synthesize
    console.print("[bold]Synthesizing strategy document...[/bold]")
    strategy = synthesize_strategy(username, summaries)

    doc = StrategyDocument(
        influencer=username,
        total_posts=len(summaries),
        educational_posts=edu_count,
        topics=strategy.get("topics", {}),
        processes=strategy.get("processes", []),
        frameworks=strategy.get("frameworks", []),
        raw_post_summaries=summaries,
    )

    out_path = Path(output) if output else folder_path / "strategy.json"
    out_path.write_text(doc.model_dump_json(indent=2), encoding="utf-8")
    console.print(f"[bold green]Strategy document saved to {out_path}[/bold green]")
    console.print(f"  Topics: {len(doc.topics)}")
    console.print(f"  Processes: {len(doc.processes)}")
    console.print(f"  Frameworks: {len(doc.frameworks)}")
