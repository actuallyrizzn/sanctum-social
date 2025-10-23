#!/usr/bin/env python3
"""Queue management utilities for Void bot."""
import json
import argparse
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any, Union
from rich.console import Console
from rich.table import Table
from rich.prompt import Confirm
from functools import wraps

console = Console()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("queue_manager")

# Queue directories
QUEUE_DIR = Path("data/queues/bluesky")
QUEUE_ERROR_DIR = QUEUE_DIR / "errors"
QUEUE_NO_REPLY_DIR = QUEUE_DIR / "no_reply"


# Error Classification System
class QueueError(Exception):
    """Base class for queue-related errors."""
    def __init__(self, message: str, filepath: Optional[Path] = None, operation: str = "unknown"):
        super().__init__(message)
        self.filepath = filepath
        self.operation = operation
        self.timestamp = datetime.now()
        self.message = message

class TransientQueueError(QueueError):
    """Transient error that can be retried (file locks, network timeouts)."""
    pass

class PermanentQueueError(QueueError):
    """Permanent error that should not be retried (corrupted files, permission denied)."""
    pass

class QueueHealthError(QueueError):
    """Queue health-related error (disk full, directory inaccessible)."""
    pass


# Retry Logic Framework
def retry_with_exponential_backoff(max_retries: int = 3, base_delay: float = 1.0, max_delay: float = 60.0):
    """Decorator for retry logic with exponential backoff."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    
                    if attempt == max_retries:
                        logger.error(f"Function {func.__name__} failed after {max_retries} retries: {e}")
                        raise e
                    
                    if not is_transient_error(e):
                        logger.error(f"Function {func.__name__} failed with permanent error: {e}")
                        raise e
                    
                    # Calculate delay with exponential backoff
                    delay = min(base_delay * (2 ** attempt), max_delay)
                    logger.warning(f"Function {func.__name__} failed (attempt {attempt + 1}/{max_retries + 1}), retrying in {delay:.1f}s: {e}")
                    time.sleep(delay)
            
            raise last_exception
        return wrapper
    return decorator


def is_transient_error(error: Exception) -> bool:
    """Determine if an error is transient and can be retried."""
    transient_errors = (
        PermissionError,  # File locked
        OSError,         # Disk full, network issues
        json.JSONDecodeError,  # Corrupted JSON
        ConnectionError,  # Network issues
        TimeoutError     # Operation timeout
    )
    return isinstance(error, transient_errors)


def classify_queue_error(error: Exception, filepath: Optional[Path] = None, operation: str = "unknown") -> QueueError:
    """Classify an error into appropriate queue error type."""
    if isinstance(error, (ConnectionError, TimeoutError)):
        return TransientQueueError(f"Network error: {error}", filepath, operation)
    elif isinstance(error, PermissionError):
        return TransientQueueError(f"Permission error: {error}", filepath, operation)
    elif isinstance(error, OSError):
        if "No space left" in str(error) or "disk full" in str(error).lower():
            return QueueHealthError(f"Disk full: {error}", filepath, operation)
        else:
            return TransientQueueError(f"File system error: {error}", filepath, operation)
    elif isinstance(error, json.JSONDecodeError):
        return PermanentQueueError(f"Corrupted JSON: {error}", filepath, operation)
    else:
        return QueueError(f"Unknown error: {error}", filepath, operation)


def log_queue_error(error: QueueError, context: Dict[str, Any] = None) -> None:
    """Log queue errors with structured context."""
    context = context or {}
    log_data = {
        "error_type": type(error).__name__,
        "message": error.message,
        "filepath": str(error.filepath) if error.filepath else None,
        "operation": error.operation,
        "timestamp": error.timestamp.isoformat(),
        "context": context
    }
    
    if isinstance(error, QueueHealthError):
        logger.critical(f"Queue health error: {log_data}")
    elif isinstance(error, PermanentQueueError):
        logger.error(f"Permanent queue error: {log_data}")
    elif isinstance(error, TransientQueueError):
        logger.warning(f"Transient queue error: {log_data}")
    else:
        logger.error(f"Queue error: {log_data}")


@retry_with_exponential_backoff(max_retries=3)
def load_notification(filepath: Path) -> Optional[dict]:
    """Load a notification from a JSON file with retry logic."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        logger.debug(f"Successfully loaded notification from {filepath}")
        return data
    except Exception as e:
        queue_error = classify_queue_error(e, filepath, "load_notification")
        log_queue_error(queue_error, {"filepath": str(filepath)})
        
        if isinstance(queue_error, PermanentQueueError):
            # Move corrupted file to error directory
            try:
                error_file = QUEUE_ERROR_DIR / filepath.name
                QUEUE_ERROR_DIR.mkdir(parents=True, exist_ok=True)
                filepath.rename(error_file)
                logger.info(f"Moved corrupted file to error directory: {error_file}")
            except Exception as move_error:
                logger.error(f"Failed to move corrupted file: {move_error}")
        
        raise queue_error


@retry_with_exponential_backoff(max_retries=3)
def save_notification(notification: dict, filepath: Path) -> bool:
    """Save a notification to a JSON file with retry logic."""
    try:
        # Ensure directory exists
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        # Write to temporary file first, then rename (atomic operation)
        temp_file = filepath.with_suffix('.tmp')
        with open(temp_file, 'w', encoding='utf-8') as f:
            json.dump(notification, f, indent=2, ensure_ascii=False)
        
        # Atomic rename
        temp_file.replace(filepath)
        logger.debug(f"Successfully saved notification to {filepath}")
        return True
    except Exception as e:
        queue_error = classify_queue_error(e, filepath, "save_notification")
        log_queue_error(queue_error, {"filepath": str(filepath), "notification_keys": list(notification.keys())})
        raise queue_error


# Queue Health Monitoring System
class QueueMetrics:
    """Container for queue metrics."""
    def __init__(self):
        self.queue_size = 0
        self.error_size = 0
        self.no_reply_size = 0
        self.total_size = 0
        self.unique_handles = 0
        self.oldest_notification = None
        self.newest_notification = None
        self.error_rate = 0.0
        self.processing_rate = 0.0
        self.timestamp = datetime.now()


class QueueHealthMonitor:
    """Monitor queue health and provide metrics."""
    
    def __init__(self):
        self.metrics_history = []
        self.max_history = 100
    
    def get_queue_metrics(self) -> QueueMetrics:
        """Get current queue metrics."""
        metrics = QueueMetrics()
        
        # Collect metrics from all directories
        for directory, key in [(QUEUE_DIR, 'queue'), (QUEUE_ERROR_DIR, 'errors'), (QUEUE_NO_REPLY_DIR, 'no_reply')]:
            if not directory.exists():
                continue
            
            count = 0
            handles = set()
            timestamps = []
            
            for filepath in directory.glob("*.json"):
                if filepath.is_dir():
                    continue
                
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        notif_data = json.load(f)
                    
                    count += 1
                    handle = notif_data.get('author', {}).get('handle', 'unknown')
                    handles.add(handle)
                    
                    # Extract timestamp
                    indexed_at = notif_data.get('indexed_at', '')
                    if indexed_at:
                        timestamps.append(indexed_at)
                        
                except Exception as e:
                    logger.warning(f"Error reading file {filepath} for metrics: {e}")
                    count += 1  # Count as processed even if corrupted
            
            if key == 'queue':
                metrics.queue_size = count
            elif key == 'errors':
                metrics.error_size = count
            elif key == 'no_reply':
                metrics.no_reply_size = count
            
            metrics.unique_handles = len(handles)
        
        metrics.total_size = metrics.queue_size + metrics.error_size + metrics.no_reply_size
        
        # Calculate error rate
        if metrics.total_size > 0:
            metrics.error_rate = (metrics.error_size + metrics.no_reply_size) / metrics.total_size
        
        # Store metrics in history
        self.metrics_history.append(metrics)
        if len(self.metrics_history) > self.max_history:
            self.metrics_history.pop(0)
        
        return metrics
    
    def check_queue_health(self) -> str:
        """Check overall queue health."""
        metrics = self.get_queue_metrics()
        
        # Health checks
        if metrics.error_rate > 0.5:  # More than 50% errors
            return "CRITICAL"
        elif metrics.error_rate > 0.2:  # More than 20% errors
            return "WARNING"
        elif metrics.total_size > 1000:  # Large queue
            return "WARNING"
        elif metrics.queue_size == 0 and metrics.total_size > 0:  # All in error state
            return "CRITICAL"
        else:
            return "HEALTHY"
    
    def get_error_rate(self) -> float:
        """Calculate current error rate."""
        metrics = self.get_queue_metrics()
        return metrics.error_rate
    
    def get_processing_rate(self) -> float:
        """Calculate notifications processed per minute."""
        if len(self.metrics_history) < 2:
            return 0.0
        
        recent_metrics = self.metrics_history[-1]
        older_metrics = self.metrics_history[-2]
        
        time_diff = (recent_metrics.timestamp - older_metrics.timestamp).total_seconds() / 60
        if time_diff == 0:
            return 0.0
        
        processed_diff = older_metrics.total_size - recent_metrics.total_size
        return max(0, processed_diff / time_diff)
    
    def detect_queue_backlog(self) -> bool:
        """Detect if queue is backing up."""
        if len(self.metrics_history) < 3:
            return False
        
        recent_metrics = self.metrics_history[-3:]
        queue_sizes = [m.queue_size for m in recent_metrics]
        
        # Check if queue size is consistently increasing
        return all(queue_sizes[i] < queue_sizes[i+1] for i in range(len(queue_sizes)-1))
    
    def get_queue_size_trend(self) -> str:
        """Get queue size trend (increasing, decreasing, stable)."""
        if len(self.metrics_history) < 2:
            return "unknown"
        
        recent_size = self.metrics_history[-1].queue_size
        older_size = self.metrics_history[-2].queue_size
        
        if recent_size > older_size * 1.1:  # 10% increase
            return "increasing"
        elif recent_size < older_size * 0.9:  # 10% decrease
            return "decreasing"
        else:
            return "stable"


def repair_corrupted_queue_files(queue_dir: Path = None) -> Dict[str, int]:
    """Detect and repair corrupted queue files."""
    if queue_dir is None:
        queue_dir = QUEUE_DIR
        
    repair_stats = {
        "scanned": 0,
        "corrupted": 0,
        "repaired": 0,
        "moved_to_errors": 0
    }
    
    if not queue_dir.exists():
        logger.warning(f"Queue directory {queue_dir} does not exist")
        return repair_stats
    
    for filepath in queue_dir.glob("*.json"):
        repair_stats["scanned"] += 1
        
        try:
            # Try to load the file
            with open(filepath, 'r', encoding='utf-8') as f:
                json.load(f)
            logger.debug(f"File {filepath.name} is valid")
        except json.JSONDecodeError as e:
            repair_stats["corrupted"] += 1
            logger.warning(f"Corrupted file detected: {filepath.name} - {e}")
            
            # Try to repair by removing invalid characters
            try:
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                # Basic repair attempt - remove null bytes and fix common issues
                content = content.replace('\x00', '')
                content = content.strip()
                
                # Try to parse again
                json.loads(content)
                
                # Write repaired content
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                repair_stats["repaired"] += 1
                logger.info(f"Repaired corrupted file: {filepath.name}")
                
            except Exception as repair_error:
                logger.error(f"Failed to repair {filepath.name}: {repair_error}")
                
                # Move to error directory
                try:
                    error_file = QUEUE_ERROR_DIR / filepath.name
                    QUEUE_ERROR_DIR.mkdir(parents=True, exist_ok=True)
                    filepath.rename(error_file)
                    repair_stats["moved_to_errors"] += 1
                    logger.info(f"Moved unrecoverable file to error directory: {error_file}")
                except Exception as move_error:
                    logger.error(f"Failed to move corrupted file: {move_error}")
    
    logger.info(f"Queue repair completed: {repair_stats}")
    return repair_stats


def list_notifications(handle_filter: str = None, show_all: bool = False):
    """List all notifications in the queue, optionally filtered by handle."""
    # Collect notifications from all directories if show_all is True
    if show_all:
        dirs_to_check = [QUEUE_DIR, QUEUE_ERROR_DIR, QUEUE_NO_REPLY_DIR]
    else:
        dirs_to_check = [QUEUE_DIR]
    
    all_notifications = []
    error_count = 0
    
    for directory in dirs_to_check:
        if not directory.exists():
            continue
            
        # Get source directory name for display
        if directory == QUEUE_DIR:
            source = "queue"
        elif directory == QUEUE_ERROR_DIR:
            source = "errors"
        elif directory == QUEUE_NO_REPLY_DIR:
            source = "no_reply"
        else:
            source = "unknown"
        
        for filepath in directory.glob("*.json"):
            # Skip subdirectories
            if filepath.is_dir():
                continue
                
            try:
                notif = load_notification(filepath)
                if notif and isinstance(notif, dict):
                    notif['_filepath'] = filepath
                    notif['_source'] = source
                    
                    # Apply handle filter if specified
                    if handle_filter:
                        author_handle = notif.get('author', {}).get('handle', '')
                        if handle_filter.lower() not in author_handle.lower():
                            continue
                    
                    all_notifications.append(notif)
            except QueueError as e:
                error_count += 1
                logger.warning(f"Skipping file {filepath.name} due to error: {e.message}")
                continue
    
    if error_count > 0:
        console.print(f"[yellow]Skipped {error_count} files due to errors[/yellow]")
    
    # Sort by indexed_at
    all_notifications.sort(key=lambda x: x.get('indexed_at', ''), reverse=True)
    
    # Display results
    if not all_notifications:
        if handle_filter:
            console.print(f"[yellow]No notifications found for handle containing '{handle_filter}'[/yellow]")
        else:
            console.print("[yellow]No notifications found in queue[/yellow]")
        return
    
    table = Table(title=f"Queue Notifications ({len(all_notifications)} total)")
    table.add_column("File", style="cyan", width=20)
    table.add_column("Source", style="magenta", width=10)
    table.add_column("Handle", style="green", width=25)
    table.add_column("Display Name", width=25)
    table.add_column("Text", width=40)
    table.add_column("Time", style="dim", width=20)
    
    for notif in all_notifications:
        author = notif.get('author', {})
        handle = author.get('handle', 'unknown')
        display_name = author.get('display_name', '')
        text = notif.get('record', {}).get('text', '')[:40]
        if len(notif.get('record', {}).get('text', '')) > 40:
            text += "..."
        indexed_at = notif.get('indexed_at', '')[:19]  # Trim milliseconds
        filename = notif['_filepath'].name[:20]
        source = notif['_source']
        
        table.add_row(filename, source, f"@{handle}", display_name, text, indexed_at)
    
    console.print(table)
    return all_notifications


def delete_by_handle(handle: str, dry_run: bool = False, force: bool = False):
    """Delete all notifications from a specific handle."""
    # Remove @ if present
    handle = handle.lstrip('@')
    
    # Find all notifications from this handle
    console.print(f"\\n[bold]Searching for notifications from @{handle}...[/bold]\\n")
    
    to_delete = []
    dirs_to_check = [QUEUE_DIR, QUEUE_ERROR_DIR, QUEUE_NO_REPLY_DIR]
    
    for directory in dirs_to_check:
        if not directory.exists():
            continue
            
        for filepath in directory.glob("*.json"):
            if filepath.is_dir():
                continue
                
            try:
                notif = load_notification(filepath)
                if notif and isinstance(notif, dict):
                    author_handle = notif.get('author', {}).get('handle', '')
                    if author_handle.lower() == handle.lower():
                        to_delete.append({
                            'filepath': filepath,
                            'notif': notif,
                            'source': directory.name
                        })
            except QueueError as e:
                logger.warning(f"Skipping file {filepath.name} due to error: {e.message}")
                continue
    
    if not to_delete:
        console.print(f"[yellow]No notifications found from @{handle}[/yellow]")
        return
    
    # Display what will be deleted
    table = Table(title=f"Notifications to Delete from @{handle}")
    table.add_column("File", style="cyan")
    table.add_column("Location", style="magenta")
    table.add_column("Text", width=50)
    table.add_column("Time", style="dim")
    
    for item in to_delete:
        notif = item['notif']
        text = notif.get('record', {}).get('text', '')[:50]
        if len(notif.get('record', {}).get('text', '')) > 50:
            text += "..."
        indexed_at = notif.get('indexed_at', '')[:19]
        
        table.add_row(
            item['filepath'].name,
            item['source'],
            text,
            indexed_at
        )
    
    console.print(table)
    console.print(f"\\n[bold red]Found {len(to_delete)} notifications to delete[/bold red]")
    
    if dry_run:
        console.print("\\n[yellow]DRY RUN - No files were deleted[/yellow]")
        return
    
    # Confirm deletion
    if not force and not Confirm.ask("\\nDo you want to delete these notifications?"):
        console.print("[yellow]Deletion cancelled[/yellow]")
        return
    
    # Delete the files
    deleted_count = 0
    for item in to_delete:
        try:
            item['filepath'].unlink()
            deleted_count += 1
            console.print(f"[green]✓[/green] Deleted {item['filepath'].name}")
        except Exception as e:
            console.print(f"[red]✗[/red] Failed to delete {item['filepath'].name}: {e}")
    
    console.print(f"\\n[bold green]Successfully deleted {deleted_count} notifications[/bold green]")


def count_by_handle():
    """Show detailed count of notifications by handle."""
    handle_counts = {}
    
    # Collect counts from all directories
    for directory, location in [(QUEUE_DIR, 'queue'), (QUEUE_ERROR_DIR, 'errors'), (QUEUE_NO_REPLY_DIR, 'no_reply')]:
        if not directory.exists():
            continue
            
        for filepath in directory.glob("*.json"):
            if filepath.is_dir():
                continue
                
            try:
                notif = load_notification(filepath)
                if notif and isinstance(notif, dict):
                    handle = notif.get('author', {}).get('handle', 'unknown')
                    
                    if handle not in handle_counts:
                        handle_counts[handle] = {'queue': 0, 'errors': 0, 'no_reply': 0, 'total': 0}
                    
                    handle_counts[handle][location] += 1
                    handle_counts[handle]['total'] += 1
            except QueueError as e:
                logger.warning(f"Skipping file {filepath.name} due to error: {e.message}")
                continue
    
    if not handle_counts:
        console.print("[yellow]No notifications found in any queue[/yellow]")
        return
    
    # Sort by total count
    sorted_handles = sorted(handle_counts.items(), key=lambda x: x[1]['total'], reverse=True)
    
    # Display results
    table = Table(title=f"Notification Count by Handle ({len(handle_counts)} unique handles)")
    table.add_column("Handle", style="green", width=30)
    table.add_column("Queue", style="cyan", justify="right")
    table.add_column("Errors", style="red", justify="right")
    table.add_column("No Reply", style="yellow", justify="right")
    table.add_column("Total", style="bold magenta", justify="right")
    
    for handle, counts in sorted_handles:
        table.add_row(
            f"@{handle}",
            str(counts['queue']) if counts['queue'] > 0 else "-",
            str(counts['errors']) if counts['errors'] > 0 else "-",
            str(counts['no_reply']) if counts['no_reply'] > 0 else "-",
            str(counts['total'])
        )
    
    console.print(table)
    
    # Summary statistics
    total_notifications = sum(h['total'] for h in handle_counts.values())
    avg_per_handle = total_notifications / len(handle_counts)
    
    console.print(f"\n[bold]Summary:[/bold]")
    console.print(f"  Total notifications: {total_notifications}")
    console.print(f"  Unique handles: {len(handle_counts)}")
    console.print(f"  Average per handle: {avg_per_handle:.1f}")
    
    # Top user info
    if sorted_handles:
        top_handle, top_counts = sorted_handles[0]
        percentage = (top_counts['total'] / total_notifications) * 100
        console.print(f"  Most active: @{top_handle} ({top_counts['total']} notifications, {percentage:.1f}% of total)")


def stats():
    """Show queue statistics."""
    stats_data = {
        'queue': {'count': 0, 'handles': set()},
        'errors': {'count': 0, 'handles': set()},
        'no_reply': {'count': 0, 'handles': set()}
    }
    
    # Collect stats
    for directory, key in [(QUEUE_DIR, 'queue'), (QUEUE_ERROR_DIR, 'errors'), (QUEUE_NO_REPLY_DIR, 'no_reply')]:
        if not directory.exists():
            continue
            
        for filepath in directory.glob("*.json"):
            if filepath.is_dir():
                continue
                
            try:
                notif = load_notification(filepath)
                if notif and isinstance(notif, dict):
                    stats_data[key]['count'] += 1
                    handle = notif.get('author', {}).get('handle', 'unknown')
                    stats_data[key]['handles'].add(handle)
            except QueueError as e:
                logger.warning(f"Skipping file {filepath.name} due to error: {e.message}")
                continue
    
    # Display stats
    table = Table(title="Queue Statistics")
    table.add_column("Location", style="cyan")
    table.add_column("Count", style="yellow")
    table.add_column("Unique Handles", style="green")
    
    for key, label in [('queue', 'Active Queue'), ('errors', 'Errors'), ('no_reply', 'No Reply')]:
        table.add_row(
            label,
            str(stats_data[key]['count']),
            str(len(stats_data[key]['handles']))
        )
    
    console.print(table)
    
    # Show top handles
    all_handles = {}
    for location_data in stats_data.values():
        for handle in location_data['handles']:
            all_handles[handle] = all_handles.get(handle, 0) + 1
    
    if all_handles:
        sorted_handles = sorted(all_handles.items(), key=lambda x: x[1], reverse=True)[:10]
        
        top_table = Table(title="Top 10 Handles by Notification Count")
        top_table.add_column("Handle", style="green")
        top_table.add_column("Count", style="yellow")
        
        for handle, count in sorted_handles:
            top_table.add_row(f"@{handle}", str(count))
        
        console.print("\\n")
        console.print(top_table)


def main():
    parser = argparse.ArgumentParser(description="Manage Void bot notification queue")
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List notifications in queue')
    list_parser.add_argument('--handle', help='Filter by handle (partial match)')
    list_parser.add_argument('--all', action='store_true', help='Include errors and no_reply folders')
    
    # Delete command
    delete_parser = subparsers.add_parser('delete', help='Delete notifications from a specific handle')
    delete_parser.add_argument('handle', help='Handle to delete notifications from')
    delete_parser.add_argument('--dry-run', action='store_true', help='Show what would be deleted without deleting')
    delete_parser.add_argument('--force', action='store_true', help='Skip confirmation prompt')
    
    # Stats command
    stats_parser = subparsers.add_parser('stats', help='Show queue statistics')
    
    # Count command
    count_parser = subparsers.add_parser('count', help='Show detailed count by handle')
    
    # Health command
    health_parser = subparsers.add_parser('health', help='Check queue health and metrics')
    
    # Repair command
    repair_parser = subparsers.add_parser('repair', help='Repair corrupted queue files')
    
    args = parser.parse_args()
    
    if args.command == 'list':
        list_notifications(args.handle, args.all)
    elif args.command == 'delete':
        delete_by_handle(args.handle, args.dry_run, args.force)
    elif args.command == 'stats':
        stats()
    elif args.command == 'count':
        count_by_handle()
    elif args.command == 'health':
        # Show queue health
        monitor = QueueHealthMonitor()
        metrics = monitor.get_queue_metrics()
        health_status = monitor.check_queue_health()
        
        console.print(f"\n[bold]Queue Health Status:[/bold] [{'red' if health_status == 'CRITICAL' else 'yellow' if health_status == 'WARNING' else 'green'}]{health_status}[/]")
        
        table = Table(title="Queue Metrics")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="yellow")
        
        table.add_row("Queue Size", str(metrics.queue_size))
        table.add_row("Error Size", str(metrics.error_size))
        table.add_row("No Reply Size", str(metrics.no_reply_size))
        table.add_row("Total Size", str(metrics.total_size))
        table.add_row("Unique Handles", str(metrics.unique_handles))
        table.add_row("Error Rate", f"{metrics.error_rate:.1%}")
        table.add_row("Processing Rate", f"{monitor.get_processing_rate():.1f}/min")
        table.add_row("Queue Trend", monitor.get_queue_size_trend())
        table.add_row("Backlog Detected", "Yes" if monitor.detect_queue_backlog() else "No")
        
        console.print(table)
    elif args.command == 'repair':
        console.print("[yellow]Scanning for corrupted queue files...[/yellow]")
        repair_stats = repair_corrupted_queue_files()
        
        table = Table(title="Repair Results")
        table.add_column("Operation", style="cyan")
        table.add_column("Count", style="yellow")
        
        table.add_row("Files Scanned", str(repair_stats['scanned']))
        table.add_row("Corrupted Files", str(repair_stats['corrupted']))
        table.add_row("Files Repaired", str(repair_stats['repaired']))
        table.add_row("Moved to Errors", str(repair_stats['moved_to_errors']))
        
        console.print(table)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()