"""
邮件通知模块

发送任务执行结果通知
"""
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from pathlib import Path
import logging


class EmailNotifier:
    """邮件通知器"""
    
    def __init__(self, config):
        """
        初始化邮件通知器
        
        Args:
            config: 邮件配置字典
        """
        self.smtp_server = config.get('smtp_server', 'smtp.gmail.com')
        self.smtp_port = config.get('smtp_port', 587)
        self.sender = config.get('sender', '')
        self.password = os.getenv('EMAIL_PASSWORD', config.get('password', ''))
        self.recipients = config.get('recipients', [])
        self.on_success = config.get('on_success', True)
        self.on_failure = config.get('on_failure', True)
        self.language = str(config.get('_language', 'zh')).strip().lower()
        self.text = (lambda zh, en: en) if self.language.startswith('en') else (lambda zh, en: zh)
        
        self.logger = logging.getLogger(__name__)
    
    def send_notification(self, success=True, stats=None, error_msg=None, duration=0):
        """
        发送通知邮件
        
        Args:
            success: 任务是否成功
            stats: 统计信息字典
            error_msg: 错误信息
            duration: 执行耗时（秒）
        
        Returns:
            bool: 是否发送成功
        """
        # 检查是否需要发送 / Check whether notification is needed
        if success and not self.on_success:
            return True
        if not success and not self.on_failure:
            return True
        
        # 检查配置 / Validate config
        if not self.sender or not self.recipients:
            self.logger.warning(self.text(
                "邮件发送者或收件人未配置，跳过邮件通知",
                "Email sender or recipients are not configured, skipping email notification"
            ))
            return False
        
        if not self.password:
            self.logger.warning(self.text("邮件密码未配置，跳过邮件通知", "Email password is not configured, skipping email notification"))
            return False
        
        try:
            # 创建邮件 / Build message
            msg = MIMEMultipart('alternative')
            msg['From'] = self.sender
            msg['To'] = ', '.join(self.recipients)
            msg['Subject'] = self._get_subject(success)
            
            # 生成邮件内容 / Generate email content
            html_content = self._generate_html_content(success, stats, error_msg, duration)
            text_content = self._generate_text_content(success, stats, error_msg, duration)
            
            # 添加内容 / Attach content
            msg.attach(MIMEText(text_content, 'plain', 'utf-8'))
            msg.attach(MIMEText(html_content, 'html', 'utf-8'))
            
            # 发送邮件 / Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender, self.password)
                server.send_message(msg)
            
            self.logger.info(self.text(
                f"邮件通知发送成功: {', '.join(self.recipients)}",
                f"Email notification sent successfully: {', '.join(self.recipients)}"
            ))
            return True
            
        except Exception as e:
            self.logger.error(self.text(f"邮件发送失败: {str(e)}", f"Failed to send email: {str(e)}"), exc_info=True)
            return False
    
    def _get_subject(self, success):
        """生成邮件主题"""
        date_str = datetime.now().strftime('%Y-%m-%d')
        if success:
            return self.text(f"✅ Daily arXiv 任务成功 - {date_str}", f"✅ Daily arXiv Task Succeeded - {date_str}")
        else:
            return self.text(f"❌ Daily arXiv 任务失败 - {date_str}", f"❌ Daily arXiv Task Failed - {date_str}")
    
    def _generate_text_content(self, success, stats, error_msg, duration):
        """生成纯文本内容"""
        date_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        content = []
        content.append("=" * 60)
        content.append(self.text("Daily arXiv 任务执行报告", "Daily arXiv Task Report"))
        content.append("=" * 60)
        content.append(self.text(f"执行时间: {date_str}", f"Execution time: {date_str}"))
        content.append(self.text(
            f"执行结果: {'✅ 成功' if success else '❌ 失败'}",
            f"Result: {'✅ Success' if success else '❌ Failed'}"
        ))
        content.append(self.text(f"执行耗时: {duration:.2f} 秒", f"Duration: {duration:.2f} seconds"))
        content.append("")
        
        if success and stats:
            content.append(self.text("统计信息:", "Statistics:"))
            content.append("-" * 60)
            content.append(self.text(f"  论文数量: {stats.get('papers_count', 0)}", f"  Papers: {stats.get('papers_count', 0)}"))
            content.append(self.text(f"  总结数量: {stats.get('summaries_count', 0)}", f"  Summaries: {stats.get('summaries_count', 0)}"))
            content.append(self.text(f"  研究类别: {stats.get('categories_count', 0)}", f"  Categories: {stats.get('categories_count', 0)}"))
            content.append(self.text(f"  关键词数: {stats.get('keywords_count', 0)}", f"  Keywords: {stats.get('keywords_count', 0)}"))
            content.append("")
        
        if not success and error_msg:
            content.append(self.text("错误信息:", "Error details:"))
            content.append("-" * 60)
            content.append(error_msg)
            content.append("")
        
        content.append("=" * 60)
        content.append(self.text("访问 Web 界面: http://localhost:5000", "Open Web UI: http://localhost:5000"))
        content.append("=" * 60)
        
        return '\n'.join(content)
    
    def _generate_html_content(self, success, stats, error_msg, duration):
        """生成 HTML 内容"""
        date_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        status_color = '#28a745' if success else '#dc3545'
        status_icon = '✅' if success else '❌'
        status_text = '成功' if success else '失败'
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .header {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 30px;
                    border-radius: 10px;
                    text-align: center;
                    margin-bottom: 30px;
                }}
                .header h1 {{
                    margin: 0;
                    font-size: 24px;
                }}
                .status {{
                    background: {status_color};
                    color: white;
                    padding: 15px;
                    border-radius: 8px;
                    text-align: center;
                    font-size: 20px;
                    margin-bottom: 20px;
                }}
                .info {{
                    background: #f8f9fa;
                    padding: 20px;
                    border-radius: 8px;
                    margin-bottom: 20px;
                }}
                .info-item {{
                    padding: 10px 0;
                    border-bottom: 1px solid #dee2e6;
                }}
                .info-item:last-child {{
                    border-bottom: none;
                }}
                .info-label {{
                    font-weight: bold;
                    color: #666;
                }}
                .stats {{
                    display: grid;
                    grid-template-columns: repeat(2, 1fr);
                    gap: 15px;
                    margin: 20px 0;
                }}
                .stat-card {{
                    background: white;
                    padding: 20px;
                    border-radius: 8px;
                    text-align: center;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }}
                .stat-value {{
                    font-size: 32px;
                    font-weight: bold;
                    color: #667eea;
                }}
                .stat-label {{
                    color: #666;
                    margin-top: 5px;
                }}
                .error {{
                    background: #f8d7da;
                    color: #721c24;
                    padding: 15px;
                    border-radius: 8px;
                    border-left: 4px solid #dc3545;
                    margin: 20px 0;
                }}
                .footer {{
                    text-align: center;
                    margin-top: 30px;
                    padding-top: 20px;
                    border-top: 1px solid #dee2e6;
                    color: #666;
                }}
                .button {{
                    display: inline-block;
                    padding: 12px 30px;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    text-decoration: none;
                    border-radius: 25px;
                    margin-top: 20px;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>📊 Daily arXiv 任务执行报告</h1>
            </div>
            
            <div class="status">
                {status_icon} 执行结果: {status_text}
            </div>
            
            <div class="info">
                <div class="info-item">
                    <span class="info-label">执行时间:</span> {date_str}
                </div>
                <div class="info-item">
                    <span class="info-label">执行耗时:</span> {duration:.2f} 秒
                </div>
            </div>
        """
        
        if success and stats:
            html += """
            <div class="stats">
                <div class="stat-card">
                    <div class="stat-value">{papers}</div>
                    <div class="stat-label">📄 论文数量</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{summaries}</div>
                    <div class="stat-label">📝 总结数量</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{categories}</div>
                    <div class="stat-label">🏷️ 研究类别</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{keywords}</div>
                    <div class="stat-label">🔑 关键词数</div>
                </div>
            </div>
            """.format(
                papers=stats.get('papers_count', 0),
                summaries=stats.get('summaries_count', 0),
                categories=stats.get('categories_count', 0),
                keywords=stats.get('keywords_count', 0)
            )
        
        if not success and error_msg:
            html += f"""
            <div class="error">
                <strong>错误信息:</strong><br>
                {error_msg.replace(chr(10), '<br>')}
            </div>
            """
        
        html += """
            <div class="footer">
                <a href="http://localhost:5000" class="button">📊 查看 Web 界面</a>
                <p style="margin-top: 20px; font-size: 12px;">
                    这是一封自动发送的邮件，请勿回复。
                </p>
            </div>
        </body>
        </html>
        """
        
        return html


def send_test_email(config):
    """发送测试邮件"""
    notifier = EmailNotifier(config)
    
    test_stats = {
        'papers_count': 20,
        'summaries_count': 20,
        'categories_count': 2,
        'keywords_count': 50
    }
    
    print("\n📧 发送测试邮件...")
    success = notifier.send_notification(
        success=True,
        stats=test_stats,
        duration=120.5
    )
    
    if success:
        print("✅ 测试邮件发送成功！")
    else:
        print("❌ 测试邮件发送失败！")
    
    return success
