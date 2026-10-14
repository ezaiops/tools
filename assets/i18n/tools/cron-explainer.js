/* Cron explainer page dictionary. Chrome strings live in common.js. */
window.I18N_DICTS = window.I18N_DICTS || [];
window.I18N_DICTS.push({
  "Cron expression explainer": "Cron 表达式解释器",
  "Paste a cron expression and get a plain-English description plus the next ten times it will fire in your local timezone. Works with standard five-field cron and special strings like @daily.": "粘贴 cron 表达式，得到人话描述，以及它在本地时区未来十次触发的时间。支持标准五字段 cron 和 @daily 之类的特殊字符串。",
  "Cron expression": "Cron 表达式",
  "minute hour day-of-month month day-of-week": "分 时 日 月 周",
  "Try:": "试试：",
  "every minute": "每分钟",
  "every 5 min": "每 5 分钟",
  "hourly": "每小时",
  "weekday 9am": "工作日 9 点",
  "1st of month": "每月 1 日",
  "Explain": "解释",
  "In plain English": "人话描述",
  "Next 10 runs (your local timezone)": "未来 10 次运行（本地时区）",
  "Field breakdown": "字段分解",
  "Field": "字段",
  "Expression": "表达式",
  "Allowed values": "允许值",
  "Expands to": "展开为",
  "Allowed": "取值范围",
  "Special characters": "特殊字符",
  "Minute": "分钟",
  "Hour": "小时",
  "Day of month": "日",
  "Month": "月",
  "Day of week": "周",
  "1-12 or JAN-DEC": "1-12 或 JAN-DEC",
  "0-7 (0 and 7 = Sunday) or SUN-SAT": "0-7（0 和 7 均为周日）或 SUN-SAT",

  "Cron syntax reference": "Cron 语法参考",

  "el:Special strings: @reboot runs once at startup; @yearly/@annually = 0 0 1 1 *; @monthly = 0 0 1 * *; @weekly = 0 0 * * 0; @daily/@midnight = 0 0 * * *; @hourly = 0 * * * *.": "特殊字符串：<code>@reboot</code> 启动时运行一次；<code>@yearly</code>/<code>@annually</code> = <code>0 0 1 1 *</code>；<code>@monthly</code> = <code>0 0 1 * *</code>；<code>@weekly</code> = <code>0 0 * * 0</code>；<code>@daily</code>/<code>@midnight</code> = <code>0 0 * * *</code>；<code>@hourly</code> = <code>0 * * * *</code>。",
  "el:The day-of-month and day-of-week fields are OR'ed when both are restricted — 0 0 1 * 1 fires on the 1st of the month and every Monday. When both are * they behave as \"every day\".": "当月和周两个字段都被限制时，它们之间是「或」的关系——<code>0 0 1 * 1</code> 会在每月 1 日<em>以及</em>每个周一触发。两者都为 <code>*</code> 时才表示「每天」。",

  "Which timezone are the next run times shown in?": "未来运行时间显示的是哪个时区？",
  "Does this support Quartz 6/7-field expressions?": "支持 Quartz 的 6/7 字段表达式吗？",
  "My crontab didn't run — what should I check?": "我的 crontab 没有执行，该检查什么？",
  "el:Your browser's local timezone. Cron on a server typically runs in UTC (or the system timezone), so if you schedule 0 9 * * * on a UTC box it fires at local midnight for UTC+9 — always check the server's timezone before trusting a schedule.": "你的浏览器本地时区。服务器上的 cron 通常以 UTC（或系统时区）运行，所以 UTC 机器上的 <code>0 9 * * *</code> 对 UTC+9 的用户是本地零点触发——信任排程之前，先确认服务器的时区。",
  "el:No — this explainer targets standard five-field Unix cron. Quartz expressions add seconds and year fields (e.g. 0 0 9 * * ? 2026) and also use ?, which plain cron does not understand.": "不支持——本解释器面向标准五字段 Unix cron。Quartz 表达式额外带有秒和年字段（例如 <code>0 0 9 * * ? 2026</code>），还使用 <code>?</code>，普通 cron 不认识它。",
  "el:The three usual suspects: the cron daemon isn't running or the user's crontab isn't installed (crontab -l), paths inside the command aren't absolute, and the timezone differs from your expectation. Percent signs in crontab commands must be escaped as \\%.": "三个常见嫌疑人：cron 守护进程没运行或用户的 crontab 没安装（<code>crontab -l</code> 看不到就是没装）、命令里的路径不是绝对路径、时区和预期不一致。另外 crontab 命令中的百分号必须转义为 <code>\\%</code>。"
});
