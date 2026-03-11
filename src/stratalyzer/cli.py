import json
import sys
import io
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import click
from rich.console import Console
from rich.progress import Progress
from stratalyzer.scanner import scan_folder
from stratalyzer.extractor import extract_all
from stratalyzer.summarizer import summarize_post
from stratalyzer.synthesizer import synthesize_strategy
from stratalyzer.models import PostSummary, StrategyDocument, Extraction
from stratalyzer.scriptgen import generate_script, generate_hooks, generate_ideas, rewrite_script
from stratalyzer.youtube_miner import parse_all_transcripts, score_all

# Force UTF-8 stdout on Windows to handle Unicode from LLM responses
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

console = Console(highlight=False)
MAX_SUMMARY_WORKERS = 10
_summary_cache_lock = threading.Lock()


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

    # Step 2: Extract (parallelized internally)
    console.print("[bold]Extracting content...[/bold]")
    with Progress() as progress:
        all_extractions = extract_all(posts, folder_path, progress)

    # Step 3: Summarize each post (parallelized, with caching)
    console.print("[bold]Summarizing posts...[/bold]")
    username = posts[0][0].username if posts else "unknown"

    summary_cache_path = folder_path / ".stratalyzer_summaries.json"
    summary_cache = {}
    if summary_cache_path.exists():
        summary_cache = json.loads(summary_cache_path.read_text(encoding="utf-8"))

    # Build work items
    work_items = list(zip(range(len(posts)), posts, all_extractions))
    summaries: list[PostSummary | None] = [None] * len(posts)

    def _summarize_one(item):
        idx, post_files, extractions = item
        first = post_files[0]
        cache_key = str(first.timestamp)

        with _summary_cache_lock:
            if cache_key in summary_cache:
                result = summary_cache[cache_key]
                return idx, post_files, extractions, result

        result = summarize_post(
            post_id=first.post_id,
            username=first.username,
            timestamp=first.timestamp,
            extractions=extractions,
        )

        with _summary_cache_lock:
            summary_cache[cache_key] = result
            summary_cache_path.write_text(
                json.dumps(summary_cache, indent=2, default=str),
                encoding="utf-8",
            )

        return idx, post_files, extractions, result

    with Progress() as progress:
        task = progress.add_task("Summarizing", total=len(posts))

        with ThreadPoolExecutor(max_workers=MAX_SUMMARY_WORKERS) as executor:
            futures = {executor.submit(_summarize_one, item): item for item in work_items}
            for future in as_completed(futures):
                idx, post_files, extractions, result = future.result()
                first = post_files[0]
                summaries[idx] = PostSummary(
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
                progress.update(task, advance=1)

    summaries = [s for s in summaries if s is not None]
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


@main.command()
@click.argument("strategy", type=click.Path(exists=True, dir_okay=False))
@click.argument("topic")
@click.option("--funnel", "-f", default="middle", type=click.Choice(["top", "middle", "bottom"]), help="Funnel position")
@click.option("--duration", "-d", default=60, help="Target duration in seconds")
@click.option("--count", "-n", default=1, help="Number of scripts to generate")
def script(strategy: str, topic: str, funnel: str, duration: int, count: int):
    """Generate video script(s) from a strategy document."""
    console.print(f"[bold]Generating {count} script(s) for: {topic}[/bold]")
    result = generate_script(Path(strategy), topic, funnel, duration, count)
    click.echo()
    click.echo(result)


@main.command()
@click.argument("strategy", type=click.Path(exists=True, dir_okay=False))
@click.argument("source", type=click.Path(exists=True, dir_okay=False))
@click.option("--format", "-F", "output_format", default="full",
              type=click.Choice(["caption", "short", "full"]),
              help="Output format: caption (text overlay), short (7-15s script), full (50-60s script)")
@click.option("--funnel", "-f", default="middle", type=click.Choice(["top", "middle", "bottom"]), help="Funnel position")
@click.option("--duration", "-d", default=60, help="Target duration in seconds")
def rewrite(strategy: str, source: str, output_format: str, funnel: str, duration: int):
    """Rewrite a rambling video/transcript into a tight script.

    SOURCE can be a video file (.mp4, .mov, .webm) or a text file (.txt) containing a transcript.
    """
    source_path = Path(source)
    video_exts = {".mp4", ".mov", ".webm"}

    if source_path.suffix.lower() in video_exts:
        console.print(f"[bold]Transcribing {source_path.name}...[/bold]")
        from stratalyzer.transcriber import transcribe_video
        transcript = transcribe_video(source_path)
        if not transcript:
            console.print("[red]Could not extract transcript from video.[/red]")
            return
        console.print(f"[green]Transcript: {len(transcript.split())} words[/green]")
    else:
        transcript = source_path.read_text(encoding="utf-8").strip()
        if not transcript:
            console.print("[red]Source file is empty.[/red]")
            return
        console.print(f"[green]Loaded transcript: {len(transcript.split())} words[/green]")

    format_labels = {"caption": "text overlay captions", "short": "short talking head script", "full": "full script"}
    console.print(f"[bold]Generating {format_labels[output_format]}...[/bold]")
    result = rewrite_script(Path(strategy), transcript, funnel, duration, format=output_format)
    click.echo()
    click.echo(result)


@main.command()
@click.argument("strategy", type=click.Path(exists=True, dir_okay=False))
@click.argument("topic")
@click.option("--count", "-n", default=10, help="Number of hooks to generate")
def hooks(strategy: str, topic: str, count: int):
    """Generate hook variations for a topic."""
    console.print(f"[bold]Generating {count} hooks for: {topic}[/bold]")
    result = generate_hooks(Path(strategy), topic, count)
    click.echo()
    click.echo(result)


@main.command()
@click.argument("strategy", type=click.Path(exists=True, dir_okay=False))
@click.option("--count", "-n", default=20, help="Number of ideas to generate")
@click.option("--pillar", "-p", default=None, help="Focus on a specific content pillar")
def ideas(strategy: str, count: int, pillar: str | None):
    """Generate content ideas using the Three-List system."""
    console.print(f"[bold]Generating {count} content ideas...[/bold]")
    result = generate_ideas(Path(strategy), count, pillar)
    click.echo()
    click.echo(result)


@main.command()
@click.argument("transcript_dir", type=click.Path(exists=True, file_okay=False))
@click.option("--min-words", "-m", default=100, help="Minimum word count to score")
@click.option("--output", "-o", default=None, help="Output JSON file path")
def mine(transcript_dir: str, min_words: int, output: str | None):
    """Score YouTube transcripts for viral potential.

    TRANSCRIPT_DIR should contain .vtt files downloaded via yt-dlp.
    Parses, scores each on skin-in-the-game / reframe potential / emotional punch,
    and outputs a ranked list of the best takes.
    """
    transcript_path = Path(transcript_dir)

    console.print(f"[bold]Parsing transcripts from {transcript_path.name}...[/bold]")
    transcripts = parse_all_transcripts(transcript_path)
    total = len(transcripts)
    eligible = sum(1 for v in transcripts.values() if v["word_count"] >= min_words)
    console.print(f"Found {total} transcripts, {eligible} with {min_words}+ words")

    if eligible == 0:
        console.print("[yellow]No transcripts meet the minimum word count.[/yellow]")
        return

    out_path = Path(output) if output else transcript_path / "scores.json"

    console.print(f"[bold]Scoring {eligible} transcripts for viral potential...[/bold]")
    results = score_all(
        transcripts,
        min_words=min_words,
        output_path=out_path,
        on_progress=lambda msg: console.print(msg),
    )

    console.print(f"\n[bold]Found {len(results)} total segments across all videos[/bold]")
    console.print(f"\n[bold green]Top 20 takes:[/bold green]")
    for i, r in enumerate(results[:20], 1):
        score = r.get("overall_score", 0)
        video = r.get("video_title", "?")[:40]
        take = r.get("draft_take", "")[:70]
        skin = r.get("skin_in_the_game", 0)
        reframe = r.get("reframe_potential", 0)
        punch = r.get("emotional_punch", 0)
        color = "green" if score >= 8 else "yellow" if score >= 6 else "red"
        console.print(f"  {i:2d}. [{color}]{score}/10[/] (S:{skin} R:{reframe} E:{punch})")
        console.print(f"      Video: {video}")
        if take:
            console.print(f"      Take: {take}")

    console.print(f"\n[bold]Full results saved to {out_path}[/bold]")


@main.command()
@click.argument("scores_file", type=click.Path(exists=True, dir_okay=False))
@click.argument("strategy", type=click.Path(exists=True, dir_okay=False))
@click.argument("transcript_dir", type=click.Path(exists=True, file_okay=False))
@click.option("--min-score", "-s", default=7, help="Minimum overall score to generate")
@click.option("--format", "-F", "output_format", default="caption",
              type=click.Choice(["caption", "short", "full"]),
              help="Output format")
@click.option("--output", "-o", default=None, help="Output JSON file path")
def generate(scores_file: str, strategy: str, transcript_dir: str,
             min_score: int, output_format: str, output: str | None):
    """Generate scripts from top-scoring transcripts.

    Takes a scores.json from the 'mine' command, filters to min-score,
    and generates caption/short/full output for each.
    """
    scores = json.loads(Path(scores_file).read_text(encoding="utf-8"))
    transcript_path = Path(transcript_dir)

    # Parse transcripts to get full text
    transcripts = parse_all_transcripts(transcript_path)

    top = [s for s in scores if s.get("overall_score", 0) >= min_score]
    console.print(f"[bold]Generating {output_format} for {len(top)} transcripts (score >= {min_score})...[/bold]")

    results = []
    for i, entry in enumerate(top, 1):
        title = entry["title"]
        if title not in transcripts:
            console.print(f"  [{i}/{len(top)}] {title[:50]} - SKIP (transcript not found)")
            continue

        console.print(f"  [{i}/{len(top)}] {title[:50]}...", end=" ")
        try:
            script_output = rewrite_script(
                Path(strategy),
                transcripts[title]["text"],
                format=output_format,
            )
            entry[f"output_{output_format}"] = script_output
            results.append(entry)
            console.print("[green]OK[/green]")
        except Exception as e:
            console.print(f"[red]FAIL: {e}[/red]")
            entry[f"output_{output_format}"] = f"ERROR: {e}"
            results.append(entry)

        # Save incrementally
        out_path = Path(output) if output else transcript_path / f"generated_{output_format}.json"
        out_path.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")

    out_path = Path(output) if output else transcript_path / f"generated_{output_format}.json"
    console.print(f"\n[bold green]Generated {len(results)} scripts -> {out_path}[/bold green]")
