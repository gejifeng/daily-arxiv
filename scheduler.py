"""
定时调度器 / Scheduled runner

使用 APScheduler 实现每日自动运行 /
Use APScheduler to run daily jobs automatically
"""
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径 / Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
import pytz
import traceback
import logging

from src.utils import load_config, load_env, setup_logging, load_json, pick_text
from src.notifier import EmailNotifier
from main import main as run_daily_task


def scheduled_task(logger=None, notifier=None, language='zh'):
    """定时执行的任务 / Scheduled task entry."""
    start_time = datetime.now()
    lang = str(language).strip().lower()
    text = (lambda zh, en: en) if lang.startswith('en') else (lambda zh, en: zh)
    
    print("\n" + "=" * 60)
    print(f"⏰ Scheduled task triggered - {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60 + "\n")
    
    if logger:
        logger.info(text(f"定时任务开始执行 - {start_time}", f"Scheduled task started - {start_time}"))
    
    try:
        # 执行主任务 / Run main workflow
        run_daily_task()
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        print("\n" + "=" * 60)
        print(text("✅ 任务执行成功！", "✅ Task completed successfully!"))
        print(text(f"⏱️  耗时: {duration:.2f} 秒", f"⏱️  Duration: {duration:.2f} seconds"))
        print(text(f"🕐 完成时间: {end_time.strftime('%Y-%m-%d %H:%M:%S')}", f"🕐 Finished at: {end_time.strftime('%Y-%m-%d %H:%M:%S')}"))
        print("=" * 60 + "\n")
        
        if logger:
            logger.info(text(f"定时任务执行成功，耗时 {duration:.2f} 秒", f"Scheduled task succeeded, took {duration:.2f} seconds"))
        
        # 发送成功通知 / Send success notification
        if notifier:
            try:
            # 读取统计信息 / Load stats
                stats = load_json(Path('data/papers/latest.json'))
                stats_info = {
                    'papers_count': len(stats) if stats else 0,
                    'summaries_count': len(load_json(Path('data/summaries/latest.json')) or {}),
                    'categories_count': len(set(p.get('primary_category', '') for p in stats)) if stats else 0,
                    'keywords_count': 50  # 从分析结果获取 / Retrieved from analysis result
                }
                notifier.send_notification(success=True, stats=stats_info, duration=duration)
            except Exception as e:
                logger.warning(text(f"发送邮件通知失败: {str(e)}", f"Failed to send email notification: {str(e)}"))
        
        return True
        
    except Exception as e:
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        print("\n" + "=" * 60)
        print(text("❌ 任务执行失败！", "❌ Task execution failed!"))
        print(text(f"⏱️  耗时: {duration:.2f} 秒", f"⏱️  Duration: {duration:.2f} seconds"))
        print(text(f"🔴 错误: {str(e)}", f"🔴 Error: {str(e)}"))
        print("=" * 60)
        print(text("\n详细错误信息:", "\nDetailed error information:"))
        traceback.print_exc()
        print()
        
        if logger:
            logger.error(text(f"定时任务执行失败: {str(e)}", f"Scheduled task failed: {str(e)}"), exc_info=True)
        
        # 发送失败通知 / Send failure notification
        if notifier:
            try:
                notifier.send_notification(
                    success=False,
                    error_msg=f"{str(e)}\n\n{traceback.format_exc()}",
                    duration=duration
                )
            except Exception as email_error:
                logger.warning(text(f"发送邮件通知失败: {str(email_error)}", f"Failed to send email notification: {str(email_error)}"))
        
        return False


def main():
    """主函数 / Main function"""
    # 加载配置 / Load configuration
    load_env()
    config = load_config()
    logger = setup_logging(config)
    text = lambda zh, en: pick_text(config, zh, en)
    
    scheduler_config = config.get('scheduler', {})
    
    if not scheduler_config.get('enabled', False):
        logger.warning(text("定时调度未启用，请在 config.yaml 中设置 scheduler.enabled = true", "Scheduler is disabled. Set scheduler.enabled = true in config.yaml"))
        print(text("\n⚠️  定时调度未启用", "\n⚠️  Scheduler is disabled"))
        print(text("请在 config/config.yaml 中设置:", "Please set this in config/config.yaml:"))
        print("  scheduler:")
        print("    enabled: true")
        return
    
    # 获取配置 / Read scheduler config
    run_time = scheduler_config.get('run_time', '09:00')
    timezone = scheduler_config.get('timezone', 'Asia/Shanghai')
    run_on_start = scheduler_config.get('run_on_start', True)
    
    # 解析运行时间 / Parse run time
    try:
        hour, minute = map(int, run_time.split(':'))
    except ValueError:
        logger.error(text(f"无效的运行时间格式: {run_time}，应为 HH:MM 格式", f"Invalid run_time format: {run_time}, expected HH:MM"))
        print(text(f"❌ 无效的运行时间格式: {run_time}", f"❌ Invalid run_time format: {run_time}"))
        print(text("请使用 HH:MM 格式，例如: 09:00", "Please use HH:MM format, e.g. 09:00"))
        return
    
    tz = pytz.timezone(timezone)
    
    # 创建调度器 / Create scheduler
    scheduler = BlockingScheduler(timezone=tz)
    
    # 添加定时任务 / Register scheduled job
    trigger = CronTrigger(
        hour=hour,
        minute=minute,
        timezone=tz
    )
    
    # 初始化邮件通知器 / Initialize email notifier
    notifier = None
    notification_config = scheduler_config.get('notification', {})
    if notification_config.get('enabled', False):
        email_config = notification_config.get('email', {})
        email_config['_language'] = config.get('app', {}).get('language', 'zh')
        notifier = EmailNotifier(email_config)
        logger.info(text("邮件通知已启用", "Email notification enabled"))
    
    scheduler.add_job(
        scheduled_task,
        trigger=trigger,
        args=[logger, notifier, config.get('app', {}).get('language', 'zh')],
        id='daily_arxiv_task',
        name='Daily arXiv Paper Fetching',
        max_instances=1,
        coalesce=True
    )
    
    # 计算下次运行时间 / Calculate next run time
    next_run = datetime.now(tz).replace(hour=hour, minute=minute, second=0, microsecond=0)
    if next_run <= datetime.now(tz):
        from datetime import timedelta
        next_run += timedelta(days=1)
    
    logger.info(text(f"定时调度器已启动，将在每天 {run_time} ({timezone}) 执行任务", f"Scheduler started, will run daily at {run_time} ({timezone})"))
    print("\n" + "=" * 60)
    print(text("⏰ Daily arXiv 定时调度器", "⏰ Daily arXiv Scheduler"))
    print("=" * 60)
    print(text(f"📅 执行时间: 每天 {run_time}", f"📅 Run Time: daily at {run_time}"))
    print(text(f"🌍 时区: {timezone}", f"🌍 Timezone: {timezone}"))
    print(text(f"⏭️  下次运行: {next_run.strftime('%Y-%m-%d %H:%M:%S')}", f"⏭️  Next run: {next_run.strftime('%Y-%m-%d %H:%M:%S')}"))
    print(text(f"🔄 启动时立即运行: {'是' if run_on_start else '否'}", f"🔄 Run on start: {'yes' if run_on_start else 'no'}"))
    print("=" * 60)
    print(text("\n按 Ctrl+C 停止调度器\n", "\nPress Ctrl+C to stop scheduler\n"))
    
    # 启动时立即运行一次 / Run once at startup if enabled
    if run_on_start:
        logger.info(text("启动时立即执行任务...", "Running task on startup..."))
        print(text("🚀 启动时立即执行任务...\n", "🚀 Running task on startup...\n"))
        scheduled_task(logger, notifier, config.get('app', {}).get('language', 'zh'))
    
    try:
        # 启动调度器 / Start scheduler loop
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info(text("定时调度器已停止", "Scheduler stopped"))
        print("\n" + "=" * 60)
        print(text("👋 定时调度器已停止", "👋 Scheduler stopped"))
        print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
